"""
Review request/response schemas.

ReviewCreate          — body for POST /restaurants/{id}/reviews  (restaurant_id in URL)
ReviewCreateBody      — body for POST /reviews                   (restaurant_id in body)
ReviewUpdate          — body for PUT /reviews/{id}               (all fields optional)
ReviewResponse        — single review (used inside list and with-stats responses)
ReviewWithStatsResponse — review + updated restaurant avg_rating + review_count
ReviewPaginatedResponse — paginated review list (GET /restaurants/{id}/reviews)
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ReviewCreate(BaseModel):
    """Body for POST /restaurants/{restaurant_id}/reviews."""

    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5.")
    comment: str = Field(
        ..., min_length=10, max_length=5000,
        description="Review text (10–5 000 characters).",
        examples=["Amazing Neapolitan pizza — crispy crust, fresh ingredients. Will definitely return!"],
    )


class ReviewCreateBody(BaseModel):
    """
    Body for POST /reviews (restaurant_id supplied in body instead of URL).

    **Example:**
    ```json
    {
      "restaurant_id": 5,
      "rating": 4,
      "comment": "Great atmosphere and fantastic tacos. Service was a bit slow."
    }
    ```
    """

    restaurant_id: int = Field(..., description="ID of the restaurant being reviewed.")
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5.")
    comment: str = Field(
        ..., min_length=10, max_length=5000,
        description="Review text (10–5 000 characters).",
        examples=["Great atmosphere and fantastic tacos. Service was a bit slow."],
    )


class ReviewUpdate(BaseModel):
    """
    Body for PUT /reviews/{id}.  All fields optional.

    **Example — update only rating:**
    ```json
    { "rating": 5 }
    ```

    **Example — update both fields:**
    ```json
    { "rating": 3, "comment": "Changed my mind after a second visit — the quality dropped." }
    ```
    """

    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, min_length=10, max_length=5000)


# ---------------------------------------------------------------------------
# Embedded sub-schemas
# ---------------------------------------------------------------------------

class ReviewerInfo(BaseModel):
    """Minimal reviewer info embedded in every ReviewResponse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    profile_photo_url: Optional[str] = None


class RestaurantStats(BaseModel):
    """
    Updated restaurant stats returned after any write operation.

    Clients should use these values to update their local restaurant state
    without a separate GET /restaurants/{id} call.
    """

    restaurant_id: int
    avg_rating: float
    review_count: int


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ReviewResponse(BaseModel):
    """Single review — embedded in list and with-stats responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    restaurant_id: int
    rating: int
    comment: str
    photos: List[str] = []
    created_at: datetime
    updated_at: datetime
    user: Optional[ReviewerInfo] = None


class ReviewWithStatsResponse(BaseModel):
    """
    Returned by POST /reviews, PUT /reviews/{id}, DELETE /reviews/{id}.

    Includes the review itself **and** the restaurant's recalculated stats so
    the frontend can update both the review list and the restaurant card
    without an extra round-trip.

    On DELETE the ``review`` field is ``null`` (the row no longer exists).

    **Example (create / update):**
    ```json
    {
      "review": {
        "id": 12,
        "user_id": 3,
        "restaurant_id": 5,
        "rating": 4,
        "comment": "Great tacos, slow service.",
        "photos": [],
        "created_at": "2026-03-19T14:22:00",
        "updated_at": "2026-03-19T14:22:00",
        "user": { "id": 3, "name": "Jane Doe", "profile_photo_url": null }
      },
      "restaurant_stats": {
        "restaurant_id": 5,
        "avg_rating": 4.2,
        "review_count": 18
      }
    }
    ```

    **Example (delete):**
    ```json
    {
      "review": null,
      "restaurant_stats": { "restaurant_id": 5, "avg_rating": 4.1, "review_count": 17 }
    }
    ```
    """

    review: Optional[ReviewResponse]
    restaurant_stats: RestaurantStats


class ReviewPaginatedResponse(BaseModel):
    """Paginated list returned by GET /restaurants/{id}/reviews."""

    items: List[ReviewResponse]
    total: int
    page: int
    limit: int
    pages: int


class ReviewPhotosResponse(BaseModel):
    """Returned by POST /reviews/{id}/photos."""

    photos: List[str]
