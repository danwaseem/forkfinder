"""
AI Assistant request / response schemas.

POST /ai-assistant/chat
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Inbound
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str    # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = []
    # Optionally pass the conversation_id returned by a previous turn
    # so the backend can reload history from DB instead of the client resending it.
    conversation_id: Optional[int] = None


# ---------------------------------------------------------------------------
# Outbound building blocks
# ---------------------------------------------------------------------------

class ExtractedFilters(BaseModel):
    """Structured filters extracted from the user's message."""
    cuisine: Optional[str] = None
    price_range: Optional[str] = None          # "$" | "$$" | "$$$" | "$$$$"
    dietary_restrictions: List[str] = []       # ["vegan", "gluten-free", …]
    occasion: Optional[str] = None             # "date night", "business lunch", …
    ambiance: Optional[str] = None             # "casual", "romantic", …
    location: Optional[str] = None             # city / neighbourhood
    keywords: List[str] = []                   # other significant terms
    needs_web_search: bool = False
    web_search_query: Optional[str] = None


class RestaurantRecommendation(BaseModel):
    """A single restaurant recommendation with relevance metadata."""
    id: int
    name: str
    cuisine_type: Optional[str] = None
    price_range: Optional[str] = None
    city: Optional[str] = None
    avg_rating: float = 0.0
    review_count: int = 0
    description: Optional[str] = None
    photos: List[str] = []
    relevance_score: float = Field(ge=0.0, le=100.0)
    match_reasons: List[str] = []              # human-readable reasons


# ---------------------------------------------------------------------------
# Full response
# ---------------------------------------------------------------------------

class ChatResponse(BaseModel):
    assistant_message: str
    extracted_filters: ExtractedFilters
    recommendations: List[RestaurantRecommendation]
    reasoning: str
    follow_up_question: Optional[str] = None
    web_results_summary: Optional[str] = None
    conversation_id: Optional[int] = None
