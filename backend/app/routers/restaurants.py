"""
Restaurant CRUD and discovery router.

Endpoints:
  GET    /restaurants                — public search + listing (optional auth for is_favorited)
  GET    /restaurants/{id}           — public single restaurant detail
  POST   /restaurants                — create (any authenticated user)
  PUT    /restaurants/{id}           — update (creator or claimed owner only)
  DELETE /restaurants/{id}           — delete (creator or claimed owner only)
  POST   /restaurants/{id}/photos    — upload photo (creator or claimed owner)
  POST   /restaurants/{id}/claim     — claim unclaimed restaurant (owner role only)

Search strategy (GET /restaurants):
  ?q         — ILIKE across name, cuisine_type, description, city, zip_code
  ?cuisine   — ILIKE filter on cuisine_type
  ?city      — ILIKE filter on city
  ?zip_code  — exact or ILIKE filter on zip_code
  ?price_range — exact match ("$", "$$", "$$$", "$$$$")
  ?rating_min  — avg_rating >= value

Sort strategy (?sort=):
  rating        (default) — avg_rating DESC
  newest                  — created_at DESC
  most_reviewed           — review_count DESC
  price_asc               — price_range ASC  ($ → $$$$)
  price_desc              — price_range DESC ($$$$  → $)

Average rating:
  Denormalised avg_rating and review_count columns on the Restaurant row.
  _recalc_rating() in reviews.py updates these on every review write.
  No aggregate query needed at read time.
"""

import json
import math
from typing import Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.favorite import Favorite
from ..models.restaurant import Restaurant, RestaurantClaim
from ..models.review import Review
from ..models.user import User
from ..schemas.restaurant import (
    ClaimResponse,
    PhotosResponse,
    RestaurantCreate,
    RestaurantListResponse,
    RestaurantResponse,
    RestaurantUpdate,
)
from ..utils.auth import get_current_user, get_optional_user
from ..utils.file_upload import MAX_PHOTOS_PER_RESTAURANT, save_upload

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serialize(r: Restaurant, favorite_ids: Optional[set] = None) -> dict:
    return {
        "id": r.id,
        "name": r.name,
        "description": r.description,
        "cuisine_type": r.cuisine_type,
        "price_range": r.price_range,
        "address": r.address,
        "city": r.city,
        "state": r.state,
        "country": r.country,
        "zip_code": r.zip_code,
        "phone": r.phone,
        "website": r.website,
        "hours": json.loads(r.hours) if r.hours else {},
        "photos": json.loads(r.photos) if r.photos else [],
        "avg_rating": r.avg_rating or 0.0,
        "review_count": r.review_count or 0,
        "is_claimed": r.is_claimed,
        "created_by": r.created_by,
        "claimed_by": r.claimed_by,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "created_at": r.created_at.isoformat(),
        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        "is_favorited": (r.id in favorite_ids) if favorite_ids is not None else False,
    }


def _assert_can_edit(r: Restaurant, user: User) -> None:
    """Raise 403 if *user* is neither the creator nor the claimed owner of *r*."""
    if r.created_by != user.id and r.claimed_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this restaurant.",
        )


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

_SORT_COLS = {
    "rating":        Restaurant.avg_rating.desc(),
    "newest":        Restaurant.created_at.desc(),
    "most_reviewed": Restaurant.review_count.desc(),
    "price_asc":     Restaurant.price_range.asc(),
    "price_desc":    Restaurant.price_range.desc(),
}


@router.get(
    "",
    response_model=RestaurantListResponse,
    summary="Search and list restaurants",
    responses={
        200: {
            "description": "Paginated restaurant list",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": 1,
                                "name": "Ristorante Bello",
                                "cuisine_type": "Italian",
                                "price_range": "$$",
                                "city": "San Francisco",
                                "avg_rating": 4.5,
                                "review_count": 32,
                                "is_favorited": False,
                            }
                        ],
                        "total": 1,
                        "page": 1,
                        "limit": 12,
                        "pages": 1,
                    }
                }
            },
        }
    },
)
def list_restaurants(
    q: Optional[str] = Query(
        None,
        description="Keyword search across name, cuisine, description, city, zip code.",
    ),
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type (partial match)."),
    city: Optional[str] = Query(None, description="Filter by city (partial match)."),
    zip_code: Optional[str] = Query(None, description="Filter by zip/postal code."),
    price_range: Optional[Literal["$", "$$", "$$$", "$$$$"]] = Query(
        None, description="Filter by exact price tier."
    ),
    rating_min: Optional[float] = Query(None, ge=0, le=5, description="Minimum average rating."),
    sort: Literal["rating", "newest", "most_reviewed", "price_asc", "price_desc"] = Query(
        "rating", description="Sort order."
    ),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Public endpoint — no auth required.

    Authenticated callers receive accurate ``is_favorited`` flags.
    Anonymous callers always get ``is_favorited: false``.

    **Search behaviour:** ``?q`` runs a case-insensitive LIKE across
    ``name``, ``cuisine_type``, ``description``, ``city``, and ``zip_code``.
    Combine with ``?cuisine``, ``?city``, ``?price_range``, ``?rating_min``
    to narrow results further.

    **Example:**
    `GET /restaurants?q=pizza&city=San+Francisco&price_range=%24%24&sort=rating&page=1&limit=12`
    """
    query = db.query(Restaurant)

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Restaurant.name.ilike(like),
                Restaurant.cuisine_type.ilike(like),
                Restaurant.description.ilike(like),
                Restaurant.city.ilike(like),
                Restaurant.zip_code.ilike(like),
            )
        )
    if cuisine:
        query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))
    if city:
        query = query.filter(Restaurant.city.ilike(f"%{city}%"))
    if zip_code:
        query = query.filter(Restaurant.zip_code.ilike(f"%{zip_code}%"))
    if price_range:
        query = query.filter(Restaurant.price_range == price_range)
    if rating_min is not None:
        query = query.filter(Restaurant.avg_rating >= rating_min)

    total = query.count()
    restaurants = (
        query
        .order_by(_SORT_COLS[sort])
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    # Build favorite set for authenticated callers
    fav_ids: Optional[set] = None
    if current_user:
        rows = (
            db.query(Favorite.restaurant_id)
            .filter(Favorite.user_id == current_user.id)
            .all()
        )
        fav_ids = {row.restaurant_id for row in rows}

    return {
        "items": [_serialize(r, fav_ids) for r in restaurants],
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 1,
    }


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Get restaurant details",
    responses={
        404: {"description": "Restaurant not found"},
    },
)
def get_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """
    Return full details for a single restaurant.

    Authenticated callers receive accurate ``is_favorited``.

    **Example response:**
    ```json
    {
      "id": 1,
      "name": "Ristorante Bello",
      "cuisine_type": "Italian",
      "price_range": "$$",
      "address": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "country": "United States",
      "zip_code": "94102",
      "phone": "+1 (415) 555-0101",
      "website": "https://ristorantebello.com",
      "hours": { "monday": "11am-10pm", "sunday": "Closed" },
      "photos": ["/uploads/restaurants/abc.jpg"],
      "avg_rating": 4.5,
      "review_count": 32,
      "is_claimed": true,
      "is_favorited": false,
      "created_at": "2026-01-10T09:00:00",
      "updated_at": "2026-03-18T12:00:00"
    }
    ```
    """
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    # Compute live aggregates from the reviews table so this endpoint always
    # returns the correct avg_rating and review_count even when the stored
    # denormalized fields are stale. Override in the response dict only —
    # never write back on a GET to avoid REST idempotency violations.
    agg = db.query(
        func.count(Review.id).label("cnt"),
        func.avg(Review.rating).label("avg"),
    ).filter(Review.restaurant_id == restaurant_id).one()
    live_count = agg.cnt or 0
    live_avg   = round(float(agg.avg), 2) if agg.avg else 0.0

    fav_ids: Optional[set] = None
    if current_user:
        is_fav = (
            db.query(Favorite)
            .filter(Favorite.user_id == current_user.id, Favorite.restaurant_id == r.id)
            .first()
        )
        fav_ids = {r.id} if is_fav else set()

    result = _serialize(r, fav_ids)
    result["avg_rating"]   = live_avg
    result["review_count"] = live_count
    return result


# ---------------------------------------------------------------------------
# Write endpoints — require auth
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a restaurant listing",
    responses={
        201: {"description": "Restaurant created"},
        422: {"description": "Validation error (price_range, phone, website, hours keys)"},
    },
)
def create_restaurant(
    payload: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Any authenticated user (reviewer **or** owner) can add a restaurant listing.

    The creator becomes ``created_by`` on the row.  Owners can later claim
    ownership via ``POST /restaurants/{id}/claim``.

    **Example request body:**
    ```json
    {
      "name": "Ristorante Bello",
      "cuisine_type": "Italian",
      "price_range": "$$",
      "city": "San Francisco",
      "state": "CA",
      "country": "United States",
      "hours": { "monday": "11am-10pm", "sunday": "Closed" }
    }
    ```
    """
    data = payload.model_dump(exclude_none=True, exclude={"hours"})
    r = Restaurant(
        created_by=current_user.id,
        **data,
        hours=json.dumps(payload.hours) if payload.hours else None,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
    summary="Update a restaurant",
    responses={
        403: {"description": "Not the creator or claimed owner"},
        404: {"description": "Restaurant not found"},
        422: {"description": "Validation error"},
    },
)
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update one or more fields of a restaurant.  All fields are optional.

    Only the user who created the listing **or** the owner who claimed it
    may edit it.  Any other authenticated user receives `403`.

    **Example request body (partial update):**
    ```json
    {
      "description": "Now open for brunch on weekends!",
      "hours": { "saturday": "10am-3pm", "sunday": "10am-3pm" }
    }
    ```
    """
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(r, current_user)

    data = payload.model_dump(exclude_none=True)
    if "hours" in data:
        data["hours"] = json.dumps(data["hours"])

    for field, value in data.items():
        setattr(r, field, value)

    db.commit()
    db.refresh(r)
    return _serialize(r)


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a restaurant",
    responses={
        403: {"description": "Not the creator or claimed owner"},
        404: {"description": "Restaurant not found"},
    },
)
def delete_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a restaurant listing.

    Only the user who created the listing **or** the owner who claimed it
    may delete it.  Returns `204 No Content` on success.
    """
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(r, current_user)
    db.delete(r)
    db.commit()


# ---------------------------------------------------------------------------
# Photo upload
# ---------------------------------------------------------------------------

@router.post(
    "/{restaurant_id}/photos",
    response_model=PhotosResponse,
    summary="Upload a restaurant photo",
    responses={
        400: {"description": "File too large or unsupported MIME type"},
        403: {"description": "Not the creator or claimed owner"},
        404: {"description": "Restaurant not found"},
    },
)
def upload_restaurant_photo(
    restaurant_id: int,
    file: UploadFile = File(..., description="JPEG, PNG, WEBP or GIF — max 5 MB"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Append a photo to the restaurant's photos array.
    Returns the full updated photos list.

    Maximum 5 MB per upload.  Accepted types: JPEG, PNG, WEBP, GIF.
    """
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(r, current_user)

    existing = json.loads(r.photos) if r.photos else []
    if len(existing) >= MAX_PHOTOS_PER_RESTAURANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_PHOTOS_PER_RESTAURANT} photos per restaurant.",
        )
    url = save_upload(file, "restaurants")
    existing.append(url)
    r.photos = json.dumps(existing)
    db.commit()
    return PhotosResponse(photos=existing)


# ---------------------------------------------------------------------------
# Ownership claim
# ---------------------------------------------------------------------------

@router.post(
    "/{restaurant_id}/claim",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Claim a restaurant as its owner",
    responses={
        400: {"description": "Already claimed, or you already submitted a claim"},
        403: {"description": "Only restaurant owners may claim restaurants"},
        404: {"description": "Restaurant not found"},
    },
)
def claim_restaurant(
    restaurant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Claim an unclaimed restaurant listing.

    Only users with `role == "owner"` may call this endpoint.

    For this project, claims are **auto-approved** — the restaurant is
    immediately marked as claimed and assigned to the calling owner.
    A ``RestaurantClaim`` row is also written for audit purposes.

    **Example response:**
    ```json
    {
      "message": "Restaurant claimed successfully.",
      "restaurant_id": 5,
      "claim_status": "approved"
    }
    ```
    """
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant owners may claim restaurants. "
                   "Register or log in with an owner account.",
        )

    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    if r.is_claimed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant has already been claimed by another owner.",
        )

    existing_claim = (
        db.query(RestaurantClaim)
        .filter(
            RestaurantClaim.restaurant_id == restaurant_id,
            RestaurantClaim.owner_id == current_user.id,
        )
        .first()
    )
    if existing_claim:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a claim for this restaurant.",
        )

    # Write audit row + immediately approve
    claim = RestaurantClaim(
        restaurant_id=restaurant_id,
        owner_id=current_user.id,
        status="approved",
    )
    db.add(claim)
    r.claimed_by = current_user.id
    r.is_claimed = True
    db.commit()

    return ClaimResponse(
        message="Restaurant claimed successfully.",
        restaurant_id=restaurant_id,
        claim_status="approved",
    )
