# ForkFinder — Complete Testing Plan

## Quick Start

```bash
# Install test dependencies
cd backend
pip install pytest pytest-asyncio httpx

# Run all tests
pytest -v

# Run a specific file
pytest tests/test_auth.py -v

# Run with coverage report
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

---

## 1. Backend Unit Test Plan

Unit tests isolate a single function or class with no DB, no HTTP. Use `pytest` with mocks where needed.

### 1.1 `app/utils/auth.py`

| Test | What to assert |
|---|---|
| `hash_password` returns a bcrypt hash, not plaintext | `hashed != plain` |
| `hash_password` uses random salt (same input → different hash each call) | `hash1 != hash2` |
| `verify_password` returns True for correct password | `True` |
| `verify_password` returns False for wrong password | `False` |
| `create_access_token` produces a decodable JWT with `sub`, `role`, `exp` | payload keys present |
| `decode_token` returns the payload dict for a valid token | dict returned |
| `decode_token` raises HTTPException 401 for a garbage token | exception raised |
| Token expiry is respected (mock `datetime.utcnow`) | expired token → 401 |

### 1.2 `app/utils/file_upload.py`

| Test | What to assert |
|---|---|
| Accepted MIME types pass validation (jpeg, png, webp, gif) | no exception |
| Rejected MIME type raises 400 (e.g. application/pdf) | HTTPException 400 |
| File under 5 MB passes | saved successfully |
| File exactly 5 MB passes | saved successfully |
| File over 5 MB raises 400 | HTTPException 400 |
| Corrupted image bytes raise 400 (Pillow verify failure) | HTTPException 400 |
| Saved file exists at expected path under `uploads/` | `Path.exists() == True` |
| Oversized image is downsampled to ≤ 1920px on longest side | dimensions ≤ 1920 |
| EXIF metadata is stripped from re-encoded JPEG | no EXIF data in output |

### 1.3 `app/services/review_service.py`

| Test | What to assert |
|---|---|
| `create()` saves review row to DB | row exists after call |
| `create()` updates `avg_rating` and `review_count` on restaurant | values recalculated |
| `create()` with duplicate `(user_id, restaurant_id)` raises ValueError | ValueError |
| `create()` with nonexistent `restaurant_id` raises LookupError | LookupError |
| `update()` with wrong `user_id` raises PermissionError | PermissionError |
| `update()` with nonexistent `review_id` raises LookupError | LookupError |
| `delete()` decrements `review_count` | count -1 |
| `delete()` recalculates `avg_rating` correctly | average correct |
| `get_paginated()` returns correct page/limit slice | `len(items) == limit` |
| `get_paginated()` sorts by `highest_rating` DESC | first item has highest rating |

### 1.4 `app/services/favorites_service.py`

| Test | What to assert |
|---|---|
| `add()` creates a Favorite row | row exists |
| `add()` with existing favorite raises ValueError | ValueError |
| `add()` with nonexistent restaurant raises LookupError | LookupError |
| `remove()` deletes the Favorite row | row gone |
| `remove()` when not favorited raises ValueError | ValueError |
| `get_for_user()` returns only the calling user's favorites | `user_id` matches |

### 1.5 `app/services/preferences_service.py`

| Test | What to assert |
|---|---|
| `get()` returns defaults when no preferences saved | empty lists, radius=10 |
| `upsert()` saves cuisine/dietary/ambiance lists as JSON | stored as JSON strings |
| `upsert()` with partial payload does not overwrite other fields | existing fields preserved |
| `get()` returns `ai_context` dict with `has_preferences: True` after save | key present and True |
| Invalid enum value raises 422 via router | 422 response |

### 1.6 `app/services/owner_service.py`

| Test | What to assert |
|---|---|
| `get_dashboard()` returns correct `total_restaurants` count | matches DB count |
| `get_dashboard()` computes `avg_rating` as weighted mean | math correct |
| `get_restaurant_stats()` returns correct `rating_distribution` | star counts match reviews |
| `get_restaurant_stats()` with wrong owner raises PermissionError | PermissionError |
| Sentiment `overall` is "positive" when positive count > negative | "positive" |
| `monthly_trend` returns entries for last 6 months | 6 items max |

---

## 2. Backend Integration Test Plan

Integration tests spin up the full FastAPI app with a SQLite test DB and use `TestClient`.

### 2.1 Auth flows

- Reviewer signup → token returned → `GET /auth/me` with token → profile returned
- Owner signup → token returned → `GET /auth/me` → role is "owner"
- Login with correct credentials → token with correct `user_id`
- Login with wrong password → 401
- Reviewer using `/auth/owner/login` → 403 (role mismatch)
- Owner using `/auth/user/login` → 403 (role mismatch)
- `GET /auth/me` without token → 401
- `GET /auth/me` with expired token → 401

### 2.2 Restaurant CRUD flows

- Anonymous search → 200 with `is_favorited: false`
- Authenticated search → `is_favorited` accurate
- Create → list → verify in results
- Create → update → get detail → fields changed
- Create → delete → get detail → 404
- Non-creator update → 403
- Non-creator delete → 403
- Owner claim → restaurant `is_claimed: true`
- Second owner claim → 400

### 2.3 Review flows

- Create review → rating recalculated on restaurant
- Two users review same restaurant → avg correct
- Same user review twice → 400
- Update rating → avg recalculated
- Delete review → count decremented, avg recalculated
- Owner tries to write review → 403
- Public can read reviews → no auth needed

### 2.4 Favorites flows

- Add favorite → `is_favorited: true` on GET restaurant
- Remove favorite → `is_favorited: false`
- Add duplicate → 400
- List favorites → correct items, `favorited_at` timestamp present
- Different users have isolated favorite lists

### 2.5 Profile & preferences flows

- Update profile fields → GET /users/me returns new values
- Update preferences → GET /preferences/me returns new values + `ai_context`
- Profile photo upload → URL returned → GET /users/me has new URL

### 2.6 Owner dashboard flows

- Owner creates restaurant → `GET /owner/restaurants` includes it
- Reviewer posts review → owner's `GET /owner/dashboard` reflects updated stats
- `GET /owner/restaurants/{id}/stats` shows correct rating distribution
- `GET /owner/reviews` includes reviews for all owned restaurants

### 2.7 History flows

- Write a review → `GET /history/me` shows it in `reviews`
- Create a restaurant → `GET /history/me` shows it in `restaurants_added`

---

## 3. Frontend Component Test Plan

**Recommended stack:** Vitest + @testing-library/react + @testing-library/user-event

```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/user-event @testing-library/jest-dom jsdom
```

### 3.1 `Navbar.jsx`

- Renders "ForkFinder" logo text
- Shows Login/Register links when logged out
- Shows avatar and user name when logged in
- Dropdown opens on avatar click
- "Owner Tools" section only visible for owner role
- Dropdown closes when clicking outside
- Mobile menu toggles on hamburger click
- Active route gets brand underline highlight

### 3.2 `StarRating.jsx` / `StarDisplay.jsx`

- Renders 5 stars
- Filled stars match `rating` prop
- Interactive mode: clicking star 3 calls `onRate(3)`
- Read-only mode: clicking has no effect
- `xs` / `sm` / `lg` size classes applied correctly

### 3.3 `RestaurantCard.jsx`

- Restaurant name renders
- Price range badge shows correct color class
- Favorite button is filled/unfilled based on `is_favorited`
- Clicking favorite button calls `onFavoriteChange` callback
- Cuisine chip renders
- avg_rating and review_count display correctly
- Placeholder renders when no photo

### 3.4 `ReviewCard.jsx`

- Reviewer name and date render
- Star rating displays
- Comment text renders
- Edit/Delete buttons only visible to the review author
- Photo thumbnails render when photos present
- Color-coded rating badge (green for 5, red for 1)

### 3.5 `PhotoPicker.jsx`

- Renders "Add photo" button when empty
- Selecting valid image adds thumbnail
- Selecting a non-image file shows error message
- Selecting a >5 MB file shows error message
- Removing a file via × button removes it
- Cannot exceed `maxFiles` limit (add button disappears)
- Existing URLs render as "Saved" thumbnails
- Drag-and-drop adds files

### 3.6 `ImageUpload.jsx`

- Renders upload area when no preview
- Clicking opens file input
- Selecting valid file calls `onFile` callback
- Selecting non-image shows error
- Spinner overlay shown when `uploading={true}`
- Hover overlay shown when preview present and not uploading
- Circle/square shape classes applied correctly

### 3.7 `LoadingSpinner.jsx`

- Renders spinner element
- `fullPage` prop adds backdrop overlay

### 3.8 `Footer.jsx`

- Brand name renders
- Navigation links render
- AI status indicator renders

---

## 4. Frontend Page Test Plan

### 4.1 `Login.jsx`

- Both role cards (Reviewer / Owner) render
- Clicking role card selects it (visual active state)
- Form has email and password fields
- Submit with empty fields shows validation
- Demo credentials section present
- On successful login, navigates to `/`
- On failed login, shows error alert

### 4.2 `Register.jsx`

- Both role cards render
- Name, email, password, confirm password fields present
- Password strength bars update as user types
- Mismatched confirm password shows inline hint
- Submit sends to correct endpoint based on role

### 4.3 `Home.jsx`

- Hero section renders with search
- Cuisine chips render horizontally scrollable
- "Explore Restaurants" button navigates to `/explore`
- AI assistant teaser section renders
- Mock chat preview shows in AI section

### 4.4 `Explore.jsx`

- Search input present
- Price filter buttons render
- Rating filter buttons render
- Restaurant grid renders with mock data
- Typing in search calls API (debounced)
- Active filters appear as removable chips
- Clearing all filters resets state
- Empty state shown when no results

### 4.5 `RestaurantDetails.jsx`

- Restaurant name, cuisine, price render
- Photo hero grid renders
- Favorite button state matches `is_favorited`
- Review form only shown for logged-in reviewer
- Write review button hidden for owner
- Write review button hidden if already reviewed
- Submitting review adds it to the list
- Edit/delete visible only to review author
- Hours section shows correct day with "Today" badge

### 4.6 `AddRestaurant.jsx`

- All form sections render (Basic, Location, Contact, Hours, Photos)
- Cuisine and price range selects have options
- PhotoPicker renders in Photos section
- Submitting creates restaurant and navigates to detail
- Edit mode (with `?edit=id`) pre-fills form

### 4.7 `Profile.jsx`

- Two tabs: "Profile" and "Dining Preferences"
- Profile tab shows ImageUpload component
- All profile fields pre-filled from API
- Saving profile calls PUT /users/me
- Preferences tab shows cuisine chips, price, dietary, ambiance, sort
- Toggling chip adds/removes from list
- Saving preferences calls PUT /preferences/me

---

## 5. Manual QA Checklist

### 5.1 Authentication

- [ ] Sign up as reviewer with valid data → redirected to home, name in navbar
- [ ] Sign up with duplicate email → error toast shown
- [ ] Sign up with weak password (< 8 chars) → validation error
- [ ] Log in as reviewer → JWT in localStorage
- [ ] Log in as owner → different UI (owner menu items visible)
- [ ] Log out → JWT removed, redirected to home, nav shows Login
- [ ] Refresh page while logged in → stays logged in (token persisted)
- [ ] Navigate to protected route (`/profile`) while logged out → redirected

### 5.2 Restaurant Discovery

- [ ] Home page loads in < 2 seconds
- [ ] Cuisine chip click filters results
- [ ] Search by restaurant name returns relevant results
- [ ] Search by city name returns correct results
- [ ] Price filter shows only matching tier
- [ ] Rating filter shows only results ≥ minimum
- [ ] Sort by "Newest" changes order
- [ ] Sort by "Highly Rated" shows top-rated first
- [ ] Pagination works (page 2 shows different results)
- [ ] Restaurant card shows photo, name, price, rating, cuisine

### 5.3 Restaurant Details

- [ ] Detail page loads for any restaurant ID
- [ ] Photos hero shows first photo large, others as grid
- [ ] Hours section shows all days
- [ ] Today's hours highlighted
- [ ] Favorite button toggles and persists on reload
- [ ] Review count and avg_rating match reviews listed
- [ ] Reviews paginate correctly

### 5.4 Reviews

- [ ] Reviewer can submit a review (rating + comment)
- [ ] Submitted review appears immediately in list
- [ ] avg_rating updates in the UI after submission
- [ ] Reviewer can edit own review
- [ ] Reviewer can delete own review
- [ ] Write Review button hidden for owner accounts
- [ ] Write Review button hidden if user already reviewed
- [ ] Photo can be attached to review
- [ ] Review with < 10 char comment shows validation error

### 5.5 Favorites

- [ ] Clicking heart adds to favorites (turns red)
- [ ] Clicking heart again removes from favorites
- [ ] Favorites page shows all saved restaurants
- [ ] Favorited restaurants show red heart on Explore page

### 5.6 Profile & Preferences

- [ ] Profile photo upload works and previews immediately
- [ ] Rollback on upload error (photo reverts)
- [ ] Saving profile shows success toast
- [ ] Cuisine preference chips toggle on/off
- [ ] Price range single-select works
- [ ] Search radius slider updates label live
- [ ] Dietary/Ambiance/Sort preferences save correctly

### 5.7 Owner Dashboard

- [ ] Owner can access `/owner/dashboard`
- [ ] Reviewer gets 403 page (or redirect) for owner routes
- [ ] Dashboard shows correct totals
- [ ] Rating distribution chart renders
- [ ] Monthly trend renders
- [ ] Claiming a restaurant changes its status to "Claimed"

### 5.8 AI Assistant

- [ ] Chat opens and closes
- [ ] Sending a message returns a response
- [ ] Restaurant recommendations render as cards
- [ ] Follow-up question appears in chat
- [ ] Multi-turn: subsequent messages maintain context
- [ ] Chat is unavailable to logged-out users

---

## 6. API Test Checklist (Swagger / Postman)

### Authentication endpoints

- [ ] `POST /auth/user/signup` → 201 with token
- [ ] `POST /auth/user/signup` duplicate → 409
- [ ] `POST /auth/user/login` correct → 200 with token
- [ ] `POST /auth/user/login` wrong password → 401
- [ ] `POST /auth/owner/login` with reviewer account → 403
- [ ] `GET /auth/me` with valid token → 200
- [ ] `GET /auth/me` no token → 401

### Restaurant endpoints

- [ ] `GET /restaurants` no params → 200 list
- [ ] `GET /restaurants?q=pizza` → filtered results
- [ ] `GET /restaurants?price_range=$$` → only $$ restaurants
- [ ] `GET /restaurants?sort=invalid` → 422
- [ ] `GET /restaurants/{valid_id}` → 200 full detail
- [ ] `GET /restaurants/999999` → 404
- [ ] `POST /restaurants` with auth + valid body → 201
- [ ] `POST /restaurants` no auth → 401
- [ ] `POST /restaurants` missing name → 422
- [ ] `PUT /restaurants/{id}` as creator → 200
- [ ] `PUT /restaurants/{id}` as non-creator → 403
- [ ] `DELETE /restaurants/{id}` as creator → 204
- [ ] `POST /restaurants/{id}/claim` as owner → 201
- [ ] `POST /restaurants/{id}/claim` as reviewer → 403

### Review endpoints

- [ ] `POST /reviews` as reviewer → 201 with restaurant_stats
- [ ] `POST /reviews` as owner → 403
- [ ] `POST /reviews` no auth → 401
- [ ] `POST /reviews` duplicate → 400
- [ ] `POST /reviews` rating=0 → 422
- [ ] `POST /reviews` comment 5 chars → 422
- [ ] `GET /restaurants/{id}/reviews` no auth → 200
- [ ] `PUT /reviews/{id}` as author → 200
- [ ] `PUT /reviews/{id}` as non-author → 403
- [ ] `DELETE /reviews/{id}` as author → 200, review=null
- [ ] `DELETE /reviews/{id}` no auth → 401

### Preferences endpoints

- [ ] `GET /preferences/me` no auth → 401
- [ ] `GET /preferences/me` with token → 200 with ai_context
- [ ] `PUT /preferences/me` valid body → 200
- [ ] `PUT /preferences/me` invalid cuisine → 422

### Favorites endpoints

- [ ] `POST /favorites/{id}` → 201 is_favorited=true
- [ ] `POST /favorites/{id}` duplicate → 400
- [ ] `DELETE /favorites/{id}` → 200 is_favorited=false
- [ ] `DELETE /favorites/{id}` not favorited → 400
- [ ] `GET /favorites/me` → 200 with items

### Owner endpoints

- [ ] `GET /owner/me` with reviewer token → 403
- [ ] `GET /owner/me` with owner token → 200
- [ ] `GET /owner/dashboard` with owner token → 200
- [ ] `GET /owner/restaurants/{id}/stats` wrong owner → 403
- [ ] `PUT /owner/restaurants/{id}` correct owner → 200

### AI assistant endpoints

- [ ] `POST /ai-assistant/chat` no auth → 401
- [ ] `POST /ai-assistant/chat` with message → 200 with recommendations
- [ ] `POST /ai-assistant/chat` message too long (>2000 chars) → 422
- [ ] `POST /ai-assistant/chat` empty message → 422

---

## 7. Auth Test Cases

### JWT lifecycle

| # | Test | Expected |
|---|---|---|
| A1 | Submit valid credentials | 200 + token |
| A2 | Submit wrong password | 401 |
| A3 | Submit unknown email | 401 (same message — no enumeration) |
| A4 | Access protected endpoint without token | 401 |
| A5 | Send `Authorization: InvalidTokenHere` | 401 |
| A6 | Send token without `Bearer ` prefix | 401 |
| A7 | Manually construct a token with wrong SECRET_KEY | 401 |
| A8 | Use reviewer token on `/auth/owner/login` | 403 |
| A9 | Use owner token on `/auth/user/login` | 403 |
| A10 | `GET /auth/me` works for both reviewer and owner | 200 |

### Token content

| # | Test | Expected |
|---|---|---|
| A11 | Decoded token contains `sub` = user ID | `sub` matches `user_id` |
| A12 | Decoded token contains `role` | "user" or "owner" |
| A13 | Decoded token contains `exp` | future timestamp |
| A14 | Token response includes `token_type: "bearer"` | exact string |

---

## 8. Review Authorization Test Cases

| # | Test | Actor | Expected |
|---|---|---|---|
| R1 | Write review | Reviewer | 201 |
| R2 | Write review | Owner | 403 |
| R3 | Write review | Unauthenticated | 401 |
| R4 | Write 2nd review for same restaurant | Reviewer | 400 |
| R5 | Edit own review | Review author | 200 |
| R6 | Edit another user's review | Different reviewer | 403 |
| R7 | Edit review | Owner | 403 |
| R8 | Delete own review | Review author | 200 |
| R9 | Delete another user's review | Different reviewer | 403 |
| R10 | Delete review | Owner | 403 |
| R11 | Delete review | Unauthenticated | 401 |
| R12 | Read reviews | Unauthenticated | 200 |
| R13 | Read reviews | Owner | 200 |
| R14 | Upload photo to own review | Review author | 200 |
| R15 | Upload photo to another's review | Different reviewer | 403 |
| R16 | Upload 6th photo (limit=5) | Author | 400 |
| R17 | Rating out of range (0 or 6) | Reviewer | 422 |
| R18 | Comment under 10 characters | Reviewer | 422 |

---

## 9. Owner Authorization Test Cases

| # | Test | Actor | Endpoint | Expected |
|---|---|---|---|---|
| O1 | Get own profile | Owner | GET /owner/me | 200 |
| O2 | Get owner profile | Reviewer | GET /owner/me | 403 |
| O3 | Get dashboard | Owner | GET /owner/dashboard | 200 |
| O4 | Get dashboard | Reviewer | GET /owner/dashboard | 403 |
| O5 | Get dashboard | Unauthenticated | GET /owner/dashboard | 401 |
| O6 | List own restaurants | Owner | GET /owner/restaurants | 200, only own |
| O7 | Update own restaurant | Owner | PUT /owner/restaurants/{id} | 200 |
| O8 | Update another owner's restaurant | Other Owner | PUT /owner/restaurants/{id} | 403 |
| O9 | Get restaurant stats for own | Owner | GET /owner/restaurants/{id}/stats | 200 |
| O10 | Get restaurant stats for another's | Other Owner | GET /owner/restaurants/{id}/stats | 403 |
| O11 | Claim unclaimed restaurant | Owner | POST /owner/restaurants/{id}/claim | 200/201 |
| O12 | Claim already-claimed restaurant | Another Owner | POST /owner/restaurants/{id}/claim | 400 |
| O13 | Claim restaurant | Reviewer | POST /owner/restaurants/{id}/claim | 403 |
| O14 | Read reviews (public) | Owner | GET /restaurants/{id}/reviews | 200 |
| O15 | Write review | Owner | POST /reviews | 403 |
| O16 | Get all owner reviews | Owner | GET /owner/reviews | 200, only own |

---

## 10. Chatbot Test Cases

| # | Test | Input | Expected |
|---|---|---|---|
| C1 | Basic recommendation request | "I want Italian food in SF" | Recommendations with Italian cuisine |
| C2 | Price constraint | "Budget dinner under $$" | Restaurants with price_range ≤ "$$" |
| C3 | Dietary restriction | "Vegan-friendly restaurants" | Filtered by dietary preference |
| C4 | Ambiance request | "Romantic dinner for two" | Restaurants with romantic ambiance |
| C5 | Specific occasion | "Family lunch with kids" | Family-Friendly ambiance |
| C6 | Multi-turn: follow-up | Prior: "Italian in SF" → "Do any have outdoor seating?" | Continues context |
| C7 | Real-time query | "What's trending in Chicago right now?" | Triggers web search (needs_web_search=true) |
| C8 | No matches | "Martian cuisine near the moon" | Graceful "I couldn't find" message |
| C9 | Extract filters | "Cheap Thai place" | extracted_filters: {cuisine:"Thai", price_range:"$"} |
| C10 | Unauthenticated | POST /ai-assistant/chat without token | 401 |
| C11 | Empty message | `{"message": ""}` | 422 |
| C12 | Message too long | 2001 characters | 422 |
| C13 | Multi-turn by conversation_id | Pass returned `conversation_id` | History loaded from DB |
| C14 | AI unavailable (Ollama down) | Any message | Fallback rule-based response, not 500 |
| C15 | Response structure | Any valid message | Has: assistant_message, extracted_filters, recommendations, reasoning |

---

## 11. Responsiveness Test Checklist

Test at these breakpoints: **375px** (mobile), **768px** (tablet), **1024px** (laptop), **1440px** (desktop).

### Navigation

- [ ] 375px: hamburger menu visible, links hidden
- [ ] 375px: hamburger opens/closes mobile menu
- [ ] 768px+: full nav bar with all links visible
- [ ] Logo readable at all breakpoints

### Home Page

- [ ] Hero text wraps cleanly at 375px
- [ ] Cuisine chips scroll horizontally on mobile
- [ ] Search input full-width on mobile
- [ ] Stats row stacks vertically on mobile
- [ ] AI teaser section stacks vertically on mobile

### Explore Page

- [ ] Search bar full-width on mobile
- [ ] Filter chips wrap correctly on tablet
- [ ] Restaurant grid: 1 column at 375px, 2 at 640px, 3 at 1024px, 4 at 1280px
- [ ] Price and rating filters wrap without overflow

### Restaurant Details

- [ ] Photo hero stacks to single column on mobile (no grid)
- [ ] Name card below photo on mobile
- [ ] Hours and info sections readable at 375px
- [ ] Review form full-width on mobile

### Forms (Login, Register, AddRestaurant, Profile)

- [ ] 2-column grids collapse to 1-column on mobile
- [ ] Input fields full-width on mobile
- [ ] Submit button full-width or centered on mobile
- [ ] No horizontal scroll on any form

### Owner Dashboard

- [ ] Stats cards stack to 2-col on tablet, 1-col on mobile
- [ ] Charts resize correctly
- [ ] Review list readable on mobile

---

## 12. Accessibility Checklist

### Keyboard Navigation

- [ ] All interactive elements reachable by Tab
- [ ] Tab order logical (left-to-right, top-to-bottom)
- [ ] Star rating interactive via keyboard (Enter/Space to select)
- [ ] Dropdowns operable by keyboard
- [ ] Modal/dialogs trap focus while open
- [ ] Esc closes dropdowns and modals
- [ ] No keyboard traps on non-modal elements

### Screen Reader Compatibility

- [ ] All `<img>` have `alt` text (or `alt=""` for decorative images)
- [ ] Form inputs have associated `<label>` elements
- [ ] Star rating has `aria-label` per star (e.g. "Rate 3 out of 5")
- [ ] Icon-only buttons have `aria-label`
- [ ] Favorite button: `aria-label="Add to favorites"` / `aria-label="Remove from favorites"`
- [ ] Role cards in Login/Register use `role="radio"` or `aria-pressed`
- [ ] Tab panels use `role="tab"` and `aria-selected`
- [ ] Dynamic content (toasts, errors) use `role="alert"` or `aria-live`
- [ ] Loading states announced via `aria-busy` or `aria-label`

### Color & Contrast

- [ ] Body text (gray-700 on white): contrast ratio ≥ 4.5:1
- [ ] Brand-600 on white: contrast ratio ≥ 4.5:1
- [ ] Error red on white: contrast ratio ≥ 4.5:1
- [ ] Placeholder text contrast ≥ 3:1
- [ ] Focus ring clearly visible on all interactive elements
- [ ] Information not conveyed by color alone (e.g. error icons in addition to red text)

### Semantic HTML

- [ ] Page has a single `<h1>`
- [ ] Heading hierarchy logical (h1 → h2 → h3, no skips)
- [ ] Navigation wrapped in `<nav>` with `aria-label`
- [ ] Main content in `<main>`
- [ ] Footer in `<footer>`
- [ ] Restaurant cards use `<article>` or equivalent semantics
- [ ] Lists use `<ul>` / `<ol>`

### Forms

- [ ] Required fields marked with `aria-required="true"` (or `required`)
- [ ] Validation errors programmatically associated with their field (`aria-describedby`)
- [ ] `autocomplete` attributes on name/email/password fields
- [ ] `type="email"`, `type="password"`, `type="tel"` used correctly
- [ ] File upload has visible label and instructions

### Images & Media

- [ ] Restaurant photos have descriptive alt text
- [ ] Profile photos have alt text with user name
- [ ] SVG icons have `aria-hidden="true"` when decorative
- [ ] No information conveyed only through images

---

## Test Infrastructure Setup

### Backend dependencies

Add to `requirements.txt` or a separate `requirements-test.txt`:

```
pytest==8.1.1
pytest-asyncio==0.23.6
httpx==0.27.0
pytest-cov==5.0.0
```

### Frontend dependencies

```bash
npm install -D vitest @testing-library/react @testing-library/user-event \
  @testing-library/jest-dom jsdom @vitest/coverage-v8
```

Add to `vite.config.js`:

```js
test: {
  environment: 'jsdom',
  setupFiles: ['./src/test/setup.js'],
  globals: true,
}
```

Create `src/test/setup.js`:

```js
import '@testing-library/jest-dom'
```

### CI recommendation

Run backend tests on every PR:

```yaml
# .github/workflows/test.yml
- name: Run backend tests
  run: |
    cd backend
    pip install -r requirements.txt -r requirements-test.txt
    pytest -v --cov=app --cov-report=xml
```
