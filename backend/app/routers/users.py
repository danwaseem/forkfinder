"""
Reviewer profile and account routes — MongoDB version.

Endpoints unchanged; SQLAlchemy replaced with pymongo.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from ..database import get_db
from ..schemas.favorites import FavoritesListResponse
from ..schemas.history import HistoryResponse
from ..schemas.user import (
    PhotoUploadResponse,
    UserPreferencesSchema,
    UserProfileUpdate,
    UserResponse,
)
from ..services import favorites_service, history_service, preferences_service
from ..utils.auth import get_current_user
from ..utils.file_upload import save_upload

router = APIRouter(prefix="/users", tags=["User Profile"])


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserResponse, summary="Get own profile")
def get_profile(current_user=Depends(get_current_user)):
    return dict(current_user)


@router.put("/me", response_model=UserResponse, summary="Update own profile")
def update_profile(
    payload: UserProfileUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if payload.email and payload.email != current_user.email:
        if db.users.find_one({"email": payload.email, "_id": {"$ne": current_user.id}}):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="That email address is already in use by another account.",
            )

    updates = payload.model_dump(exclude_none=True)
    if updates:
        updates["updated_at"] = datetime.utcnow()
        db.users.update_one({"_id": current_user.id}, {"$set": updates})

    updated = db.users.find_one({"_id": current_user.id})
    return {**updated, "id": updated["_id"]}


@router.post("/me/photo", response_model=PhotoUploadResponse, summary="Upload or replace profile photo")
def upload_photo(
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    url = save_upload(file, "profiles")
    db.users.update_one(
        {"_id": current_user.id},
        {"$set": {"profile_photo_url": url, "updated_at": datetime.utcnow()}},
    )
    return PhotoUploadResponse(profile_photo_url=url)


# ---------------------------------------------------------------------------
# Dining preferences (legacy paths — delegate to preferences_service)
# ---------------------------------------------------------------------------

@router.get("/me/preferences", response_model=UserPreferencesSchema, summary="Get dining preferences")
def get_preferences(db=Depends(get_db), current_user=Depends(get_current_user)):
    return preferences_service.get(db, current_user.id)


@router.put("/me/preferences", response_model=UserPreferencesSchema, summary="Update dining preferences")
def update_preferences(
    payload: UserPreferencesSchema,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    from ..schemas.preferences import UserPreferencesIn
    return preferences_service.upsert(db, current_user.id, UserPreferencesIn(**payload.model_dump()))


# ---------------------------------------------------------------------------
# Activity history (legacy paths — delegate to service layer)
# ---------------------------------------------------------------------------

@router.get("/me/favorites", response_model=FavoritesListResponse,
            summary="List favourited restaurants (legacy)")
def get_favorites(db=Depends(get_db), current_user=Depends(get_current_user)):
    return favorites_service.get_for_user(db, user_id=current_user.id)


@router.get("/me/history", response_model=HistoryResponse,
            summary="Review history and restaurants added (legacy)")
def get_history(db=Depends(get_db), current_user=Depends(get_current_user)):
    return history_service.get_for_user(db, user_id=current_user.id)
