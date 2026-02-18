import json
import logging
import time
from typing import Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable

from app.core.config import settings
from app.core.email import (
    generate_new_account_email,
    generate_reset_password_email,
    generate_test_email,
    send_email,
)
from app.services.email_events import (
    EVENT_NEW_ACCOUNT,
    EVENT_PASSWORD_RESET,
    EVENT_TEST_EMAIL,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _send_new_account_email(payload: dict[str, Any]) -> None:
    email_to = payload.get("email_to")
    username = payload.get("username")
    password = payload.get("password")

    if not isinstance(email_to, str) or not isinstance(username, str):
        logger.warning("Invalid new account email payload: %s", payload)
        return
    if not isinstance(password, str):
        logger.warning("Invalid new account email payload: %s", payload)
        return
    if not settings.emails_enabled:
        logger.warning("Emails are disabled; skip new account email event")
        return

    email_data = generate_new_account_email(
        email_to=email_to, username=username, password=password
    )
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def _send_password_reset_email(payload: dict[str, Any]) -> None:
    email_to = payload.get("email_to")
    email = payload.get("email")
    token = payload.get("token")

    if (
        not isinstance(email_to, str)
        or not isinstance(email, str)
        or not isinstance(token, str)
    ):
        logger.warning("Invalid password reset email payload: %s", payload)
        return
    if not settings.emails_enabled:
        logger.warning("Emails are disabled; skip password reset email event")
        return

    email_data = generate_reset_password_email(email_to=email_to, email=email, token=token)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def _send_test_email(payload: dict[str, Any]) -> None:
    email_to = payload.get("email_to")
    if not isinstance(email_to, str):
        logger.warning("Invalid test email payload: %s", payload)
        return
    if not settings.emails_enabled:
        logger.warning("Emails are disabled; skip test email event")
        return

    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )


def _dispatch_email_event(payload: dict[str, Any]) -> None:
    event_type = payload.get("event_type")
    if event_type == EVENT_NEW_ACCOUNT:
        _send_new_account_email(payload)
        return
    if event_type == EVENT_PASSWORD_RESET:
        _send_password_reset_email(payload)
        return
    if event_type == EVENT_TEST_EMAIL:
        _send_test_email(payload)
        return
    logger.warning("Unknown email event type: %s payload=%s", event_type, payload)


def run() -> None:
    if not settings.KAFKA_ENABLED:
        logger.info("KAFKA_ENABLED is false; email worker exited")
        return

    while True:
        consumer: KafkaConsumer | None = None
        try:
            consumer = KafkaConsumer(
                settings.KAFKA_REGISTRATION_EMAIL_TOPIC,
                bootstrap_servers=settings.kafka_bootstrap_servers,
                group_id=settings.KAFKA_EMAIL_CONSUMER_GROUP,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
            for message in consumer:
                if isinstance(message.value, dict):
                    _dispatch_email_event(message.value)
        except (NoBrokersAvailable, KafkaError):
            logger.exception("Email worker Kafka error, retry in 5 seconds")
            time.sleep(5)
        finally:
            if consumer:
                consumer.close()


if __name__ == "__main__":
    run()
