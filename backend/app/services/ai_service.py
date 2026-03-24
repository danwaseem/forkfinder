"""
AI Assistant Service — ForkFinder
==================================
Architecture
------------
Every /ai-assistant/chat request goes through five sequential stages:

  1. Filter Extraction   — rule-based extraction of cuisine, price, dietary needs,
                           occasion, ambiance, location, and web-search trigger.
                           No LLM token cost; falls back cleanly to empty filters.

  2. DB Search           — SQLAlchemy query using extracted filters merged with the
                           user's saved preferences.

  3. Ranking             — Scoring function (0–100) that weights rating, popularity,
                           cuisine/price/location match against both the current
                           query and the user's stored preferences.

  4. Tavily Web Search   — Fires only when the rule-based extractor sets
                           needs_web_search=True (hours, events, trending queries).
                           Skipped entirely if TAVILY_API_KEY is absent.

  5. LLM Response        — Single ChatOpenAI call returning a structured JSON
                           {assistant_message, reasoning, follow_up_question}.
                           Falls back to a deterministic template if
                           OPENAI_API_KEY is absent or the call fails.

Conversation Persistence
------------------------
User and assistant messages are stored in the `conversations` /
`conversation_messages` tables.  Clients can pass `conversation_id` to
reload prior context from the DB instead of re-sending history manually.

Cost Profile (gpt-3.5-turbo)
------------------------------
  ~1 500 – 2 000 tokens per request  ≈  $0.001 – $0.002
  Tavily free tier: 1 000 searches / month
"""

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import settings
from ..models.conversation import Conversation, ConversationMessage
from ..models.restaurant import Restaurant
from ..models.user import User
from ..schemas.ai_assistant import (
    ChatResponse,
    ExtractedFilters,
    RestaurantRecommendation,
)
from . import preferences_service
from . import prompts as P


# ---------------------------------------------------------------------------
# 1. Filter Extraction
# ---------------------------------------------------------------------------

# Cuisine keywords → canonical name
_CUISINE_MAP: Dict[str, str] = {
    "italian": "Italian", "pasta": "Italian", "pizza": "Italian",
    "japanese": "Japanese", "sushi": "Japanese", "ramen": "Japanese",
    "chinese": "Chinese", "dim sum": "Chinese", "dumpling": "Chinese",
    "mexican": "Mexican", "taco": "Mexican", "burrito": "Mexican",
    "indian": "Indian", "curry": "Indian",
    "thai": "Thai", "pad thai": "Thai",
    "american": "American", "burger": "American", "bbq": "American",
    "barbecue": "American", "steak": "American", "steakhouse": "American",
    "french": "French", "bistro": "French",
    "mediterranean": "Mediterranean", "greek": "Mediterranean",
    "korean": "Korean",
    "vietnamese": "Vietnamese", "pho": "Vietnamese",
    "spanish": "Spanish", "tapas": "Spanish",
    "middle eastern": "Middle Eastern", "lebanese": "Middle Eastern",
    "turkish": "Turkish",
    "ethiopian": "Ethiopian",
    "peruvian": "Peruvian",
    "seafood": "Seafood", "fish": "Seafood",
    "vegetarian": "Vegetarian",
    "vegan": "Vegan",
    "fusion": "Fusion",
}

_PRICE_MAP: Dict[str, str] = {
    "cheap": "$", "budget": "$", "affordable": "$", "inexpensive": "$",
    "moderate": "$$", "mid-range": "$$", "mid range": "$$",
    "upscale": "$$$", "fancy": "$$$", "nicer": "$$$",
    "fine dining": "$$$$", "fine-dining": "$$$$", "expensive": "$$$$",
    "splurge": "$$$$", "special occasion": "$$$$",
}

_DIETARY_MAP: Dict[str, str] = {
    "vegan": "vegan", "vegetarian": "vegetarian",
    "gluten-free": "gluten-free", "gluten free": "gluten-free",
    "halal": "halal", "kosher": "kosher",
    "dairy-free": "dairy-free", "dairy free": "dairy-free",
    "nut-free": "nut-free", "nut free": "nut-free",
    "keto": "keto", "paleo": "paleo",
}

_OCCASION_MAP: Dict[str, str] = {
    "date night": "date night", "date": "date night", "romantic": "date night",
    "anniversary": "anniversary",
    "birthday": "birthday", "celebration": "birthday",
    "business lunch": "business", "work lunch": "business",
    "business dinner": "business", "client dinner": "business",
    "family dinner": "family", "family": "family",
    "brunch": "brunch",
    "late night": "late night", "late-night": "late night",
    "happy hour": "happy hour",
    "group": "group dining", "large group": "group dining",
    "solo": "solo dining",
}

_AMBIANCE_MAP: Dict[str, str] = {
    "casual": "casual", "laid-back": "casual", "relaxed": "casual",
    "intimate": "intimate", "quiet": "intimate", "cozy": "intimate",
    "romantic": "intimate",
    "lively": "lively", "fun": "lively", "energetic": "lively", "vibrant": "lively",
    "outdoor": "outdoor seating", "patio": "outdoor seating", "terrace": "outdoor seating",
    "rooftop": "rooftop",
    "trendy": "trendy", "hip": "trendy", "modern": "trendy",
    "upscale": "upscale", "elegant": "upscale", "sophisticated": "upscale",
    "sports bar": "sports bar", "bar": "bar",
    "family-friendly": "family-friendly", "kid-friendly": "family-friendly",
}

_WEB_TRIGGERS = {
    "hours", "open now", "open today", "open late", "closing time",
    "event", "events", "live music", "special", "specials",
    "trending", "new restaurant", "just opened", "recently opened",
    "what's new", "popular right now", "best right now",
}

# Location patterns: "in/near/around <City>" or "in <City>, <State>"
_LOCATION_RE = re.compile(
    r"\b(?:in|near|around|at)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
)

# Stop-words to exclude from keyword extraction
_STOPWORDS = frozenset({
    "a", "an", "the", "is", "in", "on", "at", "to", "for", "of", "and",
    "or", "i", "me", "my", "we", "you", "can", "want", "need", "find",
    "looking", "something", "some", "any", "with", "good", "great", "best",
    "place", "places", "restaurant", "restaurants", "food", "eat", "eating",
    "dinner", "lunch", "breakfast", "meal", "where", "what", "which", "how",
    "are", "there", "around", "near", "like", "do", "would", "could",
})


def extract_filters(
    message: str,
    conversation_history: List[Dict],
    user_prefs: Dict,
) -> ExtractedFilters:
    """
    Rule-based extraction of search filters from the user's message.
    Also consults the last two assistant turns for context continuity.
    No LLM calls — zero token cost.
    """
    # Combine current message with recent assistant context for richer parsing
    recent_context = " ".join(
        entry.get("content", "")
        for entry in conversation_history[-4:]
        if entry.get("role") == "user"
    )
    text = f"{recent_context} {message}".lower().strip()
    original = f"{recent_context} {message}".strip()

    # --- Cuisine ---
    cuisine: Optional[str] = None
    for kw, canonical in _CUISINE_MAP.items():
        if kw in text:
            cuisine = canonical
            break

    # --- Price range ---
    price_range: Optional[str] = None
    for kw, sym in _PRICE_MAP.items():
        if kw in text:
            price_range = sym
            break
    # "$$$" or "$$" written literally
    if not price_range:
        for sym in ["$$$$", "$$$", "$$", "$"]:
            if sym in message:
                price_range = sym
                break

    # --- Dietary restrictions ---
    dietary: List[str] = []
    for kw, canonical in _DIETARY_MAP.items():
        if kw in text and canonical not in dietary:
            dietary.append(canonical)

    # --- Occasion ---
    occasion: Optional[str] = None
    for kw, canonical in sorted(_OCCASION_MAP.items(), key=lambda x: -len(x[0])):
        if kw in text:
            occasion = canonical
            break

    # --- Ambiance ---
    ambiance: Optional[str] = None
    for kw, canonical in sorted(_AMBIANCE_MAP.items(), key=lambda x: -len(x[0])):
        if kw in text:
            ambiance = canonical
            break

    # --- Location ---
    location: Optional[str] = None
    loc_match = _LOCATION_RE.search(original)
    if loc_match:
        location = loc_match.group(1)
    # Fall back to user's first preferred location if none in message
    if not location and user_prefs.get("preferred_locations"):
        location = user_prefs["preferred_locations"][0]

    # --- Web search trigger ---
    needs_web = any(trigger in text for trigger in _WEB_TRIGGERS)
    web_query: Optional[str] = None
    if needs_web:
        base = f"{cuisine or ''} restaurant {location or ''} {message}".strip()
        web_query = base[:150]

    # --- Residual keywords ---
    words = re.findall(r"[a-z]+", text)
    cuisine_words = set(cuisine.lower().split()) if cuisine else set()
    keywords = [
        w for w in words
        if w not in _STOPWORDS and len(w) > 3 and w not in cuisine_words
    ]
    # Deduplicate while preserving order
    seen: set = set()
    unique_kw = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            unique_kw.append(w)

    return ExtractedFilters(
        cuisine=cuisine,
        price_range=price_range,
        dietary_restrictions=dietary,
        occasion=occasion,
        ambiance=ambiance,
        location=location,
        keywords=unique_kw[:10],
        needs_web_search=needs_web,
        web_search_query=web_query,
    )


# ---------------------------------------------------------------------------
# 2. DB Search
# ---------------------------------------------------------------------------

def _search_restaurants(
    db: Session,
    filters: ExtractedFilters,
    user_prefs: Dict,
    limit: int = 10,
) -> List[Restaurant]:
    """
    Build a SQLAlchemy query from extracted filters + user preferences.
    Returns up to `limit` Restaurant ORM objects for scoring.
    """
    q = db.query(Restaurant)

    # Cuisine — prefer explicit query, fall back to user preference
    cuisine = filters.cuisine
    if not cuisine and user_prefs.get("cuisine"):
        cuisine = user_prefs["cuisine"][0]
    if cuisine:
        q = q.filter(Restaurant.cuisine_type.ilike(f"%{cuisine}%"))

    # Price range
    price = filters.price_range
    if not price and user_prefs.get("price_range"):
        price = user_prefs["price_range"]
    if price:
        q = q.filter(Restaurant.price_range == price)

    # Location
    if filters.location:
        q = q.filter(
            or_(
                Restaurant.city.ilike(f"%{filters.location}%"),
                Restaurant.state.ilike(f"%{filters.location}%"),
                Restaurant.zip_code.ilike(f"%{filters.location}%"),
            )
        )

    # Keyword broadening — search name + description
    if filters.keywords:
        # Use the top 2 keywords to avoid over-filtering
        kw_filters = [
            or_(
                Restaurant.name.ilike(f"%{kw}%"),
                Restaurant.description.ilike(f"%{kw}%"),
            )
            for kw in filters.keywords[:2]
        ]
        if len(kw_filters) == 1:
            q = q.filter(kw_filters[0])
        elif kw_filters:
            q = q.filter(or_(*kw_filters))

    results = q.order_by(Restaurant.avg_rating.desc()).limit(limit).all()

    # If the filtered query returned nothing, broaden: drop cuisine/price filter
    if not results and (cuisine or price):
        broad_q = db.query(Restaurant)
        if filters.location:
            broad_q = broad_q.filter(
                or_(
                    Restaurant.city.ilike(f"%{filters.location}%"),
                    Restaurant.state.ilike(f"%{filters.location}%"),
                )
            )
        results = broad_q.order_by(Restaurant.avg_rating.desc()).limit(limit).all()

    return results


# ---------------------------------------------------------------------------
# 3. Ranking
# ---------------------------------------------------------------------------

def _build_match_reasons(
    r: Restaurant,
    filters: ExtractedFilters,
    user_prefs: Dict,
) -> List[str]:
    reasons = []
    if filters.cuisine and r.cuisine_type and filters.cuisine.lower() in r.cuisine_type.lower():
        reasons.append(f"{r.cuisine_type} cuisine matches your request")
    elif user_prefs.get("cuisine") and r.cuisine_type:
        for c in user_prefs["cuisine"]:
            if c.lower() in r.cuisine_type.lower():
                reasons.append(f"{r.cuisine_type} cuisine matches your saved preferences")
                break
    if r.avg_rating >= 4.5:
        reasons.append(f"Highly rated ({r.avg_rating:.1f}/5)")
    elif r.avg_rating >= 4.0:
        reasons.append(f"Well rated ({r.avg_rating:.1f}/5)")
    if filters.price_range and r.price_range == filters.price_range:
        price_labels = {"$": "Budget-friendly", "$$": "Mid-range", "$$$": "Upscale", "$$$$": "Fine dining"}
        reasons.append(f"{price_labels.get(r.price_range, r.price_range)} ({r.price_range})")
    if r.review_count >= 100:
        reasons.append(f"Popular with diners ({r.review_count} reviews)")
    if filters.location and r.city and filters.location.lower() in r.city.lower():
        reasons.append(f"Located in {r.city}")
    return reasons or [f"Rated {r.avg_rating:.1f}/5 · {r.review_count} reviews"]


def _score(
    r: Restaurant,
    filters: ExtractedFilters,
    user_prefs: Dict,
) -> float:
    """
    Score a restaurant 0–100 for relevance.

      Rating score     : 0–40  (linear from 0–5 stars)
      Popularity bonus : 0–20  (capped at 100 reviews)
      Cuisine match    : 0–20  (query match > preference match)
      Price match      : 0–10
      Location match   : 0–10
    """
    score = (r.avg_rating / 5.0) * 40

    # Popularity — 1 point per review up to 20
    score += min(r.review_count / 5.0, 20.0)

    # Cuisine
    if filters.cuisine and r.cuisine_type:
        if filters.cuisine.lower() in r.cuisine_type.lower():
            score += 20
    elif user_prefs.get("cuisine") and r.cuisine_type:
        for c in user_prefs["cuisine"]:
            if c.lower() in r.cuisine_type.lower():
                score += 10
                break

    # Price
    effective_price = filters.price_range or user_prefs.get("price_range")
    if effective_price and r.price_range == effective_price:
        score += 10

    # Location
    effective_loc = filters.location
    if effective_loc and r.city and effective_loc.lower() in r.city.lower():
        score += 10

    return round(min(score, 100.0), 2)


def rank_restaurants(
    restaurants: List[Restaurant],
    filters: ExtractedFilters,
    user_prefs: Dict,
) -> List[RestaurantRecommendation]:
    """Score, sort descending, return top 5 as typed recommendations."""
    scored = []
    for r in restaurants:
        s = _score(r, filters, user_prefs)
        reasons = _build_match_reasons(r, filters, user_prefs)
        try:
            photos = json.loads(r.photos) if r.photos else []
        except Exception:
            photos = []
        scored.append(
            RestaurantRecommendation(
                id=r.id,
                name=r.name,
                cuisine_type=r.cuisine_type,
                price_range=r.price_range,
                city=r.city,
                avg_rating=r.avg_rating or 0.0,
                review_count=r.review_count or 0,
                description=r.description,
                photos=photos[:2],
                relevance_score=s,
                match_reasons=reasons,
            )
        )
    scored.sort(key=lambda x: x.relevance_score, reverse=True)
    top = scored[:5]

    # When the user explicitly asked for a specific cuisine, only return
    # restaurants that actually match it.  Without this guard the DB
    # broadened-fallback (location-only query) can surface high-rated but
    # cuisine-unrelated restaurants that score above the weak-results
    # threshold purely from rating + location points, causing a mismatch
    # between the structured recommendation cards and the assistant text.
    if filters.cuisine:
        matched = [
            r for r in top
            if r.cuisine_type and filters.cuisine.lower() in r.cuisine_type.lower()
        ]
        return matched  # empty list → _results_are_weak() → honest fallback message

    return top


# ---------------------------------------------------------------------------
# 4. Tavily Web Search
# ---------------------------------------------------------------------------

async def _tavily_search(query: str) -> Optional[str]:
    """
    Tavily web search — returns a short plain-text summary or None on failure.
    Falls back gracefully if the API key is missing or the call fails.
    Uses the raw tavily-python client (simpler than the LangChain wrapper).
    """
    if not settings.TAVILY_API_KEY:
        return None
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        resp = client.search(
            query=query,
            search_depth="basic",
            max_results=3,
            include_answer=True,
        )
        # `include_answer=True` asks Tavily to produce a synthesized answer
        answer = resp.get("answer") or ""
        snippets = [
            r.get("content", "")[:300]
            for r in resp.get("results", [])[:3]
        ]
        parts = [p for p in [answer] + snippets if p]
        return "\n\n".join(parts)[:1200] if parts else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 5. Prompt mode selection
# ---------------------------------------------------------------------------

_VAGUENESS_THRESHOLD = 30  # relevance score below this → fallback mode
_VAGUE_MESSAGE_MIN_TOKENS = 3  # fewer content words → clarification mode


def _query_is_vague(filters: ExtractedFilters) -> bool:
    """
    A query is considered vague when it contains almost no extractable signal:
    no cuisine, no location, no occasion, no dietary, and very few keywords.
    """
    has_signal = any([
        filters.cuisine,
        filters.location,
        filters.occasion,
        filters.ambiance,
        filters.dietary_restrictions,
        len(filters.keywords) >= _VAGUE_MESSAGE_MIN_TOKENS,
    ])
    return not has_signal


def _results_are_weak(recs: List[RestaurantRecommendation]) -> bool:
    """Top result scored below threshold, or no results at all."""
    if not recs:
        return True
    return recs[0].relevance_score < _VAGUENESS_THRESHOLD


# ---------------------------------------------------------------------------
# 6. LLM Response Generation
# ---------------------------------------------------------------------------

def _build_system_content(
    message: str,
    user_name: str,
    user_prefs: Dict,
    filters: ExtractedFilters,
    recs: List[RestaurantRecommendation],
    web_summary: Optional[str],
    conversation_history: List[Dict],
) -> str:
    """
    Compose the full SystemMessage content by combining the base SYSTEM_PROMPT
    with the appropriate mode-specific prompt (response / clarification / fallback).

    Mode selection:
      clarification — query too vague to search confidently
      fallback      — search ran but returned no strong matches
      normal        — has results; use RESPONSE_PROMPT
    """
    prefs_block = P.build_prefs_block(user_prefs)
    # user_name and prefs_block must go through _safe() — user-controlled strings
    base = P.SYSTEM_PROMPT.format(user_name=_safe(user_name), prefs_block=_safe(prefs_block))

    if _query_is_vague(filters):
        mode_prompt = P.CLARIFICATION_PROMPT.format(
            message=_safe(message),
            known_block=P.build_known_block(filters),
            missing_block=P.build_missing_block(filters),
            what_was_missing="location and cuisine" if not filters.location else "cuisine or occasion",
        )
    elif _results_are_weak(recs):
        mode_prompt = P.FALLBACK_PROMPT.format(
            message=_safe(message),
            applied_filters=P.build_applied_filters_block(filters),
            result_count=len(recs),
            weak_matches_block=P.build_weak_matches_block(recs),
            prefs_block=_safe(prefs_block),
        )
    else:
        mode_prompt = P.RESPONSE_PROMPT.format(
            restaurant_block=P.build_restaurant_block(recs),
            web_block=P.build_web_block(web_summary),
        )

    return base + "\n\n" + mode_prompt


def _safe(s: str) -> str:
    """Escape curly braces in user-supplied text before .format() calls."""
    return s.replace("{", "{{").replace("}", "}}")


async def _generate_response(
    message: str,
    user_name: str,
    user_prefs: Dict,
    filters: ExtractedFilters,
    recs: List[RestaurantRecommendation],
    web_summary: Optional[str],
    conversation_history: List[Dict],
) -> Dict[str, Any]:
    """
    Build prompt → call LLM → parse JSON → return dict.
    Falls back to deterministic template if no API key or on any exception.
    """
    if not settings.OLLAMA_BASE_URL:
        return _no_llm_response(user_name, filters, recs, user_prefs, web_summary)

    raw = ""
    try:
        from langchain_community.chat_models import ChatOllama
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

        system_content = _build_system_content(
            message, user_name, user_prefs, filters, recs, web_summary, conversation_history
        )

        # Conversation history — last 6 messages (3 turns)
        history_msgs = []
        for entry in conversation_history[-6:]:
            if entry.get("role") == "user":
                history_msgs.append(HumanMessage(content=entry["content"]))
            elif entry.get("role") == "assistant":
                history_msgs.append(AIMessage(content=entry["content"]))

        messages = (
            [SystemMessage(content=system_content)]
            + history_msgs
            + [HumanMessage(content=message)]
        )

        llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
            format="json",
        )

        result = await llm.ainvoke(messages)
        raw = result.content.strip()

        # Strip markdown fences the model occasionally adds despite instructions
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw.strip())

        parsed = json.loads(raw)
        return {
            "assistant_message": parsed.get("assistant_message", raw),
            "reasoning": parsed.get("reasoning", ""),
            "follow_up_question": parsed.get("follow_up_question"),
        }

    except json.JSONDecodeError:
        # LLM responded with prose instead of JSON — use it verbatim
        return {
            "assistant_message": raw or "Sorry, I ran into a problem generating a response.",
            "reasoning": "LLM returned non-JSON output; used raw text.",
            "follow_up_question": None,
        }
    except Exception:
        return _no_llm_response(user_name, filters, recs, user_prefs, web_summary)


def _no_llm_response(
    user_name: str,
    filters: ExtractedFilters,
    recs: List[RestaurantRecommendation],
    user_prefs: Dict,
    web_summary: Optional[str],
) -> Dict[str, Any]:
    """
    Deterministic template used when OpenAI is unavailable or fails.
    Respects the same mode logic (vague / fallback / normal) so the
    experience degrades gracefully but stays coherent.
    """
    if _query_is_vague(filters):
        return {
            "assistant_message": (
                f"Hey {user_name}! I'd love to help — could you tell me "
                "what city or neighborhood you're in? That'll let me pull up "
                "the best nearby options right away."
            ),
            "reasoning": "Query too vague — requested location to narrow search.",
            "follow_up_question": None,
        }

    if _results_are_weak(recs):
        applied = P.build_applied_filters_block(filters)
        suggestion = (
            f"try removing the {'cuisine' if filters.cuisine else 'price'} filter"
            if (filters.cuisine or filters.price_range) else
            "try a different city or broaden what you're looking for"
        )
        return {
            "assistant_message": (
                f"I searched for {applied} but couldn't find a strong match "
                f"in our database. You might want to {suggestion}. "
                "I can also look for the highest-rated restaurants nearby "
                "if you tell me more about what you're in the mood for."
            ),
            "reasoning": f"No strong matches for: {applied}",
            "follow_up_question": "Want me to broaden the search, or is there a specific cuisine you have in mind?",
        }

    # Normal path — format results as clean markdown
    lines = [f"Here are some options for {user_name}:\n"]
    for r in recs:
        lines.append(
            f"**{r.name}** — {r.cuisine_type or 'Various'} · "
            f"{r.price_range or 'N/A'} · ⭐ {r.avg_rating:.1f} ({r.review_count} reviews)"
        )
        if r.city:
            lines.append(f"  📍 {r.city}")
        if r.description:
            lines.append(f"  _{r.description[:100]}_")
        if r.match_reasons:
            lines.append(f"  ✓ {r.match_reasons[0]}")
        lines.append("")

    if web_summary:
        lines.append(f"\n**From the web:** {web_summary[:400]}")

    return {
        "assistant_message": "\n".join(lines),
        "reasoning": "Results ranked by rating and preference match.",
        "follow_up_question": "Would you like more details about any of these?",
    }


# ---------------------------------------------------------------------------
# 7. Conversation Persistence
# ---------------------------------------------------------------------------

def _load_history_from_db(
    db: Session, conversation_id: int, user_id: int
) -> Tuple[List[Dict], Optional[int]]:
    """
    Load conversation history from DB. Returns (history_list, conversation_id).
    Returns ([], None) if the conversation is not found or doesn't belong to the user.
    """
    conv = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .first()
    )
    if not conv:
        return [], None
    history = [{"role": m.role, "content": m.content} for m in conv.messages]
    return history, conv.id


def _persist_turn(
    db: Session,
    user_id: int,
    conversation_id: Optional[int],
    user_message: str,
    response: Dict[str, Any],
    filters: ExtractedFilters,
    recs: List[RestaurantRecommendation],
) -> int:
    """
    Save user message + assistant response to DB.
    Creates a new Conversation row on the first turn.
    Returns the conversation_id.
    """
    if conversation_id:
        conv = (
            db.query(Conversation)
            .filter(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .first()
        )
    else:
        conv = None

    if not conv:
        conv = Conversation(user_id=user_id)
        db.add(conv)
        db.flush()  # assigns conv.id without committing

    # User message
    db.add(ConversationMessage(
        conversation_id=conv.id,
        role="user",
        content=user_message,
    ))

    # Assistant message — attach filters/recs as JSON metadata
    extra = {
        "reasoning": response.get("reasoning"),
        "follow_up_question": response.get("follow_up_question"),
        "extracted_filters": filters.model_dump(),
        "recommendation_ids": [r.id for r in recs],
    }
    db.add(ConversationMessage(
        conversation_id=conv.id,
        role="assistant",
        content=response["assistant_message"],
        extra_json=json.dumps(extra),
    ))

    db.commit()
    return conv.id


# ---------------------------------------------------------------------------
# 8. Main Entry Point
# ---------------------------------------------------------------------------

async def chat(
    message: str,
    conversation_history: List[Dict],
    db: Session,
    current_user: User,
    conversation_id: Optional[int] = None,
) -> ChatResponse:
    """
    Orchestrates all five stages and returns a fully typed ChatResponse.
    """
    # Stage 0 — resolve conversation history
    if conversation_id and not conversation_history:
        conversation_history, conversation_id = _load_history_from_db(
            db, conversation_id, current_user.id
        )

    # Stage 1 — load user preferences (cached for life of request)
    user_prefs = preferences_service.get_for_ai(db, current_user.id)

    # Stage 2 — extract filters
    filters = extract_filters(message, conversation_history, user_prefs)

    # Stage 3 — search DB
    raw_restaurants = _search_restaurants(db, filters, user_prefs)

    # Stage 4 — rank
    recommendations = rank_restaurants(raw_restaurants, filters, user_prefs)

    # Stage 5 — Tavily (only when needed)
    web_summary: Optional[str] = None
    if filters.needs_web_search:
        web_summary = await _tavily_search(filters.web_search_query or message)

    # Stage 6 — LLM response (or fallback)
    response = await _generate_response(
        message=message,
        user_name=current_user.name,
        user_prefs=user_prefs,
        filters=filters,
        recs=recommendations,
        web_summary=web_summary,
        conversation_history=conversation_history,
    )

    # Stage 7 — persist
    conv_id = _persist_turn(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id,
        user_message=message,
        response=response,
        filters=filters,
        recs=recommendations,
    )

    return ChatResponse(
        assistant_message=response["assistant_message"],
        extracted_filters=filters,
        recommendations=recommendations,
        reasoning=response.get("reasoning", ""),
        follow_up_question=response.get("follow_up_question"),
        web_results_summary=web_summary,
        conversation_id=conv_id,
    )
