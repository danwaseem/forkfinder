# ForkFinder — Restaurant Discovery Platform

A full-stack Yelp-style restaurant discovery and review platform with an AI-powered dining assistant. Built for DATA 236 Lab 1.

**Team:** Group 7 — Danish Waseem (19101511), Saketh (019101111)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Tech Stack](#tech-stack)
4. [Architecture Summary](#architecture-summary)
5. [Project Structure](#project-structure)
6. [Prerequisites](#prerequisites)
7. [Database Setup](#database-setup)
8. [Backend Setup](#backend-setup)
9. [Environment Variables](#environment-variables)
10. [Frontend Setup](#frontend-setup)
11. [Seed Data](#seed-data)
12. [Running Locally](#running-locally)
13. [API Documentation](#api-documentation)
14. [Sample Credentials](#sample-credentials)
15. [Running Tests](#running-tests)
16. [Assumptions](#assumptions)
17. [Limitations](#limitations)
18. [Future Improvements](#future-improvements)

---

## Project Overview

ForkFinder is a full-stack restaurant discovery application modeled after Yelp. It supports two distinct user roles — **reviewers** who discover and rate restaurants, and **restaurant owners** who manage listings and view analytics. An embedded AI assistant provides personalized dining recommendations powered by a local LLM (Ollama) with optional Tavily web search for real-time results.

The project demonstrates a complete production-style architecture: JWT authentication, role-based access control, file upload validation, denormalized rating aggregation, multi-turn AI conversation state, and a responsive React frontend — all built to submission-quality standard.

---

## Features

### Reviewer (User) Features

| Feature | Description |
|---|---|
| Registration & Login | Separate signup flows for reviewers and owners; JWT returned on success |
| Profile Management | Edit name, bio, phone, city, languages, gender; upload profile photo |
| Dining Preferences | Set preferred cuisines, price tier, dietary restrictions, ambiance, search radius |
| Restaurant Discovery | Full-text search + compound filters: cuisine, city, price range, minimum rating |
| Sort & Filter | Sort by highest rated, most reviewed, newest, or price (asc/desc); combine any filters |
| Restaurant Detail | Photo gallery, hours (today highlighted), contact info, rating breakdown, reviews |
| Reviews | Create, edit, and delete reviews; star rating (1–5), comment (10–5000 chars), photo |
| Favorites | Heart-toggle any restaurant; view saved list ordered newest-first |
| Activity History | Timeline of reviews written and restaurants added |
| AI Assistant | Floating chatbot for natural-language restaurant recommendations |

### Owner Features

| Feature | Description |
|---|---|
| Owner Dashboard | Aggregate stats: total restaurants, reviews, avg rating, total favorites |
| Per-Restaurant Stats | Rating distribution, 6-month review trend chart, sentiment keywords |
| Listing Management | Add, edit, and delete restaurant listings; upload up to 10 photos |
| Claim a Listing | Claim any unclaimed restaurant; single-claim enforced |
| Review Monitoring | Read all reviews across owned restaurants (owners cannot write reviews) |

### AI Assistant Features

| Feature | Description |
|---|---|
| Natural-Language Input | Understands cuisine, price, occasion, dietary, location intent |
| Preference Injection | Automatically loads the logged-in user's saved preferences as context |
| Filter Extraction | Converts free-form text to structured DB queries |
| Recommendation Cards | Returns restaurant cards with name, rating, price, and match reasoning |
| Multi-Turn Memory | Maintains conversation state — follow-up questions refine previous results |
| Web Search | Optional Tavily integration for live hours, trending spots, and current events |
| Graceful Fallback | Degrades to rule-based DB search when Ollama is unavailable |

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Frontend framework | React | 18.3 |
| Frontend build | Vite | 5.2 |
| Styling | Tailwind CSS | 3.4 |
| HTTP client | Axios | 1.7 |
| Client routing | React Router | 6.23 |
| Toast notifications | react-hot-toast | 2.4 |
| Icons | lucide-react | 0.469 |
| Backend framework | FastAPI | 0.111 |
| ASGI server | Uvicorn | 0.29 |
| ORM | SQLAlchemy | 2.0 |
| Database | MySQL | 8.0+ |
| MySQL driver | PyMySQL | 1.1 |
| Auth | python-jose (JWT) + passlib (bcrypt) | 3.3 / 1.7 |
| Validation | Pydantic | 2.7 |
| Image processing | Pillow | 10.3 |
| AI framework | LangChain + LangChain-Community | 0.1 |
| Local LLM | Ollama (llama3.2 default) | — |
| Web search | Tavily | 0.3 |
| File handling | python-multipart + aiofiles | — |
| API docs | Swagger UI + ReDoc (built-in FastAPI) | — |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                           │
│  Vite · React Router v6 · Axios (JWT interceptor) · Tailwind    │
│  AuthContext → services/ → pages/ + components/                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTP / JSON  (localhost:5173 → :8000)
┌──────────────────────────▼──────────────────────────────────────┐
│                       FastAPI Backend                            │
│                                                                  │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────────────┐  │
│  │   Routers   │ → │   Services   │ → │  SQLAlchemy ORM      │  │
│  │  (9 files)  │   │  (8 files)   │   │  MySQL 8 via PyMySQL │  │
│  └─────────────┘   └──────┬───────┘   └──────────────────────┘  │
│                           │                                      │
│                    ┌──────▼───────┐                              │
│                    │ AI Service   │                              │
│                    │  LangChain   │ ──► Ollama (local LLM)       │
│                    │  + Tavily    │ ──► Tavily Web Search        │
│                    └──────────────┘                              │
│                                                                  │
│  Middleware: CORS · GlobalExceptionHandler · StaticFiles (uploads)│
└─────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**

- **Denormalized ratings** — `avg_rating` and `review_count` are stored on the `Restaurant` row and recalculated by `review_service.recalc_rating()` on every write. This avoids expensive aggregation joins on every list query.
- **JSON columns for arrays** — `hours`, `photos`, `cuisine_preferences`, `dietary_restrictions`, and `ambiance_preferences` are stored as JSON text. Portable across MySQL versions and requires no schema migration to extend option sets.
- **Stateless JWT** — Tokens are HS256-signed, 30-day expiry. No server-side session store required. The React `AuthContext` stores the token and user object in `localStorage` and injects `Authorization: Bearer <token>` via an Axios request interceptor.
- **Role separation enforced at the API layer** — Every protected endpoint calls `require_user` or `require_owner` dependency. A reviewer attempting an owner-only route gets 403; an owner attempting to write a review gets 403. The UI hides unavailable actions but is not the enforcement point.
- **Service layer** — Business logic lives in `services/`, not in routers. Routers handle HTTP concerns (parsing, status codes, response shaping); services handle queries, calculations, and orchestration.
- **File uploads** — Pillow validates MIME type by re-opening and verifying the file header (not just the extension), strips EXIF metadata, and downsamples images larger than 1920px. Files are stored under `uploads/{profiles,restaurants,reviews}/` and served as static files.

---

## Project Structure

```
lab1/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, CORS, mounts, router includes
│   │   ├── config.py                # Settings loaded from .env
│   │   ├── database.py              # SQLAlchemy engine, Base, SessionLocal
│   │   ├── models/
│   │   │   ├── user.py              # User + UserPreferences ORM models
│   │   │   ├── restaurant.py        # Restaurant + RestaurantClaim ORM models
│   │   │   ├── review.py            # Review ORM model
│   │   │   ├── favorite.py          # Favorite ORM model
│   │   │   └── conversation.py      # Conversation + ConversationMessage models
│   │   ├── schemas/                 # Pydantic request/response models (11 files)
│   │   ├── routers/
│   │   │   ├── auth.py              # POST /auth/user/signup, /auth/user/login, owner equivalents
│   │   │   ├── users.py             # GET/PUT /users/me, POST /users/me/photo
│   │   │   ├── restaurants.py       # CRUD + search + claim + photo upload
│   │   │   ├── reviews.py           # Review CRUD, avg_rating recalculation
│   │   │   ├── favorites.py         # POST/DELETE /favorites/{id}, GET /favorites/me
│   │   │   ├── preferences.py       # GET/PUT /preferences/me
│   │   │   ├── history.py           # GET /history/me
│   │   │   ├── owner.py             # Owner dashboard, analytics, per-restaurant stats
│   │   │   └── ai_assistant.py      # POST /ai/chat (multi-turn)
│   │   ├── services/
│   │   │   ├── ai_service.py        # LangChain chain, tool calls, conversation threading
│   │   │   ├── review_service.py    # Review write + rating recalculation
│   │   │   ├── owner_service.py     # Dashboard aggregations, sentiment analysis
│   │   │   ├── favorites_service.py
│   │   │   ├── preferences_service.py
│   │   │   ├── history_service.py
│   │   │   └── prompts.py           # System prompt templates for AI
│   │   ├── middleware/
│   │   │   └── exception_handler.py # Maps SQLAlchemy / Pydantic errors to HTTP responses
│   │   └── utils/
│   │       ├── auth.py              # JWT encode/decode, get_current_user dependency
│   │       ├── file_upload.py       # Pillow validation, resize, save
│   │       └── validators.py        # Custom field validators
│   ├── tests/
│   │   ├── conftest.py              # SQLite fixtures, factory helpers, auth headers
│   │   ├── test_auth.py             # 25 tests: hashing, JWT, signup, login, roles
│   │   ├── test_restaurants.py      # 32 tests: CRUD, search, filters, claim
│   │   ├── test_reviews.py          # 29 tests: CRUD, auth matrix, rating recalc
│   │   ├── test_favorites.py        # 17 tests: add, remove, list, isolation
│   │   └── test_owner.py            # 17 tests: access control, analytics, dashboard
│   ├── docs/
│   │   ├── DEMO_SCENARIOS.md        # 20 graded demo scenarios with step-by-step instructions
│   │   ├── TEST_DATA.md             # Reference test data and boundary inputs
│   │   ├── TESTING_PLAN.md          # Full test plan (unit, integration, E2E, QA)
│   │   ├── chatbot_demo_guide.md    # AI chatbot query patterns per restaurant
│   │   ├── swagger_auth_guide.md    # How to authenticate in Swagger UI
│   │   ├── postman_collection.json  # Postman v2.1 collection (43 requests)
│   │   └── seed_data.sql            # SQL INSERT reference (use Python script to seed)
│   ├── uploads/                     # Runtime: uploaded photos (git-ignored)
│   │   ├── profiles/
│   │   ├── restaurants/
│   │   └── reviews/
│   ├── seed_data.py                 # Demo seeding script (run from backend/)
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                         # Created by you — never commit
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Route definitions
│   │   ├── context/
│   │   │   └── AuthContext.jsx      # Global auth state, localStorage, token refresh
│   │   ├── hooks/
│   │   │   ├── useAuth.js           # Auth context consumer
│   │   │   ├── useChat.js           # AI chat state machine
│   │   │   ├── useDebounce.js       # Search input debounce
│   │   │   └── useRestaurants.js    # Paginated restaurant list with filter state
│   │   ├── services/                # Typed Axios wrappers for every API endpoint
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   ├── Explore.jsx          # Search + filter + sort + restaurant grid
│   │   │   ├── RestaurantDetails.jsx # Detail view, reviews, write/edit/delete flow
│   │   │   ├── AddRestaurant.jsx    # Create/edit form with photo picker
│   │   │   ├── Profile.jsx          # Profile + photo upload
│   │   │   ├── Preferences.jsx      # Dining preference chips
│   │   │   ├── Favorites.jsx
│   │   │   ├── History.jsx
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   └── owner/
│   │   │       ├── OwnerDashboard.jsx
│   │   │       ├── OwnerRestaurants.jsx
│   │   │       ├── OwnerRestaurantDetail.jsx
│   │   │       └── OwnerReviews.jsx
│   │   ├── components/
│   │   │   ├── common/              # Navbar, Footer, StarRating, PhotoPicker, AIAssistant ...
│   │   │   ├── restaurants/         # RestaurantCard, ReviewCard, ReviewForm
│   │   │   ├── profile/             # ProfileForm, PreferencesForm, ImageUpload
│   │   │   └── owner/               # AnalyticsCard
│   │   └── utils/                   # cn(), format helpers, API error parser
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── .env                         # Created by you — never commit
├── docs/                            # Root-level docs (if any)
├── testing_checklist.md
└── README.md
```

---

## Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.11+ | 3.12 also works |
| Node.js | 18+ | 20 LTS recommended |
| MySQL | 8.0+ | Must be running before starting the backend |
| Ollama | Latest | Optional — required only for the AI assistant |
| Git | Any | — |

Install Ollama from [ollama.com](https://ollama.com) and pull the default model:

```bash
ollama pull llama3.2
```

---

## Database Setup

Create the database in MySQL before running the backend:

```sql
CREATE DATABASE restaurant_platform
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

> **Tables are created automatically** when the FastAPI app starts for the first time via `Base.metadata.create_all()`. You do not need to run any migration scripts.

If you prefer to inspect or manually apply the schema:

```bash
# Reference schema (read-only — the app creates tables itself)
cat backend/docs/seed_data.sql    # includes table structure comments
```

---

## Backend Setup

```bash
# 1. Enter the backend directory
cd backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and fill in your values (see Environment Variables section below)

# 5. Start the development server
uvicorn app.main:app --reload --port 8000
```

The server will:
- Connect to MySQL using `DATABASE_URL` from `.env`
- Auto-create all tables (`users`, `restaurants`, `reviews`, `favorites`, `restaurant_claims`, `user_preferences`, `conversations`, `conversation_messages`)
- Create `uploads/profiles/`, `uploads/restaurants/`, and `uploads/reviews/` directories
- Start serving at `http://localhost:8000`

---

## Environment Variables

Create `backend/.env` from the example:

```bash
cp backend/.env.example backend/.env
```

| Variable | Required | Example | Description |
|---|---|---|---|
| `DATABASE_URL` | Yes | `mysql+pymysql://root:password@localhost:3306/restaurant_platform` | Full SQLAlchemy connection string |
| `SECRET_KEY` | Yes | `a-long-random-string-at-least-32-chars` | JWT signing key — change this in every environment |
| `ALGORITHM` | Yes | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Yes | `43200` | Token lifetime in minutes (43200 = 30 days) |
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Ollama API endpoint — omit to disable AI |
| `OLLAMA_MODEL` | No | `llama3.2` | Model name as shown in `ollama list` |
| `TAVILY_API_KEY` | No | `tvly-xxxxxxxxxxxx` | Tavily API key for web search — omit to disable |
| `UPLOAD_DIR` | Yes | `uploads` | Relative path for uploaded file storage |
| `FRONTEND_URL` | Yes | `http://localhost:5173` | Allowed CORS origin |

**Frontend** (`frontend/.env`):

```bash
cp frontend/.env.example frontend/.env
```

| Variable | Required | Example | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Yes | `http://localhost:8000` | Backend base URL used by Axios |

---

## Frontend Setup

```bash
# 1. Enter the frontend directory
cd frontend

# 2. Configure environment
cp .env.example .env
# Ensure VITE_API_BASE_URL=http://localhost:8000

# 3. Install dependencies
npm install

# 4. Start the development server
npm run dev
```

Frontend available at: **http://localhost:5173**

To build for production:

```bash
npm run build     # outputs to frontend/dist/
npm run preview   # preview the production build locally
```

---

## Seed Data

The seed script populates the database with realistic demo data for testing and grading.

### What is seeded

| Entity | Count | Details |
|---|---|---|
| Users | 8 | 5 reviewers + 3 owners; all passwords are `password` |
| Restaurants | 90 | 14 cuisines; SF / Oakland / San Jose / South Bay; mix of claimed and unclaimed |
| Reviews | 75 | Multi-sentence, realistic; spread over past 6 months |
| Favorites | 42 | Distributed across all reviewer accounts |
| User Preferences | 5 | One set per reviewer |
| Ownership Claims | 7 | 7 restaurants claimed by 3 owners |
| AI Conversations | 2 | Demo multi-turn conversation histories |

### Running the seed script

```bash
# From the backend/ directory (with virtualenv active)
cd backend

# First run — inserts data only if the users table is empty
python seed_data.py

# Force re-seed — wipes all data first, then re-inserts
python seed_data.py --wipe

# Recalculate stored avg_rating / review_count without wiping any data
python seed_data.py --recalc
```

> The `--wipe` flag deletes all rows from every table in the correct dependency order before re-seeding. Use it to reset the database to a clean demo state.

> **Maintenance note:** If `GET /restaurants` returns `avg_rating` or `review_count` values that look stale or inconsistent with the reviews visible on the detail page (e.g., after testing, partial seeding, or manual database edits), run `python seed_data.py --recalc` to resync all stored aggregates from the reviews table without touching any other data. This is safe to run at any time.

### SQL reference

A static SQL version of the seed data is available for inspection:

```bash
# View SQL INSERT statements (passwords are placeholders — use the Python script to seed)
cat backend/docs/seed_data.sql
```

---

## Running Locally

Start all three services in separate terminals:

**Terminal 1 — MySQL** (if not already running as a service):
```bash
mysql.server start            # macOS Homebrew
# or: sudo systemctl start mysql   (Linux)
# or: net start mysql               (Windows)
```

**Terminal 2 — Ollama** (optional, for AI assistant):
```bash
ollama serve
```

**Terminal 3 — Backend**:
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 4 — Frontend**:
```bash
cd frontend
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |

---

## API Documentation

Interactive API documentation is auto-generated by FastAPI and available immediately after starting the backend.

### Swagger UI — http://localhost:8000/docs

The fastest way to explore and test every endpoint. To test protected routes:

1. Call `POST /auth/user/login` or `POST /auth/owner/login` with your credentials
2. Copy the `access_token` from the response
3. Click **Authorize** (lock icon, top right)
4. Enter: `Bearer <your_token>` (the word `Bearer` followed by a space is required)
5. Click **Authorize** → **Close**
6. All subsequent requests will include the token automatically

For a detailed walkthrough see [`backend/docs/swagger_auth_guide.md`](backend/docs/swagger_auth_guide.md).

### Postman Collection

A complete Postman v2.1 collection with 43 pre-configured requests, auto-token-save scripts, and inline examples is available at:

```
backend/docs/postman_collection.json
```

Import it via **File → Import** in Postman. Set the `base_url` collection variable to `http://localhost:8000`.

### API Summary

| Group | Key Endpoints |
|---|---|
| **Auth** | `POST /auth/user/signup`, `POST /auth/user/login`, `POST /auth/owner/signup`, `POST /auth/owner/login`, `GET /auth/me` |
| **Profile** | `GET/PUT /users/me`, `POST /users/me/photo` |
| **Preferences** | `GET/PUT /preferences/me` |
| **Restaurants** | `GET /restaurants` (search+filter), `POST /restaurants`, `GET /restaurants/{id}`, `PUT /restaurants/{id}`, `DELETE /restaurants/{id}`, `POST /restaurants/{id}/claim`, `POST /restaurants/{id}/photos` |
| **Reviews** | `GET /restaurants/{id}/reviews`, `POST /restaurants/{id}/reviews`, `PUT /reviews/{id}`, `DELETE /reviews/{id}` |
| **Favorites** | `POST /favorites/{id}`, `DELETE /favorites/{id}`, `GET /favorites/me` |
| **History** | `GET /history/me` |
| **Owner** | `GET /owner/me`, `GET /owner/dashboard`, `GET /owner/restaurants`, `GET /owner/restaurants/{id}/stats`, `GET /owner/reviews` |
| **AI** | `POST /ai/chat` |
| **Health** | `GET /health` |

---

## Sample Credentials

All demo accounts use the password: **`password`**

| Role | Name | Email | Notes |
|---|---|---|---|
| Reviewer | Jane Doe | `user@demo.com` | Has reviews, favorites, preferences; primary demo account |
| Reviewer | Marcus Johnson | `marcus@demo.com` | Oakland-focused; BBQ and casual dining reviews |
| Reviewer | Priya Patel | `priya@demo.com` | Vegetarian preferences; Indian and Mediterranean focus |
| Reviewer | Alex Rivera | `alex@demo.com` | Fine dining; omakase and French cuisine reviews |
| Reviewer | Emily Chen | `emily@demo.com` | Dim sum expert; Chinese/Japanese/Vietnamese focus |
| Owner | Mario Rossi | `owner@demo.com` | Owns Ristorante Bello + Bella Vista Rooftop |
| Owner | Wei Zhang | `wei@demo.com` | Owns Dragon Garden + Sakura Omakase |
| Owner | Sofia Hernandez | `sofia@demo.com` | Owns Taqueria La Paloma, Casa Oaxaca, Olive Branch |

The following restaurants are **unclaimed** and available for the ownership claim demo: Ramen House Natori, Spice Route, Bangkok Noodles, The Smokehouse, Blue Plate Diner, Seoul Kitchen, Pho Saigon, Café Madeleine, The Green Bowl, The Wharf Kitchen, Sunday Morning Café, and the majority of the ~70 South Bay restaurants added in the expanded dataset.

For full demo walkthrough scripts, see [`backend/docs/DEMO_SCENARIOS.md`](backend/docs/DEMO_SCENARIOS.md).

---

## Running Tests

The test suite uses pytest with an in-memory SQLite database — no MySQL or external services required.

```bash
cd backend
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_auth.py -v
pytest tests/test_restaurants.py -v

# Run with coverage report
pip install pytest-cov
pytest tests/ --cov=app --cov-report=term-missing
```

**Test coverage:**

| File | Tests | Areas Covered |
|---|---|---|
| `test_auth.py` | 25 | Password hashing, JWT, signup, login, role enforcement |
| `test_restaurants.py` | 32 | CRUD, search filters, sort, pagination, claim flow |
| `test_reviews.py` | 29 | CRUD, auth matrix (reviewer/owner/anon), rating recalculation |
| `test_favorites.py` | 17 | Add, remove, list, duplicate check, user isolation |
| `test_owner.py` | 17 | Access control on all owner routes, analytics accuracy |
| **Total** | **120** | — |

---

## Assumptions

- **Single database, no migrations framework** — SQLAlchemy's `create_all()` is used for table creation. Schema changes require manual `ALTER TABLE` or a database drop-and-recreate.
- **Local file storage** — Uploaded photos are saved to `backend/uploads/` and served as static files by FastAPI. This directory is relative to the working directory where `uvicorn` is started.
- **Ollama must be running separately** — The AI assistant makes synchronous HTTP calls to `OLLAMA_BASE_URL`. If Ollama is not running, the `/ai/chat` endpoint will return a 503 with a user-friendly error message.
- **No email verification** — Users can register with any syntactically valid email address. Out of scope for this assignment.
- **Restaurant claim is auto-approved** — `POST /restaurants/{id}/claim` immediately sets `is_claimed=True`. In a production system this would require an admin approval step.
- **No real-time features** — Review updates and rating changes require a page reload on the listing page (the detail page updates optimistically).
- **Single-region deployment assumed** — Timestamps are stored and returned as UTC. The frontend renders them as-is without timezone conversion.

---

## Limitations

- **No geolocation search** — The "search radius" preference is stored and forwarded to the AI as context, but the restaurant list endpoint filters by city string only. Distance-based filtering would require PostGIS or a geocoding service.
- **Local photo storage is not production-safe** — Files in `uploads/` are served directly from the FastAPI process. A production deployment would store files on S3 or equivalent and serve via CDN.
- **AI conversation history is per-session** — `conversation_id` is returned on first chat and must be passed back by the client. If the client loses the ID, conversation context is lost. A production system would tie conversations to the user's session automatically.
- **No pagination on owner dashboard** — The analytics dashboard loads all reviews for a given owner. For owners with thousands of reviews, this would require server-side pagination.
- **No rate limiting** — The API has no rate limiting on authentication or AI endpoints. Brute-force protection and API throttling are out of scope.
- **bcrypt work factor 12** — Suitable for development; a production deployment should benchmark and set the appropriate cost factor for the target hardware.
- **SQLite used only in tests** — There are minor behavioral differences between SQLite (tests) and MySQL (production), particularly around JSON column handling and case-sensitivity in `LIKE` queries.

---

## Future Improvements

| Priority | Improvement |
|---|---|
| High | Replace `create_all()` with Alembic migrations for safe schema evolution |
| High | Move file storage to S3 (or compatible object store) with pre-signed URL uploads |
| High | Add Redis-backed rate limiting and brute-force protection on auth endpoints |
| Medium | Geolocation search using PostGIS `ST_Distance_Sphere` or Google Maps Geocoding API |
| Medium | Email verification on signup using SendGrid or SES |
| Medium | Admin panel for claim approval workflow and content moderation |
| Medium | WebSocket-based live review feed on restaurant detail page |
| Medium | Swap Ollama for Anthropic or OpenAI API with a single config change (LangChain makes this trivial) |
| Low | Push notifications (browser/email) when a review is posted on an owned restaurant |
| Low | Social graph — follow reviewers, see their activity feed |
| Low | Multi-photo review uploads (currently limited to 1 photo per review in the UI) |
| Low | Export owner analytics as CSV / PDF |

---

## Security Notes

- Passwords hashed with bcrypt, cost factor 12 (via passlib)
- JWT tokens are HS256-signed; token secret must be rotated if compromised
- All file uploads validated with Pillow header inspection (not extension alone); EXIF stripped
- CORS restricted to `FRONTEND_URL` — wildcard origins not permitted
- All SQL queries use SQLAlchemy parameterized statements — no raw string interpolation
- Role enforcement lives in FastAPI dependencies (`require_user`, `require_owner`), not in UI conditionals
- Protected endpoints return `401 Unauthorized` for missing/expired tokens and `403 Forbidden` for wrong roles — never `404` to avoid information leakage

---

## Documentation Index

| Document | Location | Purpose |
|---|---|---|
| Demo Scenarios (20) | `backend/docs/DEMO_SCENARIOS.md` | Step-by-step grading walkthrough |
| Test Plan | `backend/docs/TESTING_PLAN.md` | Unit, integration, and E2E test strategy |
| Test Data Reference | `backend/docs/TEST_DATA.md` | Boundary values, edge cases, demo accounts |
| Chatbot Demo Guide | `backend/docs/chatbot_demo_guide.md` | AI query patterns per restaurant |
| Swagger Auth Guide | `backend/docs/swagger_auth_guide.md` | How to authenticate in Swagger UI |
| Postman Collection | `backend/docs/postman_collection.json` | 43 pre-built API requests |
| SQL Seed Reference | `backend/docs/seed_data.sql` | SQL INSERT statements (inspection only) |
