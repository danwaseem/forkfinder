import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function Favorites() {
  const [items, setItems] = useState([])   // FavoriteItem[]  { favorited_at, restaurant }
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/favorites/me')
      .then(({ data }) => setItems(data.items ?? []))
      .catch(() => setError('Failed to load favorites'))
      .finally(() => setLoading(false))
  }, [])

  const handleFavoriteToggle = (restaurantId, isFav) => {
    if (!isFav) setItems((prev) => prev.filter((item) => item.restaurant.id !== restaurantId))
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="section-title mb-6">My Favorites</h1>

      {error && (
        <div role="alert" className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl mb-4">
          {error}
        </div>
      )}

      {items.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map(({ restaurant }) => (
            <RestaurantCard
              key={restaurant.id}
              restaurant={{ ...restaurant, is_favorited: true }}
              onFavoriteToggle={handleFavoriteToggle}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-20 text-gray-500">
          <div className="text-6xl mb-4">❤️</div>
          <p className="text-lg font-medium">No favorites yet</p>
          <p className="text-sm mt-1">Browse restaurants and tap the heart icon to save them here.</p>
          <Link to="/explore" className="btn-primary mt-6 inline-flex">Explore Restaurants</Link>
        </div>
      )}
    </div>
  )
}
