# backend/app/kafka/producer.py
import json
import logging
import uuid
from datetime import datetime, timezone
from kafka import KafkaProducer

logger = logging.getLogger(__name__)
_producer = None

def get_producer(bootstrap_servers: str):
    global _producer
    if _producer is not None:
        return _producer

    if not bootstrap_servers:
        return None

    try:
        _producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers.split(","),
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

def publish(topic: str, data: dict, bootstrap_servers: str) -> bool:
    producer = get_producer(bootstrap_servers)
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
        return True
    except Exception as exc:
        logger.warning("Failed to publish to %s: %s", topic, exc)
        return False