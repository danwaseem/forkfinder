import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import { formatRating, imgUrl } from '../utils/format'
import LoadingSpinner from '../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

export default function ClaimRestaurant() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [searching, setSearching] = useState(false)
  const [claimingId, setClaimingId] = useState(null)

  if (user?.role !== 'owner') {
    return (
      <div className="max-w-xl mx-auto px-4 py-24 text-center text-gray-500">
        <div className="text-5xl mb-4">🔒</div>
        <p className="text-lg font-semibold text-gray-700">Owners only</p>
        <p className="text-sm mt-2">Only restaurant owners can claim listings.</p>
        <button onClick={() => navigate('/')} className="btn-primary mt-6">Go Home</button>
      </div>
    )
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setSearching(true)
    setSearched(false)
    try {
      const { data } = await api.get('/restaurants', {
        params: { q: query.trim(), claimed: false, limit: 20 },
      })
      setResults((data.items || []).filter((r) => !r.is_claimed))
      setSearched(true)
    } catch {
      toast.error('Search failed. Please try again.')
    } finally {
      setSearching(false)
    }
  }

  const handleClaim = async (restaurantId, restaurantName) => {
    setClaimingId(restaurantId)
    try {
      await api.post(`/restaurants/${restaurantId}/claim`)
      toast.success(`"${restaurantName}" claimed successfully!`)
      navigate('/owner/dashboard')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Claim failed')
    } finally {
      setClaimingId(null)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="mb-8">
        <h1 className="section-title">Claim a Restaurant</h1>
        <p className="text-gray-500 text-sm mt-1">
          Search for your restaurant below. Once claimed, you can manage its details, respond to reviews, and view analytics.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-8">
        <div className="flex-1">
          <label htmlFor="claim-search" className="sr-only">Search restaurant name or city</label>
          <input
            id="claim-search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Restaurant name, city, or cuisine..."
            className="input w-full"
          />
        </div>
        <button type="submit" disabled={searching || !query.trim()} className="btn-primary px-6">
          {searching ? 'Searching…' : 'Search'}
        </button>
      </form>

      {/* Results */}
      {searching && <LoadingSpinner />}

      {searched && !searching && (
        <>
          {results.length === 0 ? (
            <div className="text-center py-16 text-gray-500 card p-8">
              <div className="text-5xl mb-3">🏪</div>
              <p className="font-medium text-gray-700">No unclaimed restaurants found</p>
              <p className="text-sm mt-2">
                All matching results are already claimed, or nothing matched your search.
              </p>
              <p className="text-sm mt-1">
                If your restaurant isn't listed yet, you can{' '}
                <button
                  onClick={() => navigate('/add-restaurant')}
                  className="text-brand-600 hover:underline font-medium"
                >
                  add it here
                </button>
                .
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-sm text-gray-500 mb-2">{results.length} unclaimed restaurant{results.length !== 1 ? 's' : ''} found</p>
              {results.map((r) => (
                <article key={r.id} className="card p-4 flex items-center gap-4">
                  {/* Thumbnail */}
                  <div className="w-16 h-16 rounded-xl bg-brand-50 flex-shrink-0 overflow-hidden">
                    {r.photos?.[0] ? (
                      <img src={imgUrl(r.photos[0])} alt={r.name} className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-2xl">🍽️</div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <h2 className="font-semibold text-gray-900 truncate">{r.name}</h2>
                    <p className="text-sm text-gray-500 truncate">
                      {r.cuisine_type}
                      {r.city ? ` · ${r.city}` : ''}
                      {r.state ? `, ${r.state}` : ''}
                      {r.price_range ? ` · ${r.price_range}` : ''}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1">
                      <span className="text-amber-400 text-sm">★</span>
                      <span className="text-sm text-gray-700 font-medium">{formatRating(r.avg_rating)}</span>
                      <span className="text-xs text-gray-400">({r.review_count} reviews)</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col items-end gap-2 flex-shrink-0">
                    <button
                      onClick={() => handleClaim(r.id, r.name)}
                      disabled={claimingId === r.id}
                      className="btn-primary text-sm px-4 py-2"
                    >
                      {claimingId === r.id ? 'Claiming…' : 'Claim'}
                    </button>
                    <button
                      onClick={() => navigate(`/restaurants/${r.id}`)}
                      className="text-xs text-brand-600 hover:underline"
                    >
                      View listing
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </>
      )}

      {/* Initial state */}
      {!searched && !searching && (
        <div className="text-center py-16 text-gray-400">
          <div className="text-5xl mb-3">🔍</div>
          <p className="text-sm">Search for your restaurant to get started</p>
          <p className="text-xs mt-2">
            Don't see it?{' '}
            <button onClick={() => navigate('/add-restaurant')} className="text-brand-600 hover:underline">
              Add a new listing
            </button>
          </p>
        </div>
      )}
    </div>
  )
}
