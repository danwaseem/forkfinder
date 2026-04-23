"""
Reviews router — MongoDB version.

Endpoints unchanged; SQLAlchemy imports replaced with pymongo via review_service.
Photos are now native MongoDB arrays (no json.loads needed).
"""

import math
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from ..database import get_db
from ..kafka import topics as kafka_topics
from ..kafka.producer import publish as kafka_publish
from ..schemas.review import (
    ReviewCreate,
    ReviewCreateBody,
    ReviewPaginatedResponse,
    ReviewPhotosResponse,
    ReviewResponse,
    ReviewUpdate,
    ReviewWithStatsResponse,
)
from ..services import review_service
from ..utils.auth import get_current_user
from ..utils.file_upload import MAX_PHOTOS_PER_REVIEW, save_upload

router = APIRouter(tags=["Reviews"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialize_review(rev) -> dict:
    """Convert a review MongoDoc to a dict matching ReviewResponse."""
    return {
        "id": rev.id,
        "user_id": rev.user_id,
        "restaurant_id": rev.restaurant_id,
        "rating": rev.rating,
        "comment": rev.comment,
        "photos": rev.photos or [],
        "created_at": rev.created_at,
        "updated_at": rev.updated_at,
        "user": {
            "id": rev.user.id,
            "name": rev.user.name,
            "profile_photo_url": rev.user.profile_photo_url,
        } if rev.user else None,
    }


def _require_reviewer(user) -> None:
    if user.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant owners cannot write reviews. "
                   "Use a reviewer account to leave a review.",
        )


def _handle_service_error(exc: Exception) -> None:
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post("/reviews", response_model=ReviewWithStatsResponse,
             status_code=status.HTTP_201_CREATED, summary="Create a review")
def create_review(
    payload: ReviewCreateBody,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_reviewer(current_user)
    try:
        review, stats = review_service.create(
            db,
            user_id=current_user.id,
            restaurant_id=payload.restaurant_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except Exception as exc:
        _handle_service_error(exc)
        return

    kafka_publish(kafka_topics.REVIEW_CREATED, {
        "review_id": review.id,
        "user_id": review.user_id,
        "restaurant_id": review.restaurant_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    })

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


@router.post("/restaurants/{restaurant_id}/reviews", response_model=ReviewWithStatsResponse,
             status_code=status.HTTP_201_CREATED, summary="Create a review (restaurant_id in URL)")
def create_review_by_restaurant(
    restaurant_id: int,
    payload: ReviewCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_reviewer(current_user)
    try:
        review, stats = review_service.create(
            db,
            user_id=current_user.id,
            restaurant_id=restaurant_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except Exception as exc:
        _handle_service_error(exc)
        return

    kafka_publish(kafka_topics.REVIEW_CREATED, {
        "review_id": review.id,
        "user_id": review.user_id,
        "restaurant_id": review.restaurant_id,
        "rating": review.rating,
        "comment": review.comment,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    })

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@router.get("/restaurants/{restaurant_id}/reviews", response_model=ReviewPaginatedResponse,
            summary="List reviews for a restaurant")
def get_reviews(
    restaurant_id: int,
    sort: Literal["newest", "oldest", "highest_rating", "lowest_rating"] = Query("newest"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db=Depends(get_db),
):
    try:
        reviews, total = review_service.get_paginated(
            db, restaurant_id, sort=sort, page=page, limit=limit
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return ReviewPaginatedResponse(
        items=[ReviewResponse.model_validate(_serialize_review(r)) for r in reviews],
        total=total,
        page=page,
        limit=limit,
        pages=math.ceil(total / limit) if total else 1,
    )


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------

@router.put("/reviews/{review_id}", response_model=ReviewWithStatsResponse,
            summary="Update a review")
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_reviewer(current_user)
    if payload.rating is None and payload.comment is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Supply at least one field to update (rating or comment).",
        )
    try:
        review, stats = review_service.update(
            db,
            review_id=review_id,
            user_id=current_user.id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except Exception as exc:
        _handle_service_error(exc)
        return

    kafka_publish(kafka_topics.REVIEW_UPDATED, {
        "review_id": review.id,
        "user_id": review.user_id,
        "restaurant_id": review.restaurant_id,
        "rating": review.rating,
        "comment": review.comment,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None,
    })

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete("/reviews/{review_id}", response_model=ReviewWithStatsResponse,
               summary="Delete a review")
def delete_review(
    review_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_reviewer(current_user)

    rev_doc = db.reviews.find_one({"_id": review_id})
    _del_user_id = rev_doc["user_id"] if rev_doc else current_user.id
    _del_restaurant_id = rev_doc["restaurant_id"] if rev_doc else None

    try:
        stats = review_service.delete(db, review_id=review_id, user_id=current_user.id)
    except Exception as exc:
        _handle_service_error(exc)
        return

    kafka_publish(kafka_topics.REVIEW_DELETED, {
        "review_id": review_id,
        "user_id": _del_user_id,
        "restaurant_id": _del_restaurant_id,
    })

    return ReviewWithStatsResponse(review=None, restaurant_stats=stats)


# ---------------------------------------------------------------------------
# Photo upload
# ---------------------------------------------------------------------------

@router.post("/reviews/{review_id}/photos", response_model=ReviewPhotosResponse,
             summary="Upload a photo for a review")
def upload_review_photo(
    review_id: int,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    _require_reviewer(current_user)

    rev_doc = db.reviews.find_one({"_id": review_id})
    if rev_doc:
        existing_photos = rev_doc.get("photos") or []
        if len(existing_photos) >= MAX_PHOTOS_PER_REVIEW:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Maximum of {MAX_PHOTOS_PER_REVIEW} photos per review.",
            )

    url = save_upload(file, "reviews")
    try:
        photos = review_service.add_photo(
            db, review_id=review_id, user_id=current_user.id, photo_url=url
        )
    except Exception as exc:
        _handle_service_error(exc)
        return

    return ReviewPhotosResponse(photos=photos)
