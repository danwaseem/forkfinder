import { createSlice } from '@reduxjs/toolkit'

/**
 * Reviews slice — stores reviews for the currently-viewed restaurant.
 *
 * Populated by RestaurantDetails.jsx after fetching reviews and after
 * create / update / delete operations so DevTools shows review transitions.
 */

const initialState = {
  restaurantId: null,
  items:        [],
  total:        0,
  loading:      false,
  error:        null,
}

const reviewsSlice = createSlice({
  name: 'reviews',
  initialState,
  reducers: {
    setReviews(state, action) {
      state.restaurantId = action.payload.restaurantId
      state.items        = action.payload.items
      state.total        = action.payload.total
      state.loading      = false
      state.error        = null
    },
    addReview(state, action) {
      state.items = [action.payload, ...state.items]
      state.total += 1
    },
    updateReview(state, action) {
      const idx = state.items.findIndex((r) => r.id === action.payload.id)
      if (idx !== -1) state.items[idx] = action.payload
    },
    removeReview(state, action) {
      // action.payload: review id
      state.items = state.items.filter((r) => r.id !== action.payload)
      state.total = Math.max(0, state.total - 1)
    },
    setLoading(state, action) {
      state.loading = action.payload
    },
  },
})

export const {
  setReviews,
  addReview,
  updateReview,
  removeReview,
  setLoading,
} = reviewsSlice.actions

// ── Selectors ──────────────────────────────────────────────────────────────────
export const selectReviews             = (state) => state.reviews.items
export const selectReviewsTotal        = (state) => state.reviews.total
export const selectReviewsRestaurantId = (state) => state.reviews.restaurantId
export const selectReviewsLoading      = (state) => state.reviews.loading

export default reviewsSlice.reducer
