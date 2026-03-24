# Testing Checklist — ForkFinder

## Setup Verification
- [ ] MySQL database `restaurant_platform` created
- [ ] `.env` file populated from `.env.example`
- [ ] `pip install -r requirements.txt` runs without errors
- [ ] `uvicorn app.main:app --reload` starts on port 8000
- [ ] `http://localhost:8000/docs` opens Swagger UI
- [ ] `npm install` completes in `frontend/`
- [ ] `npm run dev` starts on port 5173
- [ ] Seed data loaded: `python seed/seed_data.py`

---

## Authentication

### User Registration
- [ ] Register with name, email, password, role=user → 201 + JWT
- [ ] Register with same email → 400 "Email already registered"
- [ ] Register with role=owner → user created with owner role
- [ ] Short password (< 6 chars) → frontend validation error
- [ ] Mismatched confirm password → frontend validation error

### Login / Logout
- [ ] Login with correct credentials → JWT returned, user stored in localStorage
- [ ] Login with wrong password → 401 "Invalid email or password"
- [ ] Login with non-existent email → 401
- [ ] Logout clears localStorage and redirects to home
- [ ] Expired/invalid JWT → 401 on any protected endpoint

---

## User Profile

### Profile Management
- [ ] View own profile at GET /users/me
- [ ] Update name, email, phone, about_me → saved correctly
- [ ] Update city, state (abbreviated), country → dropdown works
- [ ] Update languages (comma-separated) → saved as string
- [ ] Update gender → select dropdown works
- [ ] Change email to one already taken → 400 error shown
- [ ] Profile photo upload (JPEG/PNG) → photo appears in navbar
- [ ] Profile photo upload (PDF) → 400 "Only JPEG, PNG, GIF, WEBP images allowed"
- [ ] File > 5MB → 400 "File too large"

### Preferences
- [ ] Toggle multiple cuisine preferences → multi-select chips work
- [ ] Select price range → single select (toggle deselects)
- [ ] Adjust search radius slider → updates value display
- [ ] Select multiple dietary restrictions
- [ ] Select multiple ambiance preferences
- [ ] Choose sort preference (radio)
- [ ] Save preferences → GET preferences returns updated values

---

## Restaurants

### Browsing
- [ ] Home page shows top 6 rated restaurants
- [ ] Explore page loads all restaurants (paginated 12/page)
- [ ] Search by restaurant name → filtered results
- [ ] Search by cuisine keyword → filtered results
- [ ] Filter by city → filtered results
- [ ] Filter by price range → filtered results
- [ ] Filter by min rating → filtered results
- [ ] Combine multiple filters
- [ ] Clear all filters button resets results
- [ ] Pagination: next/prev page works
- [ ] Cuisine chip buttons on home navigate to filtered explore

### Restaurant Detail
- [ ] Restaurant detail page shows all fields
- [ ] Photos displayed (3-column grid layout)
- [ ] Hours sidebar shows day-by-day schedule
- [ ] Contact info (phone, website) shown
- [ ] "Claimed" badge shown for claimed restaurants

### Adding / Editing
- [ ] Add restaurant form: all fields visible
- [ ] Required field (name) missing → button disabled/error shown
- [ ] Country dropdown populated
- [ ] State abbreviated dropdown (US states)
- [ ] Hours per day (7 days)
- [ ] Photo upload (multiple files)
- [ ] Submit → restaurant created → redirect to detail page
- [ ] Edit restaurant: pre-filled form
- [ ] Edit updates correctly → redirect back to detail
- [ ] Delete from owner panel → gone from listings

---

## Reviews

### Creating Reviews
- [ ] Non-logged-in user: "Write a Review" not shown
- [ ] Logged-in user: "Write a Review" button visible
- [ ] 1–5 star rating interactive (click stars)
- [ ] Required comment field → error if empty
- [ ] Optional photo upload
- [ ] Submit → review appears at top of list
- [ ] Review date auto-set by server
- [ ] Reviewer name + avatar shown on review card
- [ ] Trying to review same restaurant twice → 400 "Already reviewed"

### Editing / Deleting Own Review
- [ ] Edit button visible only on own reviews
- [ ] Edit opens inline form with existing values
- [ ] Update rating + comment → saved correctly
- [ ] Cancel edit → form closes, no changes
- [ ] Delete button prompts confirmation dialog
- [ ] Delete confirmed → review removed from list
- [ ] Restaurant avg_rating recalculated after add/edit/delete

---

## Favorites

- [ ] Heart icon on card: toggle add/remove favorite
- [ ] Not logged in → toast "Log in to save favorites"
- [ ] Add favorite → heart filled, toast "Added to favorites"
- [ ] Remove favorite → heart empty, toast "Removed from favorites"
- [ ] Favorites page shows all saved restaurants
- [ ] Remove from favorites page → card disappears instantly

---

## History

- [ ] Reviews tab shows all user's past reviews with restaurant names
- [ ] Click restaurant name → navigates to restaurant detail
- [ ] Restaurants Added tab shows all restaurants created by user
- [ ] Empty state messages shown when no data

---

## Owner Features

### Owner Dashboard
- [ ] Accessible only with role=owner
- [ ] Non-owner navigated to home (route guard)
- [ ] Stats cards: total restaurants, total reviews, avg rating, claimed count
- [ ] My Restaurants list shows owned/claimed restaurants
- [ ] Recent Reviews section shows latest 5 reviews
- [ ] Links to manage individual restaurants

### Owner Restaurant Management
- [ ] List of all owner's restaurants with ratings
- [ ] Click restaurant → analytics detail page
- [ ] Rating breakdown bar chart (1–5 stars)
- [ ] 6-month review trend chart
- [ ] Recent reviews list (read-only for owner)
- [ ] Edit button → navigates to edit form
- [ ] Delete button → confirmation dialog → restaurant deleted

### Claiming Restaurants
- [ ] Owner role: "Claim this restaurant" button on unclaimed listings
- [ ] User role: claim button not shown (or shows error)
- [ ] After claiming: "✓ Claimed" badge visible
- [ ] Claimed restaurant appears in owner dashboard

---

## AI Assistant

### Interface
- [ ] Floating 🤖 button visible only when logged in
- [ ] Click FAB → chat panel opens
- [ ] Close button → panel closes
- [ ] Initial greeting message shown
- [ ] Quick suggestion chips shown on first load
- [ ] Click suggestion chip → pre-fills input

### Chat Functionality
- [ ] Type message → send → AI response appears
- [ ] Loading dots animation while waiting
- [ ] Restaurant cards shown in chat for matched results
- [ ] Click restaurant card → navigates to detail page (closes chat)
- [ ] Multi-turn: follow-up question in same session
- [ ] Message with cuisine keyword → returns matching restaurants
- [ ] Message with price hint ("cheap", "fancy") → filtered results
- [ ] Message about hours/events → Tavily search invoked (if key set)
- [ ] Empty response handled gracefully

### Personalization
- [ ] AI loads user preferences on first query
- [ ] Preferences reflected in recommendations
- [ ] AI mentions user's name in responses
- [ ] Fallback response works without OpenAI key

---

## Non-Functional

### Responsiveness
- [ ] Home page: mobile (375px), tablet (768px), desktop (1280px)
- [ ] Navbar: hamburger menu on mobile
- [ ] Restaurant cards: 1/2/3 column grid at breakpoints
- [ ] Forms: full-width on mobile, comfortable on desktop
- [ ] Chat panel: max-width respected on small screens

### Accessibility
- [ ] All images have alt text
- [ ] Form fields have associated labels (htmlFor/id)
- [ ] Buttons have aria-label where icon-only
- [ ] Star rating has aria-label per star
- [ ] Role/tablist/tab attributes on tab components
- [ ] Color contrast: brand-600 on white ≥ 4.5:1
- [ ] Keyboard navigation: Tab through form fields
- [ ] Focus ring visible on interactive elements
- [ ] Error messages use role="alert"

### Loading / Error States
- [ ] Full-page spinner during initial auth check
- [ ] Section spinner while fetching restaurants
- [ ] Error banner when API call fails
- [ ] Empty state illustrations when no data
- [ ] Toast notifications for success/error actions
- [ ] Disabled state on buttons during submission

### Security
- [ ] JWT required for all protected routes
- [ ] Users cannot edit other users' reviews (403)
- [ ] Users cannot delete others' restaurants (403)
- [ ] Non-owners cannot access /owner/* routes (403)
- [ ] Passwords not returned in any API response
- [ ] File uploads restricted to image MIME types
