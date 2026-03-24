"""
Reviewer (user-role) profile and account routes.

Endpoints:
  GET  /users/me               — get own profile
  PUT  /users/me               — update own profile (partial, all fields optional)
  POST /users/me/photo         — upload / replace profile photo
  GET  /users/me/preferences   — get dining preferences (legacy; prefer GET /preferences/me)
  PUT  /users/me/preferences   — update dining preferences (legacy; prefer PUT /preferences/me)
  GET  /users/me/favorites     — list favourited restaurants (legacy; prefer GET /favorites/me)
  GET  /users/me/history       — review history + restaurants added (legacy; prefer GET /history/me)

Note: /users/me/favorites and /users/me/history delegate to the service layer
so that business logic is not duplicated.
"""

import json

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User, UserPreferences
from ..schemas.favorites import FavoritesListResponse
from ..schemas.history import HistoryResponse
from ..schemas.user import (
    PhotoUploadResponse,
    UserPreferencesSchema,
    UserProfileUpdate,
    UserResponse,
)
from ..services import favorites_service, history_service
from ..utils.auth import get_current_user
from ..utils.file_upload import save_upload

router = APIRouter(prefix="/users", tags=["User Profile"])


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get own profile",
    responses={
        200: {
            "description": "Full reviewer profile",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "Jane Doe",
                        "email": "jane@example.com",
                        "role": "user",
                        "phone": "+1 (415) 555-0100",
                        "about_me": "Food lover and amateur critic.",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "United States",
                        "languages": "English, Spanish",
                        "gender": "female",
                        "profile_photo_url": "/uploads/profiles/abc.jpg",
                        "created_at": "2026-01-10T09:00:00",
                        "updated_at": "2026-03-18T12:00:00",
                    }
                }
            },
        },
        401: {"description": "Missing or invalid token"},
    },
)
def get_profile(current_user: User = Depends(get_current_user)):
    """Return the full profile of the authenticated user."""
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update own profile",
    responses={
        409: {"description": "Email already in use by another account"},
        422: {
            "description": "Validation error — invalid country, US state abbreviation, or phone format"
        },
    },
)
def update_profile(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update one or more profile fields.  All fields are optional — only supplied
    fields are written.

    **Validation rules:**
    - `country` must be a recognised English country name.
    - `state` must be a valid 2-letter USPS abbreviation when `country` is
      "United States" (e.g. "CA", "NY").  Free-form for all other countries.
    - `phone` must match international phone format.
    - `email` must be unique across all accounts.

    **Example request body:**
    ```json
    {
      "name": "Jane Doe",
      "phone": "+1 (415) 555-0100",
      "city": "San Francisco",
      "state": "CA",
      "country": "United States"
    }
    ```
    """
    if payload.email and payload.email != current_user.email:
        if db.query(User).filter(User.email == payload.email, User.id != current_user.id).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That email address is already in use by another account.",
            )

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.post(
    "/me/photo",
    response_model=PhotoUploadResponse,
    summary="Upload or replace profile photo",
    responses={
        200: {
            "description": "New profile photo URL",
            "content": {
                "application/json": {
                    "example": {"profile_photo_url": "/uploads/profiles/uuid-abc.jpg"}
                }
            },
        },
        400: {"description": "File too large (>5 MB) or unsupported MIME type"},
        401: {"description": "Missing or invalid token"},
    },
)
def upload_photo(
    file: UploadFile = File(..., description="JPEG, PNG, WEBP or GIF — max 5 MB"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a profile photo.  Replaces the existing photo URL (the old file is
    not deleted from disk, but is no longer referenced).

    Accepted MIME types: `image/jpeg`, `image/png`, `image/webp`, `image/gif`.
    Maximum file size: 5 MB.
    """
    url = save_upload(file, "profiles")
    current_user.profile_photo_url = url
    db.commit()
    return PhotoUploadResponse(profile_photo_url=url)


# ---------------------------------------------------------------------------
# Dining preferences
# ---------------------------------------------------------------------------

@router.get(
    "/me/preferences",
    response_model=UserPreferencesSchema,
    summary="Get dining preferences",
)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        return UserPreferencesSchema()

    def _parse(val):
        if val:
            try:
                return json.loads(val)
            except Exception:
                return []
        return []

    return UserPreferencesSchema(
        cuisine_preferences=_parse(prefs.cuisine_preferences),
        price_range=prefs.price_range,
        search_radius=prefs.search_radius,
        dietary_restrictions=_parse(prefs.dietary_restrictions),
        ambiance_preferences=_parse(prefs.ambiance_preferences),
        sort_preference=prefs.sort_preference,
    )


@router.put(
    "/me/preferences",
    response_model=UserPreferencesSchema,
    summary="Update dining preferences",
)
def update_preferences(
    payload: UserPreferencesSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prefs = db.query(UserPreferences).filter(UserPreferences.user_id == current_user.id).first()
    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.cuisine_preferences = json.dumps(payload.cuisine_preferences)
    prefs.price_range = payload.price_range
    prefs.search_radius = payload.search_radius
    prefs.dietary_restrictions = json.dumps(payload.dietary_restrictions)
    prefs.ambiance_preferences = json.dumps(payload.ambiance_preferences)
    prefs.sort_preference = payload.sort_preference

    db.commit()
    db.refresh(prefs)
    return payload


# ---------------------------------------------------------------------------
# Activity history  (legacy paths — delegate to service layer)
# ---------------------------------------------------------------------------

@router.get(
    "/me/favorites",
    response_model=FavoritesListResponse,
    summary="List favourited restaurants (legacy path — prefer GET /favorites/me)",
)
def get_favorites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy path kept for backwards compatibility. Delegates to favorites_service."""
    return favorites_service.get_for_user(db, user_id=current_user.id)


@router.get(
    "/me/history",
    response_model=HistoryResponse,
    summary="Review history and restaurants added (legacy path — prefer GET /history/me)",
)
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Legacy path kept for backwards compatibility. Delegates to history_service."""
    return history_service.get_for_user(db, user_id=current_user.id)
