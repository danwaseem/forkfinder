/**
 * history.js — User activity history
 *
 * Thin wrapper kept for backward compatibility with components that
 * import { historyApi } directly. The underlying call is the same
 * as usersApi.history().
 *
 * Response shape (UserHistoryResponse):
 *   {
 *     reviews:                ReviewHistoryItem[]
 *     restaurants_added:      Restaurant[]
 *     total_reviews:          number
 *     total_restaurants_added: number
 *   }
 *
 * ReviewHistoryItem:
 *   { review_id, restaurant_id, restaurant_name, restaurant_city,
 *     rating, comment, created_at, photos: string[] }
 */
import api from './api'

export const historyApi = {
  /**
   * GET /users/me/history
   * Returns the user's review history and restaurants they've added.
   *
   * @returns {Promise<UserHistoryResponse>}
   */
  get: () => api.get('/users/me/history').then((r) => r.data),
}
