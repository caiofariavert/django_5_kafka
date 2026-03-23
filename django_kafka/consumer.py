import asyncio
import importlib
import inspect
import logging
from concurrent.futures import ThreadPoolExecutor

from confluent_kafka import Consumer, Message
from confluent_kafka.aio import AIOConsumer
from django.conf import settings

# Configura o logger específico para a sua biblioteca
logger = logging.getLogger(__name__)
_executor: ThreadPoolExecutor | None = None


KAFKA_RUNNING: bool = True


async def __run_consumer(conf: dict) -> None:
    global _executor
    _executor = ThreadPoolExecutor(max_workers=10)
    consumer: AIOConsumer = AIOConsumer(conf)
    topics: list[str] = [key for key, _ in settings.KAFKA_TOPICS.items()]

    await consumer.subscribe(topics)

    try:
        while KAFKA_RUNNING:
            msg: Message = await consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                # print("Consumer error: {}".format(msg.error()))
                logger.error("Consumer error: {}".format(msg.error()))
                continue
            callback: str = settings.KAFKA_TOPICS.get(msg.topic())

            if callback is None:
                # print("No callback found for topic: {}".format(msg.topic()))
                logger.error("No callback found for topic: {}".format(msg.topic()))
                continue

            if callback == "":
                # Skip empty callbacks
                # logger.warning(
                #     "Empty callback for topic: {}. Skipping.".format(msg.topic())
                # )
                await consumer.commit(message=msg)
                continue

            # call the callback string as function
            await dynamic_call_action(callback, consumer, msg)
    except Exception as e:
        # print(e)
        logger.error(e)
    finally:
        await consumer.close()
        if _executor:
            _executor.shutdown(wait=True)


def kafka_consumer_run() -> None:

    conf = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVER,
        "group.id": settings.KAFKA_GROUP_ID,
        "auto.offset.reset": (
            settings.KAFKA_OFFSET_RESET
            if hasattr(settings, "KAFKA_OFFSET_RESET")
            else "earliest"
        ),
    }

    asyncio.run(__run_consumer(conf))


def kafka_consumer_shutdown() -> None:
    global KAFKA_RUNNING
    KAFKA_RUNNING = False


async def dynamic_call_action(action: str, consumer: Consumer, msg: Message) -> None:

    # get path removing last part splited by dot
    module_path: str = ".".join(action.split(".")[:-1])

    # get path keeping last part splited by dot
    function_name: str = action.split(".")[-1]

    # import module
    try:
        # module = __import__(module_path, fromlist=[function_name])
        module = importlib.import_module(module_path)
    except:
        # print("No module found for action: {}".format(action))
        logger.error("No module found for action: {}".format(action))
        return

    # get function from module
    try:
        function = getattr(module, function_name)
    except:
        # print("No function found for action: {}".format(action))
        logger.error("No function found for action: {}".format(action))
        return

    # call function
    try:
        loop = asyncio.get_running_loop()

        if inspect.iscoroutinefunction(function):
            await loop.run_in_executor(
                _executor,
                lambda: asyncio.run(function(consumer=consumer, msg=msg)),
            )
        else:
            await loop.run_in_executor(
                _executor, lambda: function(consumer=consumer, msg=msg)
            )
    except:
        # print("Error calling action: {}".format(action))
        logger.error("Error calling action: {}".format(action))
        return
