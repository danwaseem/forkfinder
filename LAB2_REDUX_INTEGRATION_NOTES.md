# Lab 2 Part 4 — Redux Integration Notes

## Setup

After pulling this branch, install the two new packages:

```bash
cd frontend
npm install
```

This installs `@reduxjs/toolkit ^2.2.7` and `react-redux ^9.1.2` which were added to `package.json`.

---

## Store Structure

```
src/store/
├── index.js               ← configureStore (4 reducers)
└── slices/
    ├── authSlice.js        ← user, token, isAuthenticated
    ├── restaurantsSlice.js ← items, featured, total, pages
    ├── reviewsSlice.js     ← restaurantId, items, total
    └── favoritesSlice.js   ← items, restaurantIds (for fast lookup)
```

Redux DevTools Extension:
- Chrome: https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/reduxdevtools/

---

## Slices Added

### `auth`
| Action | Dispatched from | When |
|--------|----------------|------|
| `auth/rehydrate` | AuthContext | On app mount, if localStorage has a token |
| `auth/loginSuccess` | AuthContext `_persist` | After successful login or register |
| `auth/logout` | AuthContext `logout` | On user logout |
| `auth/updateUser` | AuthContext `updateUser` | After profile/photo update |

State shape:
```js
{ user: { id, name, email, role, ... } | null, token: string | null, isAuthenticated: bool }
```

### `restaurants`
| Action | Dispatched from | When |
|--------|----------------|------|
| `restaurants/setRestaurants` | Explore.jsx | After every search/filter/page fetch |
| `restaurants/setFeatured` | Home.jsx | After top-rated fetch on page load |

State shape:
```js
{ items: Restaurant[], featured: Restaurant[], total: number, pages: number }
```

### `reviews`
| Action | Dispatched from | When |
|--------|----------------|------|
| `reviews/setReviews` | RestaurantDetails.jsx | After initial load and after post |
| `reviews/updateReview` | RestaurantDetails.jsx `onUpdated` | After editing a review |
| `reviews/removeReview` | RestaurantDetails.jsx `onDeleted` | After deleting a review |

State shape:
```js
{ restaurantId: number | null, items: Review[], total: number }
```

### `favorites`
| Action | Dispatched from | When |
|--------|----------------|------|
| `favorites/setFavorites` | Favorites.jsx | On Favorites page load |
| `favorites/addFavorite` | RestaurantDetails.jsx | When user hearts a restaurant |
| `favorites/removeFavorite` | RestaurantDetails.jsx + Favorites.jsx | When user un-hearts |
| `favorites/clearFavorites` | AuthContext `logout` | On logout |

State shape:
```js
{ items: { restaurant, favorited_at }[], restaurantIds: number[] }
```

---

## Pages / Components Connected

| File | Change |
|------|--------|
| `src/main.jsx` | Wrapped with `<Provider store={store}>` |
| `src/context/AuthContext.jsx` | Dispatches `loginSuccess`, `logout`, `updateUser`, `rehydrate` |
| `src/pages/Home.jsx` | Dispatches `setFeatured` after featured restaurants fetch |
| `src/pages/Explore.jsx` | Dispatches `setRestaurants` after every search fetch |
| `src/pages/Favorites.jsx` | Dispatches `setFavorites` on load; `removeFavorite` on un-heart |
| `src/pages/RestaurantDetails.jsx` | Dispatches `setReviews`, `addReview`/`updateReview`/`removeReview`, `addFavorite`/`removeFavorite` |

All existing `useState` / API call logic is **unchanged** — dispatch calls are additive.

---

## How to Demonstrate Redux DevTools (Two Slices for Report)

### Slice 1 — `auth` state transition

1. Open app at `http://localhost:5173`
2. Open browser DevTools → Redux DevTools tab
3. Click **Log in** and submit credentials
4. In DevTools, you will see:
   - `auth/rehydrate` (if a token was stored) OR
   - `auth/loginSuccess` with payload `{ user: { id, name, email, role }, token: "eyJ..." }`
5. **Screenshot**: the DevTools panel showing the `auth` slice with `isAuthenticated: true` and the user object

### Slice 2 — `favorites` state transition

1. While logged in, visit any restaurant page (e.g., `/restaurants/1`)
2. Click the **Save** (heart) button
3. In Redux DevTools you will see `favorites/addFavorite` with the restaurant payload
4. Click Save again to un-heart → `favorites/removeFavorite` appears
5. **Screenshot 1**: DevTools showing `favorites/addFavorite` action and the new `restaurantIds` array
6. Navigate to `/favorites` → `favorites/setFavorites` fires with the full list
7. **Screenshot 2**: DevTools showing `favorites/setFavorites` and the `items` array

### Slice 3 — `restaurants` state transition (bonus)

1. Visit `/explore` and search for a keyword
2. DevTools shows `restaurants/setRestaurants` with `items`, `total`, `pages`

---

## Running the App

```bash
# Terminal 1 — backend (MongoDB must be running)
cd backend
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm install   # only needed once after pulling
npm run dev
```

Or with Docker Compose (MongoDB + Kafka + all services):
```bash
docker compose --env-file .env.docker up --build
```

---

## Selectors Reference

```js
// auth
import { selectUser, selectIsAuthenticated, selectIsOwner } from './store/slices/authSlice'

// restaurants
import { selectRestaurants, selectFeatured, selectRestaurantsTotal } from './store/slices/restaurantsSlice'

// reviews
import { selectReviews, selectReviewsTotal } from './store/slices/reviewsSlice'

// favorites
import { selectFavorites, selectFavoriteIds, selectIsFavorited } from './store/slices/favoritesSlice'

// Usage in a component:
const user = useSelector(selectUser)
const isFav = useSelector(selectIsFavorited(restaurantId))
```
