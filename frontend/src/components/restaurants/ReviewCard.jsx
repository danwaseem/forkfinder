import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import StarRating from '../common/StarRating'
import api from '../../services/api'
import toast from 'react-hot-toast'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const RATING_LABELS = { 5: 'Excellent', 4: 'Good', 3: 'Average', 2: 'Poor', 1: 'Terrible' }
const RATING_COLORS = {
  5: 'bg-green-50  text-green-700  ring-green-200',
  4: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
  3: 'bg-amber-50  text-amber-700  ring-amber-200',
  2: 'bg-orange-50 text-orange-700 ring-orange-200',
  1: 'bg-red-50    text-red-700    ring-red-200',
}

function RatingBadge({ rating }) {
  const cls = RATING_COLORS[rating] || RATING_COLORS[3]
  return (
    <span className={`badge text-[10px] ring-1 ring-inset ${cls}`}>
      {'★'.repeat(rating)} {RATING_LABELS[rating]}
    </span>
  )
}

export default function ReviewCard({ review, onUpdated, onDeleted }) {
  const { user }   = useAuth()
  const [editing, setEditing]     = useState(false)
  const [rating,  setRating]      = useState(review.rating)
  const [comment, setComment]     = useState(review.comment)
  const [saving,  setSaving]      = useState(false)

  const isOwner  = user?.id === review.user_id
  const photos   = review.photos || []
  const avatarSrc = review.user?.profile_photo_url
    ? `${BASE}${review.user.profile_photo_url}`
    : null

  const save = async () => {
    if (!comment.trim()) { toast.error('Comment cannot be empty'); return }
    setSaving(true)
    try {
      const { data } = await api.put(`/reviews/${review.id}`, { rating, comment })
      // data is ReviewWithStatsResponse: { review, restaurant_stats }
      onUpdated?.(data.review, data.restaurant_stats)
      setEditing(false)
      toast.success('Review updated')
    } catch {
      toast.error('Failed to update review')
    } finally {
      setSaving(false)
    }
  }

  const del = async () => {
    if (!confirm('Delete this review?')) return
    try {
      const { data } = await api.delete(`/reviews/${review.id}`)
      // data is ReviewWithStatsResponse: { review: null, restaurant_stats }
      onDeleted?.(review.id, data.restaurant_stats)
      toast.success('Review deleted')
    } catch {
      toast.error('Failed to delete review')
    }
  }

  const dateStr = new Date(review.created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  return (
    <article className="py-5 border-b border-gray-100 last:border-0 first:pt-0">
      <div className="flex items-start gap-3.5">
        {/* Avatar */}
        {avatarSrc ? (
          <img src={avatarSrc} alt={review.user?.name}
            className="w-10 h-10 rounded-full object-cover shrink-0 ring-2 ring-white shadow-sm" />
        ) : (
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-brand-400 to-brand-600
                          flex items-center justify-center font-bold text-white text-sm shrink-0
                          ring-2 ring-white shadow-sm">
            {review.user?.name?.[0]?.toUpperCase() || '?'}
          </div>
        )}

        <div className="flex-1 min-w-0">
          {/* Header row */}
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <div className="flex items-center gap-2.5 flex-wrap">
              <span className="font-semibold text-sm text-gray-900">
                {review.user?.name || 'Anonymous'}
              </span>
              <RatingBadge rating={review.rating} />
            </div>
            <time className="text-xs text-gray-400 shrink-0" dateTime={review.created_at}>
              {dateStr}
            </time>
          </div>

          {editing ? (
            <div className="mt-3 space-y-3">
              <StarRating rating={rating} onRate={setRating} size="md" />
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={3}
                className="input text-sm resize-none"
                aria-label="Edit review comment"
              />
              <div className="flex gap-2">
                <button onClick={save} disabled={saving} className="btn-primary text-xs px-3 py-1.5">
                  {saving ? 'Saving…' : 'Save changes'}
                </button>
                <button onClick={() => setEditing(false)} className="btn-secondary text-xs px-3 py-1.5">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <>
              <p className="mt-2 text-sm text-gray-700 leading-relaxed">{review.comment}</p>

              {photos.length > 0 && (
                <div className="mt-3 flex gap-2 flex-wrap">
                  {photos.map((p, i) => (
                    <img
                      key={i}
                      src={`${BASE}${p}`}
                      alt={`Review photo ${i + 1}`}
                      className="w-20 h-20 object-cover rounded-xl border border-gray-100 hover:scale-105 transition-transform cursor-pointer"
                      loading="lazy"
                    />
                  ))}
                </div>
              )}

              {isOwner && (
                <div className="mt-2.5 flex gap-3">
                  <button
                    onClick={() => setEditing(true)}
                    className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
                  >
                    Edit
                  </button>
                  <button
                    onClick={del}
                    className="text-xs font-medium text-gray-400 hover:text-red-500 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </article>
  )
}
