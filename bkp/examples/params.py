from typing import Dict

# set this params on settings.py

KAFKA_BOOTSTRAP_SERVER: str = "localhost:9092"
KAFKA_CLIENT_ID: str = "client_id"
KAFKA_GROUP_ID: str = "group_id"
KAFKA_TOPICS: Dict[str, str] = {
    "topic": "path.to.function",
}
