# ForkFinder: A Full-Stack Restaurant Discovery Platform with an AI-Powered Dining Assistant

**Course:** DATA 236 Distributed Systems — Lab 1
**Project:** ForkFinder Restaurant Discovery Platform
**Group:** 7
**Authors:** Danish Waseem (19101511), Saketh (019101111)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Purpose and Goals](#2-purpose-and-goals)
3. [System Design](#3-system-design)
4. [AI Implementation](#4-ai-implementation)
5. [Results](#5-results)
6. [Challenges and Future Improvements](#6-challenges-and-future-improvements)
7. [Conclusion](#7-conclusion)

---

## 1. Introduction

Restaurant discovery apps like Yelp and Google Maps have become deeply embedded in how people choose where to eat. They work because they solve a real information problem: there are thousands of options nearby, most of them unknown to you, and filtering them by what you actually care about — cuisine, price, mood, dietary needs — is tedious to do manually. The interesting question from a systems perspective is: can a purpose-built application do this *better* than a general-purpose search engine, and can a conversational AI interface make the discovery process feel more natural?

ForkFinder is an attempt to answer that question. It is a full-stack Yelp-style restaurant discovery platform built from scratch, featuring a React frontend, a Python FastAPI backend, a MySQL database, and an embedded AI dining assistant powered by a local large language model. The platform supports two distinct user roles — diners who discover and review restaurants, and restaurant owners who manage listings and monitor analytics — each with a purpose-built interface and strict server-side access control.

This report describes the system architecture, implementation decisions, AI pipeline design, test results, challenges encountered, and directions for future improvement.

---

## 2. Purpose and Goals

The core goal of ForkFinder is to demonstrate a complete, production-style full-stack application that integrates modern AI tooling. The specific objectives were:

**Functional goals:**
- Allow diners to search, filter, and sort restaurants by cuisine, city, price tier, and minimum rating
- Support user-generated reviews with star ratings, comments, and photo uploads
- Let users save favorites and view their activity history
- Give restaurant owners a private dashboard with rating analytics, review trends, and sentiment summaries
- Provide an AI assistant that interprets natural-language queries and returns ranked restaurant recommendations personalized to each user's saved preferences

**Technical goals:**
- Build a RESTful API with clearly separated concerns: routing, service logic, and data access
- Enforce role-based access control at the API layer (not just in the frontend)
- Validate uploaded images server-side using Pillow rather than relying on file extensions
- Implement multi-turn conversation state for the AI assistant, persisted to the database so sessions can resume across page reloads
- Produce comprehensive automated tests and a grader-friendly demo scenario guide

**Learning goals:**
- Gain hands-on experience with FastAPI, SQLAlchemy, and Pydantic
- Understand the practical tradeoffs in integrating a local LLM (Ollama) versus a hosted API
- Practice designing a system with a clean separation between what the frontend enforces (UX) and what the backend enforces (security)

---

## 3. System Design

### 3.1 Architecture Overview

ForkFinder is organized as three loosely coupled services that communicate over HTTP:

```
┌─────────────────────────────────────────────────────────────────┐
│                      React Frontend (:5173)                      │
│   Vite · React Router v6 · Axios · Tailwind CSS · AuthContext   │
└──────────────────────────────┬──────────────────────────────────┘
                               │  REST / JSON
┌──────────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend (:8000)                        │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │   Routers    │→ │    Services     │→ │  SQLAlchemy ORM    │  │
│  │  (9 modules) │  │   (7 modules)   │  │  MySQL 8 via PyMySQL│  │
│  └──────────────┘  └────────┬────────┘  └────────────────────┘  │
│                             │                                    │
│                    ┌────────▼────────┐                           │
│                    │   AI Service    │──► Ollama / llama3.2      │
│                    │   LangChain     │──► Tavily Web Search      │
│                    └─────────────────┘                           │
│  Middleware: CORS · GlobalExceptionHandler · StaticFiles         │
└─────────────────────────────────────────────────────────────────┘
```

The frontend never talks directly to the database. All state mutations go through the API, which validates, authorizes, and persists them. Uploaded photos are stored in a local `uploads/` directory and served as FastAPI static files, keeping the storage concern separate from the application logic.

### 3.2 Database Design

The database has six core tables:

| Table | Key columns | Notes |
|---|---|---|
| `users` | `id`, `email`, `role`, `password_hash`, profile fields | `role` ∈ {`user`, `owner`} |
| `user_preferences` | `user_id` (FK), `cuisine_preferences` (JSON), `price_range`, `dietary_restrictions` (JSON) | One row per user |
| `restaurants` | `id`, `name`, `cuisine_type`, `price_range`, `avg_rating`, `review_count`, `hours` (JSON), `photos` (JSON), `is_claimed`, `claimed_by` | `avg_rating` and `review_count` are denormalized |
| `restaurant_claims` | `restaurant_id`, `owner_id`, `status` | Enforces single-owner-per-restaurant |
| `reviews` | `id`, `user_id`, `restaurant_id`, `rating`, `comment`, `photos` (JSON) | |
| `favorites` | `user_id`, `restaurant_id`, `created_at` | Composite unique constraint |
| `conversations` / `conversation_messages` | `conversation_id`, `role`, `content`, `extra_json` | Persists AI chat history |

One notable design choice is **denormalized ratings**: both `avg_rating` and `review_count` are stored directly on the `Restaurant` row rather than computed from a `COUNT`/`AVG` aggregation on every read. This is a deliberate tradeoff — it adds a small write cost (the `recalc_rating()` function is called on every review create, update, or delete) but makes the heavily-read restaurant listing query fast and simple. For an application where reads greatly outnumber writes, this is the correct tradeoff. If stored aggregates ever become stale (e.g., after manual database edits or partial test runs), running `python seed_data.py --recalc` from the `backend/` directory resyncs all stored values from the reviews table without touching any other data.

Array-typed fields such as `hours`, `photos`, `cuisine_preferences`, and `dietary_restrictions` are stored as JSON text. This avoids a dependency on MySQL's JSON column type (which has version-specific behavior) and makes the schema easy to extend — adding a new ambiance option, for instance, requires no `ALTER TABLE`.

### 3.3 Backend Architecture

The FastAPI backend follows a layered architecture with strict separation of concerns:

**Routers** handle HTTP: parsing request bodies, returning status codes, and shaping responses. They contain no business logic.

**Services** handle business logic: complex queries, cross-model calculations (like `recalc_rating()`), aggregations for the owner dashboard, and orchestration of the AI pipeline. Services receive a database session and return typed domain objects.

**Models** are SQLAlchemy ORM classes that map to MySQL tables. They define relationships and field types but contain no business logic.

**Schemas** are Pydantic models used for request validation and response serialization. Every API endpoint has explicit `response_model` declarations, which means FastAPI validates the response shape as well as the request shape.

**Authentication** is handled via a `get_current_user` FastAPI dependency that decodes the JWT on every request. Two role-specific wrappers — `require_user` and `require_owner` — raise `403 Forbidden` immediately if the caller's role does not match. This is the actual security boundary; the frontend only hides or shows UI elements based on role, but every protected action is re-validated at the API level.

The nine router modules are:

| Router | Prefix | Key responsibility |
|---|---|---|
| `auth` | `/auth` | Register and login for both roles |
| `users` | `/users` | Profile reads, updates, and photo uploads |
| `preferences` | `/preferences` | Dining preference CRUD |
| `restaurants` | `/restaurants` | Discovery, CRUD, photo uploads, ownership claim |
| `reviews` | `/reviews`, `/restaurants/{id}/reviews` | Review CRUD with rating recalculation |
| `favorites` | `/favorites` | Toggle and list favorites |
| `history` | `/history` | Activity log aggregation |
| `owner` | `/owner` | Dashboard analytics, per-restaurant stats |
| `ai_assistant` | `/ai` | Multi-turn chat endpoint |

### 3.4 Frontend Architecture

The React frontend uses a context-based approach for global state. `AuthContext` stores the JWT and current user object in `localStorage` and provides them via the `useAuth()` hook. An Axios request interceptor automatically attaches the `Authorization: Bearer <token>` header to every outgoing request, so individual page components never need to handle token management directly.

Route protection is implemented with a thin `PrivateRoute` wrapper that checks `AuthContext` before rendering a page. Role-specific routes (e.g., `/owner/dashboard`) additionally check `user.role === 'owner'` and redirect reviewers to the home page.

Custom hooks encapsulate stateful logic: `useRestaurants()` manages paginated restaurant lists with combined filter state, debouncing the search query with `useDebounce()` to avoid firing a new request on every keystroke. `useChat()` manages the AI assistant conversation state machine.

The `services/` directory contains one module per API resource (e.g., `restaurants.js`, `reviews.js`), each exporting typed async functions. This keeps page components clean — a component calls `reviewsService.create(restaurantId, payload)` rather than constructing Axios calls inline.

Photo uploads use an optimistic UI pattern: on file selection, `URL.createObjectURL()` immediately renders a preview to the user. The actual HTTP request runs in the background; if it fails, the preview is reverted and an error toast is shown. This is implemented consistently across profile photos, restaurant photos, and review photos.

### 3.5 Security Design

The application enforces security at multiple layers:

- **Passwords** are hashed with bcrypt at cost factor 12. Plaintext passwords are never stored or logged.
- **JWT tokens** are HS256-signed, expire after 30 days, and include the user's `id` and `role` as claims. The signing secret is loaded from the environment variable `SECRET_KEY`.
- **File uploads** are validated by Pillow's `Image.verify()`, which reads the actual file header rather than trusting the extension. EXIF metadata is stripped, and images larger than 1920px are downsampled before saving.
- **CORS** is restricted to the configured `FRONTEND_URL`. Wildcard origins are not permitted.
- **SQL injection** is prevented throughout by SQLAlchemy's parameterized query interface. No raw string interpolation is used in queries.
- **Role enforcement** lives in FastAPI dependency functions, not UI conditionals. A reviewer using `curl` or Swagger UI to call `POST /reviews` with an owner JWT will receive `403 Forbidden`.

---

## 4. AI Implementation

The AI assistant is the most architecturally interesting component of ForkFinder. Rather than making a single LLM call and hoping for a good result, the service breaks the problem into seven discrete, testable stages. This pipeline design makes the system robust: each stage can be reasoned about independently, and failures at any stage have bounded consequences.

### 4.1 Pipeline Overview

Every call to `POST /ai/chat` passes through these stages in sequence:

```
User message
     │
     ▼
Stage 0: Load conversation history (from DB if conversation_id supplied)
     │
     ▼
Stage 1: Load user preferences (cuisine, price, dietary, ambiance)
     │
     ▼
Stage 2: Rule-based filter extraction (zero LLM token cost)
     │     cuisine · price · dietary · occasion · ambiance · location · web trigger
     ▼
Stage 3: SQLAlchemy DB search using extracted filters + preferences
     │     fallback: broaden filters if no results returned
     ▼
Stage 4: Relevance scoring and ranking (0–100 point scale)
     │
     ▼
Stage 5: Tavily web search (only if "hours", "trending", "open now" detected)
     │
     ▼
Stage 6: LLM response generation via LangChain + ChatOllama
     │     fallback: deterministic template if Ollama unavailable
     ▼
Stage 7: Persist turn to database, return conversation_id
```

### 4.2 Stage 2: Rule-Based Filter Extraction

The filter extraction step is the most important stage in the pipeline because it determines what gets searched. The key design decision here is to implement it as a **pure rule-based system with no LLM involvement**. This means:

1. It runs in microseconds (no network call, no token cost)
2. It always produces output — there is no risk of the LLM refusing the question or hallucinating a filter value
3. It is fully deterministic and easy to test

The extractor maintains keyword dictionaries for five filter dimensions:

- **Cuisine**: maps food-related keywords to canonical cuisine types (e.g., "pasta" → "Italian", "dim sum" → "Chinese", "ramen" → "Japanese")
- **Price**: maps sentiment words to dollar signs (e.g., "cheap" → "\$", "splurge" → "\$\$\$\$", "fine dining" → "\$\$\$\$")
- **Dietary restrictions**: detects terms like "vegan", "gluten-free", "halal", "keto"
- **Occasion**: maps context words to standardized labels (e.g., "romantic" → "date night", "large group" → "group dining")
- **Ambiance**: detects "rooftop", "outdoor seating", "casual", "sports bar", and similar terms

A separate regex pattern extracts location from phrases like "near Mission District" or "in Oakland". If no location is found in the message, the user's first saved `preferred_locations` entry is used as a fallback.

The extractor also scans for web-search trigger words — "hours", "open now", "trending", "just opened" — and sets a `needs_web_search` flag that activates Stage 5.

To support multi-turn conversations, the extractor processes not just the current message but also the last four user messages from conversation history. This allows follow-up queries like "What about outdoor seating?" to inherit the cuisine and location context from earlier in the conversation.

### 4.3 Stages 3–4: Database Search and Ranking

The DB search builds a SQLAlchemy query from the extracted filters, with automatic fallback behavior: if the combined filters return zero results, the query is broadened by dropping the cuisine and price constraints and re-running with only the location filter. This prevents the frustrating experience of the assistant returning "no results found" for reasonable queries.

The ranking function scores each candidate restaurant on a 0–100 scale using five independent components:

| Component | Max Points | Logic |
|---|---|---|
| Star rating | 40 | Linear scaling: `(avg_rating / 5.0) × 40` |
| Popularity | 20 | 1 point per 5 reviews, capped at 20 |
| Cuisine match | 20 | 20 pts if query cuisine matches; 10 pts if it matches saved preference |
| Price match | 10 | Exact match on price range |
| Location match | 10 | City contains the extracted or preferred location string |

This scoring formula reflects genuine relevance signals: a 4.8-star restaurant at the right price tier with 50 reviews will outscore a 5.0-star restaurant with 1 review and the wrong cuisine. The top 5 results by score are returned as typed `RestaurantRecommendation` objects, each carrying a list of human-readable `match_reasons` that explain why the restaurant was recommended.

### 4.4 Stage 5: Tavily Web Search

The Tavily integration handles queries that the database alone cannot answer: current business hours, recently opened restaurants, special events, or "what's trending" questions. The web search fires only when the `needs_web_search` flag is set, keeping it out of the critical path for ordinary queries.

If `TAVILY_API_KEY` is absent from the environment, this stage is silently skipped. The search returns a plain-text summary (up to 1,200 characters) synthesized from the top three web results, which is passed as a `web_block` to the LLM prompt in Stage 6.

### 4.5 Stage 6: LLM Response Generation

The LLM stage uses LangChain's `ChatOllama` abstraction to call a locally running Ollama model (default: `llama3.2`). Three distinct prompt modes are selected based on the query:

- **Normal mode**: The system prompt includes the top-ranked restaurant results, the web search summary (if any), and the user's preferences. The LLM is instructed to write a conversational response and suggest a follow-up question.
- **Clarification mode**: Triggered when the filter extractor finds no meaningful signal in the message (no cuisine, no location, no occasion). The LLM is asked to identify what is missing and request it from the user.
- **Fallback mode**: Triggered when the DB search returned no strong matches. The LLM is asked to explain what was searched, acknowledge the weak results, and suggest how the user could broaden their query.

The LLM is prompted to return structured JSON with three fields: `assistant_message`, `reasoning`, and `follow_up_question`. The response is parsed with `json.loads()`, with a guard for the case where the model returns prose instead of JSON (in which case the raw text is used verbatim).

If Ollama is not running or returns an error, the service falls back to a deterministic template that formats the ranked results into clean markdown. This ensures the assistant never returns a blank response or an unhandled exception — it degrades gracefully.

### 4.6 Stage 7: Conversation Persistence

User messages and assistant responses are written to the `conversations` and `conversation_messages` tables. The assistant message row carries an `extra_json` field that stores the reasoning, extracted filters, and recommendation IDs alongside the message text. This means the conversation history is recoverable across sessions — if the user returns to the chat window after closing it, the client can pass the `conversation_id` to reload the prior context from the database rather than starting fresh.

### 4.7 Example End-to-End Flow

> **User:** "I want something romantic and Italian for dinner tonight, budget around $$"

| Stage | Output |
|---|---|
| Filter extraction | `cuisine=Italian, price_range=$$, ambiance=intimate, occasion=date night` |
| DB search | Returns Italian restaurants in the user's preferred city (San Francisco), ordered by rating |
| Ranking | Ristorante Bello scores 89/100 (4.67 stars, Italian, $$, SF); Bella Vista scores 72/100 |
| Web search | Not triggered (no web trigger words in message) |
| LLM response | "For a romantic Italian dinner at $$, I'd recommend Ristorante Bello in North Beach — candlelit, authentic Neapolitan pasta, and a wine list to match. Would you like outdoor seating, or is an intimate indoor table perfect?" |
| Persist | `conversation_id=1` returned; client stores it for follow-up turns |

---

## 5. Results

### 5.1 Suggested Screenshots

The following screenshots are recommended for inclusion in the final submission. Suggested captions are provided for each.

---

**Screenshot 1 — Home Page**
> *Caption: ForkFinder home page with the hero search bar and featured restaurant cards. The navigation bar displays role-appropriate links for a logged-in reviewer.*

---

**Screenshot 2 — Explore / Search Page with Active Filters**
> *Caption: The Explore page with compound filters applied: Italian cuisine, $$ price range, minimum 4.0 stars, sorted by Highest Rated. Active filters are displayed as removable chips above the restaurant grid.*

---

**Screenshot 3 — Restaurant Detail Page**
> *Caption: Restaurant detail page for Ristorante Bello, showing the photo hero layout, today's operating hours highlighted with a "Today" badge, the At a Glance sidebar, star rating distribution, and user reviews.*

---

**Screenshot 4 — Write a Review (with Photo Preview)**
> *Caption: The inline review form on the restaurant detail page. A photo has been selected and displays as a 96×96 thumbnail with a remove button; the star rating is set to 4 and a comment has been typed.*

---

**Screenshot 5 — Favorites Page**
> *Caption: The Favorites page for user Jane Doe, showing saved restaurants ordered by most recently added. Each card includes a filled heart icon, restaurant details, and a direct link to the detail page.*

---

**Screenshot 6 — Dining Preferences Form**
> *Caption: The Dining Preferences form with cuisine chips, price tier selection, ambiance toggles, dietary restriction checkboxes, and a search radius slider. Changes are saved with a single button click.*

---

**Screenshot 7 — Owner Analytics Dashboard**
> *Caption: The Owner Dashboard for Mario Rossi, showing aggregate statistics (3 restaurants, 7 total reviews, 4.5 average rating), a 6-month review trend chart, star rating distribution bars, and the most recent reviewer comments.*

---

**Screenshot 8 — AI Assistant Chat Window**
> *Caption: The AI Assistant chat window showing a multi-turn conversation. The first turn requested "romantic Italian dinner, $$"; the assistant returned Ristorante Bello as the top recommendation. The follow-up asked about outdoor seating, and the assistant refined the suggestion to Bella Vista Rooftop.*

---

**Screenshot 9 — Swagger UI with Authorization**
> *Caption: The Swagger UI at localhost:8000/docs showing the Authentication tag expanded and the Authorize dialog open. A Bearer token has been pasted in, enabling direct API testing from the browser.*

---

**Screenshot 10 — Mobile View (390px width)**
> *Caption: ForkFinder rendered at iPhone 14 Pro width (390px). The restaurant grid collapses to a single column, the navigation links move to a hamburger menu, and all touch targets meet the 44×44px minimum.*

---

**Screenshot 11 — 403 Response in Swagger UI**
> *Caption: Swagger UI showing a 403 Forbidden response from POST /reviews when called with an owner-role JWT, demonstrating that role-based access control is enforced at the API level regardless of client.*

---

**Screenshot 12 — Add Restaurant Form**
> *Caption: The Add Restaurant form with all sections visible: basic info, address, hours builder (per-day rows), and the photo picker with a selected image thumbnail showing its file size.*

---

### 5.2 API Test Results Summary

The test suite covers 120 test cases across five modules, using an in-memory SQLite database isolated per test (no MySQL dependency required to run tests):

| Module | Tests | Pass Rate | Areas Tested |
|---|---|---|---|
| `test_auth.py` | 25 | 100% | Bcrypt hashing correctness, JWT claims, signup validation, login success/failure, cross-role login rejection |
| `test_restaurants.py` | 32 | 100% | List with all filter combinations, full CRUD, hour key validation, price range validation, claim flow, 404 handling |
| `test_reviews.py` | 29 | 100% | Create/edit/delete auth matrix (reviewer/owner/anon × each action), rating recalculation after each write |
| `test_favorites.py` | 17 | 100% | Add, remove, duplicate prevention (400), per-user isolation, favorited_at timestamp |
| `test_owner.py` | 17 | 100% | 403 for all owner routes with reviewer token, 401 with no token, analytics accuracy, claim enforcement |
| **Total** | **120** | **100%** | — |

**Key access control assertions verified by tests:**

- `POST /reviews` with an owner JWT → `403 Forbidden`
- `GET /owner/dashboard` with a reviewer JWT → `403 Forbidden`
- `PUT /reviews/{id}` with a different reviewer's JWT → `403 Forbidden`
- `DELETE /restaurants/{id}` for a restaurant created by another user → `403 Forbidden`
- `POST /restaurants/{id}/claim` when the restaurant is already claimed → `400 Bad Request`
- Any protected endpoint with no Authorization header → `401 Unauthorized`

**Validation boundary tests verified:**

- Review comment of 9 characters → `422 Unprocessable Entity`
- Review rating of 0 or 6 → `422 Unprocessable Entity`
- Restaurant `price_range` of `$$$$$` → `422 Unprocessable Entity`
- Invalid `hours` key (e.g., `"funday"`) → `422 Unprocessable Entity`
- Password shorter than 8 characters → `400 Bad Request`

**Manual API tests via Swagger UI** confirmed:

- `GET /health` → `200 OK` (no auth required)
- `POST /auth/user/signup` with duplicate email → `400` with descriptive message
- `POST /auth/user/login` with wrong password → `401 Unauthorized`
- `GET /restaurants?cuisine=Italian&price_range=$$&sort=rating` → returns correct filtered, sorted subset
- `POST /restaurants/{id}/photos` with a PDF renamed to `.jpg` → `400 Bad Request` (Pillow header check)
- `GET /owner/dashboard` → all aggregated stats match manual count from seed data

---

## 6. Challenges and Future Improvements

### 6.1 Challenges

**Designing the AI pipeline without over-engineering it.** The initial instinct was to let the LLM handle everything: extract filters, search the database, rank results, and write the response in a single call. After experimentation, this approach was abandoned. LLMs are unreliable at producing structured filter queries, they hallucinate restaurant names and attributes, and a failed LLM call would take down the entire recommendation flow. The five-stage pipeline, where the LLM only handles the final natural-language response, proved far more reliable and debuggable.

**Role-based access control at scale.** Implementing `require_user` and `require_owner` as FastAPI dependencies was straightforward, but ensuring complete coverage — that every protected endpoint actually uses a dependency — required methodical review. The test suite was indispensable here: `test_owner.py` parametrizes all four owner-only `GET` endpoints and asserts both `403` (wrong role) and `401` (unauthenticated) for each, making coverage systematic rather than remembered.

**Bcrypt in test fixtures.** The test `conftest.py` creates user objects via factory helpers. Early versions called `hash_password()` for every test user, which added measurable overhead because bcrypt is intentionally slow. The fix was to generate the hash once per test session and reuse it for all test users — a small change with significant impact on test suite runtime.

**Multi-turn AI context.** Making follow-up queries ("What about outdoor seating?") work correctly without losing the context established in earlier turns was tricky. The solution — accumulating the last four user messages into the filter extraction input — works well for most conversational patterns, but can be confused by topic changes mid-conversation. This is documented as a known limitation.

**JSON columns in SQLite vs. MySQL.** The test suite uses SQLite for speed and isolation. SQLite does not support MySQL's JSON column type, which meant all `json.dumps/loads` calls in the models had to be explicit and not rely on database-level JSON parsing. This turned out to be a good constraint — it made the application more portable and the data handling more explicit.

### 6.2 Limitations

- **No geolocation search.** The "search radius" preference is forwarded to the AI as text context, but the restaurant list endpoint filters by city string only. True distance-based filtering requires PostGIS or a geocoding API, which was outside the scope of this assignment.
- **Local file storage.** Photos are saved to the filesystem on the same server as the application. This is not suitable for a multi-instance deployment or for large file volumes. A production system would use S3 or similar object storage.
- **No schema migrations.** SQLAlchemy's `create_all()` creates tables on first run but cannot handle schema changes. Adding a new column or modifying a constraint requires a manual `ALTER TABLE` or a database reset. Alembic would be the correct tool for a production codebase.
- **AI conversation context is session-scoped by ID.** If the client loses the `conversation_id`, the conversation history is orphaned. A production system would retrieve the user's most recent open conversation automatically on login.
- **No rate limiting or brute-force protection.** The authentication endpoints are not rate-limited. A production deployment would require rate limiting on login, registration, and AI chat endpoints.

### 6.3 Future Improvements

**Near-term (most impactful):**
- Migrate schema management to Alembic for safe, versioned migrations
- Move file storage to S3 with pre-signed upload URLs, so the API server never touches binary files
- Add Redis-based rate limiting on auth and AI endpoints

**Medium-term:**
- Implement PostGIS-based distance filtering so the search radius preference has real effect
- Add email verification on signup using a transactional email service
- Build an admin panel for claim approval moderation (currently all claims are auto-approved)
- Add WebSocket-based live review feeds on the restaurant detail page

**Longer-term:**
- Swap the local Ollama model for a Claude or GPT-4 API call with a single configuration change — LangChain's abstraction makes this trivial
- Implement a social graph (follow reviewers, see their activity feed) to increase engagement
- Add CSV/PDF export for owner analytics to support offline reporting

---

## 7. Conclusion

ForkFinder demonstrates that a production-quality full-stack application — with authentication, role-based access control, file upload handling, relational data modeling, and AI integration — can be built with a relatively small and readable codebase when the architecture is designed carefully from the start.

The most important lesson from this project is that **AI integration works best as a last mile, not a foundation**. The AI assistant is effective because it receives structured, validated inputs from the five preceding pipeline stages. The LLM is asked to do the one thing it is genuinely good at — generating a warm, contextually appropriate natural-language response — and everything that could go wrong before that point (filter extraction, database search, ranking, web lookup) is handled by deterministic code that can be unit tested and reasoned about independently.

The second key lesson is that **security must be layered**. The frontend hides the review form from owner accounts, but the API also rejects review submissions from owner tokens with a 403. Both layers are necessary: the frontend layer provides good UX, and the API layer provides actual security. The test suite verifies the API layer systematically, making it easy to catch regressions as the codebase evolves.

The 120 automated tests, 20 graded demo scenarios, complete Swagger documentation, and realistic seed data ensure the system is fully evaluable without manual setup beyond starting the three services.

---

## Appendix A: Technology Versions

| Technology | Version |
|---|---|
| Python | 3.11 |
| FastAPI | 0.111.0 |
| SQLAlchemy | 2.0.30 |
| PyMySQL | 1.1.0 |
| Pydantic | 2.7.1 |
| python-jose | 3.3.0 |
| passlib[bcrypt] | 1.7.4 |
| Pillow | 10.3.0 |
| LangChain | 0.1.20 |
| langchain-community | 0.0.38 |
| tavily-python | 0.3.3 |
| Node.js | 20 LTS |
| React | 18.3.1 |
| Vite | 5.2.12 |
| Tailwind CSS | 3.4.4 |
| Axios | 1.7.2 |
| React Router | 6.23.1 |
| MySQL | 8.0 |
| Ollama model | llama3.2 |

---

## Appendix B: API Endpoint Summary

| Method | Endpoint | Auth | Role |
|---|---|---|---|
| GET | `/health` | None | Any |
| POST | `/auth/user/register` | None | — |
| POST | `/auth/user/login` | None | — |
| POST | `/auth/owner/register` | None | — |
| POST | `/auth/owner/login` | None | — |
| GET | `/users/me` | JWT | Reviewer |
| PUT | `/users/me` | JWT | Reviewer |
| POST | `/users/me/photo` | JWT | Reviewer |
| GET | `/preferences/me` | JWT | Reviewer |
| PUT | `/preferences/me` | JWT | Reviewer |
| GET | `/restaurants` | Optional | Any |
| POST | `/restaurants` | JWT | Any |
| GET | `/restaurants/{id}` | Optional | Any |
| PUT | `/restaurants/{id}` | JWT | Creator / Claimer |
| DELETE | `/restaurants/{id}` | JWT | Creator / Claimer |
| POST | `/restaurants/{id}/claim` | JWT | Owner |
| POST | `/restaurants/{id}/photos` | JWT | Creator / Claimer |
| GET | `/restaurants/{id}/reviews` | Optional | Any |
| POST | `/restaurants/{id}/reviews` | JWT | Reviewer |
| PUT | `/reviews/{id}` | JWT | Review author |
| DELETE | `/reviews/{id}` | JWT | Review author |
| POST | `/favorites/{id}` | JWT | Reviewer |
| DELETE | `/favorites/{id}` | JWT | Reviewer |
| GET | `/favorites/me` | JWT | Reviewer |
| GET | `/history/me` | JWT | Reviewer |
| GET | `/owner/me` | JWT | Owner |
| GET | `/owner/dashboard` | JWT | Owner |
| GET | `/owner/restaurants` | JWT | Owner |
| GET | `/owner/restaurants/{id}/stats` | JWT | Owner (of that restaurant) |
| GET | `/owner/reviews` | JWT | Owner |
| POST | `/ai/chat` | JWT | Any |
