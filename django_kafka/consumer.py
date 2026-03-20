import asyncio
import importlib
import logging

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.structs import ConsumerRecord, OffsetAndMetadata
from django.conf import settings

logger = logging.getLogger(__name__)

_consumer_instance: AIOKafkaConsumer | None = None


def _parse_kafka_topics() -> tuple[dict[str, str], dict[str, list[str]]]:
    """
    Parse KAFKA_TOPICS configuração e retorna:
    - topic_to_callback: {tópico → função}
    - queue_topics: {fila → [tópicos]}
    """
    topic_to_callback = {}
    queue_topics = {}

    for queue_name, topics_dict in settings.KAFKA_TOPICS.items():
        if isinstance(topics_dict, dict):
            queue_topics[queue_name] = list(topics_dict.keys())
            topic_to_callback.update(topics_dict)
        else:
            # backward compatibility: valor direto é a função
            topic_to_callback[queue_name] = topics_dict
            if "default" not in queue_topics:
                queue_topics["default"] = []
            queue_topics["default"].append(queue_name)

    return topic_to_callback, queue_topics


async def kafka_consumer_run() -> None:
    global _consumer_instance

    topic_to_callback, queue_topics = _parse_kafka_topics()

    all_topics = list(topic_to_callback.keys())
    consumer = AIOKafkaConsumer(
        *all_topics,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
        group_id=settings.KAFKA_GROUP_ID,
        auto_offset_reset=getattr(settings, "KAFKA_OFFSET_RESET", "earliest"),
        enable_auto_commit=False,
    )

    _consumer_instance = consumer
    await consumer.start()

    # Criar fila e worker para cada fila
    queues = {queue_name: asyncio.Queue() for queue_name in queue_topics}
    reverse_queue_map = {}
    for queue_name, topics in queue_topics.items():
        for topic in topics:
            reverse_queue_map[topic] = queue_name

    workers = [
        asyncio.create_task(
            _queue_worker(queue_name, queues[queue_name], consumer, topic_to_callback)
        )
        for queue_name in queue_topics
    ]

    try:
        async for msg in consumer:
            queue_name = reverse_queue_map.get(msg.topic, "default")
            await queues[queue_name].put(msg)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(e)
    finally:
        # Sinal para workers pararem
        for queue in queues.values():
            await queue.put(None)

        # Aguarda conclusão dos workers
        await asyncio.gather(*workers, return_exceptions=True)
        await consumer.stop()
        _consumer_instance = None


def kafka_consumer_shutdown() -> None:
    global _consumer_instance
    if _consumer_instance is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_consumer_instance.stop())
        except RuntimeError:
            asyncio.run(_consumer_instance.stop())


async def _queue_worker(
    queue_name: str,
    queue: asyncio.Queue,
    consumer: AIOKafkaConsumer,
    topic_to_callback: dict[str, str],
) -> None:
    """Worker que processa mensagens de uma fila sequencialmente"""
    while True:
        msg = await queue.get()
        if msg is None:  # Sinal para parar
            break

        await _dispatch(msg, consumer, topic_to_callback, queue_name)


async def _dispatch(
    msg: ConsumerRecord,
    consumer: AIOKafkaConsumer,
    topic_to_callback: dict[str, str],
    queue_name: str,
) -> None:
    callback: str = topic_to_callback.get(msg.topic)

    if callback is None:
        logger.error("No callback found for topic: {}".format(msg.topic))
        return

    if callback == "":
        tp = TopicPartition(msg.topic, msg.partition)
        await consumer.commit({tp: OffsetAndMetadata(msg.offset + 1, "")})
        return

    module_path: str = ".".join(callback.split(".")[:-1])
    function_name: str = callback.split(".")[-1]

    logger.debug(
        "Attempting to load callback: {} | module: {} | function: {}".format(
            callback, module_path, function_name
        )
    )

    try:
        module = importlib.import_module(module_path)
        logger.debug("Module loaded successfully: {}".format(module_path))
        function = getattr(module, function_name)
    except AttributeError:
        logger.error(
            "No function '{}' found in module '{}' | Available: {}".format(
                function_name, module_path, dir(module)
            )
        )
        return
    except Exception as e:
        logger.error(
            "Error importing callback '{}' | module: {} | error: {}".format(
                callback, module_path, e
            )
        )
        return

    try:
        loop = asyncio.get_running_loop()

        if asyncio.iscoroutinefunction(function):
            # Roda em thread separada com seu próprio event loop
            # Garante que o event loop principal nunca seja bloqueado,
            # permitindo que outras filas processem em paralelo
            await loop.run_in_executor(
                None,
                lambda: asyncio.run(function(consumer=consumer, msg=msg)),
            )
        else:
            await loop.run_in_executor(
                None, lambda: function(consumer=consumer, msg=msg)
            )
        tp = TopicPartition(msg.topic, msg.partition)
        await consumer.commit({tp: OffsetAndMetadata(msg.offset + 1, "")})
        logger.debug(
            "Message processed from queue '{}': topic={}".format(queue_name, msg.topic)
        )
    except Exception as e:
        logger.error(
            "Error calling action {} in queue '{}': {}".format(callback, queue_name, e)
        )
