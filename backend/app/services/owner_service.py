"""
Owner service layer — MongoDB version.

Public API (unchanged signatures):
    get_restaurants(db, owner_id)
    get_restaurant_stats(db, owner_id, restaurant_id)
    get_dashboard(db, owner_id)
    get_restaurant_reviews(db, owner_id, restaurant_id, page, limit)
    get_all_reviews(db, owner_id, limit)
    update_restaurant(db, owner_id, restaurant_id, payload)
    claim_restaurant(db, owner_id, restaurant_id)
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from math import ceil
from typing import Any, Dict, List, Optional

from ..database import _next_id, _ns
from ..schemas.owner import (
    MonthlyTrend,
    OwnerDashboardResponse,
    OwnerRestaurantItem,
    OwnerRestaurantsListResponse,
    OwnerReviewItem,
    OwnerReviewsListResponse,
    RatingDistribution,
    RestaurantStatsResponse,
    SentimentSummary,
)
from ..schemas.restaurant import ClaimResponse, RestaurantUpdate

# ---------------------------------------------------------------------------
# Sentiment keyword sets (unchanged)
# ---------------------------------------------------------------------------

_POSITIVE_WORDS = frozenset([
    "great", "excellent", "amazing", "fantastic", "wonderful", "delicious",
    "love", "loved", "best", "perfect", "outstanding", "friendly", "recommend",
    "recommended", "fresh", "beautiful", "clean", "awesome", "superb",
    "incredible", "fabulous", "enjoyable", "tasty", "yummy", "cozy", "warm",
    "attentive", "generous", "good", "nice", "pleasant", "charming", "lovely",
    "impressive", "splendid", "satisfied", "happy",
])

_NEGATIVE_WORDS = frozenset([
    "bad", "terrible", "awful", "horrible", "disgusting", "worst", "rude",
    "slow", "cold", "dirty", "disappointed", "disappointing", "poor",
    "overpriced", "mediocre", "bland", "stale", "gross", "nasty",
    "unfriendly", "noisy", "crowded", "avoid", "never",
    "unpleasant", "underwhelming", "tasteless", "inedible", "unhappy",
    "neglected", "ignored", "wrong", "mistake", "error", "problem",
])

_TOKEN_RE = re.compile(r"[a-z]+")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _r_to_item(r_doc: dict) -> OwnerRestaurantItem:
    r = _ns(r_doc)
    return OwnerRestaurantItem(
        id=r.id,
        name=r.name,
        cuisine_type=r.cuisine_type,
        address=r.address,
        city=r.city,
        state=r.state,
        country=r.country,
        zip_code=r.zip_code,
        price_range=r.price_range,
        phone=r.phone,
        website=r.website,
        avg_rating=r.avg_rating or 0.0,
        review_count=r.review_count or 0,
        is_claimed=r.is_claimed or False,
        photos=r.photos or [],
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _rev_to_item(rev_doc: dict, restaurant_name: Optional[str] = None,
                 user_name: str = "Unknown", user_photo: Optional[str] = None) -> OwnerReviewItem:
    rev = _ns(rev_doc)
    return OwnerReviewItem(
        id=rev.id,
        restaurant_id=rev.restaurant_id,
        restaurant_name=restaurant_name,
        rating=rev.rating,
        comment=rev.comment,
        photos=rev.photos or [],
        user_name=user_name,
        user_photo=user_photo,
        created_at=rev.created_at,
    )


def _compute_distribution(review_docs: List[dict]) -> RatingDistribution:
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rev in review_docs:
        counts[rev.get("rating", 0)] = counts.get(rev.get("rating", 0), 0) + 1
    return RatingDistribution(
        star_1=counts[1], star_2=counts[2], star_3=counts[3],
        star_4=counts[4], star_5=counts[5],
    )


def _compute_monthly_trend(review_docs: List[dict]) -> List[MonthlyTrend]:
    now = datetime.utcnow()
    trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        count = sum(
            1 for rev in review_docs
            if month_start <= rev.get("created_at", datetime.min) < month_end
        )
        trend.append(MonthlyTrend(month=month_start.strftime("%b %Y"), count=count))
    return trend


def _compute_sentiment(review_docs: List[dict]) -> SentimentSummary:
    pos_total: Counter = Counter()
    neg_total: Counter = Counter()
    positive_reviews = negative_reviews = neutral_reviews = 0

    for rev in review_docs:
        comment = rev.get("comment") or ""
        words = _TOKEN_RE.findall(comment.lower())
        pos = sum(1 for w in words if w in _POSITIVE_WORDS)
        neg = sum(1 for w in words if w in _NEGATIVE_WORDS)
        for w in words:
            if w in _POSITIVE_WORDS:
                pos_total[w] += 1
            if w in _NEGATIVE_WORDS:
                neg_total[w] += 1
        if pos > neg:
            positive_reviews += 1
        elif neg > pos:
            negative_reviews += 1
        else:
            neutral_reviews += 1

    total = len(review_docs)
    if total == 0:
        return SentimentSummary(
            positive_count=0, negative_count=0, neutral_count=0,
            overall="neutral", top_positive_words=[], top_negative_words=[],
        )

    pos_ratio = positive_reviews / total
    neg_ratio = negative_reviews / total
    if pos_ratio >= 0.6:
        overall = "positive"
    elif neg_ratio >= 0.4:
        overall = "negative"
    elif pos_ratio >= 0.3 and neg_ratio >= 0.2:
        overall = "mixed"
    else:
        overall = "neutral"

    return SentimentSummary(
        positive_count=positive_reviews,
        negative_count=negative_reviews,
        neutral_count=neutral_reviews,
        overall=overall,
        top_positive_words=[w for w, _ in pos_total.most_common(5)],
        top_negative_words=[w for w, _ in neg_total.most_common(5)],
    )


def _get_owned_restaurants(db, owner_id: int) -> List[dict]:
    return list(
        db.restaurants.find({"$or": [{"created_by": owner_id}, {"claimed_by": owner_id}]})
        .sort("name", 1)
    )


def _assert_owns(r_doc: dict, owner_id: int) -> None:
    if r_doc.get("created_by") != owner_id and r_doc.get("claimed_by") != owner_id:
        raise PermissionError("Not your restaurant")


def _get_user_name_photo(db, user_id: int):
    u = db.users.find_one({"_id": user_id}, {"name": 1, "profile_photo_url": 1})
    if not u:
        return "Unknown", None
    return u.get("name", "Unknown"), u.get("profile_photo_url")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_restaurants(db, owner_id: int) -> OwnerRestaurantsListResponse:
    docs = _get_owned_restaurants(db, owner_id)
    return OwnerRestaurantsListResponse(items=[_r_to_item(d) for d in docs], total=len(docs))


def get_restaurant_stats(db, owner_id: int, restaurant_id: int) -> RestaurantStatsResponse:
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise LookupError("Restaurant not found")
    _assert_owns(r_doc, owner_id)

    all_reviews = list(db.reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1))
    fav_count = db.favorites.count_documents({"restaurant_id": restaurant_id})
    recent = all_reviews[:10]

    recent_items = []
    for rev_doc in recent:
        uname, uphoto = _get_user_name_photo(db, rev_doc["user_id"])
        recent_items.append(_rev_to_item(rev_doc, r_doc.get("name"), uname, uphoto))

    return RestaurantStatsResponse(
        restaurant=_r_to_item(r_doc),
        rating_distribution=_compute_distribution(all_reviews),
        monthly_trend=_compute_monthly_trend(all_reviews),
        recent_reviews=recent_items,
        sentiment=_compute_sentiment(all_reviews),
        total_favorites=fav_count,
    )


def get_dashboard(db, owner_id: int) -> OwnerDashboardResponse:
    restaurant_docs = _get_owned_restaurants(db, owner_id)
    restaurant_ids = [d["_id"] for d in restaurant_docs]

    empty_dist = RatingDistribution()
    empty_sent = SentimentSummary(
        positive_count=0, negative_count=0, neutral_count=0,
        overall="neutral", top_positive_words=[], top_negative_words=[],
    )

    if not restaurant_ids:
        return OwnerDashboardResponse(
            total_restaurants=0, total_reviews=0, avg_rating=0.0, total_favorites=0,
            rating_distribution=empty_dist, monthly_trend=_compute_monthly_trend([]),
            recent_reviews=[], sentiment=empty_sent, restaurants=[],
        )

    all_reviews = list(
        db.reviews.find({"restaurant_id": {"$in": restaurant_ids}}).sort("created_at", -1)
    )
    total_reviews = len(all_reviews)
    avg_rating = (
        round(sum(rev["rating"] for rev in all_reviews) / total_reviews, 2)
        if total_reviews > 0 else 0.0
    )
    fav_count = db.favorites.count_documents({"restaurant_id": {"$in": restaurant_ids}})
    recent = all_reviews[:10]

    recent_items = []
    for rev_doc in recent:
        uname, uphoto = _get_user_name_photo(db, rev_doc["user_id"])
        r_doc = db.restaurants.find_one({"_id": rev_doc["restaurant_id"]}, {"name": 1})
        recent_items.append(_rev_to_item(
            rev_doc, r_doc.get("name") if r_doc else None, uname, uphoto
        ))

    return OwnerDashboardResponse(
        total_restaurants=len(restaurant_docs),
        total_reviews=total_reviews,
        avg_rating=avg_rating,
        total_favorites=fav_count,
        rating_distribution=_compute_distribution(all_reviews),
        monthly_trend=_compute_monthly_trend(all_reviews),
        recent_reviews=recent_items,
        sentiment=_compute_sentiment(all_reviews),
        restaurants=[_r_to_item(d) for d in restaurant_docs],
    )


def get_restaurant_reviews(db, owner_id: int, restaurant_id: int,
                           page: int = 1, limit: int = 20) -> OwnerReviewsListResponse:
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise LookupError("Restaurant not found")
    _assert_owns(r_doc, owner_id)

    filt = {"restaurant_id": restaurant_id}
    total = db.reviews.count_documents(filt)
    reviews = list(
        db.reviews.find(filt).sort("created_at", -1)
        .skip((page - 1) * limit).limit(limit)
    )
    items = []
    for rev_doc in reviews:
        uname, uphoto = _get_user_name_photo(db, rev_doc["user_id"])
        items.append(_rev_to_item(rev_doc, r_doc.get("name"), uname, uphoto))

    return OwnerReviewsListResponse(
        items=items, total=total, page=page, limit=limit,
        pages=ceil(total / limit) if total > 0 else 1,
    )


def get_all_reviews(db, owner_id: int, limit: int = 50) -> OwnerReviewsListResponse:
    restaurant_ids = [d["_id"] for d in _get_owned_restaurants(db, owner_id)]
    if not restaurant_ids:
        return OwnerReviewsListResponse(items=[], total=0, page=1, limit=limit, pages=1)

    filt = {"restaurant_id": {"$in": restaurant_ids}}
    total = db.reviews.count_documents(filt)
    reviews = list(db.reviews.find(filt).sort("created_at", -1).limit(limit))

    items = []
    for rev_doc in reviews:
        uname, uphoto = _get_user_name_photo(db, rev_doc["user_id"])
        r_doc = db.restaurants.find_one({"_id": rev_doc["restaurant_id"]}, {"name": 1})
        items.append(_rev_to_item(
            rev_doc, r_doc.get("name") if r_doc else None, uname, uphoto
        ))

    return OwnerReviewsListResponse(
        items=items, total=total, page=1, limit=limit,
        pages=ceil(total / limit) if total > 0 else 1,
    )


def update_restaurant(db, owner_id: int, restaurant_id: int,
                      payload: RestaurantUpdate) -> dict:
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise LookupError("Restaurant not found")
    _assert_owns(r_doc, owner_id)

    updates = payload.model_dump(exclude_none=True)
    if updates:
        updates["updated_at"] = datetime.utcnow()
        db.restaurants.update_one({"_id": restaurant_id}, {"$set": updates})

    return db.restaurants.find_one({"_id": restaurant_id})


def claim_restaurant(db, owner_id: int, restaurant_id: int) -> ClaimResponse:
    r_doc = db.restaurants.find_one({"_id": restaurant_id})
    if not r_doc:
        raise LookupError("Restaurant not found")
    if r_doc.get("is_claimed"):
        raise ValueError("This restaurant has already been claimed by another owner.")
    if db.restaurant_claims.find_one({"restaurant_id": restaurant_id, "owner_id": owner_id}):
        raise ValueError("You have already submitted a claim for this restaurant.")

    claim_id = _next_id(db, "restaurant_claims")
    now = datetime.utcnow()
    db.restaurant_claims.insert_one({
        "_id": claim_id,
        "restaurant_id": restaurant_id,
        "owner_id": owner_id,
        "status": "approved",
        "created_at": now,
    })
    db.restaurants.update_one(
        {"_id": restaurant_id},
        {"$set": {"claimed_by": owner_id, "is_claimed": True, "updated_at": now}},
    )
    return ClaimResponse(
        message="Restaurant claimed successfully.",
        restaurant_id=restaurant_id,
        claim_status="approved",
    )
