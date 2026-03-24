"""
Review service layer.

All business logic for reviews lives here.  The router handles HTTP
concerns (request parsing, response shaping, auth); this module handles
the database operations.

Public API:
    get_paginated(db, restaurant_id, sort, page, limit) -> (list[Review], total)
    create(db, user_id, restaurant_id, rating, comment) -> (Review, RestaurantStats)
    update(db, review_id, user_id, rating, comment)     -> (Review, RestaurantStats)
    delete(db, review_id, user_id)                      -> RestaurantStats
    recalc_rating(restaurant, db)                       -> RestaurantStats

Errors raised here are plain Python ValueError / PermissionError.
The router converts them to HTTPExceptions so this layer stays DB-only.
"""

import json
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..models.restaurant import Restaurant
from ..models.review import Review
from ..schemas.review import RestaurantStats


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

def _fetch_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if r is None:
        raise LookupError(f"Restaurant {restaurant_id} not found.")
    return r


def _fetch_review(db: Session, review_id: int) -> Review:
    rev = db.query(Review).filter(Review.id == review_id).first()
    if rev is None:
        raise LookupError(f"Review {review_id} not found.")
    return rev


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def recalc_rating(restaurant: Restaurant, db: Session) -> RestaurantStats:
    """
    Re-compute avg_rating and review_count from the reviews table and persist
    to the restaurant row.

    Must be called after any review create, update, or delete.
    Returns a RestaurantStats with the freshly committed values.
    """
    reviews = db.query(Review).filter(Review.restaurant_id == restaurant.id).all()
    count = len(reviews)
    avg = round(sum(r.rating for r in reviews) / count, 2) if count else 0.0

    restaurant.review_count = count
    restaurant.avg_rating = avg
    db.commit()

    return RestaurantStats(
        restaurant_id=restaurant.id,
        avg_rating=avg,
        review_count=count,
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

_SORT_COLS = {
    "newest":         Review.created_at.desc(),
    "oldest":         Review.created_at.asc(),
    "highest_rating": Review.rating.desc(),
    "lowest_rating":  Review.rating.asc(),
}


def get_paginated(
    db: Session,
    restaurant_id: int,
    sort: str = "newest",
    page: int = 1,
    limit: int = 10,
) -> Tuple[list, int]:
    """
    Return (reviews_page, total_count) for a restaurant.

    Raises LookupError if the restaurant doesn't exist.
    """
    _fetch_restaurant(db, restaurant_id)  # 404 guard

    order = _SORT_COLS.get(sort, Review.created_at.desc())
    base = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(order)
    )
    total = base.count()
    items = base.offset((page - 1) * limit).limit(limit).all()
    return items, total


# ---------------------------------------------------------------------------
# Write
# ---------------------------------------------------------------------------

def create(
    db: Session,
    user_id: int,
    restaurant_id: int,
    rating: int,
    comment: str,
) -> Tuple[Review, RestaurantStats]:
    """
    Create a review and return (new_review, updated_restaurant_stats).

    Raises:
        LookupError     — restaurant not found
        ValueError      — user has already reviewed this restaurant
    """
    r = _fetch_restaurant(db, restaurant_id)

    duplicate = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id, Review.user_id == user_id)
        .first()
    )
    if duplicate:
        raise ValueError("You have already reviewed this restaurant.")

    review = Review(
        user_id=user_id,
        restaurant_id=restaurant_id,
        rating=rating,
        comment=comment,
    )
    db.add(review)
    db.flush()   # write row and populate review.id without a full commit
    db.refresh(review)

    stats = recalc_rating(r, db)  # commits both the review and updated stats
    db.refresh(review)            # re-read after commit to get fresh timestamps
    return review, stats


def update(
    db: Session,
    review_id: int,
    user_id: int,
    rating: Optional[int],
    comment: Optional[str],
) -> Tuple[Review, RestaurantStats]:
    """
    Update a review and return (updated_review, updated_restaurant_stats).

    Raises:
        LookupError     — review not found
        PermissionError — review belongs to a different user
    """
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only edit your own reviews.")

    if rating is not None:
        review.rating = rating
    if comment is not None:
        review.comment = comment

    db.flush()

    r = _fetch_restaurant(db, review.restaurant_id)
    stats = recalc_rating(r, db)
    db.refresh(review)
    return review, stats


def delete(
    db: Session,
    review_id: int,
    user_id: int,
) -> RestaurantStats:
    """
    Delete a review and return updated_restaurant_stats.

    Raises:
        LookupError     — review not found
        PermissionError — review belongs to a different user
    """
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only delete your own reviews.")

    restaurant_id = review.restaurant_id
    db.delete(review)
    db.flush()   # remove the row before we recount

    r = _fetch_restaurant(db, restaurant_id)
    return recalc_rating(r, db)


def add_photo(
    db: Session,
    review_id: int,
    user_id: int,
    photo_url: str,
) -> list:
    """
    Append *photo_url* to the review's photos array.
    Returns the full updated photos list.

    Raises:
        LookupError     — review not found
        PermissionError — review belongs to a different user
    """
    review = _fetch_review(db, review_id)
    if review.user_id != user_id:
        raise PermissionError("You can only add photos to your own reviews.")

    existing = json.loads(review.photos) if review.photos else []
    existing.append(photo_url)
    review.photos = json.dumps(existing)
    db.commit()
    return existing
