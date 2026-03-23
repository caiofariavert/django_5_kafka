import asyncio
import logging
import socket
from types import FunctionType
from uuid import uuid4

from confluent_kafka.aio import AIOProducer
from django.conf import settings

# Configura o logger específico para a sua biblioteca
logger = logging.getLogger(__name__)


def producer(
    topic: str, message: str, key: str = None, on_delivery: FunctionType = None
) -> None:

    if key is None:
        key: str = str(uuid4())

    conf = {
        "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVER,
        "client.id": socket.gethostname(),
    }

    producer = AIOProducer(conf)

    headers = {
        "producer_id": settings.KAFKA_CLIENT_ID,
        "hostname": socket.gethostname(),
    }
    delivery_info = {}

    def delivery_report(err, msg):
        """
        Reports the success or failure of a message delivery.
        Args:
            err (KafkaError): The error that occurred on None on success.
            msg (Message): The message that was produced or failed.
        """

        if err is not None:
            logger.error("Delivery failed for User record {}: {}".format(msg.key(), err))
            delivery_info['error'] = str(err)
        else:
            delivery_info.update({
                "topic": msg.topic(),
                "key": msg.key().decode() if msg.key() else None,
                "message": msg.value().decode() if msg.value() else None,
                "partition": msg.partition(),
                "offset": msg.offset(),
            })

    async def produce_message(producer: AIOProducer, topic, key, message, on_delivery, headers):
        try:
            # produce() returns a Future; first await the coroutine to get the Future,
            # then await the Future to get the delivered Message.
            delivery_future = await producer.produce(
                topic,
                key=key,
                value=message,
                on_delivery=on_delivery or delivery_report,
                headers=headers,
            )
            delivered_msg = await delivery_future
            # Optionally flush any remaining buffered messages before shutdown
            await producer.flush()
        finally:
            await producer.close()
        return delivered_msg

    delivery_info = asyncio.run(produce_message(producer, topic, key, message, on_delivery, headers))

    return delivery_info
