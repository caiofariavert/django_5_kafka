from django_kafka.django_kafka.producer import producer

# settings.KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
# settings.KAFKA_CLIENT_ID = "client_id"

# Simple producer
producer("topic", "message")


# producer with key
producer("topic", "message", key="key")


# producer with on_delivery callback
def on_delivery(err, msg):
    if err is not None:
        print("Delivery failed for User record {}: {}".format(msg.key(), err))
        return
    print(
        "User record {} successfully produced to {} [{}] at offset {}".format(
            msg.key(), msg.topic(), msg.partition(), msg.offset()
        )
    )


producer("topic", "message", on_delivery=on_delivery)
