#!/usr/bin/env python3
"""
Restaurant Worker — Kafka consumer for restaurant events.

Subscribes to:  restaurant.created  |  restaurant.updated  |  restaurant.claimed

For each message consumed:
  1. Writes a document to the restaurant_events MongoDB collection (audit trail).
  2. Logs the event to stdout.
  3. Manually commits the Kafka offset.

Run locally:
    MONGODB_URL=mongodb://localhost:27017 \\
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \\
    python -m workers.restaurant_worker
"""

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [restaurant-worker] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("restaurant_worker")

MONGODB_URL             = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME         = os.getenv("MONGODB_DB_NAME", "restaurant_platform")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID          = os.getenv("KAFKA_GROUP_ID", "restaurant-worker-group")

TOPICS = ["restaurant.created", "restaurant.updated", "restaurant.claimed"]

from pymongo import MongoClient


def _get_collection():
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    db.restaurant_events.create_index("event_id", name="restaurant_events_event_id", background=True)
    return db.restaurant_events


def _process(collection, msg) -> bool:
    try:
        raw = msg.value.decode("utf-8") if isinstance(msg.value, bytes) else msg.value
        envelope = json.loads(raw)
        data = envelope.get("data", {})

        actor = (
            data.get("created_by")
            or data.get("updated_by")
            or data.get("claimed_by")
        )

        doc = {
            "event_id":      envelope.get("event_id", "unknown"),
            "event_type":    envelope.get("topic", msg.topic),
            "restaurant_id": data.get("restaurant_id"),
            "actor_user_id": actor,
            "payload":       json.dumps(envelope),
            "processed_at":  datetime.now(timezone.utc),
        }
        collection.insert_one(doc)

        logger.info(
            "✓ Consumed  topic=%-25s  restaurant_id=%-5s  actor_user_id=%-5s  event_id=%s",
            doc["event_type"],
            doc["restaurant_id"],
            doc["actor_user_id"],
            doc["event_id"],
        )
        return True

    except Exception as exc:
        logger.error("Failed to process message from %s: %s", msg.topic, exc)
        return False


def run() -> None:
    logger.info("Restaurant Worker starting up")
    logger.info("MongoDB  : %s / %s", MONGODB_URL, MONGODB_DB_NAME)
    logger.info("Kafka    : %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("Topics   : %s", TOPICS)

    collection = _get_collection()

    try:
        from kafka import KafkaConsumer
        from kafka.errors import NoBrokersAvailable

        consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            consumer_timeout_ms=1000,
        )
        logger.info("Connected to Kafka — waiting for messages...")

    except NoBrokersAvailable as exc:
        logger.error("Cannot connect to Kafka at %s: %s", KAFKA_BOOTSTRAP_SERVERS, exc)
        sys.exit(1)

    running = True

    def _stop(sig, _frame):
        nonlocal running
        logger.info("Shutdown signal received.")
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT,  _stop)

    try:
        while running:
            try:
                for msg in consumer:
                    if not running:
                        break
                    if _process(collection, msg):
                        consumer.commit()
            except StopIteration:
                pass
            except Exception as exc:
                logger.error("Consumer loop error: %s", exc)
    finally:
        consumer.close()
        logger.info("Restaurant Worker stopped.")


if __name__ == "__main__":
    run()
