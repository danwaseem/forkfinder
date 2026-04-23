"""
Favorites router.

Endpoints:
  POST   /favorites/{restaurant_id}  — mark a restaurant as favorite
  DELETE /favorites/{restaurant_id}  — remove from favorites
  GET    /favorites/me               — list all favorites (newest first)

Access:
  All three endpoints require authentication.
  Both reviewer and owner accounts may favorite restaurants.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..schemas.favorites import FavoritesListResponse, FavoriteToggleResponse
from ..services import favorites_service
from ..utils.auth import get_current_user

router = APIRouter(prefix="/favorites", tags=["Favorites"])


def _handle(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Toggle endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{restaurant_id}",
    response_model=FavoriteToggleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a restaurant to favorites",
    responses={
        201: {
            "description": "Restaurant added",
            "content": {
                "application/json": {
                    "example": {
                        "restaurant_id": 5,
                        "is_favorited": True,
                        "message": "Added to favorites.",
                    }
                }
            },
        },
        400: {"description": "Already in favorites"},
        404: {"description": "Restaurant not found"},
    },
)
def add_favorite(
    restaurant_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Mark a restaurant as a favorite for the authenticated user.

    Returns `400` if already favorited — use `DELETE` to unfavorite first.
    """
    try:
        return favorites_service.add(db, user_id=current_user.id, restaurant_id=restaurant_id)
    except Exception as exc:
        _handle(exc)


@router.delete(
    "/{restaurant_id}",
    response_model=FavoriteToggleResponse,
    summary="Remove a restaurant from favorites",
    responses={
        200: {
            "description": "Restaurant removed",
            "content": {
                "application/json": {
                    "example": {
                        "restaurant_id": 5,
                        "is_favorited": False,
                        "message": "Removed from favorites.",
                    }
                }
            },
        },
        400: {"description": "Not in favorites"},
    },
)
def remove_favorite(
    restaurant_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Remove a restaurant from the authenticated user's favorites.

    Returns `400` if it was not favorited.
    """
    try:
        return favorites_service.remove(db, user_id=current_user.id, restaurant_id=restaurant_id)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=FavoritesListResponse,
    summary="List my favorites",
    responses={
        200: {
            "description": "Favorited restaurants, newest first",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "favorited_at": "2026-03-18T20:15:00",
                                "restaurant": {
                                    "id": 5,
                                    "name": "Ristorante Bello",
                                    "cuisine_type": "Italian",
                                    "price_range": "$$",
                                    "city": "San Francisco",
                                    "avg_rating": 4.5,
                                    "review_count": 32,
                                    "photos": ["/uploads/restaurants/abc.jpg"],
                                    "is_claimed": True,
                                },
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        }
    },
)
def get_favorites(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return all restaurants the authenticated user has favorited,
    ordered most-recently-favorited first.

    Always returns `is_favorited: true` on every item (all results are
    by definition favorited by this user).
    """
    return favorites_service.get_for_user(db, user_id=current_user.id)
