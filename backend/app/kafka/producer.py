# backend/app/kafka/producer.py
import json
import logging
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

from ..config import settings

logger = logging.getLogger(__name__)
_producer = None


def _get_producer():
    global _producer
    if _producer is not None:
        return _producer

    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return None

    try:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            request_timeout_ms=3000,
            max_block_ms=3000,
            retries=1,
        )
        return _producer
    except Exception as exc:
        logger.warning("Kafka producer unavailable: %s", exc)
        _producer = None
        return None


def publish(topic: str, data: dict) -> bool:
    producer = _get_producer()
    if producer is None:
        return False

    envelope = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    try:
        producer.send(topic, value=envelope)
        producer.flush(timeout=2)
        logger.info("Published event to %s (event_id=%s)", topic, envelope["event_id"])
        return True
    except Exception as exc:
        logger.warning("Failed to publish to %s: %s", topic, exc)
        return False