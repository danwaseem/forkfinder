"""
Favorites service layer.

All database logic for favorites lives here.

Public API:
    add(db, user_id, restaurant_id)    -> FavoriteToggleResponse
    remove(db, user_id, restaurant_id) -> FavoriteToggleResponse
    get_for_user(db, user_id)          -> FavoritesListResponse
    is_favorite(db, user_id, restaurant_id) -> bool

Errors:
    LookupError   — restaurant not found
    ValueError    — toggle conflict (already added / not in list)
"""

import json
from typing import List

from sqlalchemy.orm import Session

from ..models.favorite import Favorite
from ..models.restaurant import Restaurant
from ..schemas.favorites import (
    FavoriteItem,
    FavoriteRestaurant,
    FavoritesListResponse,
    FavoriteToggleResponse,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_json_list(value) -> list:
    """Safely parse a JSON-encoded list column; returns [] on any error."""
    if not value:
        return []
    try:
        return json.loads(value)
    except Exception:
        return []


def _fetch_restaurant(db: Session, restaurant_id: int) -> Restaurant:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if r is None:
        raise LookupError(f"Restaurant {restaurant_id} not found.")
    return r


def _to_favorite_restaurant(r: Restaurant) -> FavoriteRestaurant:
    return FavoriteRestaurant(
        id=r.id,
        name=r.name,
        description=r.description,
        cuisine_type=r.cuisine_type,
        price_range=r.price_range,
        city=r.city,
        state=r.state,
        country=r.country,
        photos=_parse_json_list(r.photos),
        avg_rating=r.avg_rating or 0.0,
        review_count=r.review_count or 0,
        is_claimed=r.is_claimed,
    )


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def add(db: Session, user_id: int, restaurant_id: int) -> FavoriteToggleResponse:
    """
    Mark a restaurant as a favorite.

    Raises:
        LookupError  — restaurant does not exist
        ValueError   — already in favorites
    """
    _fetch_restaurant(db, restaurant_id)

    existing = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)
        .first()
    )
    if existing:
        raise ValueError("This restaurant is already in your favorites.")

    db.add(Favorite(user_id=user_id, restaurant_id=restaurant_id))
    db.commit()

    return FavoriteToggleResponse(
        restaurant_id=restaurant_id,
        is_favorited=True,
        message="Added to favorites.",
    )


def remove(db: Session, user_id: int, restaurant_id: int) -> FavoriteToggleResponse:
    """
    Remove a restaurant from favorites.

    Raises:
        ValueError — not currently in favorites
    """
    fav = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)
        .first()
    )
    if not fav:
        raise ValueError("This restaurant is not in your favorites.")

    db.delete(fav)
    db.commit()

    return FavoriteToggleResponse(
        restaurant_id=restaurant_id,
        is_favorited=False,
        message="Removed from favorites.",
    )


def get_for_user(db: Session, user_id: int) -> FavoritesListResponse:
    """
    Return all favorites for a user, ordered most-recently-favorited first.

    Uses a JOIN so that ordering by favorites.created_at is preserved —
    a plain .in_() query against the restaurants table loses this order.
    """
    rows = (
        db.query(Favorite, Restaurant)
        .join(Restaurant, Favorite.restaurant_id == Restaurant.id)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.created_at.desc())
        .all()
    )

    items = [
        FavoriteItem(
            favorited_at=fav.created_at,
            restaurant=_to_favorite_restaurant(restaurant),
        )
        for fav, restaurant in rows
    ]

    return FavoritesListResponse(items=items, total=len(items))


def is_favorite(db: Session, user_id: int, restaurant_id: int) -> bool:
    """Return True if the user has favorited this restaurant."""
    return (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id, Favorite.restaurant_id == restaurant_id)
        .first()
    ) is not None
