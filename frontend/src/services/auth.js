/**
 * auth.js — Authentication API
 *
 * Wraps /auth/* endpoints.
 * AuthContext imports these functions — components should not call them directly.
 *
 * Response shape for login / register (TokenResponse):
 *   {
 *     access_token: string
 *     token_type:   "bearer"
 *     id:           number
 *     name:         string
 *     email:        string
 *     role:         "user" | "owner"
 *     profile_photo_url: string | null
 *   }
 */
import api from './api'

// ─── Typed endpoint wrappers ──────────────────────────────────────────────────

/**
 * Log in as a regular user.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<TokenResponse>}
 */
const loginUser = (email, password) =>
  api.post('/auth/user/login', { email, password }).then((r) => r.data)

/**
 * Log in as a restaurant owner.
 * @param {string} email
 * @param {string} password
 * @returns {Promise<TokenResponse>}
 */
const loginOwner = (email, password) =>
  api.post('/auth/owner/login', { email, password }).then((r) => r.data)

/**
 * Register a new diner account.
 * @param {string} name
 * @param {string} email
 * @param {string} password
 * @returns {Promise<TokenResponse>}
 */
const registerUser = (name, email, password) =>
  api.post('/auth/user/signup', { name, email, password }).then((r) => r.data)

/**
 * Register a new owner account.
 * @param {string} name
 * @param {string} email
 * @param {string} password
 * @returns {Promise<TokenResponse>}
 */
const registerOwner = (name, email, password) =>
  api.post('/auth/owner/signup', { name, email, password }).then((r) => r.data)

// ─── Public API ───────────────────────────────────────────────────────────────

export const authApi = {
  loginUser,
  loginOwner,
  registerUser,
  registerOwner,

  /**
   * Role-dispatched login.
   * @param {string} email
   * @param {string} password
   * @param {'user'|'owner'} role
   */
  login: (email, password, role = 'user') =>
    role === 'owner' ? loginOwner(email, password) : loginUser(email, password),

  /**
   * Role-dispatched registration.
   * @param {string} name
   * @param {string} email
   * @param {string} password
   * @param {'user'|'owner'} role
   */
  register: (name, email, password, role = 'user') =>
    role === 'owner'
      ? registerOwner(name, email, password)
      : registerUser(name, email, password),

  /**
   * Fetch the current user's profile from the token.
   * Useful for re-hydrating state on app startup.
   *
   * Response: UserResponse (same fields as TokenResponse minus access_token)
   */
  me: () => api.get('/users/me').then((r) => r.data),
}
