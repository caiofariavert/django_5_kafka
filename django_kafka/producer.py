import logging
import socket
from types import FunctionType
from uuid import uuid4

from confluent_kafka import Producer
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

    producer = Producer(conf)

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
            logger.error(f"Message delivery failed: {err}")
            delivery_info['error'] = str(err)
        else:
            logger.info(
                f"Message delivered to {msg.topic()} [partition {msg.partition()}] @ offset {msg.offset()}"
            )
            delivery_info.update({
                "topic": msg.topic(),
                "key": msg.key().decode() if msg.key() else None,
                "message": msg.value().decode() if msg.value() else None,
                "partition": msg.partition(),
                "offset": msg.offset(),
            })

    producer.produce(
        topic,
        key=key,
        value=message,
        on_delivery=on_delivery or delivery_report,
        headers=headers,
    )
    producer.flush()

    return delivery_info
