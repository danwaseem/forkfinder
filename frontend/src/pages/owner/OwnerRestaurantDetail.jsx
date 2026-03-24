import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ownerApi } from '../../services/owner'
import { restaurantsApi } from '../../services/restaurants'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import { formatDate, formatRating } from '../../utils/format'
import toast from 'react-hot-toast'

const SENTIMENT_BADGE = {
  positive: 'bg-green-100 text-green-700',
  negative: 'bg-red-100 text-red-700',
  mixed: 'bg-yellow-100 text-yellow-700',
  neutral: 'bg-gray-100 text-gray-600',
}

const CUISINES = [
  '', 'American', 'Italian', 'Mexican', 'Japanese', 'Chinese', 'Indian', 'Thai',
  'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek', 'Spanish', 'Seafood',
  'Vegan', 'Vegetarian', 'BBQ', 'Fusion',
]
const PRICE_RANGES = ['', '$', '$$', '$$$', '$$$$']

export default function OwnerRestaurantDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [stats, setStats] = useState(null)
  const [reviews, setReviews] = useState([])
  const [loadingStats, setLoadingStats] = useState(true)
  const [loadingReviews, setLoadingReviews] = useState(false)
  const [tab, setTab] = useState('overview')  // 'overview' | 'edit' | 'reviews'

  // Edit form state
  const [editForm, setEditForm] = useState({})
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    ownerApi.restaurantStats(id)
      .then((data) => {
        setStats(data)
        const r = data.restaurant
        setEditForm({
          name: r.name || '',
          cuisine_type: r.cuisine_type || '',
          price_range: r.price_range || '',
          description: r.description || '',
          address: r.address || '',
          city: r.city || '',
          state: r.state || '',
          country: r.country || '',
          zip_code: r.zip_code || '',
          phone: r.phone || '',
          website: r.website || '',
        })
      })
      .catch(() => toast.error('Failed to load restaurant data'))
      .finally(() => setLoadingStats(false))
  }, [id])

  const loadReviews = async () => {
    if (loadingReviews) return
    setLoadingReviews(true)
    try {
      const data = await ownerApi.restaurantReviews(id, { limit: 20 })
      setReviews(data.items || [])
    } catch {
      toast.error('Failed to load reviews')
    } finally {
      setLoadingReviews(false)
    }
  }

  const handleTabChange = (t) => {
    setTab(t)
    if (t === 'reviews' && reviews.length === 0) loadReviews()
  }

  const saveEdit = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await ownerApi.updateRestaurant(id, editForm)
      setStats((prev) => ({ ...prev, restaurant: updated }))
      toast.success('Restaurant updated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Update failed')
    } finally {
      setSaving(false)
    }
  }

  const handleField = (e) =>
    setEditForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))

  const handleDelete = async () => {
    if (!window.confirm(`Permanently delete "${stats?.restaurant?.name}"? This cannot be undone.`)) return
    try {
      await restaurantsApi.delete(id)
      toast.success('Restaurant deleted.')
      navigate('/owner/restaurants')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Delete failed')
    }
  }

  if (loadingStats) return <LoadingSpinner />
  if (!stats) return <div className="text-center py-20 text-gray-500">Restaurant not found.</div>

  const { restaurant: r, rating_distribution, monthly_trend, recent_reviews, sentiment } = stats
  const maxBar = Math.max(...Object.values(rating_distribution || {}), 1)
  const maxTrend = Math.max(...(monthly_trend || []).map((m) => m.review_count), 1)
  const sentimentTotal = sentiment
    ? sentiment.positive_count + sentiment.negative_count + sentiment.neutral_count
    : 0

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav aria-label="Breadcrumb" className="mb-4 text-sm text-gray-500">
        <Link to="/owner/restaurants" className="hover:text-brand-600">My Restaurants</Link>
        {' / '}
        <span className="text-gray-900 font-medium">{r.name}</span>
      </nav>

      {/* Header */}
      <div className="flex items-start justify-between gap-4 flex-wrap mb-6">
        <div>
          <h1 className="section-title">{r.name}</h1>
          <p className="text-gray-500 text-sm mt-1">
            ⭐ {formatRating(r.avg_rating)} · {r.review_count} reviews
            {r.cuisine_type && ` · ${r.cuisine_type}`}
            {r.city && ` · ${r.city}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/restaurants/${id}`} target="_blank" rel="noopener noreferrer"
            className="btn-secondary text-sm">
            View Public Page ↗
          </Link>
          <button
            onClick={handleDelete}
            className="text-sm px-4 py-2 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 transition-colors"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-gray-200 mb-6" role="tablist">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'edit', label: 'Edit Details' },
          { id: 'reviews', label: `Reviews (${r.review_count})` },
        ].map(({ id: tid, label }) => (
          <button
            key={tid}
            role="tab"
            aria-selected={tab === tid}
            onClick={() => handleTabChange(tid)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors -mb-px
              ${tab === tid
                ? 'border-brand-600 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* ── OVERVIEW TAB ── */}
      {tab === 'overview' && (
        <div className="space-y-6">
          <div className="grid lg:grid-cols-2 gap-6">

            {/* Rating distribution */}
            <section className="card p-6" aria-labelledby="rating-dist-heading">
              <h2 id="rating-dist-heading" className="font-bold text-gray-900 mb-4">Rating Breakdown</h2>
              <div className="space-y-2">
                {[5, 4, 3, 2, 1].map((star) => {
                  const count = rating_distribution?.[star] || 0
                  const pct = maxBar > 0 ? (count / maxBar) * 100 : 0
                  return (
                    <div key={star} className="flex items-center gap-3">
                      <span className="text-sm text-gray-600 w-6 flex-shrink-0">{star}★</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-amber-400 rounded-full transition-all"
                          style={{ width: `${pct}%` }}
                          role="progressbar"
                          aria-valuenow={count}
                          aria-label={`${star} stars: ${count} reviews`}
                        />
                      </div>
                      <span className="text-sm text-gray-500 w-6 text-right">{count}</span>
                    </div>
                  )
                })}
              </div>
            </section>

            {/* Monthly trend */}
            {monthly_trend?.length > 0 && (
              <section className="card p-6" aria-labelledby="trend-heading">
                <h2 id="trend-heading" className="font-bold text-gray-900 mb-4">Review Trend</h2>
                <div className="flex items-end gap-2 h-24">
                  {monthly_trend.map((m) => {
                    const barH = Math.max((m.review_count / maxTrend) * 100, 4)
                    const label = `${m.year}-${String(m.month).padStart(2, '0')}`
                    return (
                      <div key={label} className="flex-1 flex flex-col items-center gap-1">
                        <span className="text-xs text-gray-500">{m.review_count}</span>
                        <div
                          className="w-full bg-brand-400 rounded-t-sm transition-all"
                          style={{ height: `${barH}%` }}
                          title={`${label}: ${m.review_count} reviews`}
                        />
                        <span className="text-xs text-gray-400">{String(m.month).padStart(2, '0')}</span>
                      </div>
                    )
                  })}
                </div>
              </section>
            )}
          </div>

          {/* Sentiment */}
          {sentiment && sentimentTotal > 0 && (
            <section className="card p-6" aria-labelledby="sentiment-heading">
              <div className="flex items-center gap-3 mb-4">
                <h2 id="sentiment-heading" className="font-bold text-gray-900">Review Sentiment</h2>
                <span className={`badge ${SENTIMENT_BADGE[sentiment.overall] || 'bg-gray-100 text-gray-600'}`}>
                  {sentiment.overall}
                </span>
              </div>
              <div className="grid sm:grid-cols-3 gap-4 mb-4">
                {[
                  { label: 'Positive', count: sentiment.positive_count, color: 'text-green-600' },
                  { label: 'Neutral', count: sentiment.neutral_count, color: 'text-gray-500' },
                  { label: 'Negative', count: sentiment.negative_count, color: 'text-red-500' },
                ].map(({ label, count, color }) => (
                  <div key={label} className="text-center">
                    <div className={`text-2xl font-bold ${color}`}>{count}</div>
                    <div className="text-xs text-gray-400">{label}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-4">
                {sentiment.top_positive_words?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Top positive</p>
                    <div className="flex flex-wrap gap-1">
                      {sentiment.top_positive_words.map((w) => (
                        <span key={w} className="badge bg-green-50 text-green-700">{w}</span>
                      ))}
                    </div>
                  </div>
                )}
                {sentiment.top_negative_words?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 mb-1">Top negative</p>
                    <div className="flex flex-wrap gap-1">
                      {sentiment.top_negative_words.map((w) => (
                        <span key={w} className="badge bg-red-50 text-red-700">{w}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Recent reviews preview */}
          {recent_reviews?.length > 0 && (
            <section className="card" aria-labelledby="recent-heading">
              <div className="px-5 pt-5 pb-3 flex items-center justify-between">
                <h2 id="recent-heading" className="font-bold text-gray-900">Recent Reviews</h2>
                <button onClick={() => handleTabChange('reviews')} className="text-brand-600 text-sm hover:underline">
                  See all →
                </button>
              </div>
              <div className="divide-y divide-gray-50">
                {recent_reviews.slice(0, 4).map((rev) => (
                  <div key={rev.id} className="px-5 py-3">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="font-semibold text-sm text-gray-900">
                          {rev.user_name || 'Anonymous'}
                        </span>
                        <div className="flex text-amber-400 text-xs mt-0.5">
                          {'★'.repeat(rev.rating)}
                          <span className="text-gray-200">{'★'.repeat(5 - rev.rating)}</span>
                        </div>
                      </div>
                      <time className="text-xs text-gray-400 flex-shrink-0" dateTime={rev.created_at}>
                        {formatDate(rev.created_at)}
                      </time>
                    </div>
                    {rev.comment && (
                      <p className="text-sm text-gray-700 mt-1 line-clamp-2">{rev.comment}</p>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}
        </div>
      )}

      {/* ── EDIT TAB ── */}
      {tab === 'edit' && (
        <form onSubmit={saveEdit} className="card p-6 space-y-5">
          <div className="grid sm:grid-cols-2 gap-4">
            <div className="sm:col-span-2">
              <label className="label" htmlFor="edit-name">Restaurant Name</label>
              <input id="edit-name" name="name" type="text" value={editForm.name}
                onChange={handleField} className="input" required />
            </div>
            <div>
              <label className="label" htmlFor="edit-cuisine">Cuisine Type</label>
              <select id="edit-cuisine" name="cuisine_type" value={editForm.cuisine_type}
                onChange={handleField} className="input">
                {CUISINES.map((c) => <option key={c} value={c}>{c || 'Select cuisine'}</option>)}
              </select>
            </div>
            <div>
              <label className="label" htmlFor="edit-price">Price Range</label>
              <select id="edit-price" name="price_range" value={editForm.price_range}
                onChange={handleField} className="input">
                {PRICE_RANGES.map((p) => <option key={p} value={p}>{p || 'Select price range'}</option>)}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="edit-description">Description</label>
              <textarea id="edit-description" name="description" value={editForm.description}
                onChange={handleField} rows={3} className="input resize-none" />
            </div>
            <div className="sm:col-span-2">
              <label className="label" htmlFor="edit-address">Address</label>
              <input id="edit-address" name="address" type="text" value={editForm.address}
                onChange={handleField} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="edit-city">City</label>
              <input id="edit-city" name="city" type="text" value={editForm.city}
                onChange={handleField} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="edit-state">State</label>
              <input id="edit-state" name="state" type="text" value={editForm.state}
                onChange={handleField} className="input" placeholder="e.g. CA" />
            </div>
            <div>
              <label className="label" htmlFor="edit-country">Country</label>
              <input id="edit-country" name="country" type="text" value={editForm.country}
                onChange={handleField} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="edit-zip">Zip Code</label>
              <input id="edit-zip" name="zip_code" type="text" value={editForm.zip_code}
                onChange={handleField} className="input" />
            </div>
            <div>
              <label className="label" htmlFor="edit-phone">Phone</label>
              <input id="edit-phone" name="phone" type="tel" value={editForm.phone}
                onChange={handleField} className="input" placeholder="+1 (415) 555-0100" />
            </div>
            <div>
              <label className="label" htmlFor="edit-website">Website</label>
              <input id="edit-website" name="website" type="url" value={editForm.website}
                onChange={handleField} className="input" placeholder="https://..." />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={() => setTab('overview')} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary px-8">
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>
      )}

      {/* ── REVIEWS TAB ── */}
      {tab === 'reviews' && (
        <section aria-label="All reviews">
          {loadingReviews ? (
            <LoadingSpinner />
          ) : reviews.length > 0 ? (
            <div className="card divide-y divide-gray-100">
              {reviews.map((rev) => (
                <div key={rev.id} className="p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <span className="font-semibold text-sm text-gray-900">
                        {rev.user_name || 'Anonymous'}
                      </span>
                      <div className="flex text-amber-400 text-sm mt-0.5">
                        {'★'.repeat(rev.rating)}
                        <span className="text-gray-200">{'★'.repeat(5 - rev.rating)}</span>
                      </div>
                    </div>
                    <time className="text-xs text-gray-400 flex-shrink-0" dateTime={rev.created_at}>
                      {formatDate(rev.created_at)}
                    </time>
                  </div>
                  {rev.comment && (
                    <p className="mt-2 text-sm text-gray-700 leading-relaxed">{rev.comment}</p>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="card p-10 text-center text-gray-400">
              <div className="text-5xl mb-3">📝</div>
              <p>No reviews yet for this restaurant.</p>
            </div>
          )}
        </section>
      )}
    </div>
  )
}
