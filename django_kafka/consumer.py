import asyncio
import importlib
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.structs import ConsumerRecord
from django.conf import settings

logger = logging.getLogger(__name__)

_consumer_instance: AIOKafkaConsumer | None = None


async def kafka_consumer_run() -> None:
    global _consumer_instance

    consumer = AIOKafkaConsumer(
        *list(settings.KAFKA_TOPICS.keys()),
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
        group_id=settings.KAFKA_GROUP_ID,
        auto_offset_reset=getattr(settings, "KAFKA_OFFSET_RESET", "earliest"),
        enable_auto_commit=False,
    )

    _consumer_instance = consumer
    await consumer.start()

    try:
        async for msg in consumer:
            await _dispatch(msg, consumer)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(e)
    finally:
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


async def _dispatch(msg: ConsumerRecord, consumer: AIOKafkaConsumer) -> None:
    callback: str = settings.KAFKA_TOPICS.get(msg.topic)

    if callback is None:
        logger.error("No callback found for topic: {}".format(msg.topic))
        return

    if callback == "":
        await consumer.commit()
        return

    module_path: str = ".".join(callback.split(".")[:-1])
    function_name: str = callback.split(".")[-1]

    try:
        module = importlib.import_module(module_path)
    except ImportError:
        logger.error("No module found for action: {}".format(callback))
        return

    try:
        function = getattr(module, function_name)
    except AttributeError:
        logger.error("No function found for action: {}".format(callback))
        return

    try:
        if asyncio.iscoroutinefunction(function):
            await function(consumer=consumer, msg=msg)
        else:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, lambda: function(consumer=consumer, msg=msg)
            )
        await consumer.commit()
    except Exception as e:
        logger.error("Error calling action {}: {}".format(callback, e))
