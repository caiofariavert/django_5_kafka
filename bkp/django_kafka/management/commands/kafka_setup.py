from django.core.management.base import BaseCommand

from django_kafka.admin import SetupDjangoKafka


class Command(BaseCommand):
    def handle(self, *args, **options) -> None:
        SetupDjangoKafka().setup()
