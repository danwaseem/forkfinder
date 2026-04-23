#!/usr/bin/env python3
"""
Review Worker — Kafka consumer for review events.

Subscribes to:  review.created  |  review.updated  |  review.deleted

For each message consumed:
  1. Writes a document to the review_events MongoDB collection (audit trail).
  2. Logs the event to stdout.
  3. Manually commits the Kafka offset (at-least-once delivery guarantee).

This demonstrates the producer → Kafka → consumer pattern required by Lab 2:
  - Review API Service  (producer) publishes after every DB write
  - Review Worker       (consumer) processes the event asynchronously

Run locally:
    MONGODB_URL=mongodb://localhost:27017 \\
    KAFKA_BOOTSTRAP_SERVERS=localhost:9092 \\
    python -m workers.review_worker

In Docker:
    docker compose --env-file .env.docker up review-worker
"""

import json
import logging
import os
import signal
import sys
from datetime import datetime, timezone

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [review-worker] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("review_worker")

# ── Config from environment ────────────────────────────────────────────────
MONGODB_URL             = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGODB_DB_NAME         = os.getenv("MONGODB_DB_NAME", "restaurant_platform")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_GROUP_ID          = os.getenv("KAFKA_GROUP_ID", "review-worker-group")

TOPICS = ["review.created", "review.updated", "review.deleted"]

# ── MongoDB helpers ─────────────────────────────────────────────────────────

from pymongo import MongoClient


def _get_collection():
    client = MongoClient(MONGODB_URL)
    db = client[MONGODB_DB_NAME]
    db.review_events.create_index("event_id", name="review_events_event_id", background=True)
    return db.review_events


# ── Message processing ──────────────────────────────────────────────────────

def _process(collection, msg) -> bool:
    """
    Parse one Kafka message, write to review_events collection, return True on success.
    """
    try:
        raw = msg.value.decode("utf-8") if isinstance(msg.value, bytes) else msg.value
        envelope = json.loads(raw)
        data = envelope.get("data", {})

        doc = {
            "event_id":      envelope.get("event_id", "unknown"),
            "event_type":    envelope.get("topic", msg.topic),
            "review_id":     data.get("review_id"),
            "restaurant_id": data.get("restaurant_id"),
            "user_id":       data.get("user_id"),
            "payload":       json.dumps(envelope),
            "processed_at":  datetime.now(timezone.utc),
        }
        collection.insert_one(doc)

        logger.info(
            "✓ Consumed  topic=%-20s  review_id=%-5s  restaurant_id=%-5s  event_id=%s",
            doc["event_type"],
            doc["review_id"],
            doc["restaurant_id"],
            doc["event_id"],
        )
        return True

    except Exception as exc:
        logger.error("Failed to process message from %s: %s", msg.topic, exc)
        return False


# ── Main consumer loop ──────────────────────────────────────────────────────

def run() -> None:
    logger.info("Review Worker starting up")
    logger.info("MongoDB  : %s / %s", MONGODB_URL, MONGODB_DB_NAME)
    logger.info("Kafka    : %s", KAFKA_BOOTSTRAP_SERVERS)
    logger.info("Topics   : %s", TOPICS)

    collection = _get_collection()

    # ── Kafka consumer ───────────────────────────────────────────────────
    try:
        from kafka import KafkaConsumer
        from kafka.errors import NoBrokersAvailable

        consumer = KafkaConsumer(
            *TOPICS,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(","),
            group_id=KAFKA_GROUP_ID,
            auto_offset_reset="earliest",    # start from oldest unread message
            enable_auto_commit=False,        # manual commit after successful processing
            consumer_timeout_ms=1000,        # unblocks the loop every second for shutdown
        )
        logger.info("Connected to Kafka — waiting for messages...")

    except NoBrokersAvailable as exc:
        logger.error("Cannot connect to Kafka at %s: %s", KAFKA_BOOTSTRAP_SERVERS, exc)
        sys.exit(1)

    # ── Graceful shutdown ────────────────────────────────────────────────
    running = True

    def _stop(sig, _frame):
        nonlocal running
        logger.info("Shutdown signal received — finishing current batch...")
        running = False

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT,  _stop)

    # ── Poll loop ────────────────────────────────────────────────────────
    try:
        while running:
            try:
                for msg in consumer:
                    if not running:
                        break
                    if _process(collection, msg):
                        consumer.commit()
                    else:
                        logger.warning(
                            "Skipping commit for failed message on %s offset %s",
                            msg.topic, msg.offset,
                        )
            except StopIteration:
                pass   # consumer_timeout_ms expired; outer loop continues
            except Exception as exc:
                logger.error("Consumer loop error: %s", exc)
    finally:
        consumer.close()
        logger.info("Review Worker stopped.")


if __name__ == "__main__":
    run()
