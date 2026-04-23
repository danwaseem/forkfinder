"""
Kafka event producer — thin wrapper around kafka-python KafkaProducer.

Design decisions
────────────────
1.  Lazy singleton — the producer is created on the first publish() call,
    not at import time.  This keeps app startup fast and avoids import errors
    when kafka-python is present but Kafka is not running.

2.  Graceful degradation — if the broker is unreachable, publish() logs a
    warning and returns False.  It never raises.  A Kafka outage must NOT
    break API responses; the DB write already completed.

3.  Envelope format — every message is wrapped in a standard envelope:
    {
        "event_id":  "<uuid4>",
        "topic":     "<topic-name>",
        "timestamp": "<ISO-8601 UTC>",
        "data":      { ... domain-specific payload ... }
    }

Usage
─────
    from app.kafka.producer import publish
    from app.kafka import topics

    publish(topics.REVIEW_CREATED, {"review_id": 12, "user_id": 3, ...})
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ..config import settings

logger = logging.getLogger(__name__)

# Module-level singleton; None means "not yet initialised" or "unavailable"
_producer: Optional[Any] = None


def _get_producer() -> Optional[Any]:
    """
    Return the KafkaProducer singleton, creating it if necessary.
    Returns None when Kafka is disabled or unreachable.
    """
    global _producer
    if _producer is not None:
        return _producer

    if not settings.KAFKA_BOOTSTRAP_SERVERS:
        return None

    try:
        from kafka import KafkaProducer  # type: ignore[import]

        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS.split(","),
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            # Keep timeouts short so a slow broker does not hold up API requests
            request_timeout_ms=3000,
            max_block_ms=3000,
            retries=1,
        )
        logger.info(
            "Kafka producer connected to %s", settings.KAFKA_BOOTSTRAP_SERVERS
        )
    except Exception as exc:
        logger.warning(
            "Kafka producer unavailable (%s) — events will not be published. "
            "Set KAFKA_BOOTSTRAP_SERVERS and ensure the broker is running.",
            exc,
        )
        _producer = None  # stay None so we retry on the next call

    return _producer


def publish(topic: str, data: Dict[str, Any]) -> bool:
    """
    Publish an event to *topic*.

    Wraps *data* in a standard envelope and sends asynchronously (fire-and-
    forget).  Returns True if the message was queued, False if Kafka is
    unavailable.  Never raises.

    Args:
        topic: Kafka topic name (use constants from app.kafka.topics).
        data:  Domain-specific payload dict.
    """
    producer = _get_producer()
    if producer is None:
        logger.debug("Kafka not available — skipping publish to %s", topic)
        return False

    envelope: Dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "topic": topic,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }

    try:
        producer.send(topic, value=envelope)
        # flush() with a short timeout ensures the message leaves the buffer
        # before the API response is returned, without blocking indefinitely.
        producer.flush(timeout=2)
        logger.info(
            "Published event to %s (event_id=%s)", topic, envelope["event_id"]
        )
        return True
    except Exception as exc:
        logger.warning("Failed to publish to topic %s: %s", topic, exc)
        return False
