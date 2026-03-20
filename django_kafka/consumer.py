import asyncio
import importlib
import logging
from concurrent.futures import ThreadPoolExecutor

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.structs import OffsetAndMetadata
from django.conf import settings

logger = logging.getLogger(__name__)

_consumer_instances: dict[str, AIOKafkaConsumer] = {}
_executor: ThreadPoolExecutor | None = None


def _parse_kafka_topics() -> tuple[dict[str, str], dict[str, list[str]]]:
    """Parse KAFKA_TOPICS e retorna topic_to_callback e queue_topics"""
    topic_to_callback = {}
    queue_topics = {}

    for queue_name, topics_dict in settings.KAFKA_TOPICS.items():
        if isinstance(topics_dict, dict):
            queue_topics[queue_name] = list(topics_dict.keys())
            topic_to_callback.update(topics_dict)
        else:
            topic_to_callback[queue_name] = topics_dict
            if "default" not in queue_topics:
                queue_topics["default"] = []
            queue_topics["default"].append(queue_name)

    return topic_to_callback, queue_topics


async def kafka_consumer_run() -> None:
    global _consumer_instances, _executor

    topic_to_callback, queue_topics = _parse_kafka_topics()
    _executor = ThreadPoolExecutor(max_workers=50)

    # Criar um consumer por fila (ou grupo de tópicos)
    consumers_tasks = []
    for queue_name, topics in queue_topics.items():
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
            group_id=settings.KAFKA_GROUP_ID,
            auto_offset_reset=getattr(settings, "KAFKA_OFFSET_RESET", "earliest"),
            enable_auto_commit=False,
            # Aumentar timeouts para handlers lentos
            session_timeout_ms=60000 * 10,  # 10 min (default 10s)
            heartbeat_interval_ms=60000 * 10,  # 10 min (default 3s)
            max_poll_interval_ms=60000 * 10,  # 10 min (default 5 min)

        )
        _consumer_instances[queue_name] = consumer
        await consumer.start()

        # Cada fila tem sua task de consumo
        task = asyncio.create_task(
            _consume_queue(queue_name, consumer, topic_to_callback)
        )
        consumers_tasks.append(task)

    try:
        await asyncio.gather(*consumers_tasks)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Consumer error: {e}")
    finally:
        await _stop_all_consumers()


async def _consume_queue(
    queue_name: str,
    consumer: AIOKafkaConsumer,
    topic_to_callback: dict[str, str],
) -> None:
    """Consume mensagens de uma fila específica"""
    try:
        async for msg in consumer:
            await _dispatch(msg, consumer, topic_to_callback, queue_name)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error consuming queue '{queue_name}': {e}")


async def _dispatch(
    msg,
    consumer: AIOKafkaConsumer,
    topic_to_callback: dict[str, str],
    queue_name: str,
) -> None:
    """Processa uma mensagem"""
    callback: str = topic_to_callback.get(msg.topic)

    if callback is None:
        logger.error(f"No callback found for topic: {msg.topic}")
        return

    if callback == "":
        tp = TopicPartition(msg.topic, msg.partition)
        await consumer.commit({tp: OffsetAndMetadata(msg.offset + 1, "")})
        return

    module_path = ".".join(callback.split(".")[:-1])
    function_name = callback.split(".")[-1]

    try:
        module = importlib.import_module(module_path)
        function = getattr(module, function_name)
    except (ImportError, AttributeError) as e:
        logger.error(f"Cannot load callback '{callback}': {e}")
        return

    try:
        loop = asyncio.get_running_loop()

        if asyncio.iscoroutinefunction(function):
            await loop.run_in_executor(
                _executor,
                lambda: asyncio.run(function(consumer=consumer, msg=msg)),
            )
        else:
            await loop.run_in_executor(
                _executor, lambda: function(consumer=consumer, msg=msg)
            )

        tp = TopicPartition(msg.topic, msg.partition)
        await consumer.commit({tp: OffsetAndMetadata(msg.offset + 1, "")})
        logger.debug(f"Message processed from queue '{queue_name}': {msg.topic}")
    except Exception as e:
        logger.error(f"Error calling action {callback} in queue '{queue_name}': {e}")


async def _stop_all_consumers() -> None:
    """Fecha todos os consumers"""
    for queue_name, consumer in _consumer_instances.items():
        try:
            await consumer.stop()
            logger.info(f"Consumer for queue '{queue_name}' stopped")
        except Exception as e:
            logger.error(f"Error stopping consumer for queue '{queue_name}': {e}")
    _consumer_instances.clear()

    if _executor:
        _executor.shutdown(wait=True)


def kafka_consumer_shutdown() -> None:
    """Shutdown hook"""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_stop_all_consumers())
    except RuntimeError:
        asyncio.run(_stop_all_consumers())
