"""
Restaurant request/response schemas.

Validation rules:
  - name:        1–255 characters (required on create)
  - price_range: one of "$" | "$$" | "$$$" | "$$$$"
  - phone:       international phone format
  - website:     must start with http:// or https://
  - latitude:    -90 to 90
  - longitude:   -180 to 180
  - hours:       dict keys must be valid day names
                 (monday–sunday, weekdays, weekends, everyday)
"""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.validators import PHONE_RE

# Day names accepted as keys in the hours dict
_VALID_DAYS = frozenset({
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "weekdays", "weekends", "everyday",
})


# ---------------------------------------------------------------------------
# Shared base — holds all validated fields
# ---------------------------------------------------------------------------

class _RestaurantBase(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    cuisine_type: Optional[str] = Field(None, max_length=100)
    price_range: Optional[Literal["$", "$$", "$$$", "$$$$"]] = None
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=30)
    website: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    hours: Optional[Dict[str, str]] = Field(
        None,
        description=(
            "Operating hours keyed by day name. "
            'E.g. {"monday": "11am-10pm", "tuesday": "11am-10pm"}'
        ),
        examples=[{"monday": "11am-10pm", "saturday": "10am-11pm", "sunday": "Closed"}],
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not PHONE_RE.match(v):
            raise ValueError(
                "Invalid phone format. "
                "Accepted: +1 (800) 555-0100 or 800-555-0100."
            )
        return v

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError('Website must start with "http://" or "https://".')
        return v

    @field_validator("hours")
    @classmethod
    def validate_hours(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        if v is None:
            return v
        bad = [k for k in v if k.lower() not in _VALID_DAYS]
        if bad:
            raise ValueError(
                f"Invalid day key(s): {bad}. "
                f"Use: monday, tuesday, wednesday, thursday, friday, "
                f"saturday, sunday, weekdays, weekends, or everyday."
            )
        # Normalise keys to lowercase
        return {k.lower(): str(val) for k, val in v.items()}


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class RestaurantCreate(_RestaurantBase):
    """
    Payload for POST /restaurants.

    ``name`` is the only required field.

    **Example:**
    ```json
    {
      "name": "Ristorante Bello",
      "description": "Authentic Neapolitan pizza since 1995.",
      "cuisine_type": "Italian",
      "price_range": "$$",
      "address": "123 Main St",
      "city": "San Francisco",
      "state": "CA",
      "country": "United States",
      "zip_code": "94102",
      "phone": "+1 (415) 555-0101",
      "website": "https://ristorantebello.com",
      "latitude": 37.7749,
      "longitude": -122.4194,
      "hours": {
        "monday": "11am-10pm",
        "tuesday": "11am-10pm",
        "wednesday": "11am-10pm",
        "thursday": "11am-10pm",
        "friday": "11am-11pm",
        "saturday": "10am-11pm",
        "sunday": "Closed"
      }
    }
    ```
    """
    name: str = Field(..., min_length=1, max_length=255)  # required on create


class RestaurantUpdate(_RestaurantBase):
    """
    Payload for PUT /restaurants/{id}.
    All fields optional — only supplied fields are written.
    """


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class RestaurantResponse(BaseModel):
    """Full restaurant object returned by all restaurant endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[Dict[str, str]] = None
    photos: Optional[List[str]] = None
    avg_rating: float = 0.0
    review_count: int = 0
    is_claimed: bool = False
    created_by: int
    claimed_by: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_favorited: bool = False


class RestaurantListResponse(BaseModel):
    """Paginated list of restaurants."""

    items: List[RestaurantResponse]
    total: int
    page: int
    limit: int
    pages: int


class ClaimResponse(BaseModel):
    """Returned by POST /restaurants/{id}/claim."""

    message: str
    restaurant_id: int
    claim_status: Literal["approved", "pending"]


class PhotosResponse(BaseModel):
    """Returned by POST /restaurants/{id}/photos."""

    photos: List[str]
