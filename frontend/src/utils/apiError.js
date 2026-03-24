/**
 * apiError.js — Consistent error normalization for FastAPI responses
 *
 * FastAPI can return errors in several shapes:
 *   1. { detail: "string message" }                     — HTTPException
 *   2. { detail: [{ msg, loc, type }] }                 — RequestValidationError (422)
 *   3. { success: false, error: { message: "…" } }      — our custom envelope
 *   4. { message: "…" }                                 — fallback
 *
 * All helpers below normalize these into a single readable string so callers
 * never need to branch on the shape themselves.
 */

// ─── Shape extractors ────────────────────────────────────────────────────────

/**
 * Pull a human-readable message out of a FastAPI response data object.
 * Returns null if nothing recognizable is found.
 *
 * @param {unknown} data — the value of err.response.data
 * @returns {string | null}
 */
export function extractDetail(data) {
  if (!data || typeof data !== 'object') return null

  // Shape 2 — validation array: pick the first message
  if (Array.isArray(data.detail)) {
    const msgs = data.detail
      .map((e) => e.msg || e.message || String(e))
      .filter(Boolean)
    return msgs.length ? msgs.join('; ') : null
  }

  // Shape 1 — string detail
  if (typeof data.detail === 'string' && data.detail) return data.detail

  // Shape 3 — our envelope
  if (typeof data.error?.message === 'string' && data.error.message)
    return data.error.message

  // Shape 4 — plain message
  if (typeof data.message === 'string' && data.message) return data.message

  return null
}

/**
 * Get a display-ready error message from any thrown Axios error.
 *
 * @param {unknown} err
 * @param {string}  fallback
 * @returns {string}
 */
export function getErrorMessage(err, fallback = 'Something went wrong') {
  if (!err) return fallback
  return extractDetail(err?.response?.data) || err?.message || fallback
}

// ─── Status predicates ───────────────────────────────────────────────────────

/** 400 Bad Request */
export const isBadRequest    = (err) => err?.response?.status === 400
/** 401 Unauthorized — session expired / bad credentials */
export const isUnauthorized  = (err) => err?.response?.status === 401
/** 403 Forbidden — authenticated but lacks permission */
export const isForbidden     = (err) => err?.response?.status === 403
/** 404 Not Found */
export const isNotFound      = (err) => err?.response?.status === 404
/** 409 Conflict — e.g. duplicate email, already claimed */
export const isConflict      = (err) => err?.response?.status === 409
/** 422 Unprocessable Entity — FastAPI RequestValidationError */
export const isValidation    = (err) => err?.response?.status === 422
/** 5xx Server Error */
export const isServerError   = (err) => (err?.response?.status ?? 0) >= 500
/** No response at all — network offline or server unreachable */
export const isNetworkError  = (err) => !err?.response && !!err?.request

// ─── Structured error for re-throw ──────────────────────────────────────────

/**
 * ApiError — a thin wrapper you can throw instead of the raw Axios error.
 * Useful when you want to catch specific error categories in components.
 *
 * Usage:
 *   try { await restaurantsApi.create(data) }
 *   catch (err) {
 *     const ae = ApiError.from(err)
 *     if (ae.status === 409) toast.error('Restaurant already exists')
 *     else toast.error(ae.message)
 *   }
 */
export class ApiError extends Error {
  /**
   * @param {string} message   — human-readable message
   * @param {number} status    — HTTP status code (0 for network errors)
   * @param {unknown} data     — raw response data
   * @param {unknown} original — original Axios error
   */
  constructor(message, status = 0, data = null, original = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
    this.original = original
  }

  static from(err, fallback = 'Something went wrong') {
    const message = getErrorMessage(err, fallback)
    const status  = err?.response?.status ?? 0
    const data    = err?.response?.data ?? null
    return new ApiError(message, status, data, err)
  }

  get isNotFound()    { return this.status === 404 }
  get isConflict()    { return this.status === 409 }
  get isValidation()  { return this.status === 422 }
  get isUnauthorized(){ return this.status === 401 }
  get isForbidden()   { return this.status === 403 }
  get isNetwork()     { return this.status === 0 }
  get isServer()      { return this.status >= 500 }
}
