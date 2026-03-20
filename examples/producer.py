import asyncio

from django_kafka.django_kafka.producer import close_producer, producer

# settings.KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
# settings.KAFKA_CLIENT_ID = "client_id"


async def main():
    # Simple producer
    info = await producer("topic", "message")
    print(info)

    # Producer with explicit key
    info = await producer("topic", "message", key="my-key")
    print(info)

    # Fechar o producer ao encerrar a aplicação
    await close_producer()


asyncio.run(main())
