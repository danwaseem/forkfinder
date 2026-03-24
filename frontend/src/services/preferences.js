/**
 * preferences.js — User dining preferences
 *
 * All endpoints require authentication (Bearer token).
 *
 * Response / payload shape (UserPreferencesOut):
 *   {
 *     cuisine_preferences:   string[]  — e.g. ["Italian", "Sushi"]
 *     price_range:           string    — "$" | "$$" | "$$$" | "$$$$" | ""
 *     search_radius:         number    — miles (1–100)
 *     dietary_restrictions:  string[]  — e.g. ["Vegan", "Gluten-Free"]
 *     ambiance_preferences:  string[]  — e.g. ["Cozy", "Outdoor"]
 *     sort_preference:       string    — "rating" | "distance" | "newest"
 *   }
 */
import api from './api'

export const preferencesApi = {
  /**
   * GET /preferences/me
   * Fetch the authenticated user's dining preferences.
   * Returns sensible defaults if the user has never saved preferences.
   *
   * @returns {Promise<UserPreferencesOut>}
   */
  get: () => api.get('/preferences/me').then((r) => r.data),

  /**
   * PUT /preferences/me
   * Save / overwrite the authenticated user's dining preferences.
   * Send the full object (all fields are replaced on each PUT).
   *
   * @param {UserPreferencesOut} payload
   * @returns {Promise<UserPreferencesOut>}
   */
  update: (payload) =>
    api.put('/preferences/me', payload).then((r) => r.data),

  /**
   * Reset preferences to defaults by sending an empty object.
   * @returns {Promise<UserPreferencesOut>}
   */
  reset: () =>
    api.put('/preferences/me', {
      cuisine_preferences:  [],
      price_range:          '',
      search_radius:        10,
      dietary_restrictions: [],
      ambiance_preferences: [],
      sort_preference:      'rating',
    }).then((r) => r.data),
}
