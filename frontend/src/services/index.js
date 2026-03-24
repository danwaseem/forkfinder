/**
 * services/index.js — Central re-export for all API modules
 *
 * Import from here when you need multiple APIs in one file:
 *   import { restaurantsApi, reviewsApi, favoritesApi } from '../services'
 *
 * Or import a single API directly for cleaner tree-shaking:
 *   import { restaurantsApi } from '../services/restaurants'
 *
 * API surface
 * ───────────
 *   authApi         login, register, me
 *   usersApi        me, update, uploadPhoto, history
 *   restaurantsApi  list, get, create, update, delete, uploadPhoto, claim
 *   reviewsApi      list, create, update, delete, uploadPhoto
 *   favoritesApi    list, add, remove, toggle
 *   preferencesApi  get, update, reset
 *   historyApi      get
 *   ownerApi        dashboard, restaurants, updateRestaurant, uploadRestaurantPhoto,
 *                   restaurantReviews, restaurantStats, claimRestaurant,
 *                   reviews, profile, updateProfile, uploadPhoto
 *   aiApi           chat, getConversation, listConversations
 *
 * Low-level
 *   api             raw Axios instance (for one-off requests)
 *   tokenStore      get/set/clear JWT from localStorage
 *   makeFormData    wrap a File in FormData
 */

export { default as api, tokenStore, makeFormData } from './api'

export { authApi }        from './auth'
export { usersApi }       from './users'
export { restaurantsApi } from './restaurants'
export { reviewsApi }     from './reviews'
export { favoritesApi }   from './favorites'
export { preferencesApi } from './preferences'
export { historyApi }     from './history'
export { ownerApi }       from './owner'
export { aiApi }          from './ai'
