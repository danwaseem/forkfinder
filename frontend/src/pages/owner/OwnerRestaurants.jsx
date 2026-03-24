import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ownerApi } from '../../services/owner'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import { formatRating, imgUrl } from '../../utils/format'

export default function OwnerRestaurants() {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    ownerApi.restaurants()
      .then((data) => {
        // API returns OwnerRestaurantsListResponse { items, total }
        setItems(data.items || [])
        setTotal(data.total || 0)
      })
      .catch(() => setError('Failed to load restaurants.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">My Restaurants</h1>
          {total > 0 && <p className="text-gray-500 text-sm mt-1">{total} listing{total !== 1 ? 's' : ''}</p>}
        </div>
        <Link to="/add-restaurant" className="btn-primary">+ Add Restaurant</Link>
      </div>

      {error && (
        <div role="alert" className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl">
          {error}
        </div>
      )}

      {items.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {items.map((r) => {
            const cover = imgUrl(r.photos?.[0])
            return (
              <Link
                key={r.id}
                to={`/owner/restaurants/${r.id}`}
                className="card hover:shadow-md transition-shadow p-5 flex flex-col gap-3"
              >
                <div className="h-36 rounded-xl bg-gray-100 overflow-hidden">
                  {cover ? (
                    <img src={cover} alt={r.name} className="w-full h-full object-cover" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-4xl bg-brand-50">
                      🍽️
                    </div>
                  )}
                </div>
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="font-bold text-gray-900 truncate">{r.name}</h2>
                    {r.is_claimed && (
                      <span className="badge bg-green-100 text-green-700 flex-shrink-0">✓ Claimed</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">
                    {[r.cuisine_type, r.city].filter(Boolean).join(' · ')}
                  </p>
                  <div className="flex items-center gap-3 mt-2 text-sm">
                    <span className="font-semibold text-gray-900">⭐ {formatRating(r.avg_rating)}</span>
                    <span className="text-gray-400">{r.review_count} reviews</span>
                    {r.price_range && (
                      <span className="text-gray-400">{r.price_range}</span>
                    )}
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      ) : (
        <div className="text-center py-20 text-gray-500 card p-10">
          <div className="text-6xl mb-4">🏪</div>
          <p className="text-lg font-medium">No restaurants yet</p>
          <p className="text-sm text-gray-400 mt-1 mb-4">
            Add your restaurant to start collecting reviews and insights.
          </p>
          <Link to="/add-restaurant" className="btn-primary inline-flex">
            Add your first restaurant
          </Link>
        </div>
      )}
    </div>
  )
}
