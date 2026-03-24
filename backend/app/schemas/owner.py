"""
Owner-specific response schemas.

Used by:
  GET  /owner/dashboard               — aggregate stats across all owned restaurants
  GET  /owner/restaurants             — list owned restaurants
  GET  /owner/restaurants/{id}/stats  — per-restaurant stats + sentiment
  GET  /owner/restaurants/{id}/reviews — per-restaurant review list (paginated)
  GET  /owner/reviews                 — all reviews across owned restaurants
"""

from datetime import datetime
from math import ceil
from typing import List, Literal, Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------

class RatingDistribution(BaseModel):
    star_1: int = 0
    star_2: int = 0
    star_3: int = 0
    star_4: int = 0
    star_5: int = 0


class MonthlyTrend(BaseModel):
    month: str       # "Jan 2026"
    count: int


class SentimentSummary(BaseModel):
    positive_count: int
    negative_count: int
    neutral_count: int
    overall: Literal["positive", "negative", "mixed", "neutral"]
    top_positive_words: List[str]
    top_negative_words: List[str]


class OwnerReviewItem(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: Optional[str] = None
    rating: int
    comment: str
    photos: List[str] = []
    user_name: str
    user_photo: Optional[str] = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Restaurant summaries used in lists and dashboard
# ---------------------------------------------------------------------------

class OwnerRestaurantItem(BaseModel):
    id: int
    name: str
    cuisine_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    price_range: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    avg_rating: float = 0.0
    review_count: int = 0
    is_claimed: bool = False
    photos: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Endpoint response models
# ---------------------------------------------------------------------------

class OwnerRestaurantsListResponse(BaseModel):
    items: List[OwnerRestaurantItem]
    total: int


class OwnerReviewsListResponse(BaseModel):
    items: List[OwnerReviewItem]
    total: int
    page: int
    limit: int
    pages: int


class RestaurantStatsResponse(BaseModel):
    restaurant: OwnerRestaurantItem
    rating_distribution: RatingDistribution
    monthly_trend: List[MonthlyTrend]
    recent_reviews: List[OwnerReviewItem]
    sentiment: SentimentSummary
    total_favorites: int


class OwnerDashboardResponse(BaseModel):
    total_restaurants: int
    total_reviews: int
    avg_rating: float
    total_favorites: int
    rating_distribution: RatingDistribution
    monthly_trend: List[MonthlyTrend]
    recent_reviews: List[OwnerReviewItem]
    sentiment: SentimentSummary
    restaurants: List[OwnerRestaurantItem]
