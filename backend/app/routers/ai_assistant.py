"""
AI Assistant router.

Endpoints:
  POST /ai-assistant/chat  — multi-turn restaurant recommendation chat
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..schemas.ai_assistant import ChatRequest, ChatResponse
from ..services import ai_service
from ..utils.auth import get_current_user

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the AI restaurant concierge",
    responses={
        200: {
            "description": "AI recommendation response",
            "content": {
                "application/json": {
                    "example": {
                        "assistant_message": (
                            "Hi Alex! Based on your request for a romantic Italian dinner, "
                            "here are my top picks:\n\n"
                            "**Ristorante Bello** is a wonderful choice — authentic Neapolitan "
                            "pizza and pasta in a cozy, candlelit setting. Rated 4.8/5 with "
                            "142 reviews, and priced at $$ which fits your budget.\n\n"
                            "Would you like to know more about any of these?"
                        ),
                        "extracted_filters": {
                            "cuisine": "Italian",
                            "price_range": "$$",
                            "dietary_restrictions": [],
                            "occasion": "date night",
                            "ambiance": "intimate",
                            "location": "San Francisco",
                            "keywords": ["romantic", "dinner"],
                            "needs_web_search": False,
                            "web_search_query": None,
                        },
                        "recommendations": [
                            {
                                "id": 5,
                                "name": "Ristorante Bello",
                                "cuisine_type": "Italian",
                                "price_range": "$$",
                                "city": "San Francisco",
                                "avg_rating": 4.8,
                                "review_count": 142,
                                "description": "Authentic Neapolitan pizza since 1995.",
                                "photos": [],
                                "relevance_score": 88.4,
                                "match_reasons": [
                                    "Italian cuisine matches your request",
                                    "Highly rated (4.8/5)",
                                    "Mid-range ($$)",
                                ],
                            }
                        ],
                        "reasoning": "Selected Italian restaurants sorted by rating with price and ambiance match.",
                        "follow_up_question": "Would you prefer outdoor seating or indoor dining?",
                        "web_results_summary": None,
                        "conversation_id": 7,
                    }
                }
            },
        }
    },
)
async def chat(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Multi-turn restaurant recommendation chat.

    **How multi-turn works:**
    - First turn: omit `conversation_id`. The response returns a new `conversation_id`.
    - Subsequent turns: pass the same `conversation_id`.  The backend loads the prior
      turns from DB automatically — no need to re-send `conversation_history`.
    - Alternatively, always pass `conversation_history` yourself (original behaviour).

    **Filter extraction:**
    The service extracts cuisine, price range, dietary restrictions, occasion,
    ambiance, and location from the message using rule-based parsing (no extra
    LLM call).  The `extracted_filters` field in the response shows what was found.

    **Tavily web search:**
    Triggered automatically when the message mentions hours, events, trending
    restaurants, or "open now/today".  Disabled if `TAVILY_API_KEY` is not set.

    **Fallback behaviour:**
    If `OLLAMA_BASE_URL` is unreachable or the LLM call fails, the service
    returns a structured rule-based response using the same `ChatResponse` schema.
    """
    history = [m.model_dump() for m in (payload.conversation_history or [])]

    return await ai_service.chat(
        message=payload.message,
        conversation_history=history,
        db=db,
        current_user=current_user,
        conversation_id=payload.conversation_id,
    )
