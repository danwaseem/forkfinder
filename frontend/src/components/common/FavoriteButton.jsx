/**
 * FavoriteButton
 *
 * Standalone heart toggle. Handles its own API call + toast feedback.
 * The parent can optionally listen via onToggle(restaurantId, newState).
 *
 * Props:
 *   restaurantId  number | string   — required
 *   favorited     boolean           — initial state
 *   onToggle      (id, newState) => void  — optional callback after toggle
 *   size          'sm'|'md'|'lg'
 *   variant       'icon'|'button'   — icon-only vs icon+label button
 *   className     string
 */
import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'
import toast from 'react-hot-toast'

export default function FavoriteButton({
  restaurantId,
  favorited: initialFavorited = false,
  onToggle,
  size = 'md',
  variant = 'icon',
  className = '',
}) {
  const { user } = useAuth()
  const [favorited, setFavorited] = useState(initialFavorited)
  const [loading, setLoading] = useState(false)

  const iconSizes = { sm: 'w-4 h-4', md: 'w-5 h-5', lg: 'w-6 h-6' }
  const paddings  = { sm: 'p-1.5', md: 'p-2', lg: 'p-2.5' }

  const toggle = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user) { toast.error('Log in to save favorites'); return }
    if (loading) return
    setLoading(true)
    try {
      if (favorited) {
        await api.delete(`/favorites/${restaurantId}`)
        setFavorited(false)
        onToggle?.(restaurantId, false)
        toast.success('Removed from favorites')
      } else {
        await api.post(`/favorites/${restaurantId}`)
        setFavorited(true)
        onToggle?.(restaurantId, true)
        toast.success('Saved to favorites')
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error')
    } finally {
      setLoading(false)
    }
  }

  const iconEl = (
    <svg
      className={iconSizes[size]}
      fill={favorited ? 'currentColor' : 'none'}
      viewBox="0 0 24 24"
      stroke="currentColor"
      aria-hidden="true"
    >
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  )

  const baseClass = `rounded-xl border transition active:scale-95 focus:outline-none
    focus:ring-2 focus:ring-brand-400 focus:ring-offset-1 disabled:opacity-50
    ${favorited
      ? 'border-brand-300 bg-brand-50 text-brand-600 hover:bg-brand-100'
      : 'border-gray-200 text-gray-400 hover:border-brand-300 hover:text-brand-500 bg-white'
    }`

  if (variant === 'button') {
    return (
      <button
        type="button"
        onClick={toggle}
        disabled={loading}
        aria-pressed={favorited}
        aria-label={favorited ? 'Remove from favorites' : 'Save to favorites'}
        className={`${baseClass} flex items-center gap-1.5 px-3 py-2 text-sm font-medium ${className}`}
      >
        {iconEl}
        <span>{favorited ? 'Saved' : 'Save'}</span>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={toggle}
      disabled={loading}
      aria-pressed={favorited}
      aria-label={favorited ? 'Remove from favorites' : 'Save to favorites'}
      className={`${baseClass} ${paddings[size]} ${className}`}
    >
      {iconEl}
    </button>
  )
}
