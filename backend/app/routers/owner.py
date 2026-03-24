"""
Owner dashboard and restaurant management routes.

Endpoints:
  GET  /owner/me                           — get owner profile + restaurant list
  PUT  /owner/me                           — update owner profile
  POST /owner/me/photo                     — upload / replace profile photo
  GET  /owner/dashboard                    — aggregate stats across all owned restaurants
  GET  /owner/restaurants                  — list owned/claimed restaurants
  PUT  /owner/restaurants/{id}             — update an owned restaurant
  GET  /owner/restaurants/{id}/stats       — per-restaurant stats, trend, sentiment
  GET  /owner/restaurants/{id}/reviews     — paginated reviews for one restaurant
  POST /owner/restaurants/{id}/claim       — claim an unclaimed restaurant
  GET  /owner/reviews                      — recent reviews across all owned restaurants
"""

import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.owner import (
    OwnerDashboardResponse,
    OwnerRestaurantsListResponse,
    OwnerReviewsListResponse,
    RestaurantStatsResponse,
)
from ..schemas.restaurant import ClaimResponse, RestaurantResponse, RestaurantUpdate
from ..schemas.user import OwnerProfileResponse, OwnerProfileUpdate, PhotoUploadResponse
from ..services import owner_service
from ..utils.auth import get_current_user
from ..utils.file_upload import save_upload

router = APIRouter(prefix="/owner", tags=["Owner Dashboard"])


def _require_owner(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")
    return current_user


def _handle(exc: Exception) -> None:
    """Map service-layer exceptions to HTTP errors."""
    if isinstance(exc, LookupError):
        raise HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        raise HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=400, detail=str(exc))
    raise exc


# ---------------------------------------------------------------------------
# Owner profile
# ---------------------------------------------------------------------------

def _build_profile_response(current_user: User, db: Session) -> OwnerProfileResponse:
    from ..models.restaurant import Restaurant
    restaurants = (
        db.query(Restaurant)
        .filter(
            (Restaurant.created_by == current_user.id)
            | (Restaurant.claimed_by == current_user.id)
        )
        .order_by(Restaurant.name)
        .all()
    )
    return OwnerProfileResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        about_me=current_user.about_me,
        city=current_user.city,
        state=current_user.state,
        country=current_user.country,
        languages=current_user.languages,
        gender=current_user.gender,
        profile_photo_url=current_user.profile_photo_url,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        restaurants=restaurants,
    )


@router.get(
    "/me",
    response_model=OwnerProfileResponse,
    summary="Get owner profile",
    responses={
        200: {
            "description": "Owner profile with list of owned/claimed restaurants",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "Mario Rossi",
                        "email": "mario@ristorantebello.com",
                        "role": "owner",
                        "city": "San Francisco",
                        "state": "CA",
                        "country": "United States",
                        "profile_photo_url": None,
                        "created_at": "2026-01-01T08:00:00",
                        "restaurants": [
                            {
                                "id": 5,
                                "name": "Ristorante Bello",
                                "city": "San Francisco",
                                "avg_rating": 4.5,
                                "review_count": 32,
                                "is_claimed": True,
                            }
                        ],
                    }
                }
            },
        },
        401: {"description": "Missing or invalid token"},
        403: {"description": "Reviewer token — owner account required"},
    },
)
def get_owner_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """Return the owner's profile plus a summary of every restaurant they own or claimed."""
    return _build_profile_response(current_user, db)


@router.put(
    "/me",
    response_model=OwnerProfileResponse,
    summary="Update owner profile",
    responses={
        409: {"description": "Email already in use by another account"},
        422: {"description": "Validation error — invalid country, US state, or phone format"},
    },
)
def update_owner_profile(
    payload: OwnerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """Update one or more owner profile fields. All fields are optional."""
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
    return _build_profile_response(current_user, db)


@router.post(
    "/me/photo",
    response_model=PhotoUploadResponse,
    summary="Upload or replace owner profile photo",
    responses={400: {"description": "File too large or unsupported type"}},
)
def upload_owner_photo(
    file: UploadFile = File(..., description="JPEG, PNG, WEBP or GIF — max 5 MB"),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """Upload a profile photo for the restaurant owner account."""
    url = save_upload(file, "profiles")
    current_user.profile_photo_url = url
    db.commit()
    return PhotoUploadResponse(profile_photo_url=url)


# ---------------------------------------------------------------------------
# Owner dashboard
# ---------------------------------------------------------------------------

@router.get(
    "/dashboard",
    response_model=OwnerDashboardResponse,
    summary="Owner aggregate dashboard",
    responses={
        200: {
            "description": "Aggregate stats across all owned/claimed restaurants",
            "content": {
                "application/json": {
                    "example": {
                        "total_restaurants": 2,
                        "total_reviews": 75,
                        "avg_rating": 4.3,
                        "total_favorites": 120,
                        "rating_distribution": {
                            "star_1": 2, "star_2": 5, "star_3": 10,
                            "star_4": 28, "star_5": 30,
                        },
                        "monthly_trend": [
                            {"month": "Oct 2025", "count": 8},
                            {"month": "Nov 2025", "count": 12},
                            {"month": "Dec 2025", "count": 15},
                            {"month": "Jan 2026", "count": 10},
                            {"month": "Feb 2026", "count": 14},
                            {"month": "Mar 2026", "count": 16},
                        ],
                        "recent_reviews": [
                            {
                                "id": 88,
                                "restaurant_id": 5,
                                "restaurant_name": "Ristorante Bello",
                                "rating": 5,
                                "comment": "Best pasta in the city!",
                                "user_name": "Jane Doe",
                                "user_photo": None,
                                "created_at": "2026-03-20T18:30:00",
                            }
                        ],
                        "sentiment": {
                            "positive_count": 60,
                            "negative_count": 8,
                            "neutral_count": 7,
                            "overall": "positive",
                            "top_positive_words": ["great", "delicious", "cozy"],
                            "top_negative_words": ["slow", "noisy"],
                        },
                        "restaurants": [],
                    }
                }
            },
        },
        403: {"description": "Owner account required"},
    },
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    Aggregate statistics across **all** restaurants owned or claimed by this owner.

    Returns:
    - **total_restaurants** — number of restaurants
    - **total_reviews** — total reviews across all restaurants
    - **avg_rating** — weighted average rating
    - **total_favorites** — total times any owned restaurant was favorited
    - **rating_distribution** — star breakdown (1–5) across all reviews
    - **monthly_trend** — review count per month for the last 6 months
    - **recent_reviews** — 10 most recent reviews with reviewer info
    - **sentiment** — keyword-based sentiment analysis of all review text
    - **restaurants** — full list of owned restaurants with current stats
    """
    return owner_service.get_dashboard(db, owner_id=current_user.id)


# ---------------------------------------------------------------------------
# Owner restaurant management
# ---------------------------------------------------------------------------

@router.get(
    "/restaurants",
    response_model=OwnerRestaurantsListResponse,
    summary="List owned/claimed restaurants",
    responses={
        200: {
            "description": "All restaurants created or claimed by this owner",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 5,
                                "name": "Ristorante Bello",
                                "cuisine_type": "Italian",
                                "price_range": "$$",
                                "city": "San Francisco",
                                "state": "CA",
                                "country": "United States",
                                "avg_rating": 4.5,
                                "review_count": 32,
                                "is_claimed": True,
                                "photos": ["/uploads/restaurants/abc.jpg"],
                                "created_at": "2026-01-10T09:00:00",
                            }
                        ],
                        "total": 1,
                    }
                }
            },
        },
        403: {"description": "Owner account required"},
    },
)
def list_owner_restaurants(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """Return all restaurants the owner created or claimed, with current stats."""
    return owner_service.get_restaurants(db, owner_id=current_user.id)


@router.put(
    "/restaurants/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Update an owned restaurant",
    responses={
        403: {"description": "Not your restaurant"},
        404: {"description": "Restaurant not found"},
        422: {"description": "Validation error"},
    },
)
def update_owned_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    Partial update of an owned or claimed restaurant.
    All fields are optional — only supplied fields are written.
    """
    try:
        r = owner_service.update_restaurant(db, owner_id=current_user.id,
                                            restaurant_id=restaurant_id, payload=payload)
    except Exception as exc:
        _handle(exc)
        return  # unreachable; _handle always raises

    photos = r.photos
    try:
        photos = json.loads(photos) if photos else []
    except Exception:
        photos = []
    hours = r.hours
    try:
        hours = json.loads(hours) if hours else None
    except Exception:
        hours = None

    return RestaurantResponse(
        id=r.id, name=r.name, description=r.description,
        cuisine_type=r.cuisine_type, price_range=r.price_range,
        address=r.address, city=r.city, state=r.state,
        country=r.country, zip_code=r.zip_code,
        phone=r.phone, website=r.website,
        hours=hours, photos=photos,
        avg_rating=r.avg_rating or 0.0,
        review_count=r.review_count or 0,
        is_claimed=r.is_claimed or False,
        created_by=r.created_by, claimed_by=r.claimed_by,
        latitude=r.latitude, longitude=r.longitude,
        created_at=r.created_at, updated_at=r.updated_at,
        is_favorited=False,
    )


@router.get(
    "/restaurants/{restaurant_id}/stats",
    response_model=RestaurantStatsResponse,
    summary="Per-restaurant stats, trend, and sentiment",
    responses={
        403: {"description": "Not your restaurant"},
        404: {"description": "Restaurant not found"},
    },
)
def restaurant_stats(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    Detailed stats for a single owned restaurant:
    - rating distribution, 6-month review trend
    - 10 most recent reviews with reviewer names
    - keyword-based sentiment summary
    - total favorites count
    """
    try:
        return owner_service.get_restaurant_stats(db, owner_id=current_user.id,
                                                  restaurant_id=restaurant_id)
    except Exception as exc:
        _handle(exc)


@router.get(
    "/restaurants/{restaurant_id}/reviews",
    response_model=OwnerReviewsListResponse,
    summary="Paginated reviews for one owned restaurant",
    responses={
        403: {"description": "Not your restaurant"},
        404: {"description": "Restaurant not found"},
    },
)
def list_restaurant_reviews(
    restaurant_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    Paginated list of reviews for a specific owned restaurant.
    Sorted newest-first. Includes reviewer name and photo.
    """
    try:
        return owner_service.get_restaurant_reviews(
            db, owner_id=current_user.id,
            restaurant_id=restaurant_id, page=page, limit=limit,
        )
    except Exception as exc:
        _handle(exc)


@router.post(
    "/restaurants/{restaurant_id}/claim",
    response_model=ClaimResponse,
    summary="Claim an unclaimed restaurant",
    responses={
        400: {"description": "Already claimed or you already submitted a claim"},
        404: {"description": "Restaurant not found"},
    },
)
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    Claim ownership of an unclaimed restaurant listing.
    Claims are auto-approved — the restaurant is immediately assigned to this owner.
    """
    try:
        return owner_service.claim_restaurant(db, owner_id=current_user.id,
                                              restaurant_id=restaurant_id)
    except Exception as exc:
        _handle(exc)


# ---------------------------------------------------------------------------
# Cross-restaurant reviews
# ---------------------------------------------------------------------------

@router.get(
    "/reviews",
    response_model=OwnerReviewsListResponse,
    summary="Recent reviews across all owned restaurants",
    responses={
        200: {
            "description": "50 most recent reviews across all owned/claimed restaurants",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 88,
                                "restaurant_id": 5,
                                "restaurant_name": "Ristorante Bello",
                                "rating": 5,
                                "comment": "Best pasta in the city!",
                                "photos": [],
                                "user_name": "Jane Doe",
                                "user_photo": None,
                                "created_at": "2026-03-20T18:30:00",
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "limit": 50,
                        "pages": 1,
                    }
                }
            },
        },
        403: {"description": "Owner account required"},
    },
)
def all_owner_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(_require_owner),
):
    """
    The 50 most recent reviews across all restaurants owned or claimed by this owner.
    Each item includes the restaurant name, reviewer name, rating, comment, and photos.
    """
    return owner_service.get_all_reviews(db, owner_id=current_user.id)
