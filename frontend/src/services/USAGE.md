# API Integration Layer — Usage Guide

## Setup

Set your backend URL in `.env` (already created):
```
VITE_API_BASE_URL=http://localhost:8000
```

Override per-developer without touching `.env`:
```
# .env.local  (gitignored)
VITE_API_BASE_URL=http://staging.example.com
```

---

## Import patterns

```js
// Single API — best for tree-shaking
import { restaurantsApi } from '../services/restaurants'

// Multiple APIs — from the barrel
import { restaurantsApi, reviewsApi, favoritesApi } from '../services'

// Raw Axios instance (one-off calls)
import api from '../services/api'

// Error utilities
import { getErrorMessage, isNotFound, isConflict, ApiError } from '../utils/apiError'
```

---

## Auth

Auth is managed by `AuthContext` — components call `useAuth()`:

```jsx
const { user, login, register, logout, updateUser } = useAuth()

// Log in
await login('alice@example.com', 'password', 'user')   // diner
await login('owner@example.com', 'password', 'owner')  // owner

// Register
await register('Alice', 'alice@example.com', 'pw123', 'user')

// Update cached profile (after a photo upload, etc.)
updateUser({ profile_photo_url: '/uploads/photo.jpg' })
```

---

## Restaurants

```js
import { restaurantsApi } from '../services/restaurants'

// Paginated list with filters
const { items, total } = await restaurantsApi.list({
  q: 'pizza',
  cuisine: 'Italian',
  price_range: '$$',
  min_rating: 4,
  city: 'San Francisco',
  sort: 'rating',
  page: 1,
  limit: 20,
})

// Single restaurant (includes is_favorited when logged in)
const restaurant = await restaurantsApi.get(42)

// Create
const newR = await restaurantsApi.create({
  name: 'Bella Napoli',
  cuisine_type: 'Italian',
  price_range: '$$',
  city: 'San Francisco',
})

// Update
await restaurantsApi.update(42, { description: 'New description' })

// Upload cover photo
await restaurantsApi.uploadPhoto(42, file)  // file is a File object

// Claim (owner only)
await restaurantsApi.claim(42)
```

---

## Reviews

```js
import { reviewsApi } from '../services/reviews'

// List reviews for a restaurant
const { items } = await reviewsApi.list(42, { sort: 'newest' })

// Submit a review — returns { review, restaurant_stats }
const { review, restaurant_stats } = await reviewsApi.create(42, {
  rating: 5,
  comment: 'Absolutely phenomenal!',
})

// Attach a photo to the new review
await reviewsApi.uploadPhoto(review.id, photoFile)

// Edit your review
await reviewsApi.update(review.id, { rating: 4, comment: 'Updated comment' })

// Delete your review
await reviewsApi.delete(review.id)
```

---

## Favorites

```js
import { favoritesApi } from '../services/favorites'

// Fetch saved restaurants
const { items } = await favoritesApi.list()

// Toggle (convenience wrapper)
await favoritesApi.toggle(restaurantId, currentlyFavorited)

// Or explicit add / remove
await favoritesApi.add(restaurantId)
await favoritesApi.remove(restaurantId)
```

---

## User Profile

```js
import { usersApi } from '../services/users'

// Get own profile
const me = await usersApi.me()

// Update profile fields
await usersApi.update({ name: 'Alice B.', city: 'Oakland' })

// Upload profile photo
const { profile_photo_url } = await usersApi.uploadPhoto(file)
updateUser({ profile_photo_url })   // sync to AuthContext

// Activity history
const { reviews, restaurants_added, total_reviews } = await usersApi.history()
```

---

## Preferences

```js
import { preferencesApi } from '../services/preferences'

// Fetch
const prefs = await preferencesApi.get()

// Save (send the full object)
await preferencesApi.update({
  cuisine_preferences:  ['Italian', 'Sushi'],
  price_range:          '$$',
  search_radius:        15,
  dietary_restrictions: ['Vegan'],
  ambiance_preferences: ['Cozy'],
  sort_preference:      'rating',
})

// Reset to defaults
await preferencesApi.reset()
```

---

## Owner Dashboard

```js
import { ownerApi } from '../services/owner'

// All aggregated data in one call
const {
  total_restaurants,
  total_reviews,
  avg_rating,
  sentiment,
  recent_reviews,
  restaurants,
  monthly_trend,   // [{ year, month, review_count }]
} = await ownerApi.dashboard()

// Restaurant list
const { items } = await ownerApi.restaurants({ page: 1, limit: 20 })

// Update a restaurant
await ownerApi.updateRestaurant(id, { description: '…' })

// Per-restaurant analytics
const stats = await ownerApi.restaurantStats(id)

// Reviews across all restaurants
const { items: reviews } = await ownerApi.reviews({ restaurant_id: id })

// Claim a restaurant
await ownerApi.claimRestaurant(id)
```

---

## AI Assistant

```jsx
import { useRef, useState } from 'react'
import { aiApi } from '../services/ai'

function ChatComponent() {
  const conversationIdRef = useRef(null)   // persists across renders, no re-render

  const send = async (message) => {
    const data = await aiApi.chat({
      message,
      conversationId: conversationIdRef.current,   // null on first turn
    })

    // Persist for subsequent turns
    conversationIdRef.current = data.conversation_id

    // data shape:
    const {
      assistant_message,   // string — display this
      recommendations,     // Restaurant[] — inline cards
      follow_up_question,  // string|null — tappable chip
      web_results_summary, // string|null
    } = data
  }
}
```

---

## Error Handling

```js
import { getErrorMessage, isNotFound, isConflict, ApiError } from '../utils/apiError'

// Option 1 — quick message extraction
try {
  await restaurantsApi.create(payload)
} catch (err) {
  toast.error(getErrorMessage(err, 'Could not create restaurant'))
}

// Option 2 — status-specific branches
try {
  await favoritesApi.add(id)
} catch (err) {
  if (isConflict(err)) {
    toast.error('Already in favorites')
  } else {
    toast.error(getErrorMessage(err))
  }
}

// Option 3 — ApiError class for full context
try {
  await reviewsApi.create(restaurantId, payload)
} catch (err) {
  const ae = ApiError.from(err)
  if (ae.isValidation) {
    setFormError(ae.message)        // show inline in form
  } else {
    toast.error(ae.message)         // show toast for everything else
  }
}
```

---

## Global toasts (automatic)

The response interceptor in `api.js` automatically shows toasts for:

| Status | Toast shown |
|--------|-------------|
| Network / timeout | "Network error — are you connected?" |
| 401 (non-auth endpoints) | "Session expired. Please log in again." + clears token |
| 403 | "You don't have permission to do that." |
| 429 | "Too many requests — please slow down." |
| 5xx | "Server error — please try again later." |

**4xx errors (400, 404, 409, 422) are NOT toasted automatically** — handle them
in the component with context-specific messages.
