"""
History service layer.

History is computed from existing data — no dedicated table needed:

  - Reviews written by the user        → queried from the reviews table
  - Restaurants added by the user      → queried from restaurants WHERE created_by = user_id

Public API:
    get_for_user(db, user_id) -> HistoryResponse
"""

import json

from sqlalchemy.orm import Session, joinedload

from ..models.restaurant import Restaurant
from ..models.review import Review
from ..schemas.history import (
    HistoryResponse,
    RestaurantHistoryItem,
    ReviewHistoryItem,
)


def _parse_json_list(value) -> list:
    """Safely parse a JSON-encoded list column; returns [] on any error."""
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []


def get_for_user(db: Session, user_id: int) -> HistoryResponse:
    """
    Build a full history response for *user_id*.

    Both lists are ordered newest-first (created_at DESC).
    """
    # --- Reviews written by this user -----------------------------------
    review_rows = (
        db.query(Review)
        .options(joinedload(Review.restaurant))
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    reviews = [
        ReviewHistoryItem(
            review_id=rev.id,
            restaurant_id=rev.restaurant_id,
            restaurant_name=rev.restaurant.name if rev.restaurant else "Unknown",
            restaurant_city=rev.restaurant.city if rev.restaurant else None,
            restaurant_cuisine=rev.restaurant.cuisine_type if rev.restaurant else None,
            restaurant_avg_rating=(
                rev.restaurant.avg_rating if rev.restaurant and rev.restaurant.avg_rating else 0.0
            ),
            rating=rev.rating,
            comment=rev.comment,
            photos=_parse_json_list(rev.photos),
            created_at=rev.created_at,
            updated_at=rev.updated_at,
        )
        for rev in review_rows
    ]

    # --- Restaurants added by this user ---------------------------------
    restaurant_rows = (
        db.query(Restaurant)
        .filter(Restaurant.created_by == user_id)
        .order_by(Restaurant.created_at.desc())
        .all()
    )

    restaurants_added = [
        RestaurantHistoryItem(
            id=r.id,
            name=r.name,
            cuisine_type=r.cuisine_type,
            price_range=r.price_range,
            city=r.city,
            state=r.state,
            country=r.country,
            photos=_parse_json_list(r.photos),
            avg_rating=r.avg_rating or 0.0,
            review_count=r.review_count or 0,
            is_claimed=r.is_claimed,
            created_at=r.created_at,
        )
        for r in restaurant_rows
    ]

    return HistoryResponse(
        reviews=reviews,
        restaurants_added=restaurants_added,
        total_reviews=len(reviews),
        total_restaurants_added=len(restaurants_added),
    )
