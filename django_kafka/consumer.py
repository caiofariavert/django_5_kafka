import asyncio
import importlib
import logging

from confluent_kafka import Consumer, Message
from django.conf import settings

logger = logging.getLogger(__name__)

KAFKA_RUNNING: bool = True


async def kafka_consumer_run() -> None:

    conf = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVER,
        "group.id": settings.KAFKA_GROUP_ID,
        "auto.offset.reset": (
            settings.KAFKA_OFFSET_RESET
            if hasattr(settings, "KAFKA_OFFSET_RESET")
            else "earliest"
        ),
    }

    consumer: Consumer = Consumer(conf)
    topics: list[str] = list(settings.KAFKA_TOPICS.keys())
    consumer.subscribe(topics)

    loop = asyncio.get_event_loop()

    try:
        while KAFKA_RUNNING:
            # poll() é bloqueante (C extension) — executa em thread para não bloquear o event loop
            msg: Message = await loop.run_in_executor(None, consumer.poll, 1.0)

            if msg is None:
                continue
            if msg.error():
                logger.error("Consumer error: {}".format(msg.error()))
                continue

            callback: str = settings.KAFKA_TOPICS.get(msg.topic())

            if callback is None:
                logger.error("No callback found for topic: {}".format(msg.topic()))
                continue

            if callback == "":
                consumer.commit(message=msg)
                continue

            await dynamic_call_action(callback, consumer, msg)
    except Exception as e:
        logger.error(e)
    finally:
        consumer.close()


def kafka_consumer_shutdown() -> None:
    global KAFKA_RUNNING
    KAFKA_RUNNING = False


async def dynamic_call_action(action: str, consumer: Consumer, msg: Message) -> None:

    module_path: str = ".".join(action.split(".")[:-1])
    function_name: str = action.split(".")[-1]

    try:
        module = importlib.import_module(module_path)
    except ImportError:
        logger.error("No module found for action: {}".format(action))
        return

    try:
        function = getattr(module, function_name)
    except AttributeError:
        logger.error("No function found for action: {}".format(action))
        return

    try:
        if asyncio.iscoroutinefunction(function):
            await function(consumer=consumer, msg=msg)
        else:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: function(consumer=consumer, msg=msg)
            )
    except Exception as e:
        logger.error("Error calling action {}: {}".format(action, e))
