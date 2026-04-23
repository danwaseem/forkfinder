# ForkFinder — Demo Code Explanation

**Course:** DATA 236 Distributed Systems — Lab 1
**Group 7:** Danish Waseem (19101511), Saketh (019160999)

This document is a structured oral explanation guide for your live demo. Read section by section. Speak naturally — do not read bullet points verbatim.

---

## 1. High-Level Project Summary

**What is it?**
ForkFinder is a full-stack restaurant discovery and review platform, similar to Yelp. Users can search for restaurants, read and write reviews, save favorites, and get AI-powered dining recommendations through a conversational chatbot.

**What problem does it solve?**
Finding a good restaurant that matches your specific taste, budget, and mood requires scrolling through many apps and pages. ForkFinder brings that all together in one place, and adds an AI assistant that understands natural language — so instead of clicking through filters, you just say "I want something romantic and Italian for around $$."

**Why Yelp-inspired?**
Yelp is the gold standard for restaurant discovery. It has two clear user types (reviewers and business owners), a review system, search and filters, and a business analytics layer. We used it as our design reference because it covers all the core patterns of a review platform at scale.

**The two roles:**
- **Reviewer (User):** Can search restaurants, write reviews, save favorites, view their history, and use the AI assistant.
- **Restaurant Owner:** Can create and claim restaurant listings, manage them, view their analytics dashboard, and read reviews. Owners cannot write reviews — enforced at the API level, not just the UI.

---

## 2. Tech Stack Explanation

| Layer | Technology | Why we chose it |
|---|---|---|
| Frontend | React 18 + Vite | Fast development, component-based UI, Vite replaces CRA for speed |
| Styling | Tailwind CSS | Utility classes make responsive design fast without writing custom CSS |
| HTTP client | Axios | Cleaner than Fetch, easy to add interceptors for JWT |
| Routing | React Router v6 | Standard React routing; supports protected routes cleanly |
| Backend | FastAPI | Python-native, auto-generates Swagger docs, async-ready, great validation |
| ORM | SQLAlchemy 2.0 | Production-grade Python ORM; maps Python classes to SQL tables |
| Validation | Pydantic v2 | FastAPI uses Pydantic for request/response validation — tight integration |
| Database | MySQL 8.0 | Relational data with foreign keys; well-suited for a review platform |
| Auth | JWT (python-jose) + bcrypt (passlib) | Stateless tokens; bcrypt for secure password hashing |
| AI | LangChain + ChatOllama | LangChain orchestrates the pipeline; ChatOllama calls the local Ollama server |
| Local LLM | Ollama (llama3.2) | Runs locally, no API cost, good enough for structured restaurant recommendations |
| Web search | Tavily | Retrieves real-time restaurant info (hours, trending) when the query asks for live data |
| File uploads | Pillow | Validates images by reading the actual file header, not just the extension; strips EXIF |

---

## 3. Architecture Explanation

Here is how everything connects:

```
Browser (React)
      │
      │  HTTP/JSON  (Axios + JWT header)
      ▼
FastAPI Backend  (:8000)
      │
      ├── Routers   → parse requests, return responses
      ├── Services  → business logic, queries, AI pipeline
      ├── Models    → SQLAlchemy ORM classes (maps to MySQL tables)
      └── Schemas   → Pydantic classes (request/response shapes)
      │
      ├── MySQL 8.0  ← all data: users, restaurants, reviews, favorites
      │
      └── AI pipeline
            ├── Rule-based filter extraction  (no LLM cost)
            ├── SQLAlchemy DB search
            ├── Ranking function (0–100 score)
            ├── Tavily web search  (conditional)
            └── ChatOllama / Ollama  (local LLM)
```

**How JWT fits in:**
When a user logs in, the backend creates a signed JWT token containing the user's `id` and `role`. That token is stored in the browser's `localStorage`. Every API request includes it in the `Authorization: Bearer <token>` header via an Axios request interceptor (`api.js`). The backend's `get_current_user` dependency decodes and verifies this token on every protected request — no session store required.

**How Ollama and LangChain fit in:**
When you send a message to the AI assistant, FastAPI calls `ai_service.py`. This service uses LangChain's `ChatOllama` class to send a prompt to a locally running Ollama process (the llama3.2 model). The service constructs the prompt, invokes the LLM asynchronously, parses the structured JSON response, and returns recommendations. If Ollama is not running, the service falls back to a deterministic text template using the already-ranked results.

**How Tavily fits in:**
Tavily is a web search API. It fires only when the filter extractor detects "live data" keywords like "open now", "trending", "hours", or "just opened". The search returns a plain text summary from the top web results which is injected into the LLM prompt as additional context.

---

## 4. Folder / Code Structure Walkthrough

### Backend (`backend/`)

```
app/
├── main.py              ← FastAPI app, CORS config, mounts all routers, serves uploads/
├── config.py            ← Reads .env into a Settings object (DATABASE_URL, SECRET_KEY, etc.)
├── database.py          ← SQLAlchemy engine, SessionLocal, Base — get_db() dependency here
│
├── models/              ← ORM classes (map to MySQL tables)
│   ├── user.py          ← User + UserPreferences
│   ├── restaurant.py    ← Restaurant + RestaurantClaim
│   ├── review.py        ← Review
│   ├── favorite.py      ← Favorite
│   └── conversation.py  ← Conversation + ConversationMessage (AI chat history)
│
├── schemas/             ← Pydantic request/response shapes
│   ├── auth.py          ← Signup/login request + TokenResponse
│   ├── restaurant.py    ← RestaurantCreate, RestaurantResponse, etc.
│   └── review.py        ← ReviewCreate, ReviewWithStatsResponse, etc.
│
├── routers/             ← HTTP endpoints (thin layer, no logic)
│   ├── auth.py          ← /auth/user/signup, /auth/user/login, etc.
│   ├── restaurants.py   ← /restaurants (search, CRUD, claim, photos)
│   ├── reviews.py       ← /restaurants/{id}/reviews, /reviews/{id}
│   ├── favorites.py     ← /favorites/{id}, /favorites/me
│   ├── users.py         ← /users/me (profile)
│   ├── preferences.py   ← /preferences/me
│   ├── history.py       ← /history/me
│   ├── owner.py         ← /owner/dashboard, /owner/restaurants, etc.
│   └── ai_assistant.py  ← /ai-assistant/chat
│
└── services/            ← All business logic lives here
    ├── review_service.py    ← review CRUD + recalc_rating() called on every write
    ├── ai_service.py        ← full AI pipeline (5 stages)
    ├── owner_service.py     ← dashboard aggregations, sentiment analysis
    └── preferences_service.py
```

**Key principle:** Routers handle HTTP. Services handle logic. Models define data. Schemas define shapes.

### Frontend (`frontend/src/`)

```
App.jsx              ← All route definitions; PrivateRoute wraps protected pages
context/
  AuthContext.jsx    ← Global auth state; stores JWT + user in localStorage
hooks/
  useChat.js         ← AI chat state machine (messages, loading, send, reset)
  useRestaurants.js  ← Paginated restaurant list with combined filter state
  useDebounce.js     ← Debounces search input (300ms delay)
services/
  api.js             ← Axios instance + JWT interceptor + 401/403 global handler
  auth.js            ← login, signup wrappers
  restaurants.js     ← list, get, create, update, delete, claim
  reviews.js         ← create, update, delete
  favorites.js       ← add, remove, list (/favorites/me)
  ai.js              ← chat, getConversation
pages/
  Home.jsx           ← Logged-in dashboard (AI chat + quick stats) or guest hero page
  Explore.jsx        ← Search + filter + sort + restaurant grid
  RestaurantDetails.jsx ← Detail view, reviews, write/edit/delete flow
  Profile.jsx        ← Profile editor + dining preferences (combined)
  Preferences.jsx    ← Standalone dining preferences page
  AddRestaurant.jsx  ← Create/edit restaurant form with photo picker
  Favorites.jsx      ← Saved restaurants
  History.jsx        ← Reviews written + restaurants added
  owner/             ← OwnerDashboard, OwnerRestaurants, OwnerRestaurantDetail, OwnerReviews
components/
  common/            ← Navbar, Footer, StarRating, AIAssistant (floating), ChatMessageBubble
  ai/                ← ChatWindow, ChatRecommendationCard
  restaurants/       ← RestaurantCard, ReviewCard, ReviewForm
```

---

## 5. Feature-by-Feature Explanation

### 5.1 Signup and Login

**Files:** `Register.jsx`, `Login.jsx`, `auth.js` (service), `routers/auth.py`, `schemas/auth.py`, `models/user.py`

**Flow:**
1. User fills in name, email, password on the Register page.
2. React calls `POST /auth/user/signup` via `authApi.register()`.
3. FastAPI's `auth.py` validates the request with Pydantic (`UserSignupRequest`) — password must be 8–128 chars.
4. Backend hashes the password with bcrypt (cost factor 12) and creates a `User` row. It also creates an empty `UserPreferences` row for this user immediately.
5. A JWT is signed with the user's `id` and `role`, and returned as a `TokenResponse` (contains `access_token`, `user_id`, `name`, `email`, `role`).
6. `AuthContext._persist()` stores the token and user object in `localStorage`. The user object gets `id: data.user_id` added so that the rest of the frontend can use `user.id` consistently.

**Owners** hit `POST /auth/owner/signup` — same flow but `role` is set to `"owner"`. The role is enforced server-side.

**Login** calls `POST /auth/user/login` or `POST /auth/owner/login`. On 401, the Axios interceptor in `api.js` shows a toast. On the login/signup endpoints themselves, 401 is silenced (wrong password is expected) via the `SILENT_AUTH_PATHS` list.

**Database:** `users` table — one row per account. Password stored as bcrypt hash only, never plaintext.

---

### 5.2 JWT Auth and Protected Routes

**Files:** `api.js`, `AuthContext.jsx`, `App.jsx`, `utils/auth.py` (backend)

**Frontend side:**
- `api.js` has a request interceptor that reads the token from `localStorage` and injects `Authorization: Bearer <token>` into every outgoing request.
- `api.js` has a response interceptor: if any non-auth endpoint returns 401, it calls `tokenStore.clear()` and shows a "session expired" toast. 403 responses show a "no permission" toast.
- `App.jsx` wraps protected pages with `<PrivateRoute>` which checks `AuthContext` — if not logged in, redirects to `/login`.

**Backend side:**
- Every protected endpoint lists `current_user: User = Depends(get_current_user)` in its parameters.
- `get_current_user()` in `utils/auth.py` decodes the JWT, verifies the signature, and fetches the user from the DB. If the token is missing, malformed, or expired, it raises 401.
- `require_owner` wraps `get_current_user` and additionally checks `user.role == "owner"`, raising 403 otherwise.
- This is the **actual security boundary** — the UI only hides buttons, but the API will reject anything that doesn't have the right token and role.

---

### 5.3 Profile Management

**Files:** `Profile.jsx`, `users.py` (router), `models/user.py`

**What it covers:** Name, email, phone, about me, city, state (abbreviated dropdown), country (dropdown list), languages, gender. Plus profile photo upload.

**Flow:** `GET /users/me` loads current values. `PUT /users/me` saves changes. `POST /users/me/photo` handles the profile photo — Pillow validates the actual file header (not just extension), strips EXIF metadata, downsizes images over 1920px, and saves to `uploads/profiles/`. The photo URL is stored on the User row and served as a static file by FastAPI.

**Note for demo:** Profile and dining preferences are on the same page (`Profile.jsx`) — the preferences panel is at the bottom of the profile page. There's also a standalone `/preferences` page.

---

### 5.4 Dining Preferences

**Files:** `Preferences.jsx`, `Profile.jsx` (also has prefs section), `preferences.py` (router), `preferences_service.py`, `models/user.py` (UserPreferences)

**What is stored:** Cuisine preferences (multi-select chips), price range, search radius (km), dietary restrictions (multi-select), ambiance preferences (multi-select), sort preference (radio).

**How it's used:** The AI assistant loads these from the DB on every chat request and injects them into the search query and LLM prompt. This is how the assistant personalizes responses — it knows you prefer Italian and $$, for example.

**Limitation — be honest here:** The `search_radius` preference is stored and passed to the AI as context text, but the restaurant list endpoint filters by city string only. There is no actual distance calculation. This would require PostGIS or a geocoding API.

---

### 5.5 Restaurant Search, Filtering, and Pagination

**Files:** `Explore.jsx`, `useRestaurants.js`, `restaurants.js` (service), `routers/restaurants.py`

**Frontend flow:**
1. `Explore.jsx` renders a search bar + filter panel + sort selector.
2. `useDebounce.js` delays the search by 300ms after keystrokes to avoid a new API call on every character.
3. `useRestaurants.js` manages all filter state and calls `restaurantsApi.list({ q, cuisine, city, price_range, rating_min, sort, page, limit })`.
4. Results come back paginated (12 per page), rendered as `RestaurantCard` components.

**Backend flow:**
1. `GET /restaurants` in `restaurants.py` builds a SQLAlchemy query.
2. `?q` does a case-insensitive LIKE across `name`, `cuisine_type`, `description`, `city`, and `zip_code` — so keyword searches like "outdoor seating" work if that phrase appears in a restaurant's description.
3. Additional filters: `cuisine`, `city`, `zip_code`, `price_range`, `rating_min`.
4. Sort options: `rating` (default), `newest`, `most_reviewed`, `price_asc`, `price_desc`.
5. Returns `{ items, total, page, limit, pages }`.

**Rating aggregates:** `avg_rating` and `review_count` are stored directly on the Restaurant row (denormalized). This avoids a slow `COUNT`/`AVG` join on every list query. They are updated on every review write by `review_service.recalc_rating()`.

---

### 5.6 Restaurant Details

**Files:** `RestaurantDetails.jsx`, `routers/restaurants.py` (`get_restaurant`), `routers/reviews.py`

**What's shown:** Photo gallery, today's operating hours highlighted, cuisine type, price range, address, phone, website, average rating, star distribution, review count, and the list of reviews.

**How reviews load:** Two parallel calls fire on mount — `GET /restaurants/{id}` for the restaurant data and `GET /restaurants/{id}/reviews` for the paginated review list. The `review_count` displayed is overridden with the live count from the reviews query so it's always accurate.

**Rating accuracy:** `GET /restaurants/{id}` computes live `COUNT`/`AVG` from the reviews table and returns those values in the response — it does not write them back to the database (fixed in this session). The list endpoint uses stored values, so running `python seed_data.py --recalc` syncs them if they ever drift.

---

### 5.7 Reviews (Create / Edit / Delete)

**Files:** `RestaurantDetails.jsx`, `ReviewCard.jsx`, `ReviewForm.jsx`, `routers/reviews.py`, `services/review_service.py`

**Create:**
1. Logged-in reviewer sees the "Write a Review" form inline on the detail page.
2. Submits `POST /restaurants/{id}/reviews` with `{ rating, comment }` and optionally a photo.
3. Backend validates: rating 1–5, comment 10–5000 chars, one review per user per restaurant.
4. After saving, `review_service.recalc_rating()` recomputes and stores the new `avg_rating` and `review_count` on the Restaurant row, then returns those stats in the response.
5. The frontend receives the updated stats and immediately updates the displayed rating and count without a page reload.

**Edit / Delete:**
- Only the review's author sees Edit/Delete buttons — `ReviewCard.jsx` checks `user.id === review.user_id`.
- Edit hits `PUT /reviews/{id}`, delete hits `DELETE /reviews/{id}`.
- Both return `{ review, restaurant_stats }` so the frontend can update the rating display without a reload.
- Backend enforces ownership: an attempt to edit someone else's review returns 403.

**Owner restriction:** Restaurant owners cannot create, edit, or delete reviews — `POST /restaurants/{id}/reviews` checks `require_user` (reviewer role only).

---

### 5.8 Favorites

**Files:** `Favorites.jsx`, `FavoriteButton.jsx`, `favorites.js` (service), `routers/favorites.py`

**Flow:**
- The heart icon appears on every `RestaurantCard` and on the restaurant detail page.
- `POST /favorites/{id}` adds to favorites; `DELETE /favorites/{id}` removes.
- `GET /favorites/me` fetches the full list of favorited restaurants for the current user, ordered by most recently added.
- The Favorites page renders these as a grid of `RestaurantCard` components.
- `is_favorited` flag is returned on every restaurant in the list/detail responses when the user is authenticated, so the heart icon renders pre-filled.

---

### 5.9 User History

**Files:** `History.jsx`, `routers/history.py`, `services/history_service.py`

**What it shows:** A timeline of all reviews the user has written (with the restaurant name, rating, and comment), and all restaurants the user has added to the platform.

**Backend:** `GET /history/me` queries reviews and restaurants created by the current user, combines them into a sorted list, and returns a `HistoryResponse`.

---

### 5.10 Add Restaurant

**Files:** `AddRestaurant.jsx`, `routers/restaurants.py` (`create_restaurant`), `models/restaurant.py`

**What you can enter:** Name, cuisine type, address, city, state, country, zip, phone, website, description, price range, hours per day, and up to 10 photos.

**Hours:** Stored as a JSON text column on the Restaurant row — one key per day ("monday" through "sunday") with open/close times. The detail page highlights today's hours.

**Photos:** Uploaded one at a time via `POST /restaurants/{id}/photos`. Pillow validates the file header, strips EXIF, resizes if over 1920px, and saves to `uploads/restaurants/`. URLs are appended to the photos JSON array on the row.

**Who can add restaurants:** Any authenticated reviewer or owner. Owners can also edit/delete restaurants they created or claimed.

---

### 5.11 Owner Dashboard and Analytics

**Files:** `OwnerDashboard.jsx`, `OwnerRestaurants.jsx`, `OwnerRestaurantDetail.jsx`, `OwnerReviews.jsx`, `routers/owner.py`, `services/owner_service.py`

**What it shows:**
- Aggregate stats: total restaurants, total reviews, average rating across all owned restaurants, total favorites received.
- Per-restaurant stats: rating distribution (1–5 star breakdown), 6-month review trend (bar chart by month), and a sentiment keyword summary extracted from review text.
- All reviews across owned restaurants (read-only — owners cannot delete reviews, only view them).
- Listing management: edit restaurant info, photos, hours.

**Access control:** All `/owner/*` routes require `require_owner` dependency. A reviewer calling any owner route gets 403. This is verified in `test_owner.py`.

---

### 5.12 Claim Restaurant

**Files:** `RestaurantDetails.jsx` (`claimRestaurant`), `routers/restaurants.py` (`claim_restaurant`)

**Flow:**
1. Any unclaimed restaurant shows a "Claim this restaurant" button — visible only to logged-in owners.
2. Owner clicks the button → `POST /restaurants/{id}/claim`.
3. Backend checks: caller must be an owner role; restaurant must not already be claimed; this owner must not already have a pending claim.
4. If valid: `restaurant.is_claimed = True`, `restaurant.claimed_by = owner.id`, a `RestaurantClaim` row is inserted, and the response confirms success.
5. Auto-approved — no admin review step.

**Note:** There are two functional endpoints for claiming — `POST /restaurants/{id}/claim` (used by the UI) and `POST /owner/restaurants/{id}/claim` (in the owner router). Both work. The UI uses the first one. This is a known minor redundancy.

---

## 6. AI Assistant Deep Explanation

This is the most complex and impressive part of the project. Explain it clearly.

### The Core Idea

Instead of making one big LLM call and hoping for the best, the AI assistant runs a **5-stage pipeline**. The LLM only handles the final natural-language response. Everything before it — filter extraction, database search, ranking, web lookup — is deterministic code. This makes the system more reliable, testable, and predictable.

### Stage-by-Stage Breakdown

**Stage 1 — Filter Extraction (no LLM cost)**

File: `ai_service.py`, function `extract_filters()`

This is pure Python keyword matching — no LLM tokens used. It scans the user's message (and the last few messages in the conversation for context) against five keyword dictionaries:
- `_CUISINE_MAP`: e.g., "pasta" → "Italian", "ramen" → "Japanese", "bbq" → "American"
- `_PRICE_MAP`: e.g., "cheap" → "$", "splurge" → "$$$$", "fine dining" → "$$$$"
- `_DIETARY_MAP`: "vegan", "gluten-free", "halal", "keto", etc.
- `_OCCASION_MAP`: "romantic" → "date night", "anniversary", "birthday", "group dining"
- `_AMBIANCE_MAP`: "outdoor" → "outdoor seating", "rooftop", "cozy" → "intimate"

It also runs a regex to extract location from phrases like "near Mission District" or "in Oakland."

Finally, it checks for **web search trigger words** (`_WEB_TRIGGERS`): "open now", "hours", "trending", "just opened", "live music." If found, it sets `needs_web_search = True`.

For multi-turn conversations, the extractor processes the last 4 user messages together, so a follow-up like "what about outdoor seating?" inherits the cuisine and location from earlier in the conversation.

**Stage 2 — Database Search**

File: `ai_service.py`, uses SQLAlchemy

Builds a query against the `restaurants` table using the extracted filters merged with the user's saved preferences. The user's preferences are loaded from the `user_preferences` table at the start of the call.

If the combined filters return zero results, the query is broadened automatically — cuisine and price constraints are dropped and only the location filter is kept. This prevents the frustrating "no results found" experience for reasonable queries.

**Stage 3 — Ranking (0–100 score)**

File: `ai_service.py`, function scores each restaurant candidate

| Component | Max Points | Logic |
|---|---|---|
| Star rating | 40 | `(avg_rating / 5.0) × 40` |
| Popularity | 20 | 1 pt per 5 reviews, capped at 20 |
| Cuisine match | 20 | 20 if query cuisine matches; 10 if it matches saved preference |
| Price match | 10 | Exact match on price range |
| Location match | 10 | City contains extracted or preferred location string |

A 4.8-star restaurant with 50 reviews at the right price tier will outscore a 5.0-star restaurant with 1 review. The top 5 results are passed to the LLM with their scores and match reasons.

**Stage 4 — Tavily Web Search (conditional)**

Only fires when `needs_web_search = True`. Calls the Tavily API and retrieves a plain-text summary (up to 1200 characters) from the top 3 web results. This gives the LLM access to real-time info like "currently open", "just opened last month", or "trending this week" that the database cannot provide.

If `TAVILY_API_KEY` is absent from the environment, this stage is silently skipped.

**Stage 5 — LLM Response**

File: `ai_service.py`, uses `langchain_community.chat_models.ChatOllama`

The service calls a locally running Ollama server (default model: llama3.2) via LangChain's `ChatOllama` abstraction. Three prompt modes:

- **Normal mode:** System prompt includes the top-ranked restaurants, web search summary (if any), and user preferences. LLM writes a conversational response.
- **Clarification mode:** Triggered when the extractor finds no meaningful signal. LLM asks what kind of food/occasion the user has in mind.
- **Fallback mode:** DB search returned weak results. LLM explains what was searched and suggests how to broaden the query.

The LLM is instructed to return structured JSON: `{ assistant_message, reasoning, follow_up_question }`. The service parses this with `json.loads()`. If the model returns prose instead of JSON, the raw text is used verbatim.

**If Ollama is unavailable:** The `_no_llm_response()` function formats the ranked results into clean markdown text. The assistant always returns a response — it never crashes or shows a blank.

**Conversation persistence:** Every user message and assistant response is stored in `conversations` and `conversation_messages` tables. Clients pass a `conversation_id` on follow-up turns to reload context from the DB.

> **Technical note for Q&A:** The module-level docstring in `ai_service.py` says "ChatOpenAI" — this is stale documentation from an earlier version. The actual implementation at line 589 uses `ChatOllama`. The running system uses Ollama.

### Where to find it in the code

- Service: `backend/app/services/ai_service.py`
- Router: `backend/app/routers/ai_assistant.py` → `POST /ai-assistant/chat`
- Schema: `backend/app/schemas/ai_assistant.py` → `ChatResponse`, `ExtractedFilters`, `RestaurantRecommendation`
- Frontend: `frontend/src/components/ai/ChatWindow.jsx`, `ChatRecommendationCard.jsx`
- Hook: `frontend/src/hooks/useChat.js`
- Home integration: `frontend/src/pages/Home.jsx` → `HomeAIChat` component

---

## 7. Database Explanation

**Tables and what they store:**

| Table | Key Columns | Notes |
|---|---|---|
| `users` | `id`, `email`, `password_hash`, `role`, `name`, `phone`, `city`, `country`, profile fields | `role` is either `"user"` or `"owner"` |
| `user_preferences` | `user_id` (FK), `cuisine_preferences` (JSON), `price_range`, `dietary_restrictions` (JSON), `ambiance_preferences` (JSON), `search_radius`, `sort_preference` | One row per user; created with empty defaults at signup |
| `restaurants` | `id`, `name`, `cuisine_type`, `price_range`, `avg_rating`, `review_count`, `address`, `city`, `hours` (JSON), `photos` (JSON), `is_claimed`, `claimed_by`, `created_by` | `avg_rating` and `review_count` are denormalized for fast list queries |
| `restaurant_claims` | `restaurant_id`, `owner_id`, `status` | Enforces one owner per restaurant |
| `reviews` | `id`, `user_id`, `restaurant_id`, `rating`, `comment`, `photos` (JSON), `created_at` | Photo paths stored as JSON array |
| `favorites` | `user_id`, `restaurant_id`, `created_at` | Composite unique constraint prevents duplicate favorites |
| `conversations` | `id`, `user_id`, `created_at` | One conversation thread per session |
| `conversation_messages` | `id`, `conversation_id`, `role`, `content`, `extra_json` | `role` is `"user"` or `"assistant"`; `extra_json` stores extracted filters + reasoning |

**How they relate:**
- A `User` can have many `Reviews`, many `Favorites`, and many `Conversations`.
- A `Restaurant` can have many `Reviews`, many `Favorites`, and at most one `RestaurantClaim`.
- `avg_rating` and `review_count` on `Restaurant` are recalculated and written back by `review_service.recalc_rating()` on every review create, update, or delete.
- Tables are created automatically on first backend start via `Base.metadata.create_all()` — no migration scripts needed.

---

## 8. API Explanation

### Most Important Endpoints to Mention

**Auth:**
- `POST /auth/user/signup` — register reviewer
- `POST /auth/user/login` → returns JWT
- `POST /auth/owner/signup` / `/auth/owner/login` — same for owners

**Restaurants:**
- `GET /restaurants?q=pizza&city=San+Jose&price_range=$$&sort=rating` — search + filter
- `GET /restaurants/{id}` — full detail with live aggregate
- `POST /restaurants` — create listing (auth required)
- `POST /restaurants/{id}/claim` — claim for owner

**Reviews:**
- `GET /restaurants/{id}/reviews` — list with pagination
- `POST /restaurants/{id}/reviews` — create (reviewer only)
- `PUT /reviews/{id}` — edit own review
- `DELETE /reviews/{id}` — delete own review

**User:**
- `GET /users/me` / `PUT /users/me` — profile
- `GET /preferences/me` / `PUT /preferences/me` — dining prefs

**Owner:**
- `GET /owner/dashboard` — aggregate stats
- `GET /owner/restaurants/{id}/stats` — per-restaurant analytics

**AI:**
- `POST /ai-assistant/chat` — body: `{ message, conversation_id, conversation_history }`

### Swagger UI

All endpoints are auto-documented by FastAPI at `http://localhost:8000/docs`. To test protected routes: call the login endpoint, copy `access_token`, click **Authorize**, enter `Bearer <token>`.

A Postman collection with 43 pre-built requests is at `backend/docs/postman_collection.json`.

---

## 9. Demo Walkthrough Script

Run the seed script before the demo: `python seed_data.py --wipe`

**Best demo order:**

### Step 1 — Guest home page (30 seconds)
> "This is ForkFinder's home page. If you're not logged in, you see the hero search bar, top-rated restaurants, and a teaser for the AI assistant. The whole page is responsive — I can show it works on mobile too."

Click the cuisine chips to show filtering by cuisine.

### Step 2 — Explore / Search page (1 minute)
> "On the Explore page, users can search by name, keyword, cuisine, city, price range, and minimum rating. I'll search for Italian restaurants in San Jose rated at least 4 stars."

Type "Italian" in search, set city to "San Jose", set rating min to 4, change sort to "Highest Rated."

> "Results update live as I apply filters. Each card shows the restaurant name, cuisine, price tier, rating, and a heart toggle for favorites. These are served by `GET /restaurants` with query parameters."

### Step 3 — Restaurant details (1 minute)
> "Clicking a restaurant opens the detail page. You can see today's hours highlighted, the photo gallery, contact info, average rating, and all reviews below."

Scroll to reviews. Point out the star distribution.

> "The rating breakdown and review list come from two separate API calls that run in parallel on page load."

### Step 4 — Login as reviewer (30 seconds)
Log in as `user@demo.com` / `password`.

> "After login, a JWT is returned by the backend and stored in localStorage. Every request from this point includes it as a Bearer token."

### Step 5 — AI assistant on dashboard (2 minutes)
> "The home dashboard for logged-in users is split into two panels. The left side is the AI dining guide — this is Forky. Watch what happens when I type a natural language query."

Type: "I want something romantic and Italian for dinner tonight under $$"

> "The AI extracted: cuisine = Italian, ambiance = intimate/date night, price = $$. It searched the database, scored results using a ranking function that weights ratings, popularity, cuisine match, and price match, then asked Ollama to write this response. The cards link directly to each restaurant's detail page."

Click a recommendation card to show it links to the detail page. Come back.

Try a follow-up: "What about outdoor seating?"

> "The system remembers context from earlier in the conversation — the cuisine and location carry forward. This is the multi-turn feature."

Try a web search trigger: "Which ones are open right now?"

> "This message contains 'open right now' which is a web search trigger keyword. The service fires Tavily to get real-time information, which is injected into the LLM prompt as extra context."

### Step 6 — Write a review (1 minute)
Navigate to a restaurant. Scroll to "Write a Review."

> "Any logged-in reviewer can add a review. I pick a star rating with the star selector, type a comment, and optionally attach a photo."

Submit the review.

> "After submission, the average rating and review count update immediately without a page reload. The backend ran `recalc_rating()` which recomputed the aggregate from the reviews table and returned the new stats in the same response."

Show the edit/delete buttons on your own review. Edit it, save, show it updates.

### Step 7 — Favorites and History (30 seconds)
Click the heart on a restaurant card.

> "Favoriting sends `POST /favorites/{id}`. The Favorites tab shows all saved restaurants ordered by when you added them."

Click Favorites in nav. Then click History.

> "History shows every review I've written and every restaurant I've added to the platform."

### Step 8 — Profile and preferences (30 seconds)
Click Profile.

> "The profile page lets me update my personal info — name, email, phone, city, country from a dropdown, state as an abbreviated selector. At the bottom of the same page is my dining preferences panel — cuisine chips, price range, dietary restrictions, ambiance, sort preference."

> "These preferences are loaded by the AI assistant on every query to personalize recommendations."

### Step 9 — Owner flow (1.5 minutes)
Log out. Log in as `owner@demo.com` / `password`.

> "This is Mario Rossi, a restaurant owner. The navbar shows Owner Dashboard instead of reviewer links. Owners cannot write reviews — if I try calling the review endpoint with an owner token in Swagger, I get 403 Forbidden."

Go to Owner Dashboard.

> "The dashboard shows aggregate stats across all Mario's restaurants — total reviews, average rating, total favorites received. Each restaurant has a 6-month trend chart and a rating distribution breakdown."

Go to Owner Restaurants, click one.

> "Owners can edit listing info, update photos, and change hours here."

Show the Claim Restaurant flow on an unclaimed restaurant in the detail page.

> "On any unclaimed restaurant, an owner sees a 'Claim this restaurant' button. One click calls `POST /restaurants/{id}/claim` — it's auto-approved and the restaurant is immediately assigned to this owner."

### Step 10 — Swagger UI (1 minute)
Open `http://localhost:8000/docs`.

> "FastAPI auto-generates interactive API documentation. I can test every endpoint here. Let me show the role enforcement — I'll authenticate as a reviewer and try to call `GET /owner/dashboard`."

Call the reviewer login, authorize, then call `GET /owner/dashboard`.

> "403 Forbidden — the API layer rejected it. The role check is enforced in the FastAPI dependency, not just in the UI."

---

## 10. Professor Q&A Preparation

**Q: Why did you choose FastAPI over Django or Flask?**
> FastAPI is modern, async-first, and auto-generates Swagger documentation from the code. It integrates tightly with Pydantic for validation. It is also the closest Python framework to what's used in production API services today. Flask would have required more manual wiring; Django is heavier than we needed.

**Q: Why JWT instead of session-based auth?**
> JWT is stateless — the server doesn't need to store sessions. Each token is self-contained with the user's ID and role. This is better for our architecture because the frontend and backend are separate processes. The downside is that tokens cannot be individually revoked before expiry, which we documented as a known limitation.

**Q: Why MySQL?**
> The assignment specified MySQL. It's a well-established relational database that handles the foreign key relationships between users, restaurants, reviews, and favorites cleanly. Our data is structured and relational, so a relational database is the correct choice over something like MongoDB.

**Q: How does the AI assistant actually work? Does it hallucinate restaurant names?**
> No — it cannot hallucinate restaurants because the LLM never generates restaurant names. The database search and ranking happen entirely in Python before the LLM is called. The LLM only writes the conversational text wrapping results that already came from our database. The LLM receives: "here are the 5 restaurants, write a friendly response explaining why these match." It has no ability to invent restaurants.

**Q: How does Tavily work?**
> Tavily is a web search API optimized for AI applications. When the user's message contains certain keywords — "open now", "hours", "trending", "just opened" — our rule-based extractor sets a flag. The service then calls Tavily's API, gets a plain-text summary from the top 3 web results, and injects that into the LLM prompt as additional context. If there's no `TAVILY_API_KEY` configured, this stage is silently skipped.

**Q: How is role-based access control enforced?**
> Through FastAPI dependency injection. Every endpoint that requires a logged-in user has `current_user = Depends(get_current_user)`. Endpoints that require an owner specifically have `current_user = Depends(require_owner)`, which calls `get_current_user` first and then checks `user.role == "owner"`. If the check fails, it raises 403 before the handler function even runs. The frontend hides buttons too, but that is UX only — the actual enforcement is at the API layer.

**Q: How are restaurant ratings calculated?**
> We use denormalized aggregates. The `avg_rating` and `review_count` are stored directly on the restaurant row in the database. Every time a review is created, updated, or deleted, `review_service.recalc_rating()` recomputes the aggregate from the actual reviews table and writes it back. This way the list endpoint can return ratings without running an expensive `AVG`/`COUNT` join on every request.

**Q: What was the most challenging part?**
> The AI pipeline design. The initial instinct was to send the user's message to the LLM and ask it to figure out the filters, search the database, and write the response all at once. This was unreliable — LLMs hallucinate filter values and sometimes refuse queries. The solution was to separate concerns completely: rule-based extraction handles filters (deterministic, no LLM cost), SQLAlchemy handles the database search, a scoring function handles ranking, and the LLM only handles the final natural-language response. Once we separated the pipeline this way, it became much more predictable and testable.

**Q: What would you improve with more time?**
> Three things: (1) Replace the city-string location filter with real distance-based search using PostGIS — the search radius preference is stored but not actually used for filtering right now. (2) Move file storage to S3 instead of the local filesystem. (3) Add Alembic for proper database migrations instead of `create_all()`.

---

## 11. Known Limitations — How to State Them Confidently

Acknowledge these honestly — never try to hide them. Being upfront shows engineering maturity.

| Limitation | How to say it |
|---|---|
| **Search radius is stored but not used for distance filtering** | "The search radius preference is saved and passed to the AI as context. Actual distance-based filtering would require PostGIS or a geocoding API — we documented this as a future improvement." |
| **Owner signup doesn't collect restaurant location** | "The owner signs up with name, email, and password. Their restaurant location is associated when they create or claim a restaurant listing. The PDF mentioned restaurant location at signup — we handle it through the restaurant creation flow instead." |
| **No amenities field on restaurants** | "We implemented all the core restaurant fields. Amenities as a structured field was not included — attributes like 'outdoor seating' and 'wifi' are discoverable through the free-text description search." |
| **Local file storage only** | "Photos are stored on the local filesystem and served as static files by FastAPI. In production this would be S3. For the purposes of this lab, local storage demonstrates the full upload and serving pipeline." |
| **Ollama must be running separately** | "The AI assistant depends on Ollama being active. If it's not running, the assistant degrades gracefully — it still searches the database, ranks results, and returns formatted recommendations, just without the LLM-written prose." |
| **No email verification** | "Users can register with any valid email format. Email verification was out of scope for this assignment." |
| **Module docstring in ai_service.py mentions ChatOpenAI** | "The module-level docstring is stale from an earlier version. The actual implementation at line 589 uses `ChatOllama` — you can see it if the professor looks at the code." |

---

## 12. Short Versions

### 2-Minute Explanation

"ForkFinder is a Yelp-style restaurant discovery platform built with React on the frontend and FastAPI with MySQL on the backend. It supports two user roles: reviewers who search restaurants, write reviews, and save favorites, and restaurant owners who manage listings and view analytics. Authentication uses JWT — stateless tokens that carry the user's role, enforced at the API level so an owner can't write a review even if they call the endpoint directly. The standout feature is the AI assistant, 'Forky,' which runs a 5-stage pipeline: rule-based filter extraction with zero LLM cost, a database search, a scoring function that ranks on rating and preference match, optional Tavily web search for live data, and finally LangChain calling a local Ollama model to generate the conversational response. The system degrades gracefully — if Ollama is down, it still returns ranked results without the LLM text."

### 5-Minute Explanation

Cover: overview → tech stack → two roles → JWT enforcement → restaurant search with denormalized ratings → review flow with recalc_rating → AI pipeline in 5 stages (emphasize: filter extraction is pure Python, LLM only writes the final text, not the results) → owner dashboard → demo pivot to Swagger showing 403 enforcement.

Key phrase to use: *"The LLM cannot hallucinate restaurant names because it never generates them — it only wraps results that already came from our database."*

### Full Detailed Explanation

Follow sections 1 through 11 of this document in order. Budget 15–20 minutes for a full walkthrough including live demo.

---

*Generated from final codebase — accurate as of March 24, 2026.*
