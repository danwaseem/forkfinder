import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ownerApi } from '../../services/owner'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import { useAuth } from '../../context/AuthContext'
import { formatDate, formatRating, imgUrl } from '../../utils/format'

function StatCard({ icon, label, value, sub }) {
  return (
    <div className="card p-5 text-center">
      <div className="text-3xl mb-1" aria-hidden="true">{icon}</div>
      <div className="text-2xl font-bold text-gray-900">{value}</div>
      <div className="text-xs text-gray-500 mt-0.5">{label}</div>
      {sub && <div className="text-xs text-gray-400 mt-0.5">{sub}</div>}
    </div>
  )
}

function SentimentBar({ label, count, total, color }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span>{count} ({pct}%)</span>
      </div>
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  )
}

const SENTIMENT_BADGE = {
  positive: 'bg-green-100 text-green-700',
  negative: 'bg-red-100 text-red-700',
  mixed: 'bg-yellow-100 text-yellow-700',
  neutral: 'bg-gray-100 text-gray-600',
}

export default function OwnerDashboard() {
  const { user } = useAuth()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    ownerApi.dashboard()
      .then(setData)
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />
  if (error) return (
    <div className="max-w-6xl mx-auto px-4 py-12 text-center text-red-600">{error}</div>
  )

  const { total_restaurants, total_reviews, avg_rating, total_favorites,
          sentiment, recent_reviews, restaurants, monthly_trend } = data

  const sentimentTotal = sentiment
    ? sentiment.positive_count + sentiment.negative_count + sentiment.neutral_count
    : 0

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-3">
        <div>
          <h1 className="section-title">Owner Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Welcome back, {user?.name}!</p>
        </div>
        <Link to="/add-restaurant" className="btn-primary">+ Add Restaurant</Link>
      </div>

      {/* KPI stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard icon="🏪" label="Restaurants" value={total_restaurants} />
        <StatCard icon="📝" label="Total Reviews" value={total_reviews} />
        <StatCard
          icon="⭐"
          label="Average Rating"
          value={avg_rating ? Number(avg_rating).toFixed(1) : '—'}
        />
        <StatCard icon="❤️" label="Total Favorites" value={total_favorites ?? '—'} />
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* My Restaurants list */}
        <section className="lg:col-span-2" aria-label="My restaurants">
          <div className="flex items-center justify-between mb-3">
            <h2 className="font-bold text-gray-900 text-lg">My Restaurants</h2>
            <Link to="/owner/restaurants" className="text-brand-600 text-sm hover:underline">
              View all →
            </Link>
          </div>
          {restaurants?.length > 0 ? (
            <div className="space-y-3">
              {restaurants.slice(0, 5).map((r) => {
                const cover = imgUrl(r.photos?.[0])
                return (
                  <Link
                    key={r.id}
                    to={`/owner/restaurants/${r.id}`}
                    className="card p-4 flex items-center gap-4 hover:shadow-md transition-shadow"
                  >
                    <div className="w-14 h-14 rounded-xl bg-brand-50 flex items-center justify-center text-2xl flex-shrink-0 overflow-hidden">
                      {cover
                        ? <img src={cover} alt="" className="w-full h-full object-cover" />
                        : '🍽️'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-gray-900 text-sm truncate">{r.name}</p>
                      <p className="text-xs text-gray-500">
                        {[r.cuisine_type, r.city].filter(Boolean).join(' · ')}
                      </p>
                      {r.is_claimed && (
                        <span className="badge bg-green-100 text-green-700 mt-0.5">✓ Claimed</span>
                      )}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-bold text-gray-900">⭐ {formatRating(r.avg_rating)}</p>
                      <p className="text-xs text-gray-400">{r.review_count} reviews</p>
                    </div>
                  </Link>
                )
              })}
            </div>
          ) : (
            <div className="card p-10 text-center text-gray-500">
              <div className="text-5xl mb-3">🏪</div>
              <p>No restaurants yet.</p>
              <Link to="/add-restaurant" className="btn-primary mt-3 inline-flex text-sm">
                Add your first restaurant
              </Link>
            </div>
          )}
        </section>

        {/* Right column: Sentiment + Recent reviews */}
        <div className="space-y-6">

          {/* Sentiment analysis */}
          {sentiment && sentimentTotal > 0 && (
            <section className="card p-5" aria-labelledby="sentiment-heading">
              <div className="flex items-center justify-between mb-3">
                <h2 id="sentiment-heading" className="font-bold text-gray-900">Review Sentiment</h2>
                <span className={`badge ${SENTIMENT_BADGE[sentiment.overall] || 'bg-gray-100 text-gray-600'}`}>
                  {sentiment.overall}
                </span>
              </div>
              <div className="space-y-2.5 mb-4">
                <SentimentBar
                  label="Positive"
                  count={sentiment.positive_count}
                  total={sentimentTotal}
                  color="bg-green-500"
                />
                <SentimentBar
                  label="Neutral"
                  count={sentiment.neutral_count}
                  total={sentimentTotal}
                  color="bg-gray-300"
                />
                <SentimentBar
                  label="Negative"
                  count={sentiment.negative_count}
                  total={sentimentTotal}
                  color="bg-red-400"
                />
              </div>
              {sentiment.top_positive_words?.length > 0 && (
                <div className="mb-2">
                  <p className="text-xs font-medium text-gray-500 mb-1">Top positive words</p>
                  <div className="flex flex-wrap gap-1">
                    {sentiment.top_positive_words.map((w) => (
                      <span key={w} className="badge bg-green-50 text-green-700">{w}</span>
                    ))}
                  </div>
                </div>
              )}
              {sentiment.top_negative_words?.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Top negative words</p>
                  <div className="flex flex-wrap gap-1">
                    {sentiment.top_negative_words.map((w) => (
                      <span key={w} className="badge bg-red-50 text-red-700">{w}</span>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {/* Recent reviews */}
          <section className="card" aria-labelledby="recent-reviews-heading">
            <div className="px-5 pt-5 pb-3">
              <h2 id="recent-reviews-heading" className="font-bold text-gray-900">Recent Reviews</h2>
            </div>
            {recent_reviews?.length > 0 ? (
              <div className="divide-y divide-gray-50">
                {recent_reviews.slice(0, 5).map((rev) => (
                  <div key={rev.id} className="px-5 py-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate">
                          {rev.user_name || 'Anonymous'}
                        </p>
                        {rev.restaurant_name && (
                          <p className="text-xs text-gray-400">on {rev.restaurant_name}</p>
                        )}
                      </div>
                      <div className="flex text-amber-400 text-xs flex-shrink-0">
                        {'★'.repeat(rev.rating)}{'☆'.repeat(5 - rev.rating)}
                      </div>
                    </div>
                    {rev.comment && (
                      <p className="text-xs text-gray-600 mt-1 line-clamp-2">{rev.comment}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">{formatDate(rev.created_at)}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="px-5 pb-5 text-sm text-gray-400">No reviews yet.</div>
            )}
          </section>
        </div>
      </div>

      {/* Monthly trend chart (simple bar chart) */}
      {monthly_trend?.length > 0 && (
        <section className="card p-6 mt-6" aria-labelledby="trend-heading">
          <h2 id="trend-heading" className="font-bold text-gray-900 mb-4">Monthly Review Trend</h2>
          <div className="flex items-end gap-2 h-24">
            {monthly_trend.map((m) => {
              const maxCount = Math.max(...monthly_trend.map((x) => x.review_count), 1)
              const heightPct = Math.round((m.review_count / maxCount) * 100)
              return (
                <div key={`${m.year}-${m.month}`} className="flex flex-col items-center flex-1 gap-1">
                  <span className="text-xs text-gray-500">{m.review_count}</span>
                  <div
                    className="w-full bg-brand-400 rounded-t-sm transition-all"
                    style={{ height: `${Math.max(heightPct, 4)}%` }}
                    title={`${m.year}-${String(m.month).padStart(2, '0')}: ${m.review_count} reviews`}
                  />
                  <span className="text-xs text-gray-400">{String(m.month).padStart(2, '0')}</span>
                </div>
              )
            })}
          </div>
        </section>
      )}
    </div>
  )
}
