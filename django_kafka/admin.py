import asyncio
import logging

from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from django.conf import settings

logger = logging.getLogger(__name__)


class SetupDjangoKafka:

    async def create_topics(self, admin_client: AIOKafkaAdminClient, topics: list[str]) -> None:
        """Create topics asynchronously"""
        new_topics = [
            NewTopic(topic, num_partitions=3, replication_factor=1)
            for topic in topics
        ]

        try:
            await admin_client.create_topics(new_topics, validate_only=False)
            for topic in topics:
                logger.info("Topic {} created".format(topic))
        except Exception as e:
            logger.error("Failed to create topics: {}".format(e))

    async def setup_async(self) -> None:
        """Setup topics asynchronously"""
        admin_client = AIOKafkaAdminClient(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVER
        )
        await admin_client.start()

        try:
            topics = self._extract_topics()
            await self.create_topics(admin_client, topics)
        finally:
            await admin_client.close()

    def setup(self) -> None:
        """Wrapper síncrono para compatibilidade"""
        asyncio.run(self.setup_async())

    @staticmethod
    def _extract_topics() -> list[str]:
        """Extrai tópicos da estrutura KAFKA_TOPICS"""
        topics = []
        for queue_name, topics_dict in settings.KAFKA_TOPICS.items():
            if isinstance(topics_dict, dict):
                topics.extend(topics_dict.keys())
            else:
                topics.append(queue_name)
        return list(set(topics))  # Remove duplicatas
