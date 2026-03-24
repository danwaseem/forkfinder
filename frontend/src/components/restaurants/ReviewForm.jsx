/**
 * ReviewForm
 *
 * Standalone review submission form. No internal API calls — all
 * state is controlled / lifted to the parent.
 *
 * Props:
 *   onSubmit     ({ rating, comment, photo }) => Promise<void>
 *   onCancel     () => void        — show a Cancel button when provided
 *   loading      boolean           — disables form while submitting
 *   initialRating  number          — pre-fill rating (default: 5)
 *   initialComment string          — pre-fill comment (default: '')
 *   error        string            — error message to display above the form
 *   submitLabel  string            — button text (default: 'Post Review')
 *   showPhotoUpload boolean        — show the photo upload field (default: true)
 *   compact      boolean           — tighter layout (default: false)
 *   className    string
 */
import { useState } from 'react'
import StarRating from '../common/StarRating'
import ErrorAlert from '../common/ErrorAlert'

export default function ReviewForm({
  onSubmit,
  onCancel,
  loading = false,
  initialRating = 5,
  initialComment = '',
  error,
  submitLabel = 'Post Review',
  showPhotoUpload = true,
  compact = false,
  className = '',
}) {
  const [rating, setRating] = useState(initialRating)
  const [comment, setComment] = useState(initialComment)
  const [photo, setPhoto] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)

  const handlePhoto = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhoto(file)
    setPhotoPreview(URL.createObjectURL(file))
  }

  const removePhoto = () => {
    setPhoto(null)
    setPhotoPreview(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    await onSubmit?.({ rating, comment, photo })
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-4 ${className}`} noValidate>
      <ErrorAlert message={error} />

      {/* Star rating */}
      <div>
        <label className="label">Rating</label>
        <StarRating
          rating={rating}
          onRate={setRating}
          size={compact ? 'md' : 'lg'}
        />
      </div>

      {/* Comment textarea */}
      <div>
        <label htmlFor="review-comment" className="label">
          Your review <span className="text-red-500" aria-hidden="true">*</span>
        </label>
        <textarea
          id="review-comment"
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={compact ? 3 : 5}
          required
          placeholder="Share your experience — food quality, service, ambiance…"
          className="input resize-none"
          disabled={loading}
        />
        <p className="mt-1 text-xs text-gray-400 text-right">{comment.length} characters</p>
      </div>

      {/* Photo upload */}
      {showPhotoUpload && (
        <div>
          <label className="label">Photo (optional)</label>

          {photoPreview ? (
            <div className="relative inline-block">
              <img
                src={photoPreview}
                alt="Preview"
                className="w-24 h-24 rounded-xl object-cover border border-gray-200"
              />
              <button
                type="button"
                onClick={removePhoto}
                aria-label="Remove photo"
                className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-gray-800 text-white
                           flex items-center justify-center hover:bg-gray-900 transition"
              >
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          ) : (
            <label
              htmlFor="review-photo-input"
              className="flex items-center gap-3 w-fit cursor-pointer px-4 py-2.5 rounded-xl border
                         border-dashed border-gray-300 hover:border-brand-400 text-sm text-gray-500
                         hover:text-brand-600 transition"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Add a photo
              <input
                id="review-photo-input"
                type="file"
                accept="image/*"
                onChange={handlePhoto}
                className="sr-only"
              />
            </label>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={loading || !comment.trim()}
          className="btn-primary"
        >
          {loading ? 'Posting…' : submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="btn-secondary"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  )
}
