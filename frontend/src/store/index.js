import { configureStore } from '@reduxjs/toolkit'
import authReducer        from './slices/authSlice'
import restaurantsReducer from './slices/restaurantsSlice'
import reviewsReducer     from './slices/reviewsSlice'
import favoritesReducer   from './slices/favoritesSlice'

/**
 * Redux store — Lab 2 Part 4
 *
 * Slices:
 *   auth        — JWT token, user object, isAuthenticated
 *   restaurants — current search results + featured list
 *   reviews     — reviews for the currently-viewed restaurant
 *   favorites   — the authenticated user's saved restaurants
 *
 * Redux DevTools Extension automatically picks this up in the browser.
 * Install: https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd
 */
export const store = configureStore({
  reducer: {
    auth:        authReducer,
    restaurants: restaurantsReducer,
    reviews:     reviewsReducer,
    favorites:   favoritesReducer,
  },
})
