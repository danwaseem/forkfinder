/**
 * api.js — Axios instance + interceptors
 *
 * Single source of truth for all HTTP calls.
 * Import this file (or a named service module) everywhere instead of
 * importing axios directly.
 *
 * Named exports:
 *   api          — the configured Axios instance (default export too)
 *   tokenStore   — helpers to get/set/clear the JWT in localStorage
 *   makeFormData — convenience wrapper for file uploads
 */
import axios from 'axios'
import toast from 'react-hot-toast'
import { extractDetail } from '../utils/apiError'

// ─── Base URL from environment ────────────────────────────────────────────────
//  Set VITE_API_BASE_URL in .env (or .env.local for local overrides).
//  Falls back to localhost:8000 for local dev without a .env file.
const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

// ─── Token storage ────────────────────────────────────────────────────────────
const TOKEN_KEY = 'token'
const USER_KEY  = 'user'

export const tokenStore = {
  /** Read the stored JWT string (or null). */
  get: () => localStorage.getItem(TOKEN_KEY),

  /** Persist a JWT and the full user object (pass null for userObj to skip). */
  set: (token, userObj = null) => {
    localStorage.setItem(TOKEN_KEY, token)
    if (userObj !== null) {
      localStorage.setItem(USER_KEY, JSON.stringify(userObj))
    }
  },

  /** Remove both the token and cached user object. */
  clear: () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    delete api.defaults.headers.common['Authorization']
  },
}

// ─── FormData helper (file uploads) ───────────────────────────────────────────
/**
 * Wrap a File in a FormData object.
 * @param {File}   file
 * @param {string} field — form field name (default: 'file')
 * @returns {FormData}
 */
export function makeFormData(file, field = 'file') {
  const fd = new FormData()
  fd.append(field, file)
  return fd
}

// ─── Axios instance ───────────────────────────────────────────────────────────
export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Request interceptor — attach JWT ────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    const token = tokenStore.get()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    // For FormData (file uploads), remove the instance-level Content-Type so the
    // browser sets multipart/form-data with the correct boundary automatically.
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (err) => Promise.reject(err),
)

// ─── Auth endpoints — expected 401 (wrong password, etc.) ────────────────────
// These should NOT trigger the "session expired" global toast.
const SILENT_AUTH_PATHS = [
  '/auth/user/login',
  '/auth/owner/login',
  '/auth/user/signup',
  '/auth/owner/signup',
]

const isSilentAuth = (url = '') =>
  SILENT_AUTH_PATHS.some((p) => url.includes(p))

// ─── Response interceptor — normalize errors + global toasts ─────────────────
api.interceptors.response.use(
  // Pass-through on success
  (res) => res,

  (err) => {
    const status = err.response?.status
    const data   = err.response?.data
    const url    = err.config?.url ?? ''

    // ── 1. Normalize the error payload ───────────────────────────────────────
    //  Write a unified `detail` field so every caller can do:
    //    err.response?.data?.detail
    //  regardless of the original error shape.
    if (data) {
      const normalized = extractDetail(data)
      if (normalized) data.detail = normalized
    }

    // ── 2. Per-status side effects ───────────────────────────────────────────
    if (!err.response) {
      // Network error (offline, DNS failure, server down) or timeout
      if (err.code === 'ECONNABORTED') {
        toast.error('Request timed out — check your connection.')
      } else {
        toast.error('Network error — are you connected?')
      }
    } else if (status === 401 && !isSilentAuth(url)) {
      // Expired or revoked token; clear auth state and notify the user.
      // Auth login/signup endpoints are excluded (wrong password is not a session expiry).
      tokenStore.clear()
      toast.error('Session expired. Please log in again.')
    } else if (status === 403) {
      toast.error("You don't have permission to do that.")
    } else if (status === 429) {
      toast.error('Too many requests — please slow down.')
    } else if (status >= 500) {
      toast.error('Server error — please try again later.')
    }
    // 4xx errors (400, 404, 409, 422) are intentionally NOT toasted here —
    // the calling component handles them with context-specific messages.

    return Promise.reject(err)
  },
)

export default api
