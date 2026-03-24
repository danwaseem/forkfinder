"""
User preferences schemas.

Enums define the valid vocabulary for each preference dimension.
The AI assistant reads UserPreferencesOut.ai_context — a pre-built dict
that drops empty fields and formats everything into strings the LLM prompt
can include directly.

Input  → UserPreferencesIn   (all fields optional; arrays accept any order)
Output → UserPreferencesOut  (read shape; includes computed ai_context field)
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator


# ---------------------------------------------------------------------------
# Vocabulary enums  (StrEnum so values serialize as plain strings in JSON)
# ---------------------------------------------------------------------------

class CuisineType(str, Enum):
    american     = "American"
    italian      = "Italian"
    mexican      = "Mexican"
    japanese     = "Japanese"
    chinese      = "Chinese"
    indian       = "Indian"
    thai         = "Thai"
    french       = "French"
    mediterranean= "Mediterranean"
    korean       = "Korean"
    vietnamese   = "Vietnamese"
    greek        = "Greek"
    spanish      = "Spanish"
    middle_eastern = "Middle Eastern"
    caribbean    = "Caribbean"
    ethiopian    = "Ethiopian"
    seafood      = "Seafood"
    bbq          = "BBQ"
    pizza        = "Pizza"
    burgers      = "Burgers"
    sushi        = "Sushi"
    vegan        = "Vegan"
    vegetarian   = "Vegetarian"


class DietaryRestriction(str, Enum):
    vegetarian   = "Vegetarian"
    vegan        = "Vegan"
    gluten_free  = "Gluten-Free"
    halal        = "Halal"
    kosher       = "Kosher"
    dairy_free   = "Dairy-Free"
    nut_free     = "Nut-Free"
    low_carb     = "Low-Carb"
    keto         = "Keto"
    paleo        = "Paleo"
    shellfish_free = "Shellfish-Free"
    soy_free     = "Soy-Free"


class AmbianceType(str, Enum):
    casual         = "Casual"
    fine_dining    = "Fine Dining"
    family_friendly= "Family-Friendly"
    romantic       = "Romantic"
    outdoor        = "Outdoor Seating"
    sports_bar     = "Sports Bar"
    live_music     = "Live Music"
    quick_bite     = "Quick Bite"
    brunch         = "Brunch Spot"
    late_night     = "Late Night"
    rooftop        = "Rooftop"
    waterfront     = "Waterfront"


class PriceRange(str, Enum):
    budget     = "$"
    moderate   = "$$"
    upscale    = "$$$"
    fine       = "$$$$"


class SortPreference(str, Enum):
    rating        = "rating"
    newest        = "newest"
    most_reviewed = "most_reviewed"
    price_asc     = "price_asc"
    price_desc    = "price_desc"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_enum_list(values: list, enum_cls: type) -> list:
    """
    Normalise a list of strings to enum values via case-insensitive lookup
    against both the enum *name* and the enum *value*.

    Unknown entries are silently dropped so that legacy data doesn't break.
    """
    result = []
    value_map = {e.value.lower(): e for e in enum_cls}
    name_map  = {e.name.lower():  e for e in enum_cls}
    for item in values:
        key = str(item).strip().lower()
        matched = value_map.get(key) or name_map.get(key)
        if matched:
            result.append(matched)
    return result


# ---------------------------------------------------------------------------
# Input schema (write)
# ---------------------------------------------------------------------------

class UserPreferencesIn(BaseModel):
    """
    Payload for PUT /preferences/me.
    All fields are optional — only supplied fields are written.

    **Example:**
    ```json
    {
      "cuisine_preferences": ["Italian", "Japanese", "Sushi"],
      "price_range": "$$",
      "search_radius": 15,
      "preferred_locations": ["San Francisco", "Oakland"],
      "dietary_restrictions": ["Gluten-Free"],
      "ambiance_preferences": ["Casual", "Outdoor Seating"],
      "sort_preference": "rating"
    }
    ```
    """

    cuisine_preferences: Optional[List[CuisineType]] = Field(
        default=None,
        description=f"Up to 10 cuisine types. Valid values: {[e.value for e in CuisineType]}",
    )
    price_range: Optional[PriceRange] = Field(
        default=None,
        description="Preferred price tier. One of: $, $$, $$$, $$$$",
    )
    search_radius: Optional[int] = Field(
        default=None, ge=1, le=500,
        description="Search radius in miles (1–500).",
    )
    preferred_locations: Optional[List[str]] = Field(
        default=None,
        description="City/neighbourhood names the user prefers. Free-form strings.",
        examples=[["San Francisco", "Oakland"]],
    )
    dietary_restrictions: Optional[List[DietaryRestriction]] = Field(
        default=None,
        description=f"Valid values: {[e.value for e in DietaryRestriction]}",
    )
    ambiance_preferences: Optional[List[AmbianceType]] = Field(
        default=None,
        description=f"Valid values: {[e.value for e in AmbianceType]}",
    )
    sort_preference: Optional[SortPreference] = Field(
        default=None,
        description="How to sort restaurant results. One of: rating, newest, most_reviewed, price_asc, price_desc",
    )

    # Normalise string inputs → enum values before validation
    @field_validator("cuisine_preferences", mode="before")
    @classmethod
    def norm_cuisines(cls, v):
        return _normalise_enum_list(v, CuisineType) if v is not None else v

    @field_validator("dietary_restrictions", mode="before")
    @classmethod
    def norm_dietary(cls, v):
        return _normalise_enum_list(v, DietaryRestriction) if v is not None else v

    @field_validator("ambiance_preferences", mode="before")
    @classmethod
    def norm_ambiance(cls, v):
        return _normalise_enum_list(v, AmbianceType) if v is not None else v

    @field_validator("preferred_locations", mode="before")
    @classmethod
    def norm_locations(cls, v):
        if v is None:
            return v
        return [str(loc).strip() for loc in v if str(loc).strip()][:20]  # cap at 20 entries


# ---------------------------------------------------------------------------
# Output schema (read)
# ---------------------------------------------------------------------------

class UserPreferencesOut(BaseModel):
    """
    Response for GET /preferences/me and PUT /preferences/me.

    The ``ai_context`` computed field is what the AI assistant service
    reads directly — it's a flat dict with human-readable strings, ready
    to be injected into the LLM system prompt.
    """

    model_config = ConfigDict(from_attributes=True)

    cuisine_preferences: List[CuisineType] = []
    price_range: Optional[PriceRange] = None
    search_radius: int = 10
    preferred_locations: List[str] = []
    dietary_restrictions: List[DietaryRestriction] = []
    ambiance_preferences: List[AmbianceType] = []
    sort_preference: SortPreference = SortPreference.rating
    updated_at: Optional[datetime] = None

    @computed_field  # type: ignore[misc]
    @property
    def ai_context(self) -> dict:
        """
        Pre-built context dict for the AI assistant prompt.

        The AI service reads ``prefs.ai_context`` directly — no extra
        transformation needed.

        Shape:
        ```json
        {
          "has_preferences": true,
          "cuisine": ["Italian", "Sushi"],
          "price_range": "$$",
          "search_radius_miles": 15,
          "preferred_locations": ["San Francisco"],
          "dietary_needs": ["Gluten-Free"],
          "ambiance": ["Casual"],
          "sort_by": "rating"
        }
        ```
        """
        cuisines  = [c.value for c in self.cuisine_preferences]
        dietary   = [d.value for d in self.dietary_restrictions]
        ambiance  = [a.value for a in self.ambiance_preferences]

        return {
            "has_preferences": bool(cuisines or dietary or ambiance or self.preferred_locations),
            "cuisine":          cuisines,
            "price_range":      self.price_range.value if self.price_range else None,
            "search_radius_miles": self.search_radius,
            "preferred_locations": self.preferred_locations,
            "dietary_needs":    dietary,
            "ambiance":         ambiance,
            "sort_by":          self.sort_preference.value,
        }
