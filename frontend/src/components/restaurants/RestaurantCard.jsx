import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import api from '../../services/api'
import toast from 'react-hot-toast'
import { StarDisplay } from '../common/StarRating'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const PRICE_CLASSES = {
  '$':    'bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200',
  '$$':   'bg-amber-50   text-amber-700   ring-1 ring-inset ring-amber-200',
  '$$$':  'bg-orange-50  text-orange-700  ring-1 ring-inset ring-orange-200',
  '$$$$': 'bg-red-50     text-red-700     ring-1 ring-inset ring-red-200',
}

export default function RestaurantCard({ restaurant, onFavoriteToggle }) {
  const { user }    = useAuth()
  const [fav, setFav]         = useState(restaurant.is_favorited || false)
  const [toggling, setToggling] = useState(false)

  const cover = restaurant.photos?.[0] ? `${BASE}${restaurant.photos[0]}` : null

  const toggleFavorite = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (!user)   { toast.error('Log in to save favorites'); return }
    if (toggling) return
    setToggling(true)
    try {
      if (fav) {
        await api.delete(`/favorites/${restaurant.id}`)
        setFav(false)
        toast.success('Removed from favorites')
      } else {
        await api.post(`/favorites/${restaurant.id}`)
        setFav(true)
        toast.success('Saved to favorites')
      }
      onFavoriteToggle?.(restaurant.id, !fav)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error updating favorites')
    } finally {
      setToggling(false)
    }
  }

  const priceClass = PRICE_CLASSES[restaurant.price_range] || 'bg-gray-100 text-gray-600'

  return (
    <article className="card-hover group">
      <Link to={`/restaurants/${restaurant.id}`} aria-label={`View ${restaurant.name}`} className="block">

        {/* Cover photo */}
        <div className="relative h-48 bg-gray-100 overflow-hidden">
          {cover ? (
            <img
              src={cover}
              alt={`${restaurant.name}`}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.04]"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center
                            bg-gradient-to-br from-brand-50 via-brand-100 to-brand-50 text-5xl">
              🍽️
            </div>
          )}

          {/* Gradient scrim */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/30 via-transparent to-transparent" />

          {/* Top badges */}
          <div className="absolute top-3 left-3 flex items-center gap-1.5">
            {restaurant.is_claimed && (
              <span className="badge text-[10px] bg-green-500/90 text-white backdrop-blur-sm">
                ✓ Claimed
              </span>
            )}
          </div>

          {/* Favorite button */}
          <button
            onClick={toggleFavorite}
            disabled={toggling}
            aria-label={fav ? 'Remove from favorites' : 'Save to favorites'}
            aria-pressed={fav}
            className={`absolute top-3 right-3 w-8 h-8 rounded-full flex items-center justify-center
                        backdrop-blur-sm transition-all duration-150 active:scale-90
                        ${fav
                          ? 'bg-brand-600 text-white shadow-md'
                          : 'bg-white/80 text-gray-500 hover:bg-white hover:text-brand-600 shadow-sm'
                        }`}
          >
            <svg className="w-4 h-4" fill={fav ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </button>

          {/* Price in bottom-left of photo */}
          {restaurant.price_range && (
            <span className={`absolute bottom-3 left-3 badge text-[10px] font-bold ${priceClass} backdrop-blur-sm`}>
              {restaurant.price_range}
            </span>
          )}
        </div>

        {/* Card body */}
        <div className="p-4">
          <h3 className="font-bold text-gray-900 text-[15px] leading-snug line-clamp-1 group-hover:text-brand-700 transition-colors">
            {restaurant.name}
          </h3>

          {/* Meta row */}
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            {restaurant.cuisine_type && (
              <span className="badge text-[10px] bg-gray-100 text-gray-600">
                {restaurant.cuisine_type}
              </span>
            )}
            {restaurant.city && (
              <span className="flex items-center gap-1 text-xs text-gray-500">
                <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round"
                    d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                {restaurant.city}{restaurant.state ? `, ${restaurant.state}` : ''}
              </span>
            )}
          </div>

          {/* Stars */}
          <div className="mt-2.5">
            <StarDisplay rating={restaurant.avg_rating} reviewCount={restaurant.review_count} />
          </div>

          {restaurant.description && (
            <p className="mt-2 text-xs text-gray-500 line-clamp-2 leading-relaxed">
              {restaurant.description}
            </p>
          )}
        </div>
      </Link>
    </article>
  )
}
