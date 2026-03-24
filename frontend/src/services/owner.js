/**
 * owner.js — Owner-specific endpoints
 *
 * All endpoints require authentication as an owner (role === 'owner').
 * The backend enforces this; components should also gate on user.role.
 *
 * Response shapes
 * ───────────────
 * OwnerDashboardResponse:
 *   {
 *     total_restaurants:  number
 *     total_reviews:      number
 *     avg_rating:         number
 *     total_favorites:    number
 *     sentiment: {
 *       overall:            "positive"|"negative"|"mixed"|"neutral"
 *       positive_count:     number
 *       negative_count:     number
 *       neutral_count:      number
 *       top_positive_words: string[]
 *       top_negative_words: string[]
 *     }
 *     recent_reviews:     OwnerReviewItem[]
 *     restaurants:        Restaurant[]
 *     monthly_trend:      { year: number, month: number, review_count: number }[]
 *   }
 *
 * OwnerRestaurantsListResponse:
 *   { items: Restaurant[], total: number }
 *
 * OwnerReviewsListResponse:
 *   { items: OwnerReviewItem[], total: number }
 *
 * OwnerReviewItem:
 *   { id, restaurant_id, user_id, user_name, rating, comment,
 *     photos, created_at, restaurant_name? }
 *
 * OwnerRestaurantStatsResponse:
 *   { avg_rating, review_count, monthly_trend, sentiment }
 */
import api, { makeFormData } from './api'

export const ownerApi = {
  // ── Dashboard ──────────────────────────────────────────────────────────────

  /**
   * GET /owner/dashboard
   * Aggregate stats, sentiment analysis, recent reviews, restaurant list,
   * and monthly review trend — all in a single round-trip.
   *
   * @returns {Promise<OwnerDashboardResponse>}
   */
  dashboard: () => api.get('/owner/dashboard').then((r) => r.data),

  // ── Restaurants ────────────────────────────────────────────────────────────

  /**
   * GET /owner/restaurants
   * Paginated list of all restaurants owned or claimed by the current owner.
   *
   * @param {{ page?, limit?, sort? }} params
   * @returns {Promise<OwnerRestaurantsListResponse>}
   */
  restaurants: (params = {}) =>
    api.get('/owner/restaurants', { params }).then((r) => r.data),

  /**
   * PUT /owner/restaurants/:id
   * Update a restaurant managed by the current owner.
   *
   * @param {number|string} id
   * @param {Partial<Restaurant>} payload
   * @returns {Promise<Restaurant>}
   */
  updateRestaurant: (id, payload) =>
    api.put(`/owner/restaurants/${id}`, payload).then((r) => r.data),

  /**
   * POST /owner/restaurants/:id/photos
   * Upload a photo for an owned restaurant.
   *
   * @param {number|string} id
   * @param {File} file
   * @returns {Promise<Restaurant>}
   */
  uploadRestaurantPhoto: (id, file) =>
    api.post(`/owner/restaurants/${id}/photos`, makeFormData(file)).then((r) => r.data),

  /**
   * GET /owner/restaurants/:id/reviews
   * Paginated reviews for a single owned restaurant.
   *
   * @param {number|string} id
   * @param {{ page?, limit?, sort? }} params
   * @returns {Promise<OwnerReviewsListResponse>}
   */
  restaurantReviews: (id, params = {}) =>
    api.get(`/owner/restaurants/${id}/reviews`, { params }).then((r) => r.data),

  /**
   * GET /owner/restaurants/:id/stats
   * Per-restaurant analytics: rating distribution, monthly trend, sentiment.
   *
   * @param {number|string} id
   * @returns {Promise<OwnerRestaurantStatsResponse>}
   */
  restaurantStats: (id) =>
    api.get(`/owner/restaurants/${id}/stats`).then((r) => r.data),

  /**
   * POST /owner/restaurants/:id/claim
   * Claim an unclaimed restaurant.
   * Also accessible via POST /restaurants/:id/claim (public endpoint).
   *
   * @param {number|string} id
   * @returns {Promise<Restaurant>}
   */
  claimRestaurant: (id) =>
    api.post(`/owner/restaurants/${id}/claim`).then((r) => r.data),

  // ── Reviews (cross-restaurant) ─────────────────────────────────────────────

  /**
   * GET /owner/reviews
   * Recent reviews across all restaurants owned by the current owner.
   *
   * @param {{ page?, limit?, restaurant_id?, min_rating? }} params
   * @returns {Promise<OwnerReviewsListResponse>}
   */
  reviews: (params = {}) =>
    api.get('/owner/reviews', { params }).then((r) => r.data),

  // ── Owner profile ──────────────────────────────────────────────────────────

  /**
   * GET /owner/me
   * The owner's own profile (same shape as UserResponse plus business fields).
   *
   * @returns {Promise<OwnerProfileResponse>}
   */
  profile: () => api.get('/owner/me').then((r) => r.data),

  /**
   * PUT /owner/me
   * Update the owner's profile.
   *
   * @param {Partial<OwnerProfileResponse>} payload
   * @returns {Promise<OwnerProfileResponse>}
   */
  updateProfile: (payload) =>
    api.put('/owner/me', payload).then((r) => r.data),

  /**
   * POST /owner/me/photo
   * Upload / replace the owner's profile photo.
   *
   * @param {File} file
   * @returns {Promise<{ profile_photo_url: string }>}
   */
  uploadPhoto: (file) =>
    api.post('/owner/me/photo', makeFormData(file)).then((r) => r.data),
}
