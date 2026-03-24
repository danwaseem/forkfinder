"""
User profile schemas.

UserProfileUpdate      — PATCH-style update for reviewer profiles (all fields optional).
OwnerProfileUpdate     — Same fields, same validators, same rules. Alias kept separate
                         so Swagger shows them under the correct operation.
UserResponse           — Full profile returned after GET /users/me or PUT /users/me.
OwnerProfileResponse   — Owner profile + their restaurants (returned by GET /owner/me).
PhotoUploadResponse    — Returned by POST /users/me/photo and POST /owner/me/photo.
UserPreferencesSchema  — Dining preferences (only relevant for reviewer accounts).
"""

import re
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from ..utils.validators import PHONE_RE, normalize_country, validate_us_state


# ---------------------------------------------------------------------------
# Shared update schema
# ---------------------------------------------------------------------------

class _BaseProfileUpdate(BaseModel):
    """Common validated fields for both reviewer and owner profile updates."""

    name: Optional[str] = Field(
        None, min_length=2, max_length=100,
        description="Full display name.",
        examples=["Jane Doe"],
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Must be unique across all accounts.",
        examples=["jane@example.com"],
    )
    phone: Optional[str] = Field(
        None, max_length=30,
        description="International format accepted. E.g. +1 (800) 555-0100",
        examples=["+1 (800) 555-0100"],
    )
    about_me: Optional[str] = Field(
        None, max_length=2000,
        description="Short bio (max 2 000 characters).",
    )
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(
        None, max_length=100,
        description="2-letter abbreviation when country is United States (e.g. 'CA'). "
                    "Free-form for all other countries.",
        examples=["CA"],
    )
    country: Optional[str] = Field(
        None,
        description="Standard English country name. E.g. 'United States', 'France'.",
        examples=["United States"],
    )
    languages: Optional[str] = Field(
        None, max_length=500,
        description="Comma-separated list of languages. E.g. 'English, Spanish'.",
        examples=["English, Spanish"],
    )
    gender: Optional[str] = Field(
        None, max_length=50,
        description="Gender identity (free-form).",
        examples=["Female"],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError(
                "Phone number format is invalid. "
                "Accepted formats: +1 (800) 555-0100 or 800-555-0100."
            )
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return normalize_country(v)  # raises ValueError with a clear message

    @field_validator("state")
    @classmethod
    def validate_state_format(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return v.strip()

    @model_validator(mode="after")
    def validate_state_for_us(self) -> "_BaseProfileUpdate":
        """Enforce 2-letter abbreviation when country is United States."""
        validate_us_state(self.state, self.country)
        return self


class UserProfileUpdate(_BaseProfileUpdate):
    """Profile update payload for reviewer accounts (POST /users/me)."""


class OwnerProfileUpdate(_BaseProfileUpdate):
    """Profile update payload for owner accounts (POST /owner/me)."""


# ---------------------------------------------------------------------------
# Photo upload response
# ---------------------------------------------------------------------------

class PhotoUploadResponse(BaseModel):
    profile_photo_url: str


# ---------------------------------------------------------------------------
# Read responses
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    profile_photo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OwnerRestaurantSummary(BaseModel):
    """Minimal restaurant info embedded in the owner profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    avg_rating: Optional[float] = None
    review_count: int = 0
    is_claimed: bool


class OwnerProfileResponse(BaseModel):
    """Owner profile — same personal fields as UserResponse plus their restaurants."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    about_me: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    languages: Optional[str] = None
    gender: Optional[str] = None
    profile_photo_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    restaurants: List[OwnerRestaurantSummary] = []


# ---------------------------------------------------------------------------
# Dining preferences (reviewer-only)
# ---------------------------------------------------------------------------

class UserPreferencesSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cuisine_preferences: Optional[List[str]] = []
    price_range: Optional[str] = None
    search_radius: Optional[int] = Field(default=10, ge=1, le=500)
    dietary_restrictions: Optional[List[str]] = []
    ambiance_preferences: Optional[List[str]] = []
    sort_preference: Optional[str] = "rating"
