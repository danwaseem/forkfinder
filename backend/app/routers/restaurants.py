"""
Restaurant CRUD and discovery router — MongoDB version.

Endpoints unchanged; only the data access layer switched from SQLAlchemy to pymongo.
Photos and hours are now native MongoDB arrays/dicts (no JSON string encoding).
"""

import math
import re
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from ..database import get_db, _next_id, _ns
from ..kafka import topics as kafka_topics
from ..kafka.producer import publish as kafka_publish
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

def _ilike(value: str) -> dict:
    return {"$regex": re.escape(value), "$options": "i"}


def _serialize(r, is_favorited: bool = False) -> dict:
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
        "hours": r.hours or {},
        "photos": r.photos or [],
        "avg_rating": r.avg_rating or 0.0,
        "review_count": r.review_count or 0,
        "is_claimed": r.is_claimed or False,
        "created_by": r.created_by,
        "claimed_by": r.claimed_by,
        "latitude": r.latitude,
        "longitude": r.longitude,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
        "is_favorited": is_favorited,
    }


def _assert_can_edit(r, user) -> None:
    if r.created_by != user.id and r.claimed_by != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to modify this restaurant.",
        )


# ---------------------------------------------------------------------------
# Sort helpers
# ---------------------------------------------------------------------------

_SORT_MAP: Dict[str, Any] = {
    "rating":        [("avg_rating", -1)],
    "newest":        [("created_at", -1)],
    "most_reviewed": [("review_count", -1)],
    "price_asc":     [("price_range", 1)],
    "price_desc":    [("price_range", -1)],
}


# ---------------------------------------------------------------------------
# Public read endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=RestaurantListResponse, summary="Search and list restaurants")
def list_restaurants(
    q: Optional[str] = Query(None),
    cuisine: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    zip_code: Optional[str] = Query(None),
    price_range: Optional[Literal["$", "$$", "$$$", "$$$$"]] = Query(None),
    rating_min: Optional[float] = Query(None, ge=0, le=5),
    sort: Literal["rating", "newest", "most_reviewed", "price_asc", "price_desc"] = Query("rating"),
    page: int = Query(1, ge=1),
    limit: int = Query(12, ge=1, le=100),
    db=Depends(get_db),
    current_user=Depends(get_optional_user),
):
    mongo_filter: Dict[str, Any] = {}

    if q:
        pat = _ilike(q)
        mongo_filter["$or"] = [
            {"name": pat}, {"cuisine_type": pat},
            {"description": pat}, {"city": pat}, {"zip_code": pat},
        ]
    if cuisine:
        mongo_filter["cuisine_type"] = _ilike(cuisine)
    if city:
        mongo_filter["city"] = _ilike(city)
    if zip_code:
        mongo_filter["zip_code"] = _ilike(zip_code)
    if price_range:
        mongo_filter["price_range"] = price_range
    if rating_min is not None:
        mongo_filter["avg_rating"] = {"$gte": rating_min}

    total = db.restaurants.count_documents(mongo_filter)
    docs = list(
        db.restaurants.find(mongo_filter)
        .sort(_SORT_MAP[sort])
        .skip((page - 1) * limit)
        .limit(limit)
    )

    fav_set: set = set()
    if current_user:
        favs = db.favorites.find(
            {"user_id": current_user.id},
            {"restaurant_id": 1},
        )
        fav_set = {f["restaurant_id"] for f in favs}

    items = [_serialize(_ns(d), d["_id"] in fav_set) for d in docs]

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": math.ceil(total / limit) if total else 1,
    }


@router.get("/{restaurant_id}", response_model=RestaurantResponse, summary="Get restaurant details")
def get_restaurant(
    restaurant_id: int,
    db=Depends(get_db),
    current_user=Depends(get_optional_user),
):
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")

    # Live aggregate for accurate stats
    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    agg = list(db.reviews.aggregate(pipeline))
    live_count = agg[0]["count"] if agg else 0
    live_avg = round(float(agg[0]["avg"]), 2) if agg else 0.0

    is_fav = False
    if current_user:
        is_fav = bool(db.favorites.find_one(
            {"user_id": current_user.id, "restaurant_id": restaurant_id}
        ))

    result = _serialize(_ns(r_doc), is_fav)
    result["avg_rating"] = live_avg
    result["review_count"] = live_count
    return result


# ---------------------------------------------------------------------------
# Write endpoints
# ---------------------------------------------------------------------------

@router.post("", response_model=RestaurantResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a restaurant listing")
def create_restaurant(
    payload: RestaurantCreate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    restaurant_id = _next_id(db, "restaurants")
    now = datetime.utcnow()
    data = payload.model_dump(exclude_none=True)
    doc = {
        "_id": restaurant_id,
        "created_by": current_user.id,
        "avg_rating": 0.0,
        "review_count": 0,
        "is_claimed": False,
        "claimed_by": None,
        "photos": [],
        "created_at": now,
        "updated_at": now,
        **data,
    }
    db.restaurants.insert_one(doc)

    kafka_publish(kafka_topics.RESTAURANT_CREATED, {
        "restaurant_id": restaurant_id,
        "name": doc.get("name"),
        "created_by": current_user.id,
        "created_at": now.isoformat(),
    })

    return _serialize(_ns(doc))


@router.put("/{restaurant_id}", response_model=RestaurantResponse, summary="Update a restaurant")
def update_restaurant(
    restaurant_id: int,
    payload: RestaurantUpdate,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(_ns(r_doc), current_user)

    updates = payload.model_dump(exclude_none=True)
    updates["updated_at"] = datetime.utcnow()
    db.restaurants.update_one({"_id": restaurant_id}, {"$set": updates})

    kafka_publish(kafka_topics.RESTAURANT_UPDATED, {
        "restaurant_id": restaurant_id,
        "updated_by": current_user.id,
        "updated_at": updates["updated_at"].isoformat(),
    })

    return _serialize(_ns(db.restaurants.find_one({"_id": restaurant_id})))


@router.delete("/{restaurant_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a restaurant")
def delete_restaurant(
    restaurant_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(_ns(r_doc), current_user)
    db.restaurants.delete_one({"_id": restaurant_id})


@router.post("/{restaurant_id}/photos", response_model=PhotosResponse,
             summary="Upload a restaurant photo")
def upload_restaurant_photo(
    restaurant_id: int,
    file: UploadFile = File(...),
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    _assert_can_edit(_ns(r_doc), current_user)

    existing = r_doc.get("photos") or []
    if len(existing) >= MAX_PHOTOS_PER_RESTAURANT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum of {MAX_PHOTOS_PER_RESTAURANT} photos per restaurant.",
        )
    url = save_upload(file, "restaurants")
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$push": {"photos": url}, "$set": {"updated_at": datetime.utcnow()}},
    )
    return PhotosResponse(photos=existing + [url])


@router.post("/{restaurant_id}/claim", response_model=ClaimResponse,
             status_code=status.HTTP_201_CREATED, summary="Claim a restaurant as its owner")
def claim_restaurant(
    restaurant_id: int,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only restaurant owners may claim restaurants.",
        )

    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Restaurant not found.")
    if r_doc.get("is_claimed"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This restaurant has already been claimed by another owner.",
        )
    if db.restaurant_claims.find_one({"restaurant_id": restaurant_id, "owner_id": current_user.id}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted a claim for this restaurant.",
        )

    now = datetime.utcnow()
    claim_id = _next_id(db, "restaurant_claims")
    db.restaurant_claims.insert_one({
        "_id": claim_id,
        "restaurant_id": restaurant_id,
        "owner_id": current_user.id,
        "status": "approved",
        "created_at": now,
    })
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"claimed_by": current_user.id, "is_claimed": True, "updated_at": now}},
    )

    kafka_publish(kafka_topics.RESTAURANT_CLAIMED, {
        "restaurant_id": restaurant_id,
        "claimed_by": current_user.id,
        "claimed_at": now.isoformat(),
    })

    return ClaimResponse(
        message="Restaurant claimed successfully.",
        restaurant_id=restaurant_id,
        claim_status="approved",
    )
