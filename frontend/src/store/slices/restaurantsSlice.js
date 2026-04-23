import { createSlice } from '@reduxjs/toolkit'

/**
 * Restaurants slice — stores the current search result page and featured list.
 *
 * Populated by Explore.jsx (search results) and Home.jsx (featured list).
 * Pages continue to manage loading / error locally; they dispatch here after
 * a successful fetch so DevTools shows restaurant data transitions.
 */

const initialState = {
  items:    [],
  featured: [],
  total:    0,
  pages:    1,
  loading:  false,
  error:    null,
}

const restaurantsSlice = createSlice({
  name: 'restaurants',
  initialState,
  reducers: {
    setRestaurants(state, action) {
      state.items   = action.payload.items
      state.total   = action.payload.total
      state.pages   = action.payload.pages
      state.loading = false
      state.error   = null
    },
    setFeatured(state, action) {
      state.featured = action.payload
    },
    setLoading(state, action) {
      state.loading = action.payload
    },
    setError(state, action) {
      state.error   = action.payload
      state.loading = false
    },
  },
})

export const {
  setRestaurants,
  setFeatured,
  setLoading,
  setError,
} = restaurantsSlice.actions

// ── Selectors ──────────────────────────────────────────────────────────────────
export const selectRestaurants        = (state) => state.restaurants.items
export const selectFeatured           = (state) => state.restaurants.featured
export const selectRestaurantsTotal   = (state) => state.restaurants.total
export const selectRestaurantsPages   = (state) => state.restaurants.pages
export const selectRestaurantsLoading = (state) => state.restaurants.loading

export default restaurantsSlice.reducer
