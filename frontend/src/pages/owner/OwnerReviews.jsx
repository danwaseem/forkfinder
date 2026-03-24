import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ownerApi } from '../../services/owner'
import { formatRating, formatDate, imgUrl } from '../../utils/format'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import { StarDisplay } from '../../components/common/StarRating'

const RATING_OPTIONS = ['All', '5', '4', '3', '2', '1']

export default function OwnerReviews() {
  const [reviews, setReviews] = useState([])
  const [restaurants, setRestaurants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters
  const [filterRestaurant, setFilterRestaurant] = useState('')
  const [filterRating, setFilterRating] = useState('All')

  useEffect(() => {
    Promise.all([ownerApi.reviews(), ownerApi.restaurants()])
      .then(([revData, restData]) => {
        setReviews(revData.items || [])
        setRestaurants(restData.items || [])
      })
      .catch(() => setError('Failed to load reviews'))
      .finally(() => setLoading(false))
  }, [])

  const filtered = reviews.filter((r) => {
    const matchRest = !filterRestaurant || String(r.restaurant_id) === filterRestaurant
    const matchRating = filterRating === 'All' || r.rating === parseInt(filterRating)
    return matchRest && matchRating
  })

  // Sentiment summary per restaurant
  const sentimentMap = reviews.reduce((acc, r) => {
    const key = r.restaurant_id
    if (!acc[key]) acc[key] = { pos: 0, neg: 0, neu: 0 }
    if (r.rating >= 4) acc[key].pos++
    else if (r.rating <= 2) acc[key].neg++
    else acc[key].neu++
    return acc
  }, {})

  if (loading) return <LoadingSpinner fullPage />

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="section-title">Reviews Dashboard</h1>
        <span className="text-sm text-gray-500">{reviews.length} total review{reviews.length !== 1 ? 's' : ''}</span>
      </div>

      {error && (
        <div role="alert" className="p-4 mb-6 bg-red-50 border border-red-200 text-red-700 rounded-xl">
          {error}
        </div>
      )}

      {/* Sentiment overview */}
      {restaurants.length > 0 && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {restaurants.map((rest) => {
            const s = sentimentMap[rest.id] || { pos: 0, neg: 0, neu: 0 }
            const total = s.pos + s.neg + s.neu
            return (
              <div key={rest.id} className="card p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-50 overflow-hidden flex-shrink-0">
                    {rest.photos?.[0] ? (
                      <img src={imgUrl(rest.photos[0])} alt={rest.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-lg">🍽️</div>
                    )}
                  </div>
                  <div className="min-w-0">
                    <Link to={`/owner/restaurants/${rest.id}`} className="font-semibold text-sm text-gray-900 hover:text-brand-600 truncate block">
                      {rest.name}
                    </Link>
                    <StarDisplay rating={rest.avg_rating} reviewCount={rest.review_count} size="sm" />
                  </div>
                </div>
                {total > 0 ? (
                  <div className="space-y-1.5">
                    {[
                      { label: 'Positive', count: s.pos, color: 'bg-green-500', textColor: 'text-green-700' },
                      { label: 'Neutral', count: s.neu, color: 'bg-yellow-400', textColor: 'text-yellow-700' },
                      { label: 'Negative', count: s.neg, color: 'bg-red-500', textColor: 'text-red-700' },
                    ].map(({ label, count, color, textColor }) => (
                      <div key={label} className="flex items-center gap-2 text-xs">
                        <span className={`w-16 ${textColor}`}>{label}</span>
                        <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            className={`h-full ${color} rounded-full transition-all`}
                            style={{ width: total > 0 ? `${(count / total) * 100}%` : '0%' }}
                          />
                        </div>
                        <span className="w-6 text-right text-gray-500">{count}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-gray-400">No reviews yet</p>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <select
          value={filterRestaurant}
          onChange={(e) => setFilterRestaurant(e.target.value)}
          className="input py-2 pr-8 text-sm w-auto"
          aria-label="Filter by restaurant"
        >
          <option value="">All restaurants</option>
          {restaurants.map((r) => (
            <option key={r.id} value={String(r.id)}>{r.name}</option>
          ))}
        </select>

        <div className="flex gap-1" role="group" aria-label="Filter by rating">
          {RATING_OPTIONS.map((opt) => (
            <button
              key={opt}
              onClick={() => setFilterRating(opt)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition ${
                filterRating === opt
                  ? 'bg-brand-600 text-white border-brand-600'
                  : 'border-gray-200 text-gray-600 hover:border-brand-300'
              }`}
            >
              {opt === 'All' ? 'All' : `${opt}★`}
            </button>
          ))}
        </div>

        {(filterRestaurant || filterRating !== 'All') && (
          <button
            onClick={() => { setFilterRestaurant(''); setFilterRating('All') }}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Review list */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-gray-500 card p-8">
          <div className="text-4xl mb-3">📝</div>
          <p>{reviews.length === 0 ? 'No reviews yet across your restaurants.' : 'No reviews match your filters.'}</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filtered.map((rev) => {
            const rest = restaurants.find((r) => r.id === rev.restaurant_id)
            return (
              <article key={rev.id} className="card p-5">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div className="flex items-center gap-3">
                    {/* Reviewer avatar */}
                    <div className="w-9 h-9 rounded-full bg-brand-100 text-brand-700 font-bold text-sm flex items-center justify-center flex-shrink-0">
                      {rev.user_name?.[0]?.toUpperCase() || '?'}
                    </div>
                    <div>
                      <p className="font-semibold text-sm text-gray-900">{rev.user_name || 'Anonymous'}</p>
                      <div className="flex items-center gap-0.5 mt-0.5">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <span key={i} className={`text-sm ${i < rev.rating ? 'text-amber-400' : 'text-gray-300'}`}>★</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    {rest && (
                      <Link to={`/owner/restaurants/${rest.id}`} className="text-xs font-medium text-brand-600 hover:underline block">
                        {rest.name}
                      </Link>
                    )}
                    <time className="text-xs text-gray-400 block mt-0.5" dateTime={rev.created_at}>
                      {formatDate(rev.created_at)}
                    </time>
                  </div>
                </div>

                <p className="mt-3 text-sm text-gray-700 leading-relaxed">{rev.comment}</p>

                {rev.photos?.length > 0 && (
                  <div className="mt-3 flex gap-2 flex-wrap">
                    {rev.photos.map((p, i) => (
                      <img
                        key={i}
                        src={imgUrl(p)}
                        alt=""
                        className="w-16 h-16 rounded-lg object-cover"
                        loading="lazy"
                      />
                    ))}
                  </div>
                )}

                {/* Sentiment badge */}
                <div className="mt-3">
                  {rev.rating >= 4 ? (
                    <span className="badge bg-green-100 text-green-700 text-xs">Positive</span>
                  ) : rev.rating <= 2 ? (
                    <span className="badge bg-red-100 text-red-700 text-xs">Negative</span>
                  ) : (
                    <span className="badge bg-yellow-100 text-yellow-700 text-xs">Neutral</span>
                  )}
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
