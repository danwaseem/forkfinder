"""
Preferences service layer.

All database read/write logic for user preferences lives here.
Both the preferences router and the AI assistant service import from this module.

Public API:
    get(db, user_id)                    -> UserPreferencesOut
    upsert(db, user_id, payload)        -> UserPreferencesOut
    get_for_ai(db, user_id)             -> dict  (the ai_context dict)
"""

import json
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models.user import UserPreferences
from ..schemas.preferences import (
    AmbianceType,
    CuisineType,
    DietaryRestriction,
    PriceRange,
    SortPreference,
    UserPreferencesIn,
    UserPreferencesOut,
    _normalise_enum_list,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _safe_json_load(value: Optional[str]) -> list:
    """Parse a JSON-encoded list column; return [] on missing/invalid data."""
    if not value:
        return []
    try:
        result = json.loads(value)
        return result if isinstance(result, list) else []
    except (ValueError, TypeError):
        return []


def _row_to_out(row: UserPreferences) -> UserPreferencesOut:
    """Convert a UserPreferences ORM row to UserPreferencesOut."""
    raw_cuisines  = _safe_json_load(row.cuisine_preferences)
    raw_dietary   = _safe_json_load(row.dietary_restrictions)
    raw_ambiance  = _safe_json_load(row.ambiance_preferences)
    raw_locations = _safe_json_load(row.preferred_locations)

    # Normalise stored strings back to enum instances (legacy data may have
    # been written without enum validation, so we use the tolerant normaliser).
    cuisines = _normalise_enum_list(raw_cuisines, CuisineType)
    dietary  = _normalise_enum_list(raw_dietary,  DietaryRestriction)
    ambiance = _normalise_enum_list(raw_ambiance, AmbianceType)

    try:
        price = PriceRange(row.price_range) if row.price_range else None
    except ValueError:
        price = None

    try:
        sort = SortPreference(row.sort_preference) if row.sort_preference else SortPreference.rating
    except ValueError:
        sort = SortPreference.rating

    return UserPreferencesOut(
        cuisine_preferences=cuisines,
        price_range=price,
        search_radius=row.search_radius or 10,
        preferred_locations=[str(loc) for loc in raw_locations],
        dietary_restrictions=dietary,
        ambiance_preferences=ambiance,
        sort_preference=sort,
        updated_at=row.updated_at,
    )


def _empty_out() -> UserPreferencesOut:
    return UserPreferencesOut()


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def get(db: Session, user_id: int) -> UserPreferencesOut:
    """
    Fetch preferences for *user_id*.

    Returns an empty UserPreferencesOut (all defaults) if no row exists yet,
    so callers never need to handle None.
    """
    row = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if row is None:
        return _empty_out()
    return _row_to_out(row)


def upsert(db: Session, user_id: int, payload: UserPreferencesIn) -> UserPreferencesOut:
    """
    Create or update preferences for *user_id*.

    Only fields that are explicitly provided (not None) are written.
    Fields not included in *payload* keep their existing values.
    """
    row = db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()
    if row is None:
        row = UserPreferences(user_id=user_id)
        db.add(row)

    if payload.cuisine_preferences is not None:
        row.cuisine_preferences = json.dumps([c.value for c in payload.cuisine_preferences])

    if payload.price_range is not None:
        row.price_range = payload.price_range.value

    if payload.search_radius is not None:
        row.search_radius = payload.search_radius

    if payload.preferred_locations is not None:
        row.preferred_locations = json.dumps(payload.preferred_locations)

    if payload.dietary_restrictions is not None:
        row.dietary_restrictions = json.dumps([d.value for d in payload.dietary_restrictions])

    if payload.ambiance_preferences is not None:
        row.ambiance_preferences = json.dumps([a.value for a in payload.ambiance_preferences])

    if payload.sort_preference is not None:
        row.sort_preference = payload.sort_preference.value

    db.commit()
    db.refresh(row)
    return _row_to_out(row)


def get_for_ai(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Return the ``ai_context`` dict for the AI assistant.

    This is the only function ai_service.py needs to call.
    The dict shape is stable — the AI prompt builder can destructure it
    without needing to know about Pydantic models or enums.

    Example output:
    ```json
    {
      "has_preferences": true,
      "cuisine": ["Italian", "Japanese"],
      "price_range": "$$",
      "search_radius_miles": 15,
      "preferred_locations": ["San Francisco"],
      "dietary_needs": ["Gluten-Free"],
      "ambiance": ["Casual", "Outdoor Seating"],
      "sort_by": "rating"
    }
    ```
    """
    return get(db, user_id).ai_context
