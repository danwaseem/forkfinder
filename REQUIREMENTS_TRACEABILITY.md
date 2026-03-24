# ForkFinder — Requirements Traceability Matrix

Every graded feature mapped to the exact files that implement it, the database tables it touches,
its current status, and any notes a grader needs to know.

All findings are based on reading the actual source code. File paths are relative to `lab1/`.

**Status key:**
- ✅ **Complete** — Fully implemented, no known issues
- ⚠️ **Partial** — Implemented but has a confirmed gap or bug
- 🔴 **Broken** — Will fail during a demo; fix required
- ❌ **Missing** — Not found in the codebase

---

## Section 1 — Authentication & Authorization

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| A1 | Reviewer registration with name, email, password | `routers/auth.py` → `POST /auth/user/signup` | `pages/Register.jsx`, `services/auth.js` | `users` | ✅ | Role fixed to `"user"` at signup; cannot be overridden |
| A2 | Owner registration with name, email, password | `routers/auth.py` → `POST /auth/owner/signup` | `pages/Register.jsx`, `services/auth.js` | `users` | ✅ | Role fixed to `"owner"`; separate role-card in UI |
| A3 | Reviewer login → JWT returned | `routers/auth.py` → `POST /auth/user/login` | `pages/Login.jsx`, `services/auth.js`, `context/AuthContext.jsx` | `users` | ✅ | Returns `TokenResponse` with `access_token`, `user_id`, `name`, `role` |
| A4 | Owner login → JWT returned | `routers/auth.py` → `POST /auth/owner/login` | `pages/Login.jsx`, `services/auth.js` | `users` | ✅ | 403 if account role is `"user"` |
| A5 | Cross-role login rejected (owner token on reviewer endpoint) | `routers/auth.py` (403 on wrong role) | — | `users` | ✅ | `POST /auth/user/login` with an owner email → 403; verified in test_auth.py |
| A6 | JWT stored client-side and sent on every request | `utils/auth.py` (`decode_access_token`) | `context/AuthContext.jsx`, `services/api.js` (request interceptor) | — | ✅ | Token in `localStorage["token"]`; `Authorization: Bearer` header set on Axios defaults |
| A7 | Token expiry handled gracefully | `utils/auth.py` (exp claim checked) | `services/api.js` (response interceptor) | — | ⚠️ | Backend rejects expired tokens with 401. Frontend has a 401 interceptor that clears localStorage and redirects to `/login`. Verify interceptor skips auth endpoints (SILENT_AUTH_PATHS list present). |
| A8 | Password hashed with bcrypt | `utils/auth.py` (`hash_password`, `verify_password`) | — | `users.password_hash` | ✅ | passlib bcrypt cost=12; plaintext never stored |
| A9 | Password minimum 8 characters | `schemas/auth.py` `UserSignupRequest` (min_length=8) | `pages/Register.jsx` (inline strength hints) | — | ⚠️ | Backend enforces 8-128 chars. Frontend shows uppercase/number/lowercase hints that backend does NOT enforce — creates UX inconsistency. A password of `"aaaaaaaa"` passes backend but shows red hints in UI. |
| A10 | Duplicate email rejected on signup | `routers/auth.py` (409 Conflict) | `pages/Register.jsx` (shows `err.response.data.detail`) | `users.email` (UNIQUE) | ✅ | — |
| A11 | `require_user` dependency blocks owners | `utils/auth.py` or inline in `routers/reviews.py` (`_require_reviewer`) | — | — | ✅ | Owner calling `POST /reviews` → 403; verified in test_reviews.py |
| A12 | `require_owner` dependency blocks reviewers | `routers/owner.py` (`_require_owner`) | — | — | ✅ | Reviewer calling any `/owner/*` → 403; verified in test_owner.py |
| A13 | Unauthenticated requests to protected routes → 401 | `utils/auth.py` (`get_current_user` raises 401) | `App.jsx` (`RequireAuth` wrapper) | — | ✅ | Backend: 401 on missing/invalid token. Frontend: redirect to `/login`. |
| A14 | Logout clears session | — | `context/AuthContext.jsx` (`logout()`) | — | ✅ | Removes `localStorage["token"]` and `localStorage["user"]`; clears Axios default header |

---

## Section 2 — User Profile

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| P1 | Get own profile | `routers/users.py` → `GET /users/me` OR `routers/auth.py` → `GET /auth/me` | `pages/Profile.jsx` (calls `GET /users/me`) | `users` | ⚠️ | Backend has `GET /auth/me` (confirmed in auth.py). Frontend calls `GET /users/me`. Confirm `users.py` also defines `GET /users/me` — if it does not, Profile page never loads existing data. |
| P2 | Update name, phone, bio, city, state, country, languages, gender | `routers/users.py` → `PUT /users/me` | `pages/Profile.jsx` (sends all profile fields) | `users` | ✅ | All fields optional; backend does partial update |
| P3 | Upload and display profile photo | `routers/users.py` → `POST /users/me/photo`, `utils/file_upload.py` | `pages/Profile.jsx` (optimistic preview), `services/users.js` | `users.profile_photo_url` | ⚠️ | Upload works. Display uses hardcoded `http://localhost:8000${photo_url}` — breaks outside localhost. Fix: use `import.meta.env.VITE_API_URL`. |
| P4 | Profile photo validated (not extension-based), EXIF stripped | `utils/file_upload.py` (Pillow `Image.verify()`, re-encode) | `pages/Profile.jsx` (client-side MIME + 5 MB check) | — | ✅ | Backend: Pillow header check + EXIF strip. Client: MIME type + 5 MB guard before sending. |
| P5 | Owner has identical profile management | `routers/owner.py` → `GET /owner/me`, `PUT /owner/me`, `POST /owner/me/photo` | `pages/owner/OwnerDashboard.jsx` | `users` | ✅ | Owner profile managed via `/owner/me` endpoints |

---

## Section 3 — Dining Preferences

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| PR1 | Save cuisine preferences (multi-select) | `routers/preferences.py` → `PUT /preferences/me` | `pages/Preferences.jsx` (`cuisine_preferences` array) | `user_preferences.cuisine_preferences` (JSON) | ✅ | 23 cuisine enum values supported |
| PR2 | Save price range preference | `routers/preferences.py` | `pages/Preferences.jsx` (`price_range`) | `user_preferences.price_range` | ✅ | — |
| PR3 | Save dietary restrictions | `routers/preferences.py` | `pages/Preferences.jsx` (`dietary_restrictions`) | `user_preferences.dietary_restrictions` (JSON) | ✅ | 12 enum values: Vegetarian, Vegan, Gluten-Free, Halal, etc. |
| PR4 | Save ambiance preferences | `routers/preferences.py` | `pages/Preferences.jsx` (`ambiance_preferences`) | `user_preferences.ambiance_preferences` (JSON) | ✅ | 12 ambiance options including Romantic, Rooftop, Sports Bar |
| PR5 | Save preferred locations | `routers/preferences.py` (accepts `preferred_locations`) | `pages/Preferences.jsx` (sends `preferred_locations`) | `user_preferences.preferred_locations` (JSON) | ✅ | Max 20 entries; correctly sent and accepted |
| PR6 | Save search radius | `routers/preferences.py` (1–500 miles) | `pages/Preferences.jsx` (`search_radius` slider) | `user_preferences.search_radius` | ✅ | — |
| PR7 | Save sort preference | `routers/preferences.py` (enum: rating, newest, most_reviewed, price_asc, price_desc) | `pages/Preferences.jsx` (includes all 5 options) | `user_preferences.sort_preference` | ✅ | Frontend options match backend enum exactly |
| PR8 | Preferences fed to AI assistant automatically | `services/ai_service.py` (`preferences_service.get_for_ai()` called in `chat()`) | — | `user_preferences` | ✅ | `ai_context` computed field in `UserPreferencesOut` passed to LLM system prompt |

---

## Section 4 — Restaurant Discovery

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| D1 | Keyword search (name, description, city) | `routers/restaurants.py` → `GET /restaurants?q=` (ILIKE across name, cuisine_type, description, city, zip_code) | `pages/Explore.jsx` (debounced `q` param) | `restaurants` | ✅ | 300 ms debounce via `useDebounce()` hook |
| D2 | Filter by cuisine | `routers/restaurants.py` (`cuisine` param, partial ILIKE match) | `pages/Explore.jsx` (cuisine chip selection) | `restaurants.cuisine_type` | ✅ | — |
| D3 | Filter by city | `routers/restaurants.py` (`city` param, partial ILIKE match) | `pages/Explore.jsx` (`city` param) | `restaurants.city` | ✅ | — |
| D4 | Filter by price range | `routers/restaurants.py` (`price_range` param, exact match) | `pages/Explore.jsx` (price buttons) | `restaurants.price_range` | ✅ | — |
| D5 | Filter by minimum rating | `routers/restaurants.py` (`rating_min` param) | `pages/Explore.jsx` (rating slider) | `restaurants.avg_rating` | 🔴 | **Frontend sends `min_rating`; backend reads `rating_min`. Rating filter has zero effect.** Fix in Explore.jsx: rename param. |
| D6 | Sort by highest rated | `routers/restaurants.py` (`sort=rating`) | `pages/Explore.jsx` | `restaurants.avg_rating` | ✅ | Default sort |
| D7 | Sort by newest | `routers/restaurants.py` (`sort=newest`) | `pages/Explore.jsx` | `restaurants.created_at` | ✅ | — |
| D8 | Sort by most reviewed | `routers/restaurants.py` (`sort=most_reviewed`) | `pages/Explore.jsx` | `restaurants.review_count` | ✅ | — |
| D9 | Sort by price (asc/desc) | `routers/restaurants.py` (`sort=price_asc`, `sort=price_desc`) | `pages/Explore.jsx` | `restaurants.price_range` | ✅ | — |
| D10 | Active filters shown as removable chips | — | `pages/Explore.jsx` (chip UI with × per filter) | — | ✅ | "Clear all" resets all filters |
| D11 | Pagination (page + limit) | `routers/restaurants.py` (returns `total`, `page`, `limit`, `pages`) | `pages/Explore.jsx` (uses `data.pages`) | `restaurants` | ✅ | Default limit=12 |
| D12 | `is_favorited` flag on list results for auth users | `routers/restaurants.py` (`get_optional_user`, checks Favorite table) | `pages/Explore.jsx` (heart state per card) | `favorites` | ✅ | Anonymous users always get `is_favorited: false` |

---

## Section 5 — Restaurant Detail

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| RD1 | Full restaurant detail view | `routers/restaurants.py` → `GET /restaurants/{id}` | `pages/RestaurantDetails.jsx` | `restaurants` | ✅ | — |
| RD2 | Photo gallery (hero grid) | `routers/restaurants.py` (returns `photos: list[str]`) | `pages/RestaurantDetails.jsx` | `restaurants.photos` (JSON) | ⚠️ | Photo URLs are relative paths (`/uploads/restaurants/...`). Frontend builds full URL with hardcoded `const BASE = 'http://localhost:8000'`. Fix to use env var. |
| RD3 | Hours section with today highlighted | `routers/restaurants.py` (returns `hours: dict`) | `pages/RestaurantDetails.jsx` (computes today's day key) | `restaurants.hours` (JSON) | ✅ | Hours dict keys are `monday`–`sunday`; today matched by `new Date().toLocaleDateString('en-US', {weekday:'long'}).toLowerCase()` |
| RD4 | Contact info (phone, website) | `routers/restaurants.py` | `pages/RestaurantDetails.jsx` | `restaurants.phone`, `restaurants.website` | ✅ | — |
| RD5 | Avg rating + star breakdown visible | `routers/restaurants.py` (`avg_rating`, `review_count`) | `pages/RestaurantDetails.jsx` | `restaurants` | ✅ | Individual star counts from reviews fetched separately |
| RD6 | Unclaimed/Claimed badge visible | `routers/restaurants.py` (`is_claimed` field) | `pages/RestaurantDetails.jsx` | `restaurants.is_claimed` | ✅ | — |
| RD7 | Edit button visible only to creator/claimer | `routers/restaurants.py` (`created_by`, `claimed_by` in response) | `pages/RestaurantDetails.jsx` (checks `user.id === restaurant.created_by`) | `restaurants` | ⚠️ | Condition uses `user.id`. If `user.id` is undefined due to the `user_id`/`id` field mismatch (see A3 notes), the Edit button never appears even for the creator. |

---

## Section 6 — Restaurant Management (Create / Edit / Delete)

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| RM1 | Create restaurant listing (any auth user) | `routers/restaurants.py` → `POST /restaurants` | `pages/AddRestaurant.jsx`, `services/restaurants.js` | `restaurants` | ✅ | `name` required; all other fields optional |
| RM2 | Hours builder (per-day rows) | `routers/restaurants.py` (validates day keys: monday–sunday, weekdays, weekends, everyday) | `pages/AddRestaurant.jsx` (hours object built from day inputs) | `restaurants.hours` (JSON) | ⚠️ | Backend validates day key names. Frontend has no pre-submit validation — if hours object contains an invalid key, the backend returns 422 with no field-specific hint in the UI. |
| RM3 | Website URL validated | `schemas/restaurant.py` (must start with `http://` or `https://`) | `pages/AddRestaurant.jsx` | `restaurants.website` | ⚠️ | Backend enforces scheme. Frontend has no client-side URL validation. User typing `"restaurant.com"` submits fine then sees a generic 422 error. |
| RM4 | Latitude/Longitude validated | `schemas/restaurant.py` (-90–90, -180–180) | `pages/AddRestaurant.jsx` (converts to `parseFloat`) | `restaurants.latitude`, `restaurants.longitude` | ⚠️ | Backend validates bounds. Frontend converts to float but does not check range. |
| RM5 | Upload up to 10 photos per restaurant | `routers/restaurants.py` → `POST /restaurants/{id}/photos` (max 10 enforced) | `pages/AddRestaurant.jsx` (PhotoPicker, uploads one by one) | `restaurants.photos` (JSON) | ✅ | Backend returns 400 on 11th photo |
| RM6 | Edit form pre-fills with existing data | `routers/restaurants.py` → `GET /restaurants/{id}` | `pages/AddRestaurant.jsx` (edit mode loads existing data) | `restaurants` | ✅ | Edit route: `PUT /restaurants/{id}` |
| RM7 | Edit restricted to creator or claiming owner | `routers/restaurants.py` (checks `created_by` or `claimed_by` == user.id → 403) | `pages/RestaurantDetails.jsx` (Edit button conditional) | `restaurants` | ✅ | API-level enforcement; UI is supplementary |
| RM8 | Delete restricted to creator or claiming owner | `routers/restaurants.py` → `DELETE /restaurants/{id}` (403 if not creator/owner) | — | `restaurants` | ✅ | Returns 204 No Content |
| RM9 | Non-creator cannot see Edit button | — | `pages/RestaurantDetails.jsx` (checks `user.id === created_by`) | — | ⚠️ | Same `user.id` concern as RD7. If auth field mismatch exists, all users see or don't see the button. |

---

## Section 7 — Ownership Claim

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| OC1 | Owner can claim unclaimed restaurant | `routers/restaurants.py` → `POST /restaurants/{id}/claim` | `pages/RestaurantDetails.jsx` (Claim button), `services/restaurants.js` | `restaurant_claims`, `restaurants.is_claimed`, `restaurants.claimed_by` | ✅ | Auto-approved immediately |
| OC2 | Claim sets `is_claimed=True`, assigns `claimed_by` | `routers/restaurants.py` (updates Restaurant row + inserts RestaurantClaim) | — | `restaurants`, `restaurant_claims` | ✅ | — |
| OC3 | Second claim on same restaurant → 400 | `routers/restaurants.py` (checks `is_claimed` → 400) | — | `restaurants.is_claimed` | ✅ | — |
| OC4 | Reviewer cannot claim (403) | `routers/restaurants.py` (`require_owner` dependency) | — | — | ✅ | Verified in test_owner.py |
| OC5 | Claimed restaurant appears in owner dashboard | `routers/owner.py` → `GET /owner/dashboard` (includes claimed restaurants) | `pages/owner/OwnerDashboard.jsx` | `restaurants.claimed_by` | ✅ | — |
| OC6 | Duplicate claim route | `routers/restaurants.py` (`POST /restaurants/{id}/claim`) AND `routers/owner.py` (`POST /owner/restaurants/{id}/claim`) | `services/restaurants.js` uses `/restaurants/:id/claim`; `services/owner.js` uses `/owner/restaurants/:id/claim` | — | ⚠️ | Two routes exist for the same action. Frontend `restaurants.js` calls the canonical path; `owner.js` calls the owner-prefixed path. Both work but grader may notice the inconsistency. Recommend removing one. |

---

## Section 8 — Reviews

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| RV1 | Reviewer writes review (rating 1–5, comment 10–5000) | `routers/reviews.py` → `POST /restaurants/{id}/reviews` | `pages/RestaurantDetails.jsx` (inline review form) | `reviews` | ✅ | `ReviewCreate` schema: `rating` int 1–5, `comment` str 10–5000 |
| RV2 | Owner cannot write review → 403 | `routers/reviews.py` (`_require_reviewer()` → 403 if owner) | `pages/RestaurantDetails.jsx` (Write Review button hidden for owners) | — | ✅ | UI hides form; API enforces 403. Both layers tested. |
| RV3 | One review per user per restaurant → 400 | `services/review_service.py` (checks existing review before insert) | — | `reviews` (user_id + restaurant_id uniqueness) | ✅ | — |
| RV4 | avg_rating recalculates on write | `services/review_service.py` (`recalc_rating()`) | `pages/RestaurantDetails.jsx` (uses returned `restaurant_stats`) | `restaurants.avg_rating`, `restaurants.review_count` | ✅ | Recalculates on create, update, and delete |
| RV5 | Review response includes updated avg_rating | `routers/reviews.py` (returns `ReviewWithStatsResponse` with `restaurant_stats`) | `pages/RestaurantDetails.jsx` (updates UI from response) | `restaurants` | ✅ | No page reload needed |
| RV6 | Edit own review (pre-fills existing values) | `routers/reviews.py` → `PUT /reviews/{id}` (author-only) | `pages/RestaurantDetails.jsx` (edit mode populates form) | `reviews` | ✅ | Partial update; at least one field required |
| RV7 | Cannot edit another user's review → 403 | `routers/reviews.py` (checks `review.user_id == current_user.id`) | — | — | ✅ | Verified in test_reviews.py |
| RV8 | Delete own review | `routers/reviews.py` → `DELETE /reviews/{id}` (returns `review: null` + updated stats) | `pages/RestaurantDetails.jsx` (removes from list, updates rating) | `reviews` | ✅ | — |
| RV9 | Review photo upload (up to 5) | `routers/reviews.py` → `POST /reviews/{id}/photos` | `pages/RestaurantDetails.jsx` (PhotoPicker in review form) | `reviews.photos` (JSON) | ✅ | Client-side 5 MB check present; max 5 enforced by backend |
| RV10 | Review photo preview before submit | — | `pages/RestaurantDetails.jsx` (`URL.createObjectURL()` preview + KB label) | — | ✅ | `×` remove button on hover |
| RV11 | Reviews listed on detail page (newest-first) | `routers/reviews.py` → `GET /restaurants/{id}/reviews` (sort param) | `pages/RestaurantDetails.jsx` (paginated list) | `reviews` | ✅ | — |
| RV12 | Review card shows name, rating, date, comment, photo | `schemas/review.py` (`ReviewResponse` includes `user: {id, name, profile_photo_url}`) | `components/restaurants/ReviewCard.jsx` | `reviews`, `users` | ✅ | — |

---

## Section 9 — Favorites

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| F1 | Add restaurant to favorites | `routers/favorites.py` → `POST /favorites/{id}` | `components/common/FavoriteButton.jsx`, `services/favorites.js` | `favorites` | ✅ | Returns 400 if already favorited |
| F2 | Remove restaurant from favorites | `routers/favorites.py` → `DELETE /favorites/{id}` | `components/common/FavoriteButton.jsx` | `favorites` | ✅ | Returns 400 if not currently favorited |
| F3 | Heart toggle with toast feedback | — | `components/common/FavoriteButton.jsx` (react-hot-toast) | — | ✅ | Optimistic update with revert on error |
| F4 | Favorites list page (newest-first) | `routers/favorites.py` → `GET /favorites/me` | `pages/Favorites.jsx`, `services/favorites.js` | `favorites` | 🔴 | **Frontend `favorites.js` calls `GET /favorites` — backend defines `GET /favorites/me`. The Favorites page will always return 404.** Fix: change `GET /favorites` → `GET /favorites/me` in `services/favorites.js`. |
| F5 | Heart state persists across navigation | — | `pages/Explore.jsx` (reads `is_favorited` from restaurant list), `pages/RestaurantDetails.jsx` | `favorites` | ✅ | `is_favorited` returned per restaurant in list response |
| F6 | Remove from Favorites page works | `routers/favorites.py` → `DELETE /favorites/{id}` | `pages/Favorites.jsx` | `favorites` | ✅ | Item removed optimistically from list |

---

## Section 10 — Activity History

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| H1 | Reviews Written section (newest-first) | `routers/history.py` → `GET /history/me` | `pages/History.jsx`, `services/history.js` | `reviews`, `restaurants` | ✅ | Returns `reviews[]` with restaurant name, rating, comment |
| H2 | Restaurants Added section (newest-first) | `routers/history.py` | `pages/History.jsx` | `restaurants` (filtered by `created_by`) | ✅ | Returns `restaurants_added[]` with name, city, cuisine, avg_rating |
| H3 | Links navigate to correct detail pages | — | `pages/History.jsx` (router links) | — | ✅ | — |
| H4 | Works for both reviewer and owner accounts | `routers/history.py` (no role restriction) | — | — | ✅ | `get_current_user` (not `require_user`) used |

---

## Section 11 — Owner Dashboard & Analytics

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| OD1 | Aggregate stats: restaurant count, review count, avg rating, total favorites | `routers/owner.py` → `GET /owner/dashboard` (`OwnerDashboardResponse`) | `pages/owner/OwnerDashboard.jsx` | `restaurants`, `reviews`, `favorites` | ✅ | Stats computed over all restaurants where `created_by` or `claimed_by` = owner.id |
| OD2 | Rating distribution (1–5 star breakdown) | `routers/owner.py` (`rating_distribution` in response) | `pages/owner/OwnerDashboard.jsx` | `reviews` | ✅ | — |
| OD3 | 6-month review trend chart (monthly counts) | `routers/owner.py` (`monthly_trend[]` in response) | `pages/owner/OwnerDashboard.jsx` | `reviews.created_at` | ✅ | — |
| OD4 | Sentiment keywords (positive/negative terms) | `routers/owner.py`, `services/owner_service.py` (`sentiment` in response) | `pages/owner/OwnerDashboard.jsx` | `reviews.comment` | ✅ | Extracted from review text |
| OD5 | Recent reviews with reviewer name and rating | `routers/owner.py` (`recent_reviews[]` in response) | `pages/owner/OwnerDashboard.jsx` | `reviews`, `users` | ✅ | — |
| OD6 | Per-restaurant stats page | `routers/owner.py` → `GET /owner/restaurants/{id}/stats` | `pages/owner/OwnerRestaurantDetail.jsx` | `reviews`, `favorites` | ✅ | 403 if querying another owner's restaurant |
| OD7 | Owner restaurant list | `routers/owner.py` → `GET /owner/restaurants` | `pages/owner/OwnerRestaurants.jsx` | `restaurants` | ✅ | Lists created + claimed restaurants |
| OD8 | Owner reviews list (all restaurants) | `routers/owner.py` → `GET /owner/reviews` | `pages/owner/OwnerReviews.jsx` | `reviews` | ✅ | 50 most recent |
| OD9 | All owner routes block reviewers (403) | `routers/owner.py` (`_require_owner()` dependency) | — | — | ✅ | Parametrized in test_owner.py across all 4 GET /owner/* paths |
| OD10 | Owner can update their restaurant listing | `routers/owner.py` → `PUT /owner/restaurants/{id}` | `pages/owner/OwnerRestaurantDetail.jsx` | `restaurants` | ✅ | 403 if not owner of that specific restaurant |

---

## Section 12 — AI Assistant

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| AI1 | Chat endpoint accepts natural-language message | `routers/ai_assistant.py` → `POST /ai-assistant/chat` (or `/ai/chat` — **verify prefix**) | `services/ai.js` → `POST /ai-assistant/chat` | `conversations`, `conversation_messages` | ⚠️ | **Endpoint path must match. Check `app/main.py` for the `include_router()` prefix used for `ai_assistant.router`.** If prefix is `/ai` not `/ai-assistant`, every chat request fails with 404. |
| AI2 | Rule-based filter extraction (cuisine, price, dietary, occasion, ambiance, location) | `services/ai_service.py` (`extract_filters()`) | — | — | ✅ | Zero LLM cost; keyword dictionaries for all 6 dimensions |
| AI3 | User preferences injected automatically | `services/ai_service.py` (`preferences_service.get_for_ai()` in `chat()`) | — | `user_preferences` | ✅ | Preferences passed as context to filter extraction AND LLM system prompt |
| AI4 | DB search from extracted filters | `services/ai_service.py` (`_search_restaurants()`) | — | `restaurants` | ✅ | Broadening fallback if combined filters return 0 results |
| AI5 | Relevance scoring + top-5 ranking | `services/ai_service.py` (`_score()`, `rank_restaurants()`) | — | — | ✅ | 0–100 score: rating 40pt, popularity 20pt, cuisine 20pt, price 10pt, location 10pt |
| AI6 | Match reasons returned with each recommendation | `services/ai_service.py` (`_build_match_reasons()`) | `components/ai/ChatRecommendationCard.jsx` | — | ✅ | Shown as bullet points on recommendation cards |
| AI7 | Tavily web search for "open now", "trending" queries | `services/ai_service.py` (`_tavily_search()`, fires when `needs_web_search=True`) | — | — | ✅ | Gracefully skipped when `TAVILY_API_KEY` absent |
| AI8 | LangChain + Ollama LLM response | `services/ai_service.py` (`_generate_response()` → `ChatOllama`) | — | — | ✅ | Model configured via `OLLAMA_MODEL` env var |
| AI9 | Deterministic fallback when Ollama unavailable | `services/ai_service.py` (`_no_llm_response()`) | — | — | ✅ | Returns formatted markdown with ranked results |
| AI10 | Three prompt modes: normal / clarification / fallback | `services/ai_service.py` (`_build_system_content()`, `_query_is_vague()`, `_results_are_weak()`) | — | — | ✅ | Clarification when no signal extracted; fallback when no DB matches |
| AI11 | Multi-turn: conversation_id returned and accepted | `services/ai_service.py` (`_persist_turn()`, `_load_history_from_db()`) | `services/ai.js` (passes `conversation_id` on subsequent turns) | `conversations`, `conversation_messages` | ✅ | History loaded from DB when `conversation_id` supplied |
| AI12 | Conversation persisted to DB | `services/ai_service.py` (`_persist_turn()` writes user + assistant messages with `extra_json` metadata) | — | `conversations`, `conversation_messages` | ✅ | — |
| AI13 | Follow-up question appended to response | `services/ai_service.py` (`follow_up_question` in response) | `components/ai/ChatWindow.jsx` | — | ✅ | — |
| AI14 | AI loading state shown during Ollama call | — | `components/common/AIAssistant.jsx` | — | ⚠️ | Verify a loading indicator (typing animation or spinner) is shown while `isLoading=true`. Ollama cold-start can take 15–30 seconds with no visual feedback otherwise. |
| AI15 | Axios timeout long enough for Ollama | — | `services/api.js` (`timeout` field) | — | ⚠️ | **Confirm `timeout` value is in milliseconds and is ≥ 30000 (30 seconds). If currently `30`, every Ollama request will timeout after 30ms.** |

---

## Section 13 — File Uploads

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| FU1 | Server-side MIME type validation (not extension) | `utils/file_upload.py` (Pillow `Image.verify()`) | — | — | ✅ | Allowed: JPEG, PNG, WEBP, GIF |
| FU2 | 5 MB file size limit | `utils/file_upload.py` (size check before Pillow) | `pages/RestaurantDetails.jsx` (client guard, review photos only) | — | ⚠️ | Backend enforces 5 MB on all uploads. Frontend only validates size client-side for **review photos**. Profile photo, restaurant photo uploads have no client-side size guard — large files fail silently at the API level. |
| FU3 | Oversized images downsampled to 1920px | `utils/file_upload.py` (`thumbnail((1920,1920))`) | — | — | ✅ | — |
| FU4 | EXIF metadata stripped | `utils/file_upload.py` (re-encode via Pillow without EXIF) | — | — | ✅ | Strips GPS, camera model, etc. |
| FU5 | UUID filenames (no path traversal) | `utils/file_upload.py` (`uuid.uuid4().hex`) | — | `uploads/` directory | ✅ | — |
| FU6 | Optimistic photo preview before upload | — | `pages/RestaurantDetails.jsx` (`URL.createObjectURL()`), `pages/Profile.jsx` | — | ✅ | Preview shown before HTTP request; reverted on error |

---

## Section 14 — Input Validation

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| V1 | Review rating: 1–5 only | `schemas/review.py` (Field ge=1, le=5) | `pages/RestaurantDetails.jsx` (star picker, no invalid value possible) | `reviews.rating` | ✅ | — |
| V2 | Review comment: 10–5000 characters | `schemas/review.py` (min_length=10, max_length=5000) | `pages/RestaurantDetails.jsx` (character counter) | `reviews.comment` | ✅ | — |
| V3 | Restaurant name: 1–255 characters (required) | `schemas/restaurant.py` (min_length=1, max_length=255) | `pages/AddRestaurant.jsx` | `restaurants.name` | ✅ | — |
| V4 | Price range: only $, $$, $$$, $$$$ | `schemas/restaurant.py` (Literal["$","$$","$$$","$$$$"]) | `pages/AddRestaurant.jsx` (dropdown) | `restaurants.price_range` | ✅ | — |
| V5 | Website: must start with http/https | `schemas/restaurant.py` (validator function) | `pages/AddRestaurant.jsx` | `restaurants.website` | ⚠️ | Backend enforces. No client-side validation — user gets generic 422 on submit. |
| V6 | Latitude: -90 to 90 | `schemas/restaurant.py` (ge=-90, le=90) | `pages/AddRestaurant.jsx` (no bounds check) | `restaurants.latitude` | ⚠️ | Backend enforces. No client-side check. |
| V7 | Longitude: -180 to 180 | `schemas/restaurant.py` (ge=-180, le=180) | `pages/AddRestaurant.jsx` (no bounds check) | `restaurants.longitude` | ⚠️ | Backend enforces. No client-side check. |
| V8 | Hours: valid day key names only | `schemas/restaurant.py` (validated keys: monday–sunday, weekdays, weekends, everyday) | `pages/AddRestaurant.jsx` (no key validation) | `restaurants.hours` (JSON) | ⚠️ | Backend enforces. No client-side check — invalid key returns 422 with no field hint. |
| V9 | Password: 8–128 characters | `schemas/auth.py` (min_length=8, max_length=128) | `pages/Register.jsx` (shows strength hints) | `users.password_hash` | ⚠️ | Backend enforces length only. Frontend shows uppercase/number hints that backend does not enforce — mismatch creates confusion. |
| V10 | Email: valid RFC format | `schemas/auth.py` (Pydantic `EmailStr`) | `pages/Login.jsx`, `pages/Register.jsx` (HTML type="email") | `users.email` | ✅ | — |
| V11 | Name: 2–100 characters | `schemas/auth.py` (min_length=2, max_length=100) | `pages/Register.jsx` | `users.name` | ✅ | — |
| V12 | Invalid inputs return 422, not 500 | `middleware/exception_handler.py` (global handler) | — | — | ✅ | Pydantic validation errors mapped to 422 with field-level detail |

---

## Section 15 — Responsive Design & UX

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| UX1 | Restaurant grid → 1 column at 640px | — | `pages/Explore.jsx` (Tailwind `sm:grid-cols-2`, `md:grid-cols-3`) | — | ✅ | — |
| UX2 | Add Restaurant form → single column on mobile | — | `pages/AddRestaurant.jsx` (Tailwind `grid-cols-1 md:grid-cols-2`) | — | ✅ | — |
| UX3 | Hamburger menu below 768px | — | `components/common/Navbar.jsx` | — | ✅ | — |
| UX4 | Restaurant detail → single column layout on mobile | — | `pages/RestaurantDetails.jsx` | — | ✅ | — |
| UX5 | No horizontal overflow at 390px | — | All pages | — | ⚠️ | Cannot verify without running the app. Responsive fixes were committed. Manual check required at 390px (iPhone 14 Pro) before submission. |
| UX6 | Toast notifications for success/error states | — | All pages (`react-hot-toast`) | — | ✅ | — |
| UX7 | Loading skeletons / spinners during data fetch | — | `components/common/LoadingSpinner.jsx`, `SkeletonLoader.jsx` | — | ✅ | — |
| UX8 | Empty state shown when list is empty | — | `components/common/EmptyState.jsx` (used on Favorites, History, Explore) | — | ✅ | — |
| UX9 | 404 / unknown route handling | — | `App.jsx` (catch-all route) | — | ⚠️ | If no catch-all `<Route path="*">` exists in App.jsx, navigating to `/restaurants/99999` or a typo URL shows a blank page. |

---

## Section 16 — API Documentation

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| DOC1 | Swagger UI accessible at /docs | `app/main.py` (FastAPI auto-generates) | — | — | ✅ | `http://localhost:8000/docs` |
| DOC2 | ReDoc accessible at /redoc | `app/main.py` | — | — | ✅ | `http://localhost:8000/redoc` |
| DOC3 | All endpoints tagged and described | `app/main.py` (`_TAGS_METADATA`), all routers (docstrings) | — | — | ✅ | 10 tag groups with descriptions |
| DOC4 | Response schemas documented | All `routers/*.py` (`response_model=` on every endpoint) | — | — | ✅ | — |
| DOC5 | Swagger auth guide | — | — | — | ✅ | `backend/docs/swagger_auth_guide.md` |
| DOC6 | Postman collection | — | — | — | ✅ | `backend/docs/postman_collection.json` (43 requests) |
| DOC7 | Demo scenarios for grader | — | — | — | ✅ | `backend/docs/DEMO_SCENARIOS.md` (20 scenarios) |

---

## Section 17 — Seed Data & Testing

| Req | Requirement | Backend File(s) | Frontend File(s) | DB Table(s) | Status | Notes |
|---|---|---|---|---|---|---|
| SD1 | Demo reviewer accounts (5+) | `seed_data.py` | — | `users` | ✅ | Jane Doe, Marcus Johnson, Priya Patel, Alex Rivera, Emily Chen — all password=`password` |
| SD2 | Demo owner accounts (3+) | `seed_data.py` | — | `users` | ✅ | Mario Rossi, Wei Zhang, Sofia Hernandez |
| SD3 | Restaurants (15+) across multiple cuisines | `seed_data.py` | — | `restaurants` | ✅ | 18 restaurants, 12 cuisines, SF/Oakland/Berkeley |
| SD4 | Multiple reviews per restaurant | `seed_data.py` | — | `reviews` | ✅ | 35 reviews spread over 6 months |
| SD5 | Favorites data | `seed_data.py` | — | `favorites` | ✅ | 18 favorites |
| SD6 | User preferences set | `seed_data.py` | — | `user_preferences` | ✅ | 5 preference sets (one per reviewer) |
| SD7 | Ownership claims | `seed_data.py` | — | `restaurant_claims`, `restaurants` | ✅ | 7 claimed restaurants |
| SD8 | AI demo conversation history | `seed_data.py` | — | `conversations`, `conversation_messages` | ✅ | 2 multi-turn conversations |
| SD9 | `--wipe` flag for clean re-seed | `seed_data.py` | — | All tables | ✅ | Deletes in correct FK order |
| T1 | Auth tests (25) | `tests/test_auth.py` | — | — | ✅ | Hashing, JWT, signup, login, cross-role |
| T2 | Restaurant tests (32) | `tests/test_restaurants.py` | — | — | ✅ | CRUD, all filter combos, claim, 404s |
| T3 | Review tests (29) | `tests/test_reviews.py` | — | — | ✅ | Auth matrix, rating recalc, boundaries |
| T4 | Favorites tests (17) | `tests/test_favorites.py` | — | — | ✅ | Toggle, list, isolation, duplicate |
| T5 | Owner tests (17) | `tests/test_owner.py` | — | — | ✅ | Access control, analytics, claim |
| T6 | Tests use isolated in-memory SQLite | `tests/conftest.py` | — | — | ✅ | DB reset between every test via `autouse` fixture |

---

## Confirmed Bug Cross-Reference

Audited against final codebase. Status column reflects actual state.

| Bug ID | Req(s) Affected | Status | Notes |
|---|---|---|---|
| BUG-01 | F4 | ✅ Fixed | `favorites.js:22` calls `GET /favorites/me` |
| BUG-02 | D5 | ✅ Fixed | `Explore.jsx:124` sends `rating_min`; matches backend `Query` param name |
| BUG-03 | RD2, P3 | ✅ Fixed | All photo/URL refs use `import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'`; no bare hardcoded strings |
| BUG-04 | AI15 | ✅ Fixed | `api.js:62` sets `timeout: 30_000` (30 seconds) |
| BUG-05 | AI1 | ✅ Fixed | `ai_assistant.py` declares `prefix="/ai-assistant"`; `ai.js` calls `/ai-assistant/chat`; aligned |
| BUG-06 | P1 | ✅ Not a bug | `GET /users/me` exists in `users.py` (router prefix `/users`, route `/me`) |
| BUG-07 | A7 | ✅ Fixed | `api.js:122–126` calls `tokenStore.clear()` + shows session-expired toast on 401; login/signup paths excluded via `SILENT_AUTH_PATHS` |
| BUG-08 | RD7, RM9 | ✅ Fixed | `AuthContext._persist` now spreads `data` and adds `id: data.user_id` before calling `setUser` and `tokenStore.set`. `user.id` is now populated; `ReviewCard.jsx:34` ownership check works correctly. |
| BUG-09 | OC6 | 🟡 Still present | Both `POST /owner/restaurants/{id}/claim` (`owner.py:419`) and `POST /restaurants/{id}/claim` (`restaurants.py`) exist. Pages use the `/restaurants/{id}/claim` path; the `/owner/…/claim` duplicate is unused by any page but present in `owner.js` service. Non-breaking but redundant. |
| BUG-10 | V9, A9 | ✅ Fixed | `Register.jsx` validates `password.length >= 8`; backend enforces `min_length=8` via Pydantic. No complexity-hint mismatch. |
