/**
 * reviews.js — Review CRUD + photo upload
 *
 * Response shapes
 * ───────────────
 * Review:
 *   { id, restaurant_id, user_id, rating, comment,
 *     photos: string[],   ← relative paths
 *     created_at, updated_at,
 *     user: { id, name, profile_photo_url } }
 *
 * ReviewListResponse:
 *   { items: Review[], total: number, page: number, limit: number }
 *
 * ReviewWithStatsResponse  (returned by POST /restaurants/:id/reviews):
 *   { review: Review, restaurant_stats: { avg_rating, review_count } }
 */
import api, { makeFormData } from './api'

export const reviewsApi = {
  /**
   * GET /restaurants/:restaurantId/reviews
   * Paginated review list for a restaurant.
   *
   * @param {number|string} restaurantId
   * @param {{ page?, limit?, sort? }} params
   * @returns {Promise<ReviewListResponse>}
   */
  list: (restaurantId, params = {}) =>
    api.get(`/restaurants/${restaurantId}/reviews`, { params }).then((r) => r.data),

  /**
   * POST /restaurants/:restaurantId/reviews
   * Submit a new review. Returns the created review AND updated restaurant stats.
   *
   * @param {number|string} restaurantId
   * @param {{ rating: number, comment: string }} payload
   * @returns {Promise<ReviewWithStatsResponse>}
   */
  create: (restaurantId, payload) =>
    api.post(`/restaurants/${restaurantId}/reviews`, payload).then((r) => r.data),

  /**
   * PUT /reviews/:reviewId
   * Edit your own review.
   *
   * @param {number|string} reviewId
   * @param {{ rating?: number, comment?: string }} payload
   * @returns {Promise<Review>}
   */
  update: (reviewId, payload) =>
    api.put(`/reviews/${reviewId}`, payload).then((r) => r.data),

  /**
   * DELETE /reviews/:reviewId
   * Delete your own review.
   *
   * @param {number|string} reviewId
   * @returns {Promise<void>}
   */
  delete: (reviewId) =>
    api.delete(`/reviews/${reviewId}`).then((r) => r.data),

  /**
   * POST /reviews/:reviewId/photos
   * Attach a photo to an existing review.
   * Returns the updated Review object.
   *
   * @param {number|string} reviewId
   * @param {File} file
   * @returns {Promise<Review>}
   */
  uploadPhoto: (reviewId, file) =>
    api.post(`/reviews/${reviewId}/photos`, makeFormData(file)).then((r) => r.data),
}
