"""
Reviews router.

Endpoints:
  POST   /reviews                            — create review (restaurant_id in body)
  GET    /restaurants/{restaurant_id}/reviews — paginated + sorted review list (public)
  PUT    /reviews/{review_id}                — update own review
  DELETE /reviews/{review_id}               — delete own review
  POST   /reviews/{review_id}/photos        — upload photo to own review

Access rules:
  - Only role="user" (reviewers) may create, update, or delete reviews.
  - Restaurant owners (role="owner") may read reviews but not write them.
  - A user may review each restaurant at most once.
  - Only the review author may edit or delete their review.

Rating aggregation:
  avg_rating and review_count on the Restaurant row are recalculated (not
  aggregated at query time) on every create / update / delete via
  review_service.recalc_rating().  The updated values are returned in
  the response so clients can update their UI without an extra round-trip.
"""

import json
import math
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
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
    """Convert a Review ORM row to a dict matching ReviewResponse."""
    return {
        "id": rev.id,
        "user_id": rev.user_id,
        "restaurant_id": rev.restaurant_id,
        "rating": rev.rating,
        "comment": rev.comment,
        "photos": json.loads(rev.photos) if rev.photos else [],
        "created_at": rev.created_at,
        "updated_at": rev.updated_at,
        "user": {
            "id": rev.user.id,
            "name": rev.user.name,
            "profile_photo_url": rev.user.profile_photo_url,
        } if rev.user else None,
    }


def _require_reviewer(user: User) -> None:
    """Raise 403 if the user is a restaurant owner (owners are read-only on reviews)."""
    if user.role == "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Restaurant owners cannot write reviews. "
                   "Use a reviewer account to leave a review.",
        )


def _handle_service_error(exc: Exception) -> None:
    """Convert service-layer exceptions to appropriate HTTPExceptions."""
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    raise exc  # unexpected — let the global handler produce a 500


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

@router.post(
    "/reviews",
    response_model=ReviewWithStatsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review",
    responses={
        201: {
            "description": "Review created; includes updated restaurant stats",
            "content": {
                "application/json": {
                    "example": {
                        "review": {
                            "id": 12,
                            "user_id": 3,
                            "restaurant_id": 5,
                            "rating": 4,
                            "comment": "Great tacos, a bit slow on service.",
                            "photos": [],
                            "created_at": "2026-03-19T14:22:00",
                            "updated_at": "2026-03-19T14:22:00",
                            "user": {
                                "id": 3,
                                "name": "Jane Doe",
                                "profile_photo_url": None,
                            },
                        },
                        "restaurant_stats": {
                            "restaurant_id": 5,
                            "avg_rating": 4.2,
                            "review_count": 18,
                        },
                    }
                }
            },
        },
        400: {"description": "Already reviewed this restaurant"},
        403: {"description": "Owners cannot write reviews"},
        404: {"description": "Restaurant not found"},
        422: {"description": "Validation error — rating out of range or comment too short"},
    },
)
def create_review(
    payload: ReviewCreateBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a new review for a restaurant.

    **Rules:**
    - Only **reviewer** accounts (`role = "user"`) may write reviews.
      Restaurant owners (`role = "owner"`) are read-only.
    - Each user may review a given restaurant **once**.
      Use `PUT /reviews/{id}` to edit an existing review.
    - `rating` must be between 1 and 5.
    - `comment` must be at least 10 characters.

    Returns the created review **and** the restaurant's recalculated
    `avg_rating` and `review_count`.
    """
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
        return  # unreachable; _handle_service_error always raises

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


@router.post(
    "/restaurants/{restaurant_id}/reviews",
    response_model=ReviewWithStatsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a review (restaurant_id in URL)",
    responses={
        400: {"description": "Already reviewed this restaurant"},
        403: {"description": "Owners cannot write reviews"},
        404: {"description": "Restaurant not found"},
    },
)
def create_review_by_restaurant(
    restaurant_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Alternate create endpoint — `restaurant_id` is in the URL path.
    Identical behaviour to `POST /reviews`.
    """
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
        return  # unreachable

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

@router.get(
    "/restaurants/{restaurant_id}/reviews",
    response_model=ReviewPaginatedResponse,
    summary="List reviews for a restaurant",
    responses={404: {"description": "Restaurant not found"}},
)
def get_reviews(
    restaurant_id: int,
    sort: Literal["newest", "oldest", "highest_rating", "lowest_rating"] = Query(
        "newest", description="Sort order."
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Paginated, sortable list of reviews for a restaurant.

    **Public endpoint** — no authentication required.
    Both reviewers and restaurant owners can read reviews.

    | sort value       | order                       |
    |------------------|-----------------------------|
    | `newest`         | most recent first (default) |
    | `oldest`         | oldest first                |
    | `highest_rating` | 5 → 1                       |
    | `lowest_rating`  | 1 → 5                       |
    """
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

@router.put(
    "/reviews/{review_id}",
    response_model=ReviewWithStatsResponse,
    summary="Update a review",
    responses={
        403: {"description": "Not your review, or you are an owner"},
        404: {"description": "Review not found"},
        422: {"description": "Validation error"},
    },
)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update rating and/or comment on your own review.
    At least one field must be supplied.

    Returns the updated review **and** the restaurant's recalculated stats.

    **Example request:**
    ```json
    { "rating": 5, "comment": "Came back a second time — even better!" }
    ```
    """
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
        return  # unreachable

    return ReviewWithStatsResponse(
        review=ReviewResponse.model_validate(_serialize_review(review)),
        restaurant_stats=stats,
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

@router.delete(
    "/reviews/{review_id}",
    response_model=ReviewWithStatsResponse,
    summary="Delete a review",
    responses={
        403: {"description": "Not your review, or you are an owner"},
        404: {"description": "Review not found"},
    },
)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete your own review.

    Returns `review: null` and the restaurant's recalculated stats.

    **Example response:**
    ```json
    {
      "review": null,
      "restaurant_stats": { "restaurant_id": 5, "avg_rating": 4.1, "review_count": 17 }
    }
    ```
    """
    _require_reviewer(current_user)
    try:
        stats = review_service.delete(db, review_id=review_id, user_id=current_user.id)
    except Exception as exc:
        _handle_service_error(exc)
        return  # unreachable

    return ReviewWithStatsResponse(review=None, restaurant_stats=stats)


# ---------------------------------------------------------------------------
# Photo upload
# ---------------------------------------------------------------------------

@router.post(
    "/reviews/{review_id}/photos",
    response_model=ReviewPhotosResponse,
    summary="Upload a photo for a review",
    responses={
        400: {"description": "File too large or unsupported type"},
        403: {"description": "Not your review"},
        404: {"description": "Review not found"},
    },
)
def upload_review_photo(
    review_id: int,
    file: UploadFile = File(..., description="JPEG, PNG, WEBP or GIF — max 5 MB"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Append a photo to your review.
    Returns the full updated photos list.

    Maximum 5 MB per upload.  Accepted types: JPEG, PNG, WEBP, GIF.
    """
    _require_reviewer(current_user)

    # Check photo count before writing to disk
    from ..models.review import Review as ReviewModel
    rev = db.query(ReviewModel).filter(ReviewModel.id == review_id).first()
    if rev:
        import json as _json
        existing_photos = _json.loads(rev.photos) if rev.photos else []
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
        return  # unreachable

    return ReviewPhotosResponse(photos=photos)
