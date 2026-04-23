"""
History service layer — MongoDB version.

History is computed from existing data — no dedicated collection needed:
  - Reviews written by the user   → reviews collection WHERE user_id == user_id
  - Restaurants added by the user → restaurants collection WHERE created_by == user_id

Public API (unchanged):
    get_for_user(db, user_id) -> HistoryResponse
"""

from ..database import _ns
from ..schemas.history import (
    HistoryResponse,
    RestaurantHistoryItem,
    ReviewHistoryItem,
)


def get_for_user(db, user_id: int) -> HistoryResponse:
    # --- Reviews written by this user -----------------------------------
    review_docs = list(
        db.reviews.find({"user_id": user_id}).sort("created_at", -1)
    )

    reviews = []
    for rev_doc in review_docs:
        r_doc = db.restaurants.find_one({"_id": rev_doc["restaurant_id"]})
        r = _ns(r_doc)
        reviews.append(ReviewHistoryItem(
            review_id=rev_doc["_id"],
            restaurant_id=rev_doc["restaurant_id"],
            restaurant_name=r.name if r else "Unknown",
            restaurant_city=r.city if r else None,
            restaurant_cuisine=r.cuisine_type if r else None,
            restaurant_avg_rating=r.avg_rating if r and r.avg_rating else 0.0,
            rating=rev_doc["rating"],
            comment=rev_doc["comment"],
            photos=rev_doc.get("photos") or [],
            created_at=rev_doc["created_at"],
            updated_at=rev_doc.get("updated_at"),
        ))

    # --- Restaurants added by this user ---------------------------------
    restaurant_docs = list(
        db.restaurants.find({"created_by": user_id}).sort("created_at", -1)
    )

    restaurants_added = [
        RestaurantHistoryItem(
            id=r_doc["_id"],
            name=r_doc["name"],
            cuisine_type=r_doc.get("cuisine_type"),
            price_range=r_doc.get("price_range"),
            city=r_doc.get("city"),
            state=r_doc.get("state"),
            country=r_doc.get("country"),
            photos=r_doc.get("photos") or [],
            avg_rating=r_doc.get("avg_rating") or 0.0,
            review_count=r_doc.get("review_count") or 0,
            is_claimed=r_doc.get("is_claimed") or False,
            created_at=r_doc["created_at"],
        )
        for r_doc in restaurant_docs
    ]

    return HistoryResponse(
        reviews=reviews,
        restaurants_added=restaurants_added,
        total_reviews=len(reviews),
        total_restaurants_added=len(restaurants_added),
    )
