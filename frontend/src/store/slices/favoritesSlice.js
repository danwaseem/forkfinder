import { createSlice } from '@reduxjs/toolkit'

/**
 * Favorites slice — stores the current user's favorited restaurants.
 *
 * Populated by Favorites.jsx on load and by RestaurantDetails.jsx on toggle.
 * Cleared on logout (dispatched by AuthContext).
 */

const initialState = {
  items:         [],   // { restaurant, favorited_at }[]
  restaurantIds: [],   // number[] — fast isFavorited lookup
  loading:       false,
  error:         null,
}

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState,
  reducers: {
    setFavorites(state, action) {
      state.items         = action.payload
      state.restaurantIds = action.payload.map((f) => f.restaurant.id)
      state.loading       = false
      state.error         = null
    },
    addFavorite(state, action) {
      // action.payload: { restaurant, favorited_at }
      const rid = action.payload.restaurant.id
      if (!state.restaurantIds.includes(rid)) {
        state.items.push(action.payload)
        state.restaurantIds.push(rid)
      }
    },
    removeFavorite(state, action) {
      // action.payload: restaurantId (number)
      state.items         = state.items.filter((f) => f.restaurant.id !== action.payload)
      state.restaurantIds = state.restaurantIds.filter((id) => id !== action.payload)
    },
    setLoading(state, action) {
      state.loading = action.payload
    },
    setError(state, action) {
      state.error   = action.payload
      state.loading = false
    },
    clearFavorites(state) {
      state.items         = []
      state.restaurantIds = []
    },
  },
})

export const {
  setFavorites,
  addFavorite,
  removeFavorite,
  setLoading,
  setError,
  clearFavorites,
} = favoritesSlice.actions

// ── Selectors ──────────────────────────────────────────────────────────────────
export const selectFavorites        = (state) => state.favorites.items
export const selectFavoriteIds      = (state) => state.favorites.restaurantIds
export const selectFavoritesLoading = (state) => state.favorites.loading
/** Factory selector — usage: useSelector(selectIsFavorited(restaurantId)) */
export const selectIsFavorited = (restaurantId) => (state) =>
  state.favorites.restaurantIds.includes(restaurantId)

export default favoritesSlice.reducer
