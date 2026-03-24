import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function History() {
  const [history, setHistory] = useState({
    reviews: [],
    restaurants_added: [],
    total_reviews: 0,
    total_restaurants_added: 0,
  })
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('reviews')
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/users/me/history')
      .then(({ data }) => setHistory(data))
      .catch(() => setError('Failed to load history'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="section-title mb-6">My History</h1>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6" role="tablist">
        <button
          role="tab"
          aria-selected={tab === 'reviews'}
          onClick={() => setTab('reviews')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition
            ${tab === 'reviews' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          My Reviews ({history.total_reviews})
        </button>
        <button
          role="tab"
          aria-selected={tab === 'added'}
          onClick={() => setTab('added')}
          className={`px-5 py-2.5 text-sm font-medium border-b-2 -mb-px transition
            ${tab === 'added' ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          Restaurants Added ({history.total_restaurants_added})
        </button>
      </div>

      {error && (
        <div role="alert" className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl mb-4">
          {error}
        </div>
      )}

      {/* Reviews tab */}
      {tab === 'reviews' && (
        history.reviews.length > 0 ? (
          <div className="space-y-4">
            {history.reviews.map((rev) => (
              <article key={rev.review_id} className="card p-5">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <Link
                      to={`/restaurants/${rev.restaurant_id}`}
                      className="font-semibold text-brand-600 hover:underline"
                    >
                      {rev.restaurant_name || `Restaurant #${rev.restaurant_id}`}
                    </Link>
                    {rev.restaurant_city && (
                      <p className="text-xs text-gray-400">{rev.restaurant_city}</p>
                    )}
                    <div className="flex items-center gap-0.5 mt-1">
                      {Array.from({ length: 5 }).map((_, i) => (
                        <span key={i} className={i < rev.rating ? 'text-amber-400' : 'text-gray-300'}>★</span>
                      ))}
                    </div>
                  </div>
                  <time className="text-xs text-gray-400" dateTime={rev.created_at}>
                    {new Date(rev.created_at).toLocaleDateString('en-US', {
                      year: 'numeric', month: 'short', day: 'numeric',
                    })}
                  </time>
                </div>
                <p className="mt-2 text-sm text-gray-700">{rev.comment}</p>
                {rev.photos?.length > 0 && (
                  <div className="mt-2 flex gap-2">
                    {rev.photos.map((p, i) => (
                      <img
                        key={i}
                        src={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}${p}`}
                        alt=""
                        className="w-16 h-16 object-cover rounded-lg"
                        loading="lazy"
                      />
                    ))}
                  </div>
                )}
              </article>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-gray-500">
            <div className="text-5xl mb-3">📝</div>
            <p>
              No reviews yet.{' '}
              <Link to="/explore" className="text-brand-600 hover:underline">Find a restaurant</Link> to review!
            </p>
          </div>
        )
      )}

      {/* Restaurants added tab */}
      {tab === 'added' && (
        history.restaurants_added.length > 0 ? (
          <div className="space-y-4">
            {history.restaurants_added.map((r) => (
              <article key={r.id} className="card p-5 flex items-center gap-4">
                <div className="w-16 h-16 rounded-xl bg-brand-50 flex items-center justify-center text-2xl flex-shrink-0 overflow-hidden">
                  {r.photos?.[0] ? (
                    <img
                      src={`${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}${r.photos[0]}`}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : '🍽️'}
                </div>
                <div className="flex-1 min-w-0">
                  <Link
                    to={`/restaurants/${r.id}`}
                    className="font-semibold text-gray-900 hover:text-brand-600"
                  >
                    {r.name}
                  </Link>
                  <p className="text-sm text-gray-500">
                    {r.cuisine_type}{r.city ? ` · ${r.city}` : ''}{r.state ? `, ${r.state}` : ''}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    Added {new Date(r.created_at).toLocaleDateString()}
                    {r.is_claimed && <span className="ml-2 text-green-600 font-medium">· Claimed</span>}
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm font-semibold text-gray-900">⭐ {(r.avg_rating || 0).toFixed(1)}</div>
                  <div className="text-xs text-gray-400">{r.review_count} reviews</div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 text-gray-500">
            <div className="text-5xl mb-3">🏪</div>
            <p>
              Haven't added any restaurants yet.{' '}
              <Link to="/add-restaurant" className="text-brand-600 hover:underline">Add one now!</Link>
            </p>
          </div>
        )
      )}
    </div>
  )
}
