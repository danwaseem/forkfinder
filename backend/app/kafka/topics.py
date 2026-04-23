"""
Kafka topic name constants.

Matches the topic table in the Lab 2 assignment exactly.
"""

# ── Review topics ──────────────────────────────────────────────────────────
REVIEW_CREATED   = "review.created"
REVIEW_UPDATED   = "review.updated"
REVIEW_DELETED   = "review.deleted"

# ── Restaurant topics ──────────────────────────────────────────────────────
RESTAURANT_CREATED = "restaurant.created"
RESTAURANT_UPDATED = "restaurant.updated"
RESTAURANT_CLAIMED = "restaurant.claimed"

# All topics — used by workers to subscribe
ALL_REVIEW_TOPICS     = [REVIEW_CREATED, REVIEW_UPDATED, REVIEW_DELETED]
ALL_RESTAURANT_TOPICS = [RESTAURANT_CREATED, RESTAURANT_UPDATED, RESTAURANT_CLAIMED]
