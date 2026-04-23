"""
Preferences service layer — MongoDB version.

Preferences are now embedded as a 'preferences' subdocument inside each user
document.  No separate collection is needed.

Public API (unchanged):
    get(db, user_id)           -> UserPreferencesOut
    upsert(db, user_id, payload) -> UserPreferencesOut
    get_for_ai(db, user_id)    -> dict
"""

from datetime import datetime
from typing import Any, Dict

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


def _prefs_to_out(prefs: dict) -> UserPreferencesOut:
    """Convert a preferences subdocument dict to UserPreferencesOut."""
    if not prefs:
        return UserPreferencesOut()

    cuisines = _normalise_enum_list(prefs.get("cuisine_preferences", []), CuisineType)
    dietary  = _normalise_enum_list(prefs.get("dietary_restrictions", []),  DietaryRestriction)
    ambiance = _normalise_enum_list(prefs.get("ambiance_preferences", []),  AmbianceType)

    try:
        price = PriceRange(prefs["price_range"]) if prefs.get("price_range") else None
    except ValueError:
        price = None

    try:
        sort = SortPreference(prefs["sort_preference"]) if prefs.get("sort_preference") else SortPreference.rating
    except ValueError:
        sort = SortPreference.rating

    return UserPreferencesOut(
        cuisine_preferences=cuisines,
        price_range=price,
        search_radius=prefs.get("search_radius", 10),
        preferred_locations=prefs.get("preferred_locations", []),
        dietary_restrictions=dietary,
        ambiance_preferences=ambiance,
        sort_preference=sort,
        updated_at=prefs.get("updated_at"),
    )


def get(db, user_id: int) -> UserPreferencesOut:
    user_doc = db.users.find_one({"_id": user_id}, {"preferences": 1})
    if not user_doc:
        return UserPreferencesOut()
    return _prefs_to_out(user_doc.get("preferences") or {})


def upsert(db, user_id: int, payload: UserPreferencesIn) -> UserPreferencesOut:
    user_doc = db.users.find_one({"_id": user_id}, {"preferences": 1})
    existing = (user_doc or {}).get("preferences") or {}

    updates: Dict[str, Any] = {}

    if payload.cuisine_preferences is not None:
        updates["preferences.cuisine_preferences"] = [c.value for c in payload.cuisine_preferences]
    if payload.price_range is not None:
        updates["preferences.price_range"] = payload.price_range.value
    if payload.search_radius is not None:
        updates["preferences.search_radius"] = payload.search_radius
    if payload.preferred_locations is not None:
        updates["preferences.preferred_locations"] = payload.preferred_locations
    if payload.dietary_restrictions is not None:
        updates["preferences.dietary_restrictions"] = [d.value for d in payload.dietary_restrictions]
    if payload.ambiance_preferences is not None:
        updates["preferences.ambiance_preferences"] = [a.value for a in payload.ambiance_preferences]
    if payload.sort_preference is not None:
        updates["preferences.sort_preference"] = payload.sort_preference.value

    updates["preferences.updated_at"] = datetime.utcnow()
    updates["updated_at"] = datetime.utcnow()

    db.users.update_one({"_id": user_id}, {"$set": updates})

    # Re-fetch and return the merged result
    updated_doc = db.users.find_one({"_id": user_id}, {"preferences": 1})
    return _prefs_to_out((updated_doc or {}).get("preferences") or {})


def get_for_ai(db, user_id: int) -> Dict[str, Any]:
    """Return the ai_context dict used by the AI assistant service."""
    return get(db, user_id).ai_context
