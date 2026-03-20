import asyncio
import logging
import socket
from uuid import uuid4

from aiokafka import AIOKafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)

_producer_instance: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER,
            client_id=getattr(settings, "KAFKA_CLIENT_ID", socket.gethostname()),
        )
        await _producer_instance.start()
    return _producer_instance


async def close_producer() -> None:
    global _producer_instance
    if _producer_instance is not None:
        await _producer_instance.stop()
        _producer_instance = None


async def aproducer(
    topic: str,
    message: str,
    key: str = None,
) -> dict:
    if key is None:
        key = str(uuid4())

    headers = [
        ("producer_id", getattr(settings, "KAFKA_CLIENT_ID", "").encode()),
        ("hostname", socket.gethostname().encode()),
    ]

    kafka_producer = await get_producer()

    try:
        metadata = await kafka_producer.send_and_wait(
            topic,
            value=message.encode() if isinstance(message, str) else message,
            key=key.encode() if isinstance(key, str) else key,
            headers=headers,
        )
        return {
            "topic": metadata.topic,
            "partition": metadata.partition,
            "offset": metadata.offset,
            "key": key,
            "message": message,
        }
    except Exception as e:
        logger.error("Delivery failed for topic {}: {}".format(topic, e))
        return {"error": str(e)}


def producer(
    topic: str,
    message: str,
    key: str = None,
) -> dict:
    return asyncio.run(aproducer(topic, message, key))
