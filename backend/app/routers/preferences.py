"""
User preferences router.

Endpoints:
  GET  /preferences/me  — get the authenticated user's preferences
  PUT  /preferences/me  — create or update preferences (partial — only sent fields written)

Both endpoints work for reviewers (role="user") and owners (role="owner").
All business logic lives in services/preferences_service.py.
"""

from fastapi import APIRouter, Depends

from ..database import get_db
from ..schemas.preferences import (
    UserPreferencesIn,
    UserPreferencesOut,
)
from ..services import preferences_service
from ..utils.auth import get_current_user

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


@router.get(
    "/me",
    response_model=UserPreferencesOut,
    summary="Get my dining preferences",
    responses={
        200: {
            "description": "Current preferences with AI context",
            "content": {
                "application/json": {
                    "example": {
                        "cuisine_preferences": ["Italian", "Japanese"],
                        "price_range": "$$",
                        "search_radius": 15,
                        "preferred_locations": ["San Francisco", "Oakland"],
                        "dietary_restrictions": ["Gluten-Free"],
                        "ambiance_preferences": ["Casual", "Outdoor Seating"],
                        "sort_preference": "rating",
                        "updated_at": "2026-03-18T10:00:00",
                        "ai_context": {
                            "has_preferences": True,
                            "cuisine": ["Italian", "Japanese"],
                            "price_range": "$$",
                            "search_radius_miles": 15,
                            "preferred_locations": ["San Francisco", "Oakland"],
                            "dietary_needs": ["Gluten-Free"],
                            "ambiance": ["Casual", "Outdoor Seating"],
                            "sort_by": "rating",
                        },
                    }
                }
            },
        }
    },
)
def get_preferences(
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Return the authenticated user's dining preferences.

    If no preferences have been saved yet, all fields return their defaults
    (empty lists, search_radius=10, sort_preference="rating").

    The response always includes an ``ai_context`` field — a pre-built dict
    that the AI assistant uses directly for personalised recommendations.
    """
    return preferences_service.get(db, current_user.id)


@router.put(
    "/me",
    response_model=UserPreferencesOut,
    summary="Create or update my dining preferences",
    responses={
        200: {"description": "Updated preferences"},
        422: {"description": "Validation error — unknown enum value or out-of-range number"},
    },
)
def update_preferences(
    payload: UserPreferencesIn,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create or update dining preferences.  All fields are **optional** —
    only the fields you include are written; everything else keeps its
    current value.

    **Valid enum values:**

    | Field | Accepted values |
    |---|---|
    | `cuisine_preferences` | American, Italian, Mexican, Japanese, Chinese, Indian, Thai, French, Mediterranean, Korean, Vietnamese, Greek, Spanish, Middle Eastern, Caribbean, Ethiopian, Seafood, BBQ, Pizza, Burgers, Sushi, Vegan, Vegetarian |
    | `price_range` | `$` `$$` `$$$` `$$$$` |
    | `dietary_restrictions` | Vegetarian, Vegan, Gluten-Free, Halal, Kosher, Dairy-Free, Nut-Free, Low-Carb, Keto, Paleo, Shellfish-Free, Soy-Free |
    | `ambiance_preferences` | Casual, Fine Dining, Family-Friendly, Romantic, Outdoor Seating, Sports Bar, Live Music, Quick Bite, Brunch Spot, Late Night, Rooftop, Waterfront |
    | `sort_preference` | `rating` `newest` `most_reviewed` `price_asc` `price_desc` |

    String matching is **case-insensitive** — `"italian"` and `"Italian"` are both accepted.

    **Example request body:**
    ```json
    {
      "cuisine_preferences": ["Italian", "Sushi"],
      "price_range": "$$",
      "search_radius": 15,
      "preferred_locations": ["San Francisco", "Oakland"],
      "dietary_restrictions": ["Gluten-Free"],
      "ambiance_preferences": ["Casual", "Outdoor Seating"],
      "sort_preference": "rating"
    }
    ```

    **Partial update — only change price range:**
    ```json
    { "price_range": "$$$" }
    ```

    **Clear dietary restrictions:**
    ```json
    { "dietary_restrictions": [] }
    ```
    """
    return preferences_service.upsert(db, current_user.id, payload)
