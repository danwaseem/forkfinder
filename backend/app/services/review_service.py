"""
Review service layer — MongoDB version.

Public API (unchanged signatures):
    get_paginated(db, restaurant_id, sort, page, limit) -> (list[MongoDoc], total)
    create(db, user_id, restaurant_id, rating, comment) -> (MongoDoc, RestaurantStats)
    update(db, review_id, user_id, rating, comment)     -> (MongoDoc, RestaurantStats)
    delete(db, review_id, user_id)                      -> RestaurantStats
    add_photo(db, review_id, user_id, photo_url)        -> list
"""

from datetime import datetime
from typing import Optional, Tuple

from ..database import _next_id, _ns
from ..schemas.review import RestaurantStats


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_restaurant(db, restaurant_id: int):
    r = _ns(db.restaurants.find_one({"_id": restaurant_id}))
    if r is None:
        raise LookupError(f"Restaurant {restaurant_id} not found.")
    return r


def _fetch_review(db, review_id: int):
    rev = _ns(db.reviews.find_one({"_id": review_id}))
    if rev is None:
        raise LookupError(f"Review {review_id} not found.")
    return rev


def _enrich_review(db, review):
    """Attach a .user sub-MongoDoc to a review for _serialize_review compatibility."""
    user_doc = db.users.find_one({"_id": review.user_id})
    review.user = _ns(user_doc)
    return review


# ---------------------------------------------------------------------------
# Rating recalculation
# ---------------------------------------------------------------------------

def recalc_rating(db, restaurant_id: int) -> RestaurantStats:
    """
    Re-compute avg_rating and review_count from the reviews collection and
    persist the updated values to the restaurant document.

    Returns a RestaurantStats with the freshly computed values.
    """
    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {
            "_id": None,
            "avg": {"$avg": "$rating"},
            "count": {"$sum": 1},
        }},
    ]
    result = list(db.reviews.aggregate(pipeline))
    if result:
        avg = round(float(result[0]["avg"]), 2)
        count = result[0]["count"]
    else:
        avg, count = 0.0, 0

    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"avg_rating": avg, "review_count": count,
                  "updated_at": datetime.utcnow()}},
    )
    return RestaurantStats(restaurant_id=restaurant_id, avg_rating=avg, review_count=count)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

_SORT_MAP = {
    "newest":         [("created_at", -1)],
    "oldest":         [("created_at",  1)],
    "highest_rating": [("rating",     -1)],
    "lowest_rating":  [("rating",      1)],
}


def get_paginated(db, restaurant_id: int, sort: str = "newest",
                  page: int = 1, limit: int = 10) -> Tuple[list, int]:
    _fetch_restaurant(db, restaurant_id)  # 404 guard

    sort_spec = _SORT_MAP.get(sort, [("created_at", -1)])
    filt = {"restaurant_id": restaurant_id}
    total = db.reviews.count_documents(filt)
    docs = list(
        db.reviews.find(filt)
        .sort(sort_spec)
        .skip((page - 1) * limit)
        .limit(limit)
    )
    reviews = [_enrich_review(db, _ns(d)) for d in docs]
    return reviews, total


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def create(db, user_id: int, restaurant_id: int,
           rating: int, comment: str) -> Tuple[object, RestaurantStats]:
    _fetch_restaurant(db, restaurant_id)

    if db.reviews.find_one({"restaurant_id": restaurant_id, "user_id": user_id}):
        raise ValueError("You have already reviewed this restaurant.")

    now = datetime.utcnow()
    review_id = _next_id(db, "reviews")
    doc = {
        "_id": review_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "rating": rating,
        "comment": comment,
        "photos": [],
        "created_at": now,
        "updated_at": now,
    }
    db.reviews.insert_one(doc)
    review = _enrich_review(db, _ns(doc))
    stats = recalc_rating(db, restaurant_id)
    return review, stats


def update(db, review_id: int, user_id: int,
           rating: Optional[int], comment: Optional[str]) -> Tuple[object, RestaurantStats]:
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only edit your own reviews.")

    updates = {"updated_at": datetime.utcnow()}
    if rating is not None:
        updates["rating"] = rating
    if comment is not None:
        updates["comment"] = comment

    db.reviews.update_one({"_id": review_id}, {"$set": updates})
    review = _enrich_review(db, _ns(db.reviews.find_one({"_id": review_id})))
    stats = recalc_rating(db, review.restaurant_id)
    return review, stats


def delete(db, review_id: int, user_id: int) -> RestaurantStats:
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only delete your own reviews.")

    restaurant_id = review.restaurant_id
    db.reviews.delete_one({"_id": review_id})
    return recalc_rating(db, restaurant_id)


def add_photo(db, review_id: int, user_id: int, photo_url: str) -> list:
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only add photos to your own reviews.")

    db.reviews.update_one(
        {"_id": review_id},
        {"$push": {"photos": photo_url}, "$set": {"updated_at": datetime.utcnow()}},
    )
    updated = _ns(db.reviews.find_one({"_id": review_id}))
    return updated.photos or []
