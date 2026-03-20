import asyncio

from django.core.management.base import BaseCommand

from django_kafka.consumer import kafka_consumer_run


class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        asyncio.run(kafka_consumer_run())
