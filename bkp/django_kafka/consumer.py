import logging

from confluent_kafka import Consumer, Message
from django.conf import settings

# Configura o logger específico para a sua biblioteca
logger = logging.getLogger(__name__)

KAFKA_RUNNING: bool = True


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

    consumer: Consumer = Consumer(conf)

    topics: list[str] = [key for key, _ in settings.KAFKA_TOPICS.items()]

    consumer.subscribe(topics)

    try:
        while KAFKA_RUNNING:
            msg: Message = consumer.poll(1.0)

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
                consumer.commit(message=msg)
                continue

            # call the callback string as function
            dynamic_call_action(callback, consumer, msg)
    except Exception as e:
        # print(e)
        logger.error(e)
    finally:
        consumer.close()


def kafka_consumer_shutdown() -> None:
    global KAFKA_RUNNING
    KAFKA_RUNNING = False


def dynamic_call_action(action: str, consumer: Consumer, msg: Message) -> None:

    # get path removing last part splited by dot
    module_path: str = ".".join(action.split(".")[:-1])

    # get path keeping last part splited by dot
    function_name: str = action.split(".")[-1]

    # import module
    try:
        module = __import__(module_path, fromlist=[function_name])
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
        function(consumer=consumer, msg=msg)
    except:
        # print("Error calling action: {}".format(action))
        logger.error("Error calling action: {}".format(action))
        return
