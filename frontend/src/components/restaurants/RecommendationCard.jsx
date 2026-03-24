/**
 * RecommendationCard
 *
 * An AI recommendation result card. Compact horizontal layout — designed
 * for inline use inside chat bubbles or a dedicated results list.
 *
 * Props:
 *   restaurant      object    — restaurant data (id, name, photos, cuisine_type,
 *                               price_range, city, avg_rating, review_count)
 *   relevanceScore  number    — 0–100 match score (optional)
 *   reasonText      string    — one-line explanation from AI (optional)
 *   onClick         () => void  — called on click (if omitted, card is a Link)
 *   size            'sm'|'md'  — thumbnail size
 *   className       string
 */
import { Link } from 'react-router-dom'
import { formatRating, imgUrl } from '../../utils/format'

function MatchBadge({ score }) {
  if (score == null) return null
  const pct = Math.round(score)
  const color = pct >= 80 ? 'text-green-700 bg-green-50 border-green-200'
    : pct >= 60 ? 'text-brand-700 bg-brand-50 border-brand-200'
    : 'text-gray-600 bg-gray-50 border-gray-200'
  return (
    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full border ${color}`}>
      {pct}% match
    </span>
  )
}

export default function RecommendationCard({
  restaurant,
  relevanceScore,
  reasonText,
  onClick,
  size = 'md',
  className = '',
}) {
  if (!restaurant) return null

  const thumbSize = size === 'sm' ? 'w-12 h-12' : 'w-16 h-16'
  const cover = restaurant.photos?.[0] ? imgUrl(restaurant.photos[0]) : null

  const inner = (
    <>
      {/* Thumbnail */}
      <div className={`${thumbSize} rounded-xl overflow-hidden bg-brand-50 flex-shrink-0`}>
        {cover ? (
          <img src={cover} alt={restaurant.name} className="w-full h-full object-cover" />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-xl">🍽️</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <p className="font-semibold text-sm text-gray-900 truncate">{restaurant.name}</p>
          <MatchBadge score={relevanceScore} />
        </div>

        <p className="text-xs text-gray-500 truncate mt-0.5">
          {[restaurant.cuisine_type, restaurant.price_range, restaurant.city]
            .filter(Boolean).join(' · ')}
        </p>

        <div className="flex items-center gap-1 mt-1">
          <span className="text-amber-400 text-xs">★</span>
          <span className="text-xs font-medium text-gray-700">{formatRating(restaurant.avg_rating)}</span>
          <span className="text-xs text-gray-400">({restaurant.review_count ?? 0})</span>
        </div>

        {reasonText && (
          <p className="text-xs text-brand-600 mt-1 truncate italic">"{reasonText}"</p>
        )}
      </div>
    </>
  )

  const sharedClass = `flex items-center gap-3 p-3 rounded-xl border border-gray-200
    hover:border-brand-300 hover:shadow-sm transition cursor-pointer bg-white ${className}`

  if (onClick) {
    return (
      <button type="button" onClick={onClick} className={`w-full text-left ${sharedClass}`}>
        {inner}
      </button>
    )
  }

  return (
    <Link to={`/restaurants/${restaurant.id}`} className={sharedClass}>
      {inner}
    </Link>
  )
}
