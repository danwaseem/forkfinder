/**
 * restaurants.js — Restaurant CRUD + photos + claim
 *
 * Response shapes
 * ───────────────
 * Restaurant:
 *   { id, name, description, address, city, state, country,
 *     phone, website, cuisine_type, price_range, hours,
 *     photos: string[],   ← relative paths, prefix with VITE_API_BASE_URL
 *     avg_rating, review_count, is_claimed, claimed_by,
 *     created_by, is_favorited, created_at }
 *
 * RestaurantListResponse:
 *   { items: Restaurant[], total: number, page: number, limit: number }
 *
 * List query params (all optional):
 *   q             — full-text search (name / description / cuisine)
 *   cuisine       — exact match
 *   price_range   — "$" | "$$" | "$$$" | "$$$$"
 *   min_rating    — minimum avg_rating
 *   city          — partial match
 *   claimed       — true | false
 *   sort          — "rating" | "newest" | "distance"
 *   page          — 1-based (default: 1)
 *   limit         — per page (default: 20)
 */
import api, { makeFormData } from './api'

export const restaurantsApi = {
  /**
   * GET /restaurants
   * Paginated, filterable list of all restaurants.
   *
   * @param {{ q?, cuisine?, price_range?, min_rating?, city?, claimed?,
   *            sort?, page?, limit? }} params
   * @returns {Promise<RestaurantListResponse>}
   */
  list: (params = {}) =>
    api.get('/restaurants', { params }).then((r) => r.data),

  /**
   * GET /restaurants/:id
   * Single restaurant with full details.
   * Includes `is_favorited` when the user is authenticated.
   *
   * @param {number|string} id
   * @returns {Promise<Restaurant>}
   */
  get: (id) => api.get(`/restaurants/${id}`).then((r) => r.data),

  /**
   * POST /restaurants
   * Create a new restaurant listing.
   *
   * @param {{ name, description?, address?, city?, state?, country?,
   *            phone?, website?, cuisine_type?, price_range?,
   *            hours?: object }} payload
   * @returns {Promise<Restaurant>}
   */
  create: (payload) =>
    api.post('/restaurants', payload).then((r) => r.data),

  /**
   * PUT /restaurants/:id
   * Update a restaurant's details.
   * Only the authenticated creator / claimer can update.
   *
   * @param {number|string} id
   * @param {Partial<Restaurant>} payload
   * @returns {Promise<Restaurant>}
   */
  update: (id, payload) =>
    api.put(`/restaurants/${id}`, payload).then((r) => r.data),

  /**
   * DELETE /restaurants/:id
   * Remove a restaurant listing.
   * Only the authenticated creator can delete.
   *
   * @param {number|string} id
   * @returns {Promise<void>}
   */
  delete: (id) => api.delete(`/restaurants/${id}`).then((r) => r.data),

  /**
   * POST /restaurants/:id/photos
   * Upload a photo and append it to the restaurant's photo list.
   * Returns the updated Restaurant object.
   *
   * @param {number|string} id
   * @param {File} file
   * @returns {Promise<Restaurant>}
   */
  uploadPhoto: (id, file) =>
    api.post(`/restaurants/${id}/photos`, makeFormData(file)).then((r) => r.data),

  /**
   * POST /restaurants/:id/claim
   * Claim an unclaimed restaurant listing (owner role required).
   *
   * @param {number|string} id
   * @returns {Promise<Restaurant>}
   */
  claim: (id) => api.post(`/restaurants/${id}/claim`).then((r) => r.data),
}
