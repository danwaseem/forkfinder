from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .middleware.exception_handler import register_exception_handlers
from .routers import ai_assistant, auth, favorites, history, owner, preferences, restaurants, reviews, users

# Create all tables
Base.metadata.create_all(bind=engine)

# Ensure upload directories exist
for sub in ("profiles", "restaurants", "reviews"):
    Path(settings.UPLOAD_DIR, sub).mkdir(parents=True, exist_ok=True)

_TAGS_METADATA = [
    {
        "name": "Health",
        "description": "Service liveness checks. No authentication required.",
    },
    {
        "name": "Authentication",
        "description": (
            "Register and log in as a **reviewer** (`/auth/user/*`) or a "
            "**restaurant owner** (`/auth/owner/*`). "
            "On success, every login/signup endpoint returns a JWT. "
            "Pass it on all protected requests as:\n\n"
            "```\nAuthorization: Bearer <token>\n```\n\n"
            "Tokens are stateless (HS256). To log out, simply discard the token "
            "on the client side."
        ),
    },
    {
        "name": "User Profile",
        "description": (
            "Manage the authenticated **reviewer** profile and profile photo. "
            "Prefer the canonical `/preferences/me`, `/favorites/me`, and "
            "`/history/me` paths over the legacy `/users/me/*` sub-paths, "
            "which are kept for backwards compatibility only."
        ),
    },
    {
        "name": "User Preferences",
        "description": (
            "Store and retrieve dining preferences: preferred cuisines, price "
            "range, dietary restrictions, ambiance, search radius, and sort "
            "order. These preferences are forwarded automatically to the AI "
            "assistant to personalise recommendations."
        ),
    },
    {
        "name": "Restaurants",
        "description": (
            "Public restaurant discovery — search by keyword, cuisine, city, "
            "price, or minimum rating; sort by rating, recency, review count, "
            "or price tier.\n\n"
            "Both reviewer and owner accounts may **create** listings. Only the "
            "creator *or* the owner who claimed the restaurant may **edit** or "
            "**delete** it.\n\n"
            "Photo uploads are capped at **10 photos** per restaurant and **5 MB** "
            "per file (JPEG, PNG, WEBP, GIF)."
        ),
    },
    {
        "name": "Reviews",
        "description": (
            "Create, read, update, and delete restaurant reviews.\n\n"
            "**Reviewer accounts only** — restaurant owners (`role=owner`) "
            "receive `403` on all write endpoints.\n\n"
            "- Rating: 1–5 (integer).\n"
            "- Comment: 10–5 000 characters.\n"
            "- Each user may review a restaurant **once** — `PUT /reviews/{id}` "
            "to update.\n"
            "- Every write returns updated `avg_rating` and `review_count` for "
            "the restaurant."
        ),
    },
    {
        "name": "Favorites",
        "description": (
            "Bookmark restaurants. Available to both reviewer and owner accounts. "
            "`POST /{id}` adds, `DELETE /{id}` removes. Returns `400` on "
            "duplicate add or missing-to-remove."
        ),
    },
    {
        "name": "History",
        "description": (
            "Activity log for the authenticated user: reviews they have written "
            "and restaurant listings they have created, both sorted newest-first. "
            "Works for both reviewer and owner accounts."
        ),
    },
    {
        "name": "Owner Dashboard",
        "description": (
            "Restaurant management and analytics for **owner** accounts "
            "(`role=owner`). All `/owner/*` endpoints return `403` for reviewer "
            "tokens.\n\n"
            "Covers: profile management, listing multiple restaurants, per-restaurant "
            "stats (rating breakdown, 6-month trend, sentiment), paginated review "
            "inbox, and ownership claims (auto-approved)."
        ),
    },
    {
        "name": "AI Assistant",
        "description": (
            "Multi-turn natural-language restaurant recommendation chat.\n\n"
            "Powered by **Ollama** (local LLM via LangChain) with optional "
            "**Tavily** web search for real-time queries (hours, events, trending). "
            "Falls back to rule-based recommendations when Ollama is unavailable.\n\n"
            "Pass `conversation_id` from a prior response to continue a session "
            "server-side, or manage history yourself via `conversation_history`."
        ),
    },
]

app = FastAPI(
    title="ForkFinder API",
    description=(
        "## ForkFinder — Restaurant Discovery & Review Platform\n\n"
        "A Yelp-inspired REST API built with **FastAPI + SQLAlchemy + MySQL**.\n\n"
        "### Base URL\n"
        "`http://localhost:8000`\n\n"
        "### Authentication\n"
        "All protected endpoints use **Bearer JWT** tokens obtained from "
        "`POST /auth/user/login` (reviewer) or `POST /auth/owner/login` (owner).\n\n"
        "In Swagger UI: click **Authorize** (🔒), paste `Bearer <token>`, click Authorize.\n\n"
        "### Two account roles\n"
        "| Role | Can do |\n"
        "|---|---|\n"
        "| `user` (reviewer) | Browse, write reviews, manage favorites, chat with AI |\n"
        "| `owner` | Browse, manage restaurant listings, view analytics, claim restaurants |\n\n"
        "### Demo credentials\n"
        "| Role | Email | Password |\n"
        "|---|---|---|\n"
        "| Reviewer | `user@demo.com` | `password` |\n"
        "| Owner | `owner@demo.com` | `password` |"
    ),
    version="1.0.0",
    openapi_tags=_TAGS_METADATA,
    docs_url="/docs",
    redoc_url="/redoc",
)

register_exception_handlers(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file serving for uploads
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(preferences.router)
app.include_router(restaurants.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(history.router)
app.include_router(owner.router)
app.include_router(ai_assistant.router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "Restaurant Platform API", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
