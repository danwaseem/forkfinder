"""
Owner service layer.

Handles all business logic for the /owner/* endpoints:
  - get_restaurants        — list all restaurants owned/claimed by a user
  - get_restaurant_stats   — per-restaurant rating distribution, trend, sentiment
  - get_dashboard          — aggregate stats across all owned restaurants
  - get_restaurant_reviews — paginated reviews for one restaurant (owner view)
  - get_all_reviews        — recent reviews across all owned restaurants
  - update_restaurant      — partial update of an owned restaurant
  - claim_restaurant       — claim an unclaimed restaurant

Raises standard Python exceptions that routers map to HTTP status codes:
  LookupError   → 404
  PermissionError → 403
  ValueError    → 400
"""

import json
import re
from collections import Counter
from datetime import datetime, timedelta
from math import ceil
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ..models.restaurant import Restaurant, RestaurantClaim
from ..models.review import Review
from ..models.user import User
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
from ..schemas.restaurant import ClaimResponse, RestaurantResponse, RestaurantUpdate

# ---------------------------------------------------------------------------
# Sentiment keyword sets
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
    "unfriendly", "noisy", "crowded", "avoid", "never", "disappointing",
    "unpleasant", "underwhelming", "tasteless", "inedible", "unhappy",
    "neglected", "ignored", "wrong", "mistake", "error", "problem",
])

_TOKEN_RE = re.compile(r"[a-z]+")


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_photos(photos_json: Optional[str]) -> List[str]:
    if not photos_json:
        return []
    try:
        return json.loads(photos_json)
    except Exception:
        return []


def _restaurant_to_item(r: Restaurant) -> OwnerRestaurantItem:
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
        photos=_parse_photos(r.photos),
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _review_to_item(rev: Review, restaurant_name: Optional[str] = None) -> OwnerReviewItem:
    return OwnerReviewItem(
        id=rev.id,
        restaurant_id=rev.restaurant_id,
        restaurant_name=restaurant_name or (rev.restaurant.name if rev.restaurant else None),
        rating=rev.rating,
        comment=rev.comment,
        photos=_parse_photos(rev.photos),
        user_name=rev.user.name if rev.user else "Unknown",
        user_photo=rev.user.profile_photo_url if rev.user else None,
        created_at=rev.created_at,
    )


def _compute_distribution(reviews: List[Review]) -> RatingDistribution:
    counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rev in reviews:
        counts[rev.rating] = counts.get(rev.rating, 0) + 1
    return RatingDistribution(
        star_1=counts[1],
        star_2=counts[2],
        star_3=counts[3],
        star_4=counts[4],
        star_5=counts[5],
    )


def _compute_monthly_trend(reviews: List[Review]) -> List[MonthlyTrend]:
    """Return review counts for each of the last 6 calendar months."""
    now = datetime.utcnow()
    trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        month_end = (month_start + timedelta(days=31)).replace(day=1)
        count = sum(1 for rev in reviews if month_start <= rev.created_at < month_end)
        trend.append(MonthlyTrend(month=month_start.strftime("%b %Y"), count=count))
    return trend


def _compute_sentiment(reviews: List[Review]) -> SentimentSummary:
    """Keyword-based sentiment — no ML required."""
    pos_total = Counter()
    neg_total = Counter()
    positive_reviews = 0
    negative_reviews = 0
    neutral_reviews = 0

    for rev in reviews:
        words = _TOKEN_RE.findall(rev.comment.lower())
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

    total = len(reviews)
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


def _get_owned_restaurants(db: Session, owner_id: int) -> List[Restaurant]:
    return (
        db.query(Restaurant)
        .filter(
            (Restaurant.created_by == owner_id) | (Restaurant.claimed_by == owner_id)
        )
        .order_by(Restaurant.name)
        .all()
    )


def _assert_owns(r: Restaurant, owner_id: int) -> None:
    if r.created_by != owner_id and r.claimed_by != owner_id:
        raise PermissionError("Not your restaurant")


def _get_favorites_count(db: Session, restaurant_ids: List[int]) -> int:
    if not restaurant_ids:
        return 0
    from ..models.favorite import Favorite
    return db.query(Favorite).filter(Favorite.restaurant_id.in_(restaurant_ids)).count()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_restaurants(db: Session, owner_id: int) -> OwnerRestaurantsListResponse:
    restaurants = _get_owned_restaurants(db, owner_id)
    items = [_restaurant_to_item(r) for r in restaurants]
    return OwnerRestaurantsListResponse(items=items, total=len(items))


def get_restaurant_stats(
    db: Session, owner_id: int, restaurant_id: int
) -> RestaurantStatsResponse:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise LookupError("Restaurant not found")
    _assert_owns(r, owner_id)

    all_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .all()
    )

    fav_count = _get_favorites_count(db, [restaurant_id])
    recent = all_reviews[:10]

    return RestaurantStatsResponse(
        restaurant=_restaurant_to_item(r),
        rating_distribution=_compute_distribution(all_reviews),
        monthly_trend=_compute_monthly_trend(all_reviews),
        recent_reviews=[_review_to_item(rev, r.name) for rev in recent],
        sentiment=_compute_sentiment(all_reviews),
        total_favorites=fav_count,
    )


def get_dashboard(db: Session, owner_id: int) -> OwnerDashboardResponse:
    restaurants = _get_owned_restaurants(db, owner_id)
    restaurant_ids = [r.id for r in restaurants]

    if not restaurant_ids:
        empty_dist = RatingDistribution()
        empty_sent = SentimentSummary(
            positive_count=0, negative_count=0, neutral_count=0,
            overall="neutral", top_positive_words=[], top_negative_words=[],
        )
        return OwnerDashboardResponse(
            total_restaurants=0,
            total_reviews=0,
            avg_rating=0.0,
            total_favorites=0,
            rating_distribution=empty_dist,
            monthly_trend=_compute_monthly_trend([]),
            recent_reviews=[],
            sentiment=empty_sent,
            restaurants=[],
        )

    all_reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .all()
    )

    total_reviews = len(all_reviews)
    avg_rating = (
        round(sum(rev.rating for rev in all_reviews) / total_reviews, 2)
        if total_reviews > 0 else 0.0
    )
    fav_count = _get_favorites_count(db, restaurant_ids)
    recent = all_reviews[:10]

    return OwnerDashboardResponse(
        total_restaurants=len(restaurants),
        total_reviews=total_reviews,
        avg_rating=avg_rating,
        total_favorites=fav_count,
        rating_distribution=_compute_distribution(all_reviews),
        monthly_trend=_compute_monthly_trend(all_reviews),
        recent_reviews=[_review_to_item(rev) for rev in recent],
        sentiment=_compute_sentiment(all_reviews),
        restaurants=[_restaurant_to_item(r) for r in restaurants],
    )


def get_restaurant_reviews(
    db: Session,
    owner_id: int,
    restaurant_id: int,
    page: int = 1,
    limit: int = 20,
) -> OwnerReviewsListResponse:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise LookupError("Restaurant not found")
    _assert_owns(r, owner_id)

    base_q = db.query(Review).filter(Review.restaurant_id == restaurant_id)
    total = base_q.count()
    reviews = (
        base_q
        .order_by(Review.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return OwnerReviewsListResponse(
        items=[_review_to_item(rev, r.name) for rev in reviews],
        total=total,
        page=page,
        limit=limit,
        pages=ceil(total / limit) if total > 0 else 1,
    )


def get_all_reviews(
    db: Session,
    owner_id: int,
    limit: int = 50,
) -> OwnerReviewsListResponse:
    restaurant_ids = [r.id for r in _get_owned_restaurants(db, owner_id)]
    if not restaurant_ids:
        return OwnerReviewsListResponse(items=[], total=0, page=1, limit=limit, pages=1)

    total = db.query(Review).filter(Review.restaurant_id.in_(restaurant_ids)).count()
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id.in_(restaurant_ids))
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )
    return OwnerReviewsListResponse(
        items=[_review_to_item(rev) for rev in reviews],
        total=total,
        page=1,
        limit=limit,
        pages=ceil(total / limit) if total > 0 else 1,
    )


def update_restaurant(
    db: Session, owner_id: int, restaurant_id: int, payload: RestaurantUpdate
) -> Restaurant:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise LookupError("Restaurant not found")
    _assert_owns(r, owner_id)

    data = payload.model_dump(exclude_none=True)
    if "hours" in data:
        data["hours"] = json.dumps(data["hours"])

    for field, value in data.items():
        setattr(r, field, value)

    db.commit()
    db.refresh(r)
    return r


def claim_restaurant(
    db: Session, owner_id: int, restaurant_id: int
) -> ClaimResponse:
    r = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not r:
        raise LookupError("Restaurant not found")

    if r.is_claimed:
        raise ValueError("This restaurant has already been claimed by another owner.")

    existing = (
        db.query(RestaurantClaim)
        .filter(
            RestaurantClaim.restaurant_id == restaurant_id,
            RestaurantClaim.owner_id == owner_id,
        )
        .first()
    )
    if existing:
        raise ValueError("You have already submitted a claim for this restaurant.")

    claim = RestaurantClaim(
        restaurant_id=restaurant_id,
        owner_id=owner_id,
        status="approved",
    )
    db.add(claim)
    r.claimed_by = owner_id
    r.is_claimed = True
    db.commit()

    return ClaimResponse(
        message="Restaurant claimed successfully.",
        restaurant_id=restaurant_id,
        claim_status="approved",
    )
