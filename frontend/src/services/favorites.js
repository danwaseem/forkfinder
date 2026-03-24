/**
 * favorites.js — Saved restaurant favorites
 *
 * All endpoints require authentication (Bearer token).
 *
 * Response shapes
 * ───────────────
 * FavoritesResponse:
 *   { items: Restaurant[], total: number }
 *
 * Each Restaurant includes `is_favorited: true` when returned from this endpoint.
 */
import api from './api'

export const favoritesApi = {
  /**
   * GET /favorites/me
   * Fetch all restaurants saved by the current user.
   *
   * @returns {Promise<FavoritesResponse>}
   */
  list: () => api.get('/favorites/me').then((r) => r.data),

  /**
   * POST /favorites/:restaurantId
   * Save a restaurant to favorites.
   * Returns 409 if already favorited.
   *
   * @param {number|string} restaurantId
   * @returns {Promise<{ message: string }>}
   */
  add: (restaurantId) =>
    api.post(`/favorites/${restaurantId}`).then((r) => r.data),

  /**
   * DELETE /favorites/:restaurantId
   * Remove a restaurant from favorites.
   * Returns 404 if not in favorites.
   *
   * @param {number|string} restaurantId
   * @returns {Promise<{ message: string }>}
   */
  remove: (restaurantId) =>
    api.delete(`/favorites/${restaurantId}`).then((r) => r.data),

  /**
   * Convenience toggle — calls add() or remove() based on current state.
   *
   * @param {number|string} restaurantId
   * @param {boolean} currentlyFavorited
   * @returns {Promise<{ message: string }>}
   */
  toggle: (restaurantId, currentlyFavorited) =>
    currentlyFavorited
      ? favoritesApi.remove(restaurantId)
      : favoritesApi.add(restaurantId),
}
