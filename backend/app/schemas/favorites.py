"""
Favorites schemas.

FavoriteRestaurant    — restaurant shape embedded in every favorites response
FavoriteItem          — one entry in the list: restaurant + when it was favorited
FavoritesListResponse — GET /favorites/me
FavoriteToggleResponse— POST and DELETE /favorites/{restaurant_id}
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class FavoriteRestaurant(BaseModel):
    """Slim restaurant representation used inside favorites lists."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    photos: List[str] = []
    avg_rating: float = 0.0
    review_count: int = 0
    is_claimed: bool = False


class FavoriteItem(BaseModel):
    """One row in the favorites list — restaurant + timestamp it was saved."""

    restaurant: FavoriteRestaurant
    favorited_at: datetime


class FavoritesListResponse(BaseModel):
    """
    Returned by GET /favorites/me.

    Items are ordered most-recently-favorited first.

    **Example:**
    ```json
    {
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
            "is_claimed": true
          }
        }
      ],
      "total": 1
    }
    ```
    """

    items: List[FavoriteItem]
    total: int


class FavoriteToggleResponse(BaseModel):
    """
    Returned by POST and DELETE /favorites/{restaurant_id}.

    ``is_favorited`` reflects the state **after** the operation.

    **Example (add):**
    ```json
    { "restaurant_id": 5, "is_favorited": true,  "message": "Added to favorites." }
    ```

    **Example (remove):**
    ```json
    { "restaurant_id": 5, "is_favorited": false, "message": "Removed from favorites." }
    ```
    """

    restaurant_id: int
    is_favorited: bool
    message: str
