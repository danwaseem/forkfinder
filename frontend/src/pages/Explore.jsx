import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import api from '../services/api'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { useChat } from '../hooks/useChat'
import ChatWindow from '../components/ai/ChatWindow'
import { setRestaurants as setRestaurantsStore } from '../store/slices/restaurantsSlice'

const CUISINES     = ['', 'Italian', 'Japanese', 'Mexican', 'Indian', 'American', 'Thai', 'Chinese', 'Mediterranean', 'French', 'Korean', 'Vietnamese', 'Greek']
const PRICE_RANGES = ['', '$', '$$', '$$$', '$$$$']
const RATINGS      = [{ label: 'Any', value: '' }, { label: '4+', value: 4 }, { label: '3+', value: 3 }, { label: '2+', value: 2 }]

const EXPLORE_SUGGESTIONS = [
  '🍣  Best sushi in the city',
  '💸  Great food under $$',
  '🌮  Authentic Mexican spots',
  '🥩  Top steakhouses',
  '🌿  Vegetarian-friendly places',
]

const PRICE_CLASSES = {
  '$':    'bg-emerald-50 text-emerald-700 border-emerald-200',
  '$$':   'bg-amber-50   text-amber-700   border-amber-200',
  '$$$':  'bg-orange-50  text-orange-700  border-orange-200',
  '$$$$': 'bg-red-50     text-red-700     border-red-200',
}

// ─── Slide-out AI panel ───────────────────────────────────────────────────────
function ExploreAIPanel({ open, onClose }) {
  const { messages, loading, send, reset, isFirstTurn } = useChat()
  const navigate = useNavigate()

  return (
    <>
      {open && (
        <div
          className="fixed inset-0 z-30 bg-black/25 lg:hidden"
          aria-hidden="true"
          onClick={onClose}
        />
      )}

      <aside
        aria-label="AI dining guide"
        className={`
          fixed top-0 right-0 bottom-0 z-40 bg-white border-l border-gray-100
          flex flex-col transition-transform duration-300 ease-out
          w-full sm:w-[400px]
          ${open ? 'translate-x-0' : 'translate-x-full'}
        `}
        style={{ boxShadow: '-8px 0 32px -4px rgb(0 0 0 / 0.10)' }}
      >
        <div className="flex items-center justify-between px-4 py-3
                        bg-gradient-to-r from-brand-600 to-brand-700 shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-white/15 border border-white/20 flex items-center justify-center text-sm">
              🍴
            </div>
            <div>
              <p className="font-semibold text-sm text-white">Forky</p>
              <p className="text-[11px] text-brand-200">AI Dining Guide</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {messages.length > 1 && (
              <button
                type="button" onClick={reset} title="New conversation"
                className="p-2 rounded-lg hover:bg-white/10 transition text-white/70 hover:text-white"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </button>
            )}
            <button
              type="button" onClick={onClose} aria-label="Close AI panel"
              className="p-2 rounded-lg hover:bg-white/10 transition text-white/70 hover:text-white"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <ChatWindow
          messages={messages} loading={loading} onSend={send} onReset={reset}
          onNavigate={() => { onClose(); navigate }}
          isFirstTurn={isFirstTurn} suggestions={EXPLORE_SUGGESTIONS} compact
        />
      </aside>
    </>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Explore() {
  const { user }                            = useAuth()
  const dispatch                            = useDispatch()
  const [searchParams, setSearchParams]     = useSearchParams()
  const [restaurants, setRestaurants]       = useState([])
  const [total, setTotal]                   = useState(0)
  const [pages, setPages]                   = useState(1)
  const [loading, setLoading]               = useState(true)
  const [error, setError]                   = useState('')
  const [aiOpen, setAiOpen]                 = useState(false)

  const [q,          setQ]          = useState(searchParams.get('q')           || '')
  const [cuisine,    setCuisine]    = useState(searchParams.get('cuisine')     || '')
  const [city,       setCity]       = useState(searchParams.get('city')        || '')
  const [priceRange, setPriceRange] = useState(searchParams.get('price_range') || '')
  const [ratingMin,  setRatingMin]  = useState(searchParams.get('rating_min')  || '')
  const [page,       setPage]       = useState(1)

  const fetchRestaurants = useCallback(async (overridePage = page) => {
    setLoading(true); setError('')
    try {
      const params = new URLSearchParams()
      if (q)          params.set('q',          q)
      if (cuisine)    params.set('cuisine',     cuisine)
      if (city)       params.set('city',        city)
      if (priceRange) params.set('price_range', priceRange)
      if (ratingMin)  params.set('rating_min',  ratingMin)
      params.set('page',  overridePage)
      params.set('limit', 12)
      const { data } = await api.get(`/restaurants?${params}`)
      setRestaurants(data.items || [])
      setTotal(data.total  || 0)
      setPages(data.pages  || 1)
      dispatch(setRestaurantsStore({ items: data.items || [], total: data.total || 0, pages: data.pages || 1 }))
    } catch {
      setError('Failed to load restaurants.')
    } finally {
      setLoading(false)
    }
  }, [q, cuisine, city, priceRange, ratingMin, page])

  useEffect(() => { fetchRestaurants(1); setPage(1) }, [cuisine, city, priceRange, ratingMin])
  useEffect(() => { fetchRestaurants(page) }, [page])

  const handleSearch = (e) => { e.preventDefault(); fetchRestaurants(1); setPage(1) }
  const clearFilters  = () => { setQ(''); setCuisine(''); setCity(''); setPriceRange(''); setRatingMin('') }
  const hasFilters    = q || cuisine || city || priceRange || ratingMin

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="section-title">Explore Restaurants</h1>
          {!loading && (
            <p className="text-sm text-gray-500 mt-1">
              {total.toLocaleString()} restaurant{total !== 1 ? 's' : ''} found
            </p>
          )}
        </div>
        {user && (
          <button
            type="button"
            onClick={() => setAiOpen(true)}
            className="btn-primary gap-2 px-4 py-2.5 text-sm"
          >
            <span className="text-base" aria-hidden="true">🍴</span>
            Ask Forky
          </button>
        )}
      </div>

      {/* ── Filters ──────────────────────────────────────────────────────────── */}
      <section aria-label="Search filters" className="card p-5 mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          {/* Search row */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <svg className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <label htmlFor="explore-search" className="sr-only">Search</label>
              <input
                id="explore-search"
                type="search"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Restaurant name, cuisine, or keyword…"
                className="input pl-10"
              />
            </div>
            <button type="submit" className="btn-primary px-6">Search</button>
          </div>

          {/* Filter grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Cuisine */}
            <div>
              <label htmlFor="filter-cuisine" className="label">Cuisine</label>
              <select
                id="filter-cuisine" value={cuisine}
                onChange={(e) => setCuisine(e.target.value)}
                className="input"
              >
                {CUISINES.map((c) => <option key={c} value={c}>{c || 'All cuisines'}</option>)}
              </select>
            </div>

            {/* City */}
            <div>
              <label htmlFor="filter-city" className="label">City</label>
              <input
                id="filter-city" type="text" value={city}
                onChange={(e) => setCity(e.target.value)}
                placeholder="Any city" className="input"
              />
            </div>

            {/* Price */}
            <div>
              <label className="label">Price range</label>
              <div className="flex gap-1.5">
                {PRICE_RANGES.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => setPriceRange(p === priceRange ? '' : p)}
                    className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all duration-150
                      ${p === '' && priceRange === ''
                        ? 'bg-gray-900 text-white border-gray-900'
                        : p !== '' && priceRange === p
                          ? `border ${PRICE_CLASSES[p]} font-bold`
                          : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                      }`}
                  >
                    {p || 'Any'}
                  </button>
                ))}
              </div>
            </div>

            {/* Rating */}
            <div>
              <label className="label">Min rating</label>
              <div className="flex gap-1.5">
                {RATINGS.map(({ label, value }) => (
                  <button
                    key={label}
                    type="button"
                    onClick={() => setRatingMin(value === ratingMin ? '' : value)}
                    className={`flex-1 py-2 rounded-xl text-xs font-semibold border transition-all duration-150
                      ${ratingMin === value
                        ? 'bg-amber-400 text-white border-amber-400 shadow-sm'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                      }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Active filter chips */}
          {hasFilters && (
            <div className="flex items-center gap-2 pt-1 flex-wrap">
              <span className="text-xs text-gray-500">Active:</span>
              {[
                { key: 'cuisine',    value: cuisine,    clear: () => setCuisine('') },
                { key: 'city',       value: city,       clear: () => setCity('') },
                { key: 'price',      value: priceRange, clear: () => setPriceRange('') },
                { key: `${ratingMin}+ ★`, value: ratingMin, clear: () => setRatingMin('') },
                { key: `"${q}"`,     value: q,          clear: () => setQ('') },
              ].filter(({ value }) => value).map(({ key, clear }) => (
                <button
                  key={key}
                  onClick={clear}
                  type="button"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-brand-50 text-brand-700
                             border border-brand-200 rounded-full text-xs font-medium hover:bg-brand-100 transition-colors"
                >
                  {key}
                  <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              ))}
              <button onClick={clearFilters} type="button" className="text-xs text-gray-400 hover:text-gray-600 transition-colors ml-1">
                Clear all
              </button>
            </div>
          )}
        </form>
      </section>

      {/* ── Results ──────────────────────────────────────────────────────────── */}
      {error && (
        <div role="alert" className="p-4 bg-red-50 border border-red-200 text-red-700 rounded-xl mb-4 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : restaurants.length > 0 ? (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {restaurants.map((r) => <RestaurantCard key={r.id} restaurant={r} />)}
          </div>

          {pages > 1 && (
            <nav aria-label="Pagination" className="flex justify-center items-center gap-2 mt-10">
              <button
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
                className="btn-secondary px-4 py-2 text-sm disabled:opacity-40"
              >
                ← Previous
              </button>
              <span className="px-4 py-2 text-sm text-gray-600 font-medium">
                Page {page} of {pages}
              </span>
              <button
                disabled={page === pages}
                onClick={() => setPage(page + 1)}
                className="btn-secondary px-4 py-2 text-sm disabled:opacity-40"
              >
                Next →
              </button>
            </nav>
          )}
        </>
      ) : (
        <div className="text-center py-24">
          <div className="text-6xl mb-4">🔍</div>
          <p className="text-lg font-semibold text-gray-700 mb-1">No restaurants found</p>
          <p className="text-sm text-gray-500 mb-4">Try adjusting your filters or search terms</p>
          {hasFilters && (
            <button onClick={clearFilters} className="btn-secondary text-sm px-5">
              Clear all filters
            </button>
          )}
          {user && (
            <div className="mt-4">
              <button onClick={() => setAiOpen(true)} className="text-brand-600 font-medium hover:underline text-sm">
                Ask Forky for suggestions →
              </button>
            </div>
          )}
        </div>
      )}

      {/* AI slide-out panel */}
      {user && <ExploreAIPanel open={aiOpen} onClose={() => setAiOpen(false)} />}
    </div>
  )
}
