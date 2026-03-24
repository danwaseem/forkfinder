/** Format a price range symbol into a human label */
export const priceLabel = {
  '$': 'Budget',
  '$$': 'Mid-range',
  '$$$': 'Upscale',
  '$$$$': 'Fine dining',
}

/** Format a numeric rating to one decimal, clamped to [0, 5] */
export function formatRating(value) {
  return Math.min(5, Math.max(0, value || 0)).toFixed(1)
}

/** Format an ISO date string to a locale-friendly short date */
export function formatDate(iso, options = { year: 'numeric', month: 'short', day: 'numeric' }) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', options)
}

/** Truncate a string to maxLen characters, appending "…" if needed */
export function truncate(str, maxLen = 120) {
  if (!str) return ''
  return str.length > maxLen ? str.slice(0, maxLen) + '…' : str
}

/** Build a full image URL from a relative /uploads/... path */
export function imgUrl(path, base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000') {
  if (!path) return null
  if (path.startsWith('http')) return path
  return `${base}${path}`
}
