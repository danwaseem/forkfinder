/**
 * users.js — Current user profile + history
 *
 * All endpoints require authentication (Bearer token).
 *
 * Response shapes
 * ───────────────
 * UserResponse:
 *   { id, name, email, phone, role, about_me, city, state, country,
 *     languages, gender, profile_photo_url, created_at, updated_at }
 *
 * UserHistoryResponse:
 *   {
 *     reviews: ReviewHistoryItem[]        — list of the user's reviews
 *     restaurants_added: Restaurant[]     — restaurants the user created
 *     total_reviews: number
 *     total_restaurants_added: number
 *   }
 *
 * ReviewHistoryItem:
 *   { review_id, restaurant_id, restaurant_name, restaurant_city,
 *     rating, comment, created_at, photos }
 */
import api, { makeFormData } from './api'

export const usersApi = {
  /**
   * GET /users/me
   * Fetch the authenticated user's full profile.
   * @returns {Promise<UserResponse>}
   */
  me: () => api.get('/users/me').then((r) => r.data),

  /**
   * PUT /users/me
   * Update the current user's profile fields.
   * Only pass the fields you want to change.
   *
   * @param {{ name?, email?, phone?, about_me?, city?, state?, country?, languages?, gender? }} payload
   * @returns {Promise<UserResponse>}
   */
  update: (payload) => api.put('/users/me', payload).then((r) => r.data),

  /**
   * POST /users/me/photo
   * Upload / replace the profile photo.
   * Returns { profile_photo_url: string }.
   *
   * @param {File} file
   * @returns {Promise<{ profile_photo_url: string }>}
   */
  uploadPhoto: (file) =>
    api.post('/users/me/photo', makeFormData(file)).then((r) => r.data),

  /**
   * GET /users/me/history
   * Fetch the user's review and restaurant activity.
   * @returns {Promise<UserHistoryResponse>}
   */
  history: () => api.get('/users/me/history').then((r) => r.data),
}
