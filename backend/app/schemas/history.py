"""
History schemas.

History is read-only — there are no write endpoints.
It is derived entirely from existing data (reviews + restaurants created_by).

ReviewHistoryItem      — one review the user wrote, with restaurant context
RestaurantHistoryItem  — one restaurant the user added to the platform
HistoryResponse        — GET /history/me  (combines both lists)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ReviewHistoryItem(BaseModel):
    """
    A review the authenticated user wrote, enriched with restaurant context
    so the frontend can render the history tab without extra API calls.
    """

    review_id: int
    restaurant_id: int
    restaurant_name: str
    restaurant_city: Optional[str] = None
    restaurant_cuisine: Optional[str] = None
    restaurant_avg_rating: float = 0.0
    rating: int
    comment: str
    photos: List[str] = []
    created_at: datetime
    updated_at: datetime


class RestaurantHistoryItem(BaseModel):
    """
    A restaurant listing the authenticated user submitted to the platform.
    Includes current rating so the user can see how their listing is doing.
    """

    id: int
    name: str
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    photos: List[str] = []
    avg_rating: float = 0.0
    review_count: int = 0
    is_claimed: bool = False
    created_at: datetime


class HistoryResponse(BaseModel):
    """
    Returned by GET /history/me.

    Both lists are ordered newest-first.

    **Example:**
    ```json
    {
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
          "updated_at": "2026-03-15T18:30:00"
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
          "is_claimed": false,
          "created_at": "2026-03-10T12:00:00"
        }
      ],
      "total_reviews": 1,
      "total_restaurants_added": 1
    }
    ```
    """

    reviews: List[ReviewHistoryItem]
    restaurants_added: List[RestaurantHistoryItem]
    total_reviews: int
    total_restaurants_added: int
