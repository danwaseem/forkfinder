/**
 * ChatRecommendationCard
 *
 * Rich restaurant card designed for inline display inside a chat thread.
 * Full-width horizontal layout with photo, rating stars, match badge,
 * price tag, and optional AI reason text.
 *
 * Props:
 *   restaurant      object   — restaurant data
 *   relevanceScore  number   — 0–100 match percentage (optional)
 *   reasonText      string   — one-line AI explanation (optional)
 *   onNavigate      () => void  — called when user taps the card (for FAB to close panel)
 */
import { Link } from 'react-router-dom'
import { imgUrl } from '../../utils/format'

const PRICE_COLORS = {
  '$':    'text-green-700 bg-green-50',
  '$$':   'text-amber-700 bg-amber-50',
  '$$$':  'text-orange-700 bg-orange-50',
  '$$$$': 'text-red-700 bg-red-50',
}

function MatchBadge({ score }) {
  if (score == null) return null
  const pct = Math.round(score)
  const cls = pct >= 80
    ? 'bg-green-100 text-green-700 border-green-200'
    : pct >= 60
      ? 'bg-brand-50 text-brand-700 border-brand-200'
      : 'bg-gray-100 text-gray-600 border-gray-200'
  return (
    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-full border ${cls}`}>
      {pct}% match
    </span>
  )
}

function StarRow({ rating, reviewCount }) {
  const r     = Math.min(5, Math.max(0, rating || 0))
  const full  = Math.floor(r)
  const empty = 5 - full
  return (
    <div className="flex items-center gap-1">
      <span className="text-amber-400 text-xs leading-none">
        {'★'.repeat(full)}<span className="text-gray-300">{'★'.repeat(empty)}</span>
      </span>
      <span className="text-xs font-semibold text-gray-800">{r.toFixed(1)}</span>
      {reviewCount != null && (
        <span className="text-[11px] text-gray-400">({reviewCount})</span>
      )}
    </div>
  )
}

export default function ChatRecommendationCard({
  restaurant: r,
  relevanceScore,
  reasonText,
  onNavigate,
}) {
  if (!r) return null
  const cover = r.photos?.[0] ? imgUrl(r.photos[0]) : null

  return (
    <Link
      to={`/restaurants/${r.id}`}
      onClick={onNavigate}
      className="flex items-start gap-3 p-3 rounded-xl border border-gray-200 bg-white
                 hover:border-brand-300 hover:shadow-sm active:scale-[0.99]
                 transition-all cursor-pointer group"
    >
      {/* Photo */}
      <div className="w-14 h-14 rounded-lg overflow-hidden bg-brand-50 flex-shrink-0 mt-0.5">
        {cover ? (
          <img
            src={cover}
            alt={r.name}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-2xl">🍽️</div>
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        {/* Name + badges row */}
        <div className="flex items-start justify-between gap-1.5 flex-wrap">
          <p className="font-semibold text-sm text-gray-900 leading-tight truncate flex-1">
            {r.name}
          </p>
          <div className="flex items-center gap-1 flex-shrink-0">
            {r.price_range && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${PRICE_COLORS[r.price_range] || 'bg-gray-100 text-gray-600'}`}>
                {r.price_range}
              </span>
            )}
            <MatchBadge score={relevanceScore} />
          </div>
        </div>

        {/* Stars */}
        <div className="mt-0.5">
          <StarRow rating={r.avg_rating} reviewCount={r.review_count} />
        </div>

        {/* Cuisine + city */}
        <p className="text-[11px] text-gray-500 mt-0.5 truncate">
          {[r.cuisine_type, r.city, r.state].filter(Boolean).join(' · ')}
        </p>

        {/* AI reason text */}
        {reasonText && (
          <p className="text-[11px] text-brand-600 italic mt-1 line-clamp-1">
            "{reasonText}"
          </p>
        )}
      </div>

      {/* Arrow */}
      <svg
        className="w-4 h-4 text-gray-300 group-hover:text-brand-400 transition flex-shrink-0 mt-1"
        fill="none" viewBox="0 0 24 24" stroke="currentColor"
      >
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
      </svg>
    </Link>
  )
}
