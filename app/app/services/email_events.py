import json
import logging
from functools import lru_cache
from typing import Any

from kafka import KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable

from app.core.config import settings

logger = logging.getLogger(__name__)

EVENT_NEW_ACCOUNT = "new_account"
EVENT_PASSWORD_RESET = "password_reset"
EVENT_TEST_EMAIL = "test_email"


@lru_cache(maxsize=1)
def _get_producer() -> KafkaProducer | None:
    if not settings.KAFKA_ENABLED:
        return None
    try:
        return KafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )
    except NoBrokersAvailable:
        logger.exception("Kafka broker unavailable for registration email events")
        return None


def _publish_email_event(payload: dict[str, Any]) -> bool:
    producer = _get_producer()
    if not producer:
        return False

    try:
        future = producer.send(settings.KAFKA_REGISTRATION_EMAIL_TOPIC, payload)
        future.get(timeout=5)
        return True
    except KafkaError:
        logger.exception("Failed to publish email event to Kafka")
        return False


def publish_registration_email_event(
    *, email_to: str, username: str, password: str
) -> bool:
    payload: dict[str, Any] = {
        "event_type": EVENT_NEW_ACCOUNT,
        "email_to": email_to,
        "username": username,
        "password": password,
    }
    return _publish_email_event(payload)


def publish_password_reset_email_event(*, email_to: str, email: str, token: str) -> bool:
    payload: dict[str, Any] = {
        "event_type": EVENT_PASSWORD_RESET,
        "email_to": email_to,
        "email": email,
        "token": token,
    }
    return _publish_email_event(payload)


def publish_test_email_event(*, email_to: str) -> bool:
    payload: dict[str, Any] = {
        "event_type": EVENT_TEST_EMAIL,
        "email_to": email_to,
    }
    return _publish_email_event(payload)
