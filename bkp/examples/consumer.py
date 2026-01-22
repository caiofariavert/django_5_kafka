from ..django_kafka import kafka_consumer_run

# settings.KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
# KAFKA_GROUP_ID = "group_id"
# KAFKA_TOPICS = {
#     "topic": "path.to.function",
# }

kafka_consumer_run()

# run command in terminal
# python manage.py kafka_consumer


# sample
# KAFKA_TOPICS = {
#     "vertc-user": "apps.user.kafka.user_consumer",
# }

# apps/user/kafka/user_consumer.py
from django_kafka.consumer import Consumer, Message


def user_consumer(consumer: Consumer, msg: Message) -> None:

    print(msg.value())
    print(msg.key())
    print(msg.partition())
    print(msg.offset())
