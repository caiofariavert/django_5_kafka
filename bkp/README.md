# Django Kafka

Python Kafka utilities library for Django projects, providing easy integration with Apache Kafka using confluent-kafka.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Producer](#producer)
  - [Consumer](#consumer)
  - [Management Commands](#management-commands)
- [Examples](#examples)
- [Advanced Configuration](#advanced-configuration)
- [Logging](#logging)
- [Development](#development)
- [License](#license)

## 🎯 Overview

Django Kafka is a Python library that simplifies integration between Django projects and Apache Kafka. It provides a clean and pythonic interface for producing and consuming Kafka messages, with full support for Django patterns.

### Features

- ✅ **Simple and efficient Producer** for sending messages
- ✅ **Consumer with automatic callback** based on configuration
- ✅ **Integrated Django management commands**
- ✅ **Auto-creation of Kafka topics**
- ✅ **Configurable logging** for debugging
- ✅ **Complete type hints** for better DX
- ✅ **Configuration via Django settings**

## 📦 Installation

This package is not available on PyPI. Install directly from the repository:

```bash
pip install git+https://github.com/vert-capital/django_kafka.git
```

### Dependencies

- Django >= 2.0
- confluent-kafka == 1.9.2
- Python >= 3.6

## ⚙️ Configuration

### 1. Add to INSTALLED_APPS

Add `django_kafka` to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'django_kafka',
]
```

### 2. Required settings

Add the following configurations to your `settings.py`:

```python
# Basic Kafka configurations
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
KAFKA_CLIENT_ID = "your-client-id"
KAFKA_GROUP_ID = "your-group-id"

# Topic mapping to callback functions
KAFKA_TOPICS = {
    "user-events": "apps.user.kafka.user_consumer",
    "order-events": "apps.orders.kafka.order_consumer",
    "notifications": "",  # Topic without callback (consume only)
}
```

### 3. Optional settings

```python
# Offset configuration (default: "earliest")
KAFKA_OFFSET_RESET = "earliest"  # or "latest"
```

## 🚀 Usage

### Producer

#### Basic usage

```python
from django_kafka.producer import producer

# Simple send
producer("user-events", "{'user_id': 123, 'action': 'login'}")

# With custom key
producer("user-events", "{'user_id': 123}", key="user-123")
```

#### With custom callback

```python
def custom_delivery_callback(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}")
    else:
        print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

producer(
    topic="user-events",
    message="{'user_id': 123}",
    key="user-123",
    on_delivery=custom_delivery_callback
)
```

### Consumer

#### Callback configuration

Create a callback function to process messages:

```python
# apps/user/kafka.py
from confluent_kafka import Consumer, Message

def user_consumer(consumer: Consumer, msg: Message) -> None:
    """
    Process messages from user-events topic
    """
    try:
        # Message data
        value = msg.value().decode('utf-8')
        key = msg.key().decode('utf-8') if msg.key() else None

        print(f"Message received: {value}")
        print(f"Key: {key}")
        print(f"Partition: {msg.partition()}")
        print(f"Offset: {msg.offset()}")

        # Your processing logic here
        # process_user_event(value)

        # Commit message after successful processing
        consumer.commit(message=msg)

    except Exception as e:
        print(f"Error processing message: {e}")
        # Error handling logic
```

#### Run the consumer

Use the Django management command:

```bash
python manage.py kafka_consumer
```

### Management Commands

#### Start consumer

```bash
python manage.py kafka_consumer
```

#### Setup topics (auto-creation)

```bash
python manage.py kafka_setup
```

This command will:
- Connect to the Kafka cluster
- Automatically create all topics defined in `KAFKA_TOPICS`
- Configure 3 partitions and replication factor 1 by default

## 💡 Examples

### Complete example - Notification system

#### 1. Configuration (settings.py)

```python
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
KAFKA_CLIENT_ID = "notification-service"
KAFKA_GROUP_ID = "notification-consumers"

KAFKA_TOPICS = {
    "user-registered": "apps.notifications.kafka.user_registered_handler",
    "order-created": "apps.notifications.kafka.order_created_handler",
    "email-queue": "apps.notifications.kafka.email_handler",
}
```

#### 2. Producer (views.py)

```python
from django.contrib.auth.models import User
from django.http import JsonResponse
from django_kafka.producer import producer
import json

def register_user(request):
    # User creation logic
    user = User.objects.create_user(
        username=request.POST['username'],
        email=request.POST['email']
    )

    # Send event to Kafka
    event_data = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'timestamp': user.date_joined.isoformat()
    }

    producer(
        topic="user-registered",
        message=json.dumps(event_data),
        key=f"user-{user.id}"
    )

    return JsonResponse({'status': 'success', 'user_id': user.id})
```

#### 3. Consumer (apps/notifications/kafka.py)

```python
from confluent_kafka import Consumer, Message
from django.core.mail import send_mail
import json
import logging

logger = logging.getLogger(__name__)

def user_registered_handler(consumer: Consumer, msg: Message) -> None:
    """
    Send welcome email to new users
    """
    try:
        # Parse message
        data = json.loads(msg.value().decode('utf-8'))

        # Send welcome email
        send_mail(
            subject='Welcome!',
            message=f'Hello {data["username"]}, welcome to our platform!',
            from_email='noreply@example.com',
            recipient_list=[data['email']],
        )

        logger.info(f"Welcome email sent to {data['email']}")

        # Confirm processing
        consumer.commit(message=msg)

    except Exception as e:
        logger.error(f"Error processing user registration: {e}")

def order_created_handler(consumer: Consumer, msg: Message) -> None:
    """
    Process order creation events
    """
    try:
        data = json.loads(msg.value().decode('utf-8'))

        # Send order created notification
        # ... processing logic

        consumer.commit(message=msg)

    except Exception as e:
        logger.error(f"Error processing order: {e}")
```

## 🔧 Advanced Configuration

### Custom headers

The producer automatically adds useful headers:

```python
headers = {
    "producer_id": settings.KAFKA_CLIENT_ID,
    "hostname": socket.gethostname(),
}
```

### Partition and replication configuration

To modify default topic settings, edit the `admin.py` file:

```python
# django_kafka/admin.py (for customization)
new_topics = [
    NewTopic(topic, num_partitions=5, replication_factor=3)
    for topic in topics
]
```

### Advanced Consumer configuration

For more advanced consumer configurations, modify `consumer.py`:

```python
conf = {
    "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVER,
    "group.id": settings.KAFKA_GROUP_ID,
    "auto.offset.reset": settings.KAFKA_OFFSET_RESET,
    "enable.auto.commit": False,  # Manual commit
    "max.poll.interval.ms": 300000,
    "session.timeout.ms": 10000,
}
```

## 📊 Logging

The library uses Django's logging system. Configure in your `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'kafka.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django_kafka': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

## 🛠 Development

### Project structure

```
django_kafka/
├── __init__.py
├── admin.py              # Administration and topic creation
├── consumer.py           # Consumer logic
├── producer.py           # Producer logic
└── management/
    └── commands/
        ├── kafka_consumer.py  # Command to start consumer
        └── kafka_setup.py     # Command to setup topics
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## ⚠️ Important considerations

1. **Error handling**: Always implement proper error handling in your callbacks
2. **Manual commit**: Only commit messages after successful processing
3. **Idempotency**: Ensure your handlers are idempotent
4. **Monitoring**: Implement adequate logging for production monitoring
5. **Security**: Configure SSL/SASL as needed for production

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Developed by [Vert Capital](https://vert-capital.com.br)**
