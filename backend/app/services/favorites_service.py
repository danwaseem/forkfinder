"""
Favorites service layer — MongoDB version.

Public API (unchanged):
    add(db, user_id, restaurant_id)         -> FavoriteToggleResponse
    remove(db, user_id, restaurant_id)      -> FavoriteToggleResponse
    get_for_user(db, user_id)               -> FavoritesListResponse
    is_favorite(db, user_id, restaurant_id) -> bool
"""

from datetime import datetime

from ..database import _next_id, _ns
from ..schemas.favorites import FavoriteItem, FavoriteRestaurant, FavoritesListResponse, FavoriteToggleResponse


def add(db, user_id: int, restaurant_id: int) -> FavoriteToggleResponse:
    r = db.restaurants.find_one({"_id": restaurant_id})
    if not r:
        raise LookupError(f"Restaurant {restaurant_id} not found.")
    if db.favorites.find_one({"user_id": user_id, "restaurant_id": restaurant_id}):
        raise ValueError("This restaurant is already in your favorites.")

    fav_id = _next_id(db, "favorites")
    db.favorites.insert_one({
        "_id": fav_id,
        "user_id": user_id,
        "restaurant_id": restaurant_id,
        "created_at": datetime.utcnow(),
    })
    return FavoriteToggleResponse(
        restaurant_id=restaurant_id, is_favorited=True, message="Added to favorites."
    )


def remove(db, user_id: int, restaurant_id: int) -> FavoriteToggleResponse:
    result = db.favorites.delete_one({"user_id": user_id, "restaurant_id": restaurant_id})
    if result.deleted_count == 0:
        raise ValueError("This restaurant is not in your favorites.")
    return FavoriteToggleResponse(
        restaurant_id=restaurant_id, is_favorited=False, message="Removed from favorites."
    )


def get_for_user(db, user_id: int) -> FavoritesListResponse:
    fav_docs = list(db.favorites.find({"user_id": user_id}).sort("created_at", -1))
    items = []
    for fav in fav_docs:
        r_doc = db.restaurants.find_one({"_id": fav["restaurant_id"]})
        if not r_doc:
            continue
        r = _ns(r_doc)
        items.append(FavoriteItem(
            favorited_at=fav["created_at"],
            restaurant=FavoriteRestaurant(
                id=r.id,
                name=r.name,
                description=r.description,
                cuisine_type=r.cuisine_type,
                price_range=r.price_range,
                city=r.city,
                state=r.state,
                country=r.country,
                photos=r.photos or [],
                avg_rating=r.avg_rating or 0.0,
                review_count=r.review_count or 0,
                is_claimed=r.is_claimed or False,
            ),
        ))
    return FavoritesListResponse(items=items, total=len(items))


def is_favorite(db, user_id: int, restaurant_id: int) -> bool:
    return bool(db.favorites.find_one({"user_id": user_id, "restaurant_id": restaurant_id}))
