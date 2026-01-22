# Usage Examples - Django Kafka

This file contains practical and advanced examples of how to use the Django Kafka library.

## 📋 Table of Contents

- [Initial Setup](#initial-setup)
- [Producer - Basic Examples](#producer---basic-examples)
- [Consumer - Basic Examples](#consumer---basic-examples)
- [Advanced Use Cases](#advanced-use-cases)
- [Django REST Framework Integration](#django-rest-framework-integration)
- [Monitoring and Logging](#monitoring-and-logging)

## 🛠 Initial Setup

### Complete settings.py

```python
# settings.py

# Required Kafka configurations
KAFKA_BOOTSTRAP_SERVER = "localhost:9092"
KAFKA_CLIENT_ID = "my-django-app"
KAFKA_GROUP_ID = "my-group-consumers"

# Topic mapping
KAFKA_TOPICS = {
    # E-commerce
    "user-registered": "apps.users.kafka.user_registered_handler",
    "user-updated": "apps.users.kafka.user_updated_handler",
    "order-created": "apps.orders.kafka.order_created_handler",
    "order-status-changed": "apps.orders.kafka.order_status_handler",
    "payment-processed": "apps.payments.kafka.payment_handler",

    # Notifications
    "email-queue": "apps.notifications.kafka.email_handler",
    "sms-queue": "apps.notifications.kafka.sms_handler",
    "push-notification": "apps.notifications.kafka.push_handler",

    # Analytics
    "user-activity": "apps.analytics.kafka.activity_handler",
    "page-view": "apps.analytics.kafka.pageview_handler",

    # Logs (no callback - storage only)
    "application-logs": "",
    "error-logs": "",
}

# Optional configurations
KAFKA_OFFSET_RESET = "earliest"

# Kafka Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'kafka_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/kafka.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django_kafka': {
            'handlers': ['kafka_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## 📤 Producer - Basic Examples

### 1. Simple message sending

```python
from django_kafka.producer import producer
import json

# User registration event
def send_user_registered_event(user):
    event_data = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'timestamp': user.date_joined.isoformat(),
        'event_type': 'USER_REGISTERED'
    }

    producer(
        topic="user-registered",
        message=json.dumps(event_data),
        key=f"user-{user.id}"
    )
```

### 2. Producer with custom callback

```python
import logging

logger = logging.getLogger(__name__)

def delivery_callback(err, msg):
    """Custom callback for delivery tracking"""
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
        # Here you can implement retry logic or alerts
    else:
        logger.info(
            f"Message delivered successfully to {msg.topic()} "
            f"[{msg.partition()}] offset {msg.offset()}"
        )

def send_critical_event(event_data):
    """Send critical event with callback"""
    producer(
        topic="critical-events",
        message=json.dumps(event_data),
        key=event_data.get('correlation_id'),
        on_delivery=delivery_callback
    )
```

### 3. Producer in Django views

```python
# views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django_kafka.producer import producer
from django.utils import timezone
import json
import logging

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class OrderCreateView(View):
    def post(self, request):
        try:
            # Process order data
            order_data = json.loads(request.body)

            # Save to database (example)
            # order = Order.objects.create(...)

            # Send event to Kafka
            event = {
                'order_id': 'ORDER_123',
                'customer_id': order_data.get('customer_id'),
                'total_amount': order_data.get('total'),
                'items': order_data.get('items'),
                'timestamp': timezone.now().isoformat(),
                'event_type': 'ORDER_CREATED'
            }

            producer(
                topic="order-created",
                message=json.dumps(event),
                key=f"order-{event['order_id']}"
            )

            return JsonResponse({
                'status': 'success',
                'order_id': event['order_id']
            })

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return JsonResponse({'error': str(e)}, status=500)
```

## 📥 Consumer - Basic Examples

### 1. Basic consumer

```python
# apps/users/kafka.py
from confluent_kafka import Consumer, Message
import json
import logging

logger = logging.getLogger(__name__)

def user_registered_handler(consumer: Consumer, msg: Message) -> None:
    """Handler for user registration events"""
    try:
        # Parse message
        data = json.loads(msg.value().decode('utf-8'))

        logger.info(f"Processing user registration: {data['user_id']}")

        # Send welcome email
        send_welcome_email(data['email'], data['username'])

        # Create additional user profile
        create_user_profile(data['user_id'])

        # Register in analytics system
        track_user_registration(data)

        # Commit after successful processing
        consumer.commit(message=msg)

        logger.info(f"User {data['user_id']} processed successfully")

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
    except Exception as e:
        logger.error(f"Error processing user registration: {e}")
        # Don't commit on error

def send_welcome_email(email, username):
    """Send welcome email"""
    from django.core.mail import send_mail

    send_mail(
        subject='Welcome to our platform!',
        message=f'Hello {username}, welcome!',
        from_email='noreply@example.com',
        recipient_list=[email],
    )

def create_user_profile(user_id):
    """Create additional user profile"""
    # Implement profile creation logic
    pass

def track_user_registration(data):
    """Register event in analytics"""
    # Implement tracking
    pass
```

### 2. Consumer with robust error handling

```python
# apps/orders/kafka.py
from confluent_kafka import Consumer, Message
from django.db import transaction
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def process_order_with_retry(order_data):
    """Process order with automatic retry"""
    # Processing logic that might fail
    update_inventory(order_data['items'])
    send_confirmation_email(order_data['customer_email'])
    update_analytics(order_data)

def order_created_handler(consumer: Consumer, msg: Message) -> None:
    """Handler for order creation with error handling"""
    try:
        data = json.loads(msg.value().decode('utf-8'))

        logger.info(f"Processing order: {data['order_id']}")

        # Use transaction to ensure consistency
        with transaction.atomic():
            process_order_with_retry(data)

        # Commit only after complete success
        consumer.commit(message=msg)

        logger.info(f"Order {data['order_id']} processed successfully")

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        # Commit to skip invalid message
        consumer.commit(message=msg)

    except Exception as e:
        logger.error(f"Error processing order: {e}")
        # Don't commit - message will be reprocessed

        # Optional: send to Dead Letter Queue after X attempts
        send_to_dlq_if_needed(msg, e)

def send_to_dlq_if_needed(msg, error):
    """Send to Dead Letter Queue after many attempts"""
    # Implement DLQ logic
    pass

def update_inventory(items):
    """Update inventory"""
    pass

def send_confirmation_email(email):
    """Send confirmation email"""
    pass

def update_analytics(data):
    """Update analytics"""
    pass
```

## 🚀 Advanced Use Cases

### 1. Real-time notification system

```python
# apps/notifications/kafka.py
from confluent_kafka import Consumer, Message
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import logging

logger = logging.getLogger(__name__)

def push_notification_handler(consumer: Consumer, msg: Message) -> None:
    """Handler for push notifications via WebSocket"""
    try:
        data = json.loads(msg.value().decode('utf-8'))

        # Send via WebSocket using Django Channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{data['user_id']}",
            {
                'type': 'notification_message',
                'message': data['message'],
                'notification_type': data['type']
            }
        )

        # Save notification to database
        save_notification_to_db(data)

        consumer.commit(message=msg)

    except Exception as e:
        logger.error(f"Error sending notification: {e}")

def save_notification_to_db(data):
    """Save notification to database"""
    # Implement database saving
    pass

# views.py - Notification trigger
from django_kafka.producer import producer
from django.utils import timezone

def send_notification(user_id, message, notification_type):
    """Send notification via Kafka"""
    notification_data = {
        'user_id': user_id,
        'message': message,
        'type': notification_type,
        'timestamp': timezone.now().isoformat()
    }

    producer(
        topic="push-notification",
        message=json.dumps(notification_data),
        key=f"user-{user_id}"
    )
```

### 2. Audit system

```python
# apps/audit/kafka.py
from confluent_kafka import Consumer, Message
import json
import logging

logger = logging.getLogger(__name__)

def audit_log_handler(consumer: Consumer, msg: Message) -> None:
    """Handler for audit logs"""
    try:
        data = json.loads(msg.value().decode('utf-8'))

        # Save to audit database
        from apps.audit.models import AuditLog
        AuditLog.objects.create(
            user_id=data.get('user_id'),
            action=data.get('action'),
            resource=data.get('resource'),
            timestamp=data.get('timestamp'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            details=data.get('details', {})
        )

        consumer.commit(message=msg)

    except Exception as e:
        logger.error(f"Error processing audit log: {e}")

# middleware.py - Capture audit events
from django_kafka.producer import producer
from django.utils import timezone
import json

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Send audit event
        if request.user.is_authenticated:
            audit_data = {
                'user_id': request.user.id,
                'action': f"{request.method} {request.path}",
                'resource': request.path,
                'timestamp': timezone.now().isoformat(),
                'ip_address': self.get_client_ip(request),
                'user_agent': request.META.get('HTTP_USER_AGENT'),
                'status_code': response.status_code
            }

            producer(
                topic="audit-logs",
                message=json.dumps(audit_data),
                key=f"user-{request.user.id}"
            )

        return response

    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
```

## 🔄 Django REST Framework Integration

### Serializers with Kafka events

```python
# serializers.py
from rest_framework import serializers
from django_kafka.producer import producer
from django.utils import timezone
import json

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

    def create(self, validated_data):
        user = super().create(validated_data)

        # Send creation event
        event_data = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'timestamp': user.date_joined.isoformat(),
            'event_type': 'USER_CREATED'
        }

        producer(
            topic="user-events",
            message=json.dumps(event_data),
            key=f"user-{user.id}"
        )

        return user

    def update(self, instance, validated_data):
        old_email = instance.email
        user = super().update(instance, validated_data)

        # Send update event if email changed
        if old_email != user.email:
            event_data = {
                'user_id': user.id,
                'old_email': old_email,
                'new_email': user.email,
                'timestamp': timezone.now().isoformat(),
                'event_type': 'USER_EMAIL_CHANGED'
            }

            producer(
                topic="user-events",
                message=json.dumps(event_data),
                key=f"user-{user.id}"
            )

        return user
```

### ViewSets with events

```python
# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_kafka.producer import producer
from django.utils import timezone
import json

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel order and send event"""
        order = self.get_object()

        if order.status != 'PENDING':
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update status
        order.status = 'CANCELLED'
        order.save()

        # Send event
        event_data = {
            'order_id': order.id,
            'customer_id': order.customer.id,
            'old_status': 'PENDING',
            'new_status': 'CANCELLED',
            'cancelled_by': request.user.id,
            'timestamp': timezone.now().isoformat(),
            'event_type': 'ORDER_CANCELLED'
        }

        producer(
            topic="order-events",
            message=json.dumps(event_data),
            key=f"order-{order.id}"
        )

        return Response({'status': 'cancelled'})
```

## 📊 Monitoring and Logging

### Kafka health check

```python
# apps/monitoring/views.py
from django.http import JsonResponse
from confluent_kafka.admin import AdminClient
from django.conf import settings

def kafka_health_check(request):
    """Check Kafka connection health"""
    try:
        admin_client = AdminClient({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVER
        })

        # Try to list topics
        metadata = admin_client.list_topics(timeout=5)

        return JsonResponse({
            'status': 'healthy',
            'topics_count': len(metadata.topics),
            'broker_count': len(metadata.brokers)
        })

    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

### Custom metrics

```python
# apps/monitoring/kafka.py
import time
from django.core.cache import cache
import json
import logging

logger = logging.getLogger(__name__)

def metrics_handler(consumer: Consumer, msg: Message) -> None:
    """Collect processing metrics"""
    start_time = time.time()

    try:
        # Process message
        data = json.loads(msg.value().decode('utf-8'))

        # Your business logic here
        process_business_logic(data)

        consumer.commit(message=msg)

        # Record success metric
        processing_time = time.time() - start_time
        record_metric('kafka.message.processed', 1, {
            'topic': msg.topic(),
            'status': 'success',
            'processing_time': processing_time
        })

    except Exception as e:
        # Record error metric
        record_metric('kafka.message.failed', 1, {
            'topic': msg.topic(),
            'error_type': type(e).__name__
        })
        raise

def record_metric(metric_name, value, tags=None):
    """Record metric (implement with your monitoring tool)"""
    # Example with cache for simple aggregation
    cache_key = f"metric:{metric_name}:{hash(str(tags))}"
    current_value = cache.get(cache_key, 0)
    cache.set(cache_key, current_value + value, timeout=3600)

def process_business_logic(data):
    """Process business logic"""
    pass
```

## 🔧 Useful commands for development

### Script to test producer

```python
# scripts/test_producer.py
import os
import sys
import django

# Configure Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django_kafka.producer import producer
from django.utils import timezone
import json

def test_producer():
    """Test message sending"""
    for i in range(10):
        event_data = {
            'test_id': i,
            'message': f'Test message {i}',
            'timestamp': timezone.now().isoformat()
        }

        producer(
            topic="test-topic",
            message=json.dumps(event_data),
            key=f"test-{i}"
        )

        print(f"Message {i} sent")

if __name__ == '__main__':
    test_producer()
```

### Docker Compose for development

```yaml
# docker-compose.yml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    depends_on:
      - kafka
    ports:
      - "8080:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
```

### Management command for testing

```python
# management/commands/test_kafka.py
from django.core.management.base import BaseCommand
from django_kafka.producer import producer
from django.utils import timezone
import json

class Command(BaseCommand):
    help = 'Test Kafka producer and consumer'

    def add_arguments(self, parser):
        parser.add_argument('--messages', type=int, default=10)
        parser.add_argument('--topic', type=str, default='test-topic')

    def handle(self, *args, **options):
        messages = options['messages']
        topic = options['topic']

        self.stdout.write(f'Sending {messages} messages to {topic}...')

        for i in range(messages):
            event_data = {
                'test_id': i,
                'message': f'Test message {i}',
                'timestamp': timezone.now().isoformat()
            }

            producer(
                topic=topic,
                message=json.dumps(event_data),
                key=f"test-{i}"
            )

            self.stdout.write(f'Message {i} sent')

        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {messages} messages')
        )
```

---

This file provides comprehensive examples for using the Django Kafka library in different scenarios and complexity levels.
