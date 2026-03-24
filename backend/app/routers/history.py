"""
History router.

Endpoints:
  GET /history/me — reviews written + restaurants added by the authenticated user

History is computed from existing data — no dedicated table is required:
  • Reviews     → reviews table WHERE user_id = me
  • Restaurants → restaurants table WHERE created_by = me

Both lists are ordered newest-first (created_at DESC).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.history import HistoryResponse
from ..services import history_service
from ..utils.auth import get_current_user

router = APIRouter(prefix="/history", tags=["History"])


@router.get(
    "/me",
    response_model=HistoryResponse,
    summary="Get my activity history",
    responses={
        200: {
            "description": "Reviews written and restaurants added by the user",
            "content": {
                "application/json": {
                    "example": {
                        "reviews": [
                            {
                                "review_id": 12,
                                "restaurant_id": 5,
                                "restaurant_name": "Ristorante Bello",
                                "restaurant_city": "San Francisco",
                                "restaurant_cuisine": "Italian",
                                "restaurant_avg_rating": 4.5,
                                "rating": 5,
                                "comment": "Best pizza in the city!",
                                "photos": [],
                                "created_at": "2026-03-15T18:30:00",
                                "updated_at": "2026-03-15T18:30:00",
                            }
                        ],
                        "restaurants_added": [
                            {
                                "id": 9,
                                "name": "New Thai Place",
                                "cuisine_type": "Thai",
                                "price_range": "$",
                                "city": "Oakland",
                                "avg_rating": 0.0,
                                "review_count": 0,
                                "is_claimed": False,
                                "created_at": "2026-03-10T12:00:00",
                            }
                        ],
                        "total_reviews": 1,
                        "total_restaurants_added": 1,
                    }
                }
            },
        }
    },
)
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return the authenticated user's activity history.

    **`reviews`** — every review the user has written, with the restaurant's
    name, city, cuisine, and current average rating embedded so the frontend
    can render the history tab without additional requests.

    **`restaurants_added`** — every restaurant listing the user submitted to
    the platform, with current rating and claim status.

    Both lists are sorted newest-first.
    Works for both reviewer (`role="user"`) and owner (`role="owner"`) accounts.
    """
    return history_service.get_for_user(db, user_id=current_user.id)
