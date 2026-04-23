"""
MongoDB database layer — replaces SQLAlchemy/MySQL.

Public API
----------
get_db()        — FastAPI dependency; yields a pymongo.database.Database
_next_id(db, collection_name)  — auto-increment integer _id via counters collection
_ns(doc)        — convert a MongoDB document dict to a MongoDoc (attribute + dict access)

MongoDB Collections
-------------------
users            — {_id: int, name, email, password_hash, role, preferences: {...}, ...}
restaurants      — {_id: int, name, cuisine_type, photos: list, hours: dict, ...}
restaurant_claims— {_id: int, restaurant_id, owner_id, status, created_at}
reviews          — {_id: int, user_id, restaurant_id, rating, comment, photos: list, ...}
favorites        — {_id: int, user_id, restaurant_id, created_at}
conversations    — {_id: int, user_id, messages: [{role, content, created_at}], ...}
sessions         — server-side session audit (ObjectId _id, not exposed via API)
review_events    — Kafka audit trail (ObjectId _id)
restaurant_events— Kafka audit trail (ObjectId _id)
counters         — auto-increment sequences {_id: collection_name, seq: int}
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import ReturnDocument

from .config import settings

_client: MongoClient | None = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGODB_URL)
    return _client


def get_db() -> Database:
    """FastAPI dependency — returns the MongoDB database."""
    return _get_client()[settings.MONGODB_DB_NAME]


def _next_id(db: Database, collection_name: str) -> int:
    """Return the next auto-increment integer ID for a collection."""
    result = db.counters.find_one_and_update(
        {"_id": collection_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return result["seq"]


class MongoDoc(dict):
    """
    MongoDB document dict with attribute access.

    Allows code like `user.id`, `user.email` in addition to `user["id"]`.
    This preserves the SQLAlchemy ORM attribute-access pattern throughout
    routers/services without any structural changes.
    """

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            return None  # matches SQLAlchemy nullable column behaviour

    def __setattr__(self, name: str, value):
        self[name] = value


def _ns(doc: dict | None) -> MongoDoc | None:
    """
    Convert a raw pymongo document to a MongoDoc.

    Maps MongoDB's ``_id`` field to ``id`` so the rest of the codebase
    can continue using ``.id`` without any changes.
    """
    if doc is None:
        return None
    d = dict(doc)
    if "_id" in d:
        d["id"] = d.pop("_id")
    return MongoDoc(d)


def init_indexes(db: Database) -> None:
    """
    Create MongoDB indexes.  Called once at application startup.
    Safe to call repeatedly — MongoDB ignores already-existing indexes.
    """
    # users
    db.users.create_index("email", unique=True, name="users_email_unique")

    # restaurants
    db.restaurants.create_index([("name", ASCENDING)], name="restaurants_name")
    db.restaurants.create_index([("cuisine_type", ASCENDING)], name="restaurants_cuisine")
    db.restaurants.create_index([("city", ASCENDING)], name="restaurants_city")
    db.restaurants.create_index([("avg_rating", DESCENDING)], name="restaurants_rating")

    # reviews
    db.reviews.create_index(
        [("restaurant_id", ASCENDING), ("user_id", ASCENDING)],
        unique=True,
        name="reviews_restaurant_user_unique",
    )
    db.reviews.create_index([("restaurant_id", ASCENDING)], name="reviews_restaurant")
    db.reviews.create_index([("user_id", ASCENDING)], name="reviews_user")

    # favorites
    db.favorites.create_index(
        [("user_id", ASCENDING), ("restaurant_id", ASCENDING)],
        unique=True,
        name="favorites_user_restaurant_unique",
    )

    # sessions
    db.sessions.create_index([("user_id", ASCENDING)], name="sessions_user")
    db.sessions.create_index("jti", name="sessions_jti")
    db.sessions.create_index("expires_at", expireAfterSeconds=0, name="sessions_ttl")

    # review_events / restaurant_events
    db.review_events.create_index("event_id", name="review_events_event_id")
    db.restaurant_events.create_index("event_id", name="restaurant_events_event_id")
