/**
 * StarRating  — interactive star picker
 * StarDisplay — compact read-only rating display
 */

export default function StarRating({ rating, onRate, max = 5, size = 'md' }) {
  const sizes   = { sm: 'text-lg', md: 'text-2xl', lg: 'text-3xl' }
  const readOnly = !onRate

  return (
    <div
      className={`flex gap-0.5 ${sizes[size]}`}
      role={readOnly ? 'img' : 'group'}
      aria-label={readOnly ? `${rating} out of ${max} stars` : 'Star rating selector'}
    >
      {Array.from({ length: max }, (_, i) => {
        const filled = i < Math.round(rating)
        return (
          <button
            key={i}
            type="button"
            aria-label={`Rate ${i + 1} star${i !== 0 ? 's' : ''}`}
            onClick={() => onRate?.(i + 1)}
            disabled={readOnly}
            className={`leading-none transition-colors
              ${filled ? 'text-amber-400' : 'text-gray-200'}
              ${readOnly
                ? 'cursor-default'
                : 'cursor-pointer hover:text-amber-300 hover:scale-110 transition-transform'
              }
              focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 rounded
            `}
          >
            ★
          </button>
        )
      })}
    </div>
  )
}

/**
 * Props:
 *   rating        number
 *   reviewCount   number   — omit to hide
 *   size          'xs'|'sm'|'md'|'lg'
 *   showEmpty     boolean
 */
export function StarDisplay({ rating, reviewCount, size = 'sm', showEmpty = false }) {
  const textSz  = { xs: 'text-[10px]', sm: 'text-xs', md: 'text-sm', lg: 'text-base' }
  const starSz  = { xs: 'text-xs',     sm: 'text-sm', md: 'text-base', lg: 'text-lg' }

  const r     = Math.min(5, Math.max(0, rating || 0))
  const full  = Math.floor(r)
  const half  = r - full >= 0.25 && r - full < 0.75
  const empty = 5 - full - (half ? 1 : 0)

  if (showEmpty && (!reviewCount || reviewCount === 0)) {
    return <span className={`${textSz[size]} text-gray-400`}>No reviews yet</span>
  }

  return (
    <div className="flex items-center gap-1.5">
      <span className={`${starSz[size]} leading-none`} aria-hidden="true">
        <span className="text-amber-400">{'★'.repeat(full)}{half ? '½' : ''}</span>
        <span className="text-gray-200">{'★'.repeat(empty)}</span>
      </span>
      <span className={`font-semibold text-gray-900 ${textSz[size]}`}>{r.toFixed(1)}</span>
      {reviewCount !== undefined && (
        <span className={`text-gray-500 ${textSz[size]}`}>
          ({reviewCount.toLocaleString()} {reviewCount === 1 ? 'review' : 'reviews'})
        </span>
      )}
    </div>
  )
}
