import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ReviewCard from '../components/restaurants/ReviewCard'
import StarRating, { StarDisplay } from '../components/common/StarRating'
import toast from 'react-hot-toast'
import {
  setReviews  as setReviewsStore,
  addReview   as addReviewAction,
  updateReview,
  removeReview,
} from '../store/slices/reviewsSlice'
import { addFavorite, removeFavorite } from '../store/slices/favoritesSlice'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const PRICE_CLASSES = {
  '$':    'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  '$$':   'bg-amber-50   text-amber-700   ring-1 ring-inset ring-amber-200',
  '$$$':  'bg-orange-50  text-orange-700  ring-1 ring-inset ring-orange-200',
  '$$$$': 'bg-red-50     text-red-700     ring-1 ring-inset ring-red-200',
}

// ─── Info row (icon + text) ────────────────────────────────────────────────────
function InfoRow({ icon, children }) {
  return (
    <div className="flex items-start gap-3 text-sm text-gray-700">
      <span className="text-base mt-px shrink-0 text-gray-400" aria-hidden="true">{icon}</span>
      <span className="leading-relaxed">{children}</span>
    </div>
  )
}

// ─── Rating breakdown bar ──────────────────────────────────────────────────────
function RatingBar({ label, count, total }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-3 text-right text-gray-500 shrink-0">{label}</span>
      <span className="text-amber-400 text-[10px] leading-none">★</span>
      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-amber-400 transition-all duration-700"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-6 text-right text-gray-400 shrink-0">{count}</span>
    </div>
  )
}

export default function RestaurantDetails() {
  const { id }       = useParams()
  const { user }     = useAuth()
  const navigate     = useNavigate()
  const dispatch     = useDispatch()

  const [restaurant, setRestaurant] = useState(null)
  const [reviews,    setReviews]    = useState([])
  const [favorited,  setFavorited]  = useState(false)
  const [loading,    setLoading]    = useState(true)
  const [error,      setError]      = useState('')

  const [showForm,     setShowForm]     = useState(false)
  const [rating,       setRating]       = useState(5)
  const [comment,      setComment]      = useState('')
  const [reviewPhoto,  setReviewPhoto]  = useState(null)
  const [submitting,   setSubmitting]   = useState(false)
  const [claiming,     setClaiming]     = useState(false)

  const reviewRef    = useRef(null)
  const photoInputRef = useRef(null)

  useEffect(() => {
    Promise.all([
      api.get(`/restaurants/${id}`),
      api.get(`/restaurants/${id}/reviews`),
    ])
      .then(([rRes, revRes]) => {
        // Anchor review_count to the live total from the reviews query so the
        // displayed count always matches the actual rendered cards, regardless
        // of whether the stored denormalized field is stale.
        setRestaurant({ ...rRes.data, review_count: revRes.data.total ?? rRes.data.review_count })
        const revItems = revRes.data.items || []
        setReviews(revItems)
        setFavorited(rRes.data.is_favorited || false)
        dispatch(setReviewsStore({ restaurantId: parseInt(id), items: revItems, total: revRes.data.total || 0 }))
      })
      .catch(() => setError('Restaurant not found.'))
      .finally(() => setLoading(false))
  }, [id])

  const toggleFavorite = async () => {
    if (!user) { toast.error('Log in to save favorites'); return }
    try {
      if (favorited) {
        await api.delete(`/favorites/${id}`)
        setFavorited(false)
        dispatch(removeFavorite(parseInt(id)))
        toast.success('Removed from favorites')
      } else {
        await api.post(`/favorites/${id}`)
        setFavorited(true)
        dispatch(addFavorite({
          restaurant: { ...restaurant, id: parseInt(id) },
          favorited_at: new Date().toISOString(),
        }))
        toast.success('Saved to favorites')
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error')
    }
  }

  const submitReview = async (e) => {
    e.preventDefault()
    if (!comment.trim()) { toast.error('Please write a comment'); return }
    setSubmitting(true)
    try {
      const { data: reviewResponse } = await api.post(`/restaurants/${id}/reviews`, { rating, comment })
      const created = reviewResponse.review
      if (reviewPhoto) {
        const fd = new FormData()
        fd.append('file', reviewPhoto)
        await api.post(`/reviews/${created.id}/photos`, fd)
      }
      const [{ data }, { data: rData }] = await Promise.all([
        api.get(`/restaurants/${id}/reviews`),
        api.get(`/restaurants/${id}`),
      ])
      const refreshedItems = data.items || []
      setReviews(refreshedItems)
      setRestaurant(rData)
      dispatch(setReviewsStore({ restaurantId: parseInt(id), items: refreshedItems, total: data.total || 0 }))
      setComment(''); setRating(5); setReviewPhoto(null); setShowForm(false)
      toast.success('Review posted!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to post review')
    } finally {
      setSubmitting(false)
    }
  }

  const claimRestaurant = async () => {
    if (!user || user.role !== 'owner') { toast.error('Only restaurant owners can claim listings'); return }
    setClaiming(true)
    try {
      await api.post(`/restaurants/${id}/claim`)
      const { data } = await api.get(`/restaurants/${id}`)
      setRestaurant(data)
      toast.success('Restaurant claimed!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Claim failed')
    } finally {
      setClaiming(false)
    }
  }

  if (loading) return <LoadingSpinner fullPage />

  if (error || !restaurant) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4">
        <div className="text-6xl mb-4">🍽️</div>
        <p className="text-xl font-semibold text-gray-700 mb-2">{error || 'Restaurant not found.'}</p>
        <p className="text-gray-500 text-sm mb-6">It may have been removed or the link is incorrect.</p>
        <button onClick={() => navigate('/explore')} className="btn-primary">Browse Restaurants</button>
      </div>
    )
  }

  const photos     = restaurant.photos || []
  const hours      = restaurant.hours  || {}
  const canEdit    = user && (user.id === restaurant.created_by || user.id === restaurant.claimed_by)
  const hasReviewed = reviews.some((r) => r.user_id === user?.id)

  // Rating breakdown — computed from fetched reviews (used for bar percentages only)
  const ratingCounts = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 }
  reviews.forEach((r) => { if (ratingCounts[r.rating] !== undefined) ratingCounts[r.rating]++ })
  // Use the authoritative stored count for all displayed numbers.
  // reviews.length is only the current fetched page; restaurant.review_count is always the true total.
  const totalReviews = restaurant.review_count || 0

  return (
    <div className="bg-gray-50 min-h-screen pb-16">

      {/* ── Photo hero ────────────────────────────────────────────────────────── */}
      <div className="w-full bg-gray-200 overflow-hidden" style={{ maxHeight: 420 }}>
        {photos.length > 0 ? (
          <div
            className="grid gap-1"
            style={{
              gridTemplateColumns: photos.length >= 2 ? '2fr 1fr' : '1fr',
              maxHeight: 420,
            }}
          >
            {/* Main photo */}
            <div className="overflow-hidden" style={{ maxHeight: 420 }}>
              <img
                src={`${BASE}${photos[0]}`}
                alt={`${restaurant.name} — main photo`}
                className="w-full h-full object-cover"
                style={{ maxHeight: 420 }}
              />
            </div>
            {/* Side photos */}
            {photos.length >= 2 && (
              <div className="flex flex-col gap-1" style={{ maxHeight: 420 }}>
                {photos.slice(1, 3).map((p, i) => (
                  <div key={i} className="flex-1 overflow-hidden">
                    <img
                      src={`${BASE}${p}`}
                      alt={`${restaurant.name} — photo ${i + 2}`}
                      className="w-full h-full object-cover"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ) : (
          <div className="w-full flex items-center justify-center text-8xl"
            style={{ height: 300, background: 'linear-gradient(135deg, #fff1f2 0%, #fecdd3 100%)' }}>
            🍽️
          </div>
        )}
      </div>

      {/* ── Main content ─────────────────────────────────────────────────────── */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">

        {/* Name card — overlaps hero */}
        <div className="card p-6 -mt-6 relative z-10 mb-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex-1 min-w-0">
              {/* Title */}
              <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight leading-tight">
                {restaurant.name}
              </h1>

              {/* Badges row */}
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                {restaurant.cuisine_type && (
                  <span className="badge bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200">
                    {restaurant.cuisine_type}
                  </span>
                )}
                {restaurant.price_range && (
                  <span className={`badge font-bold ${PRICE_CLASSES[restaurant.price_range] || 'bg-gray-100 text-gray-600'}`}>
                    {restaurant.price_range}
                  </span>
                )}
                {restaurant.is_claimed && (
                  <span className="badge bg-green-50 text-green-700 ring-1 ring-inset ring-green-200">
                    ✓ Claimed
                  </span>
                )}
              </div>

              {/* Rating */}
              <div className="mt-3">
                <StarDisplay rating={restaurant.avg_rating} reviewCount={restaurant.review_count} size="md" />
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-2 flex-wrap shrink-0">
              <button
                onClick={toggleFavorite}
                aria-pressed={favorited}
                aria-label={favorited ? 'Remove from favorites' : 'Save to favorites'}
                className={`btn-icon gap-1.5 ${
                  favorited ? 'border-brand-300 bg-brand-50 text-brand-600' : ''
                }`}
              >
                <svg className="w-4 h-4" fill={favorited ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                </svg>
                {favorited ? 'Saved' : 'Save'}
              </button>

              {!restaurant.is_claimed && user?.role === 'owner' && (
                <button onClick={claimRestaurant} disabled={claiming} className="btn-secondary text-sm px-4">
                  {claiming ? 'Claiming…' : '✅ Claim'}
                </button>
              )}
              {canEdit && (
                <button onClick={() => navigate(`/add-restaurant?edit=${id}`)} className="btn-secondary text-sm px-4">
                  ✏️ Edit
                </button>
              )}
            </div>
          </div>

          {restaurant.description && (
            <p className="mt-4 text-gray-600 leading-relaxed border-t border-gray-100 pt-4">
              {restaurant.description}
            </p>
          )}
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* ── Left: reviews ─────────────────────────────────────────────────── */}
          <div className="lg:col-span-2 space-y-5">

            {/* Rating summary */}
            {totalReviews > 0 && (
              <div className="card p-5">
                <h2 className="card-title mb-4">Ratings & Reviews</h2>
                <div className="flex items-start gap-8">
                  {/* Big number */}
                  <div className="text-center shrink-0">
                    <p className="text-5xl font-extrabold text-gray-900">
                      {(restaurant.avg_rating || 0).toFixed(1)}
                    </p>
                    <div className="flex justify-center mt-1">
                      <StarDisplay rating={restaurant.avg_rating} size="xs" />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{totalReviews} reviews</p>
                  </div>
                  {/* Bars */}
                  <div className="flex-1 space-y-2">
                    {[5, 4, 3, 2, 1].map((n) => (
                      <RatingBar key={n} label={n} count={ratingCounts[n]} total={totalReviews} />
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Reviews section */}
            <section aria-label="Customer reviews">
              <div className="flex items-center justify-between mb-3">
                <h2 className="section-title">Reviews <span className="text-gray-400 font-normal text-xl">({totalReviews})</span></h2>
                {user && !hasReviewed && (
                  <button
                    ref={reviewRef}
                    onClick={() => setShowForm(!showForm)}
                    className="btn-primary text-sm px-4 py-2"
                  >
                    ✏️ Write a Review
                  </button>
                )}
              </div>

              {/* Review form */}
              {showForm && (
                <div className="card p-6 mb-5 animate-fade-up">
                  <h3 className="card-title mb-4">Your Review</h3>
                  <form onSubmit={submitReview} className="space-y-4">
                    <div>
                      <label className="label">Your rating</label>
                      <StarRating rating={rating} onRate={setRating} size="lg" />
                    </div>
                    <div>
                      <label htmlFor="review-comment" className="label">Your experience</label>
                      <textarea
                        id="review-comment"
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        rows={4}
                        className="input resize-none"
                        placeholder="What did you enjoy? What could be better?"
                        required
                      />
                    </div>
                    <div>
                      <label className="label">Add a photo <span className="text-gray-400 font-normal">(optional)</span></label>
                      {reviewPhoto ? (
                        <div className="relative w-24 h-24 group">
                          <img
                            src={URL.createObjectURL(reviewPhoto)}
                            alt="Review photo preview"
                            className="w-full h-full object-cover rounded-xl border border-gray-200"
                          />
                          <button
                            type="button"
                            onClick={() => { setReviewPhoto(null); photoInputRef.current && (photoInputRef.current.value = '') }}
                            aria-label="Remove photo"
                            className="absolute -top-1.5 -right-1.5 w-5 h-5 rounded-full bg-gray-900 text-white
                                       flex items-center justify-center opacity-0 group-hover:opacity-100
                                       transition-opacity hover:bg-red-600 text-xs font-bold leading-none"
                          >
                            ×
                          </button>
                          <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white
                                          text-[9px] px-1 py-0.5 rounded-b-xl truncate">
                            {(reviewPhoto.size / 1024).toFixed(0)} KB
                          </div>
                        </div>
                      ) : (
                        <button
                          type="button"
                          onClick={() => photoInputRef.current?.click()}
                          className="w-24 h-24 rounded-xl border-2 border-dashed border-gray-300
                                     flex flex-col items-center justify-center gap-1 text-gray-400
                                     hover:border-brand-400 hover:text-brand-500 hover:bg-brand-50/40
                                     transition-all duration-150"
                        >
                          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                          </svg>
                          <span className="text-[10px] font-medium">Add photo</span>
                        </button>
                      )}
                      <input
                        ref={photoInputRef}
                        type="file"
                        accept="image/*"
                        onChange={(e) => {
                          const f = e.target.files?.[0]
                          if (!f) return
                          if (!f.type.startsWith('image/')) { toast.error('Please select an image file.'); return }
                          if (f.size > 5 * 1024 * 1024) { toast.error('Photo must be under 5 MB.'); return }
                          setReviewPhoto(f)
                        }}
                        className="sr-only"
                        aria-hidden="true"
                      />
                    </div>
                    <div className="flex gap-2.5 pt-1">
                      <button type="submit" disabled={submitting} className="btn-primary px-6">
                        {submitting ? 'Posting…' : 'Post Review'}
                      </button>
                      <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {reviews.length > 0 ? (
                <div className="card p-5">
                  {reviews.map((rev) => (
                    <ReviewCard
                      key={rev.id}
                      review={rev}
                      onUpdated={(updated, stats) => {
                        setReviews((prev) => prev.map((r) => r.id === updated.id ? updated : r))
                        dispatch(updateReview(updated))
                        if (stats) setRestaurant((prev) => ({ ...prev, avg_rating: stats.avg_rating, review_count: stats.review_count }))
                      }}
                      onDeleted={(revId, stats) => {
                        setReviews((prev) => prev.filter((r) => r.id !== revId))
                        dispatch(removeReview(revId))
                        if (stats) setRestaurant((prev) => ({ ...prev, avg_rating: stats.avg_rating, review_count: stats.review_count }))
                      }}
                    />
                  ))}
                </div>
              ) : (
                <div className="card p-10 text-center">
                  <div className="text-4xl mb-3">💬</div>
                  <p className="font-semibold text-gray-700 mb-1">No reviews yet</p>
                  <p className="text-sm text-gray-500">Be the first to share your experience!</p>
                  {user && !hasReviewed && (
                    <button onClick={() => setShowForm(true)} className="btn-primary mt-4 text-sm px-5">
                      Write the first review
                    </button>
                  )}
                </div>
              )}
            </section>
          </div>

          {/* ── Sidebar ───────────────────────────────────────────────────────── */}
          <aside className="space-y-4" aria-label="Restaurant details">

            {/* Contact & location */}
            <div className="card p-5 space-y-3">
              <h2 className="card-title">Details</h2>
              {restaurant.address && (
                <InfoRow icon="📍">
                  {restaurant.address}
                  {restaurant.city    ? `, ${restaurant.city}`    : ''}
                  {restaurant.state   ? `, ${restaurant.state}`   : ''}
                  {restaurant.country ? `, ${restaurant.country}` : ''}
                </InfoRow>
              )}
              {restaurant.phone && (
                <InfoRow icon="📞">
                  <a href={`tel:${restaurant.phone}`} className="hover:text-brand-600 transition-colors">
                    {restaurant.phone}
                  </a>
                </InfoRow>
              )}
              {restaurant.website && (
                <InfoRow icon="🌐">
                  <a
                    href={restaurant.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-brand-600 hover:underline break-all"
                  >
                    {restaurant.website.replace(/^https?:\/\//, '')}
                  </a>
                </InfoRow>
              )}
            </div>

            {/* Hours */}
            {Object.keys(hours).length > 0 && (
              <div className="card p-5">
                <h2 className="card-title mb-3">Hours</h2>
                <dl className="space-y-2">
                  {Object.entries(hours).map(([day, time]) => {
                    const isToday = new Date().toLocaleDateString('en-US', { weekday: 'long' }).toLowerCase() === day.toLowerCase()
                    return (
                      <div key={day} className={`flex justify-between text-sm ${isToday ? 'font-semibold text-brand-700' : ''}`}>
                        <dt className="capitalize text-gray-600">{day}{isToday && <span className="ml-1.5 text-[10px] bg-brand-100 text-brand-700 px-1.5 py-0.5 rounded-full">Today</span>}</dt>
                        <dd className="font-medium text-gray-800">{time}</dd>
                      </div>
                    )
                  })}
                </dl>
              </div>
            )}

            {/* Cuisine/price info */}
            <div className="card p-5 space-y-3">
              <h2 className="card-title">At a Glance</h2>
              {restaurant.cuisine_type && (
                <InfoRow icon="🍴">Cuisine: <span className="font-medium ml-1">{restaurant.cuisine_type}</span></InfoRow>
              )}
              {restaurant.price_range && (
                <InfoRow icon="💰">Price: <span className="font-medium ml-1">{restaurant.price_range}</span></InfoRow>
              )}
              {restaurant.review_count > 0 && (
                <InfoRow icon="⭐">
                  {restaurant.avg_rating?.toFixed(1)} avg across {restaurant.review_count} reviews
                </InfoRow>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  )
}
