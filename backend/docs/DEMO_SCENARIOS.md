# ForkFinder — 20 Manual Demo Scenarios

Use these scenarios during grading or live demonstrations. Each scenario includes the setup state, steps to execute, and what to verify. All scenarios assume the seed data from `TEST_DATA.md` is loaded.

**Demo credentials:**
- Reviewer: `user@demo.com` / `password`
- Owner: `owner@demo.com` / `password`

---

## Scenario 1 — New Reviewer Registration & First Search

**Goal:** Demonstrate the complete onboarding flow for a new user.

**Steps:**
1. Open the app at `/`
2. Click **Sign Up** in the navbar
3. Select the **Reviewer** role card
4. Enter: Name = `Alice Tester`, Email = `alice@test.com`, Password = `testpass1`
5. Click **Create Account**
6. Verify redirected to home, navbar shows "Alice Tester"
7. Click **Explore** in the navbar
8. Type "Italian" in the search bar
9. Observe filtered results showing Italian restaurants

**Verify:**
- [ ] Account created, JWT stored
- [ ] Navbar updates with user's name
- [ ] Search results contain only Italian restaurants

---

## Scenario 2 — Restaurant Owner Registration & Dashboard

**Goal:** Show owner-specific UI and role separation.

**Steps:**
1. Open the app in an incognito/private window
2. Click **Sign Up → Restaurant Owner**
3. Register with `newowner@test.com` / `ownerpass1`
4. Observe the navbar shows **Owner Tools** section
5. Navigate to `/owner/dashboard`
6. Observe the dashboard loads with empty state

**Verify:**
- [ ] Role card selection works
- [ ] Owner navbar items visible
- [ ] `/owner/dashboard` accessible
- [ ] Reviewer accounts do NOT see "Owner Tools"

---

## Scenario 3 — Full Restaurant Discovery Flow

**Goal:** Demonstrate search, filter, and sort all working together.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Go to **Explore**
2. Click the **Italian** cuisine chip — observe results narrow
3. Click the **$$** price button — results narrow further
4. Change sort to **Highest Rated** — order changes
5. Set rating minimum to **4.0** — low-rated restaurants disappear
6. Click the **×** on an active filter chip — that filter clears
7. Click **Clear all** — all filters reset

**Verify:**
- [ ] Each filter compounds correctly (AND logic)
- [ ] Active filters shown as removable chips
- [ ] Sort changes visible order
- [ ] Clear all resets to default state

---

## Scenario 4 — Restaurant Detail Page

**Goal:** Show a rich restaurant detail view with all sections.

**Steps:**
1. Go to Explore and click on **Ristorante Bello**
2. Observe the photo hero (main photo + 2 side photos)
3. Scroll to the hours section — today's day should be highlighted in brand color
4. Observe the **At a Glance** sidebar (phone, website, cuisine, price)
5. Observe the average rating and star breakdown
6. Scroll to reviews — multiple reviews visible with reviewer names

**Verify:**
- [ ] Photo grid renders correctly
- [ ] Today's hours highlighted with "Today" badge
- [ ] Rating distribution bars visible
- [ ] Reviews show reviewer avatar, name, rating, comment

---

## Scenario 5 — Write, Edit, and Delete a Review

**Goal:** Demonstrate the full review lifecycle.

**Setup:** Log in as `user@demo.com`; choose a restaurant with no existing review from this user

**Steps:**
1. Open **Spice Route** restaurant detail
2. Click **Write a Review**
3. Set rating to 4 stars
4. Type: `"The lamb rogan josh was exceptional — perfectly balanced spices."`
5. Click **Post Review**
6. Verify review appears immediately, avg_rating updates
7. Click the **Edit** icon on the new review
8. Change rating to 5 stars, update comment
9. Click **Save** — review updates in place
10. Click **Delete** — review disappears, avg_rating recalculates

**Verify:**
- [ ] Review appears without page refresh
- [ ] avg_rating and review_count update after each action
- [ ] Edit pre-fills existing values
- [ ] Delete returns `review: null` with updated stats

---

## Scenario 6 — Review Authorization Boundary

**Goal:** Show that owners cannot write reviews.

**Setup:** Log in as `owner@demo.com`

**Steps:**
1. Navigate to **Taqueria La Paloma** detail page
2. Observe the **Write a Review** button is **not visible**
3. Try `POST /reviews` directly in Swagger UI with owner token
4. Observe `403 Forbidden` response

**Verify:**
- [ ] UI hides the review form for owner accounts
- [ ] API enforces 403 even if UI is bypassed

---

## Scenario 7 — Favorites Management

**Goal:** Demonstrate the favorites feature end-to-end.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. On **Explore**, click the ♡ heart on **Dragon Garden**
2. Heart turns red/filled — toast "Added to favorites"
3. Click the heart again — toast "Removed from favorites"
4. Add **Ristorante Bello** and **Spice Route** to favorites
5. Navigate to **Favorites** page
6. Verify both restaurants appear, newest-first
7. Remove **Spice Route** from the Favorites page — it disappears

**Verify:**
- [ ] Heart state persists on navigation (reload page to confirm)
- [ ] Favorites count correct on the Favorites page
- [ ] Remove from Favorites page works

---

## Scenario 8 — Profile Photo Upload

**Goal:** Demonstrate image upload with preview.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Go to **My Account → Profile**
2. Click the avatar photo
3. Select a JPEG image from your local files
4. Observe the **optimistic preview** appears instantly
5. Observe the upload spinner briefly
6. Reload the page — new photo persists

**Verify:**
- [ ] Preview appears before upload completes
- [ ] Photo URL updated in the DB
- [ ] Photo visible in navbar avatar after reload

---

## Scenario 9 — Dining Preferences & AI Context

**Goal:** Show preferences update and their effect on AI recommendations.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Go to **My Account → Dining Preferences**
2. Select: Cuisines = `Italian`, `Japanese`; Price = `$$`; Dietary = `Gluten-Free`; Ambiance = `Casual`
3. Move search radius slider to 20 miles
4. Click **Save Preferences**
5. Open the AI Assistant chat
6. Type: `"What do you recommend for dinner tonight?"`
7. Observe recommendations aligned with saved preferences

**Verify:**
- [ ] Preference chips toggle correctly
- [ ] Save shows success toast
- [ ] GET `/preferences/me` returns `ai_context` with set values
- [ ] AI recommendations reflect Italian/Japanese, $$, gluten-free context

---

## Scenario 10 — Add a New Restaurant Listing

**Goal:** Show the AddRestaurant form with photo upload.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Click **Add Restaurant** (in navbar or from a button on Explore)
2. Fill in: Name = `Noodle House`, Cuisine = `Vietnamese`, Price = `$`, City = `Oakland`
3. Add hours for Monday–Friday: `11am – 9pm`
4. Click **+Add photo** and select an image
5. Observe image thumbnail with KB size label
6. Click **Add Restaurant**
7. Verify redirected to the new restaurant's detail page

**Verify:**
- [ ] All form sections render correctly
- [ ] Photo picker shows thumbnail with × remove button
- [ ] Restaurant created and appears in search
- [ ] Created restaurant appears in `GET /history/me` → `restaurants_added`

---

## Scenario 11 — Edit an Existing Restaurant

**Goal:** Show edit mode pre-fills the form with existing data.

**Setup:** Log in as `user@demo.com`; use a restaurant created by this user

**Steps:**
1. Navigate to the Noodle House detail page (created in Scenario 10)
2. Click **Edit** button (visible to creator)
3. Observe form pre-filled with existing values
4. Change description to: `"Fresh Vietnamese pho and banh mi. Best broth in Oakland."`
5. Add Sunday hours: `Closed`
6. Click **Update Restaurant**

**Verify:**
- [ ] Form loads with existing values
- [ ] Changes saved and reflected on detail page immediately
- [ ] Non-creator does NOT see the Edit button

---

## Scenario 12 — Owner Claiming a Restaurant

**Goal:** Demonstrate the ownership claim workflow.

**Setup:** Log in as `owner@demo.com`

**Steps:**
1. Navigate to **Spice Route** detail page (unclaimed)
2. Observe the "Unclaimed" badge
3. Click **Claim This Restaurant**
4. Observe success toast "Restaurant claimed successfully"
5. Observe the "Claimed" badge now shows on the restaurant
6. Navigate to `/owner/dashboard`
7. Verify Spice Route appears in owned restaurants list

**Verify:**
- [ ] `is_claimed` changes to `true` in API response
- [ ] `claimed_by` set to owner's user ID
- [ ] Restaurant appears in owner's dashboard
- [ ] Second owner cannot claim the same restaurant (400)

---

## Scenario 13 — Owner Dashboard Analytics

**Goal:** Show the owner analytics dashboard.

**Setup:** Log in as `owner@demo.com` (has Ristorante Bello with multiple reviews)

**Steps:**
1. Navigate to `/owner/dashboard`
2. Observe: Total Restaurants, Total Reviews, Avg Rating, Total Favorites
3. Observe the rating distribution (star breakdown)
4. Observe the 6-month review trend chart
5. Observe the sentiment summary (positive/negative keywords)
6. Scroll to Recent Reviews — reviewer names and ratings visible
7. Click on **Ristorante Bello** in the restaurant list — opens per-restaurant stats

**Verify:**
- [ ] All stats match the actual reviews in the DB
- [ ] Monthly trend shows correct month labels
- [ ] Sentiment reflects actual review text
- [ ] Per-restaurant stats page loads for each restaurant

---

## Scenario 14 — AI Assistant — Basic Recommendation

**Goal:** Demonstrate the AI chatbot giving restaurant recommendations.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Open the AI Assistant (chat icon or `/assistant`)
2. Type: `"I want Italian food tonight, something cozy and romantic"`
3. Observe the assistant response with recommendations
4. Click on a recommendation card — should link to the restaurant detail
5. Type a follow-up: `"What about one with outdoor seating?"`
6. Observe context maintained from previous turn

**Verify:**
- [ ] Response includes `assistant_message` with natural language
- [ ] Recommendation cards show name, rating, price, match reasons
- [ ] `extracted_filters` includes `cuisine: "Italian"`, `ambiance: "romantic"`
- [ ] Follow-up question appears at end of response
- [ ] `conversation_id` returned and used on second turn

---

## Scenario 15 — AI Assistant — Multi-Turn Conversation

**Goal:** Verify conversation state persists across multiple turns.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Open AI Assistant
2. Turn 1: `"Find me a place for a business lunch, professional setting"`
3. Note the `conversation_id` (visible in Network tab)
4. Turn 2: `"Under $50 per person"`
5. Turn 3: `"What about vegetarian options?"`
6. Observe all three constraints compound in recommendations

**Verify:**
- [ ] Each subsequent turn refines (not replaces) recommendations
- [ ] `conversation_id` same across all turns
- [ ] Recommendations remain relevant to cumulative constraints

---

## Scenario 16 — Review Photo Upload

**Goal:** Show attaching a photo to a review.

**Setup:** Log in as `user@demo.com`

**Steps:**
1. Navigate to **Dragon Garden** detail
2. Click **Write a Review**
3. Set rating to 5 stars, add a comment
4. Click the **+Add photo** button in the review form
5. Observe the selected photo appears as a 96×96 thumbnail with × remove
6. Hover over thumbnail — remove button appears
7. Submit the review
8. Observe the review renders with the photo thumbnail

**Verify:**
- [ ] Photo preview shown before submission
- [ ] × button removes the photo selection
- [ ] Submitted review shows photo in review card
- [ ] Photo URL stored in `review.photos` array

---

## Scenario 17 — Responsiveness Demo

**Goal:** Show the app works correctly on mobile.

**Steps:**
1. Open browser DevTools → set device to iPhone 14 Pro (390px wide)
2. Navigate to the home page — observe stacked hero layout
3. Open the hamburger menu — mobile nav slides in
4. Navigate to Explore — 1-column restaurant grid
5. Open a restaurant detail — single-column layout, stacked hero
6. Open the Add Restaurant form — grid inputs stack to single column

**Verify:**
- [ ] No horizontal overflow at 390px
- [ ] All text readable (no overflow or overlap)
- [ ] Buttons full-width or centered
- [ ] Touch targets at least 44×44px

---

## Scenario 18 — Input Validation Edge Cases

**Goal:** Show the app handles invalid input gracefully.

**Steps:**
1. On Register: enter a 7-character password → validation error shown
2. On Register: enter mismatched confirm password → inline hint shown
3. On Write Review: submit with 9-character comment → error shown
4. On Add Restaurant: enter `$$$$$` as price range → API returns 422
5. On Profile: enter an invalid phone format → validation error
6. On photo upload: select a PDF file → client-side error shown
7. On photo upload: select a 6 MB image → client-side error shown

**Verify:**
- [ ] Client-side validation catches most errors before API call
- [ ] API-side validation catches anything that slips through
- [ ] Error messages are user-friendly (not raw stack traces)

---

## Scenario 19 — Access Control Boundary Demo

**Goal:** Demonstrate that role-based access is enforced at the API level, not just the UI.

**Tools:** Swagger UI at `http://localhost:8000/docs`

**Steps:**
1. Log in as `owner@demo.com` → copy token
2. In Swagger UI, authorize with owner token
3. Try `POST /reviews` with a valid body → observe 403
4. Log in as `user@demo.com` → copy token, authorize
5. Try `GET /owner/dashboard` → observe 403
6. Try `GET /owner/me` → observe 403
7. Use reviewer token to `PUT /reviews/{id}` for someone else's review → observe 403
8. Try `DELETE /restaurants/{id}` for a restaurant you didn't create → observe 403

**Verify:**
- [ ] Every forbidden action returns exactly 403 (not 404 or 500)
- [ ] Unauthenticated requests return 401
- [ ] Error detail messages are descriptive

---

## Scenario 20 — History & Activity Tracking

**Goal:** Show the activity history page.

**Setup:** Log in as `user@demo.com` (has reviews and created restaurants)

**Steps:**
1. Navigate to **Profile → Activity** (or `/history`)
2. Observe the **Reviews Written** section with restaurant name, rating, comment
3. Observe the **Restaurants Added** section listing created restaurants
4. Click on a restaurant in history — navigates to detail page
5. Verify the API endpoint directly: `GET /history/me` in Swagger UI

**Verify:**
- [ ] Both sections present (`reviews` and `restaurants_added`)
- [ ] Both lists ordered newest-first
- [ ] Restaurant name, city, cuisine, and current avg_rating shown
- [ ] Links navigate to the correct detail pages

---

## Grading Checklist

| Scenario | Feature Area | Points Focus |
|---|---|---|
| 1 | Auth — reviewer registration | Registration flow, JWT |
| 2 | Auth — owner registration | Role separation, UI |
| 3 | Discovery — search & filter | Compound filtering, UX |
| 4 | Discovery — detail view | Rich UI, hours, ratings |
| 5 | Reviews — full CRUD | Create/Edit/Delete, recalculation |
| 6 | Auth — role enforcement | Owner cannot review |
| 7 | Favorites — management | Toggle, list, persistence |
| 8 | Profile — photo upload | File upload, preview |
| 9 | Preferences — save & AI use | Preferences, AI context |
| 10 | Restaurants — create | Form, photo, navigation |
| 11 | Restaurants — edit | Pre-fill, partial update |
| 12 | Owner — claim flow | Claim, dashboard, single-claim |
| 13 | Owner — analytics | Dashboard stats, accuracy |
| 14 | AI — basic chat | Recommendations, filter extraction |
| 15 | AI — multi-turn | Conversation state persistence |
| 16 | Reviews — photo upload | Review media |
| 17 | UI — responsiveness | Mobile layout |
| 18 | Validation — edge cases | Client + server validation |
| 19 | Auth — API-level enforcement | Security, boundary testing |
| 20 | History — activity log | Data aggregation |
