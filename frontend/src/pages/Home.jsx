import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useDispatch } from 'react-redux'
import api from '../services/api'
import RestaurantCard from '../components/restaurants/RestaurantCard'
import LoadingSpinner from '../components/common/LoadingSpinner'
import { useAuth } from '../context/AuthContext'
import { useChat } from '../hooks/useChat'
import ChatWindow from '../components/ai/ChatWindow'
import { setFeatured as setFeaturedStore } from '../store/slices/restaurantsSlice'

const CUISINES = ['Italian', 'Japanese', 'Mexican', 'Indian', 'American', 'Thai', 'Chinese', 'Mediterranean']

const HOME_SUGGESTIONS = [
  '🍝  Best Italian near me',
  '💑  Romantic dinner for two',
  '💸  Good food under $$',
  '🥗  Top vegan restaurants',
]

// ─── Inline AI chat panel ─────────────────────────────────────────────────────
function HomeAIChat() {
  const { messages, loading, send, reset, isFirstTurn } = useChat()

  return (
    <div className="card flex flex-col overflow-hidden" style={{ height: 540 }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3
                      bg-gradient-to-r from-brand-600 to-brand-700 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-white/15 flex items-center justify-center text-sm border border-white/20">
            🍴
          </div>
          <div>
            <p className="font-semibold text-sm text-white leading-tight">Forky</p>
            <p className="text-[11px] text-brand-200 leading-tight">AI Dining Guide</p>
          </div>
        </div>
        {messages.length > 1 && (
          <button
            type="button"
            onClick={reset}
            title="New conversation"
            className="p-2 rounded-lg hover:bg-white/10 transition text-white/70 hover:text-white"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        )}
      </div>

      <ChatWindow
        messages={messages}
        loading={loading}
        onSend={send}
        onReset={reset}
        isFirstTurn={isFirstTurn}
        suggestions={HOME_SUGGESTIONS}
        compact={false}
      />
    </div>
  )
}

// ─── Quick stat card ──────────────────────────────────────────────────────────
function QuickStat({ label, value, icon, to }) {
  return (
    <Link
      to={to}
      className="card p-4 flex items-center gap-3.5 hover:-translate-y-0.5 transition-all duration-150 group"
      style={{ boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.06)' }}
    >
      <div className="w-10 h-10 rounded-xl bg-brand-50 flex items-center justify-center text-xl shrink-0">
        {icon}
      </div>
      <div>
        <p className="text-xl font-bold text-gray-900 group-hover:text-brand-600 transition-colors">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </Link>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────
export default function Home() {
  const { user }      = useAuth()
  const navigate      = useNavigate()
  const dispatch      = useDispatch()
  const [featured, setFeatured] = useState([])
  const [loading, setLoading]   = useState(true)
  const [searchQ, setSearchQ]   = useState('')
  const [stats, setStats]       = useState(null)

  useEffect(() => {
    api.get('/restaurants?limit=6&sort=rating')
      .then(({ data }) => {
        const items = data.items || []
        setFeatured(items)
        dispatch(setFeaturedStore(items))
      })
      .finally(() => setLoading(false))
    if (user) {
      api.get('/users/me/history').then(({ data }) => setStats(data)).catch(() => {})
    }
  }, [user])

  const handleSearch = (e) => {
    e.preventDefault()
    navigate(`/explore?q=${encodeURIComponent(searchQ)}`)
  }

  // ── Logged-in dashboard ───────────────────────────────────────────────────
  if (user) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome */}
        <div className="mb-7">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user.name?.split(' ')[0] || 'there'} 👋
          </h1>
          <p className="text-gray-500 text-sm mt-1">What are you in the mood for today?</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-7">
          {/* AI Chat — 2/3 width */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <h2 className="font-bold text-gray-900">AI Dining Guide</h2>
              <span className="badge bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200 text-[10px]">
                ✨ Powered by AI
              </span>
            </div>
            <HomeAIChat />
          </div>

          {/* Sidebar */}
          <aside className="space-y-5">
            {stats && (
              <div>
                <h2 className="font-bold text-gray-900 mb-3">Your Activity</h2>
                <div className="space-y-2.5">
                  <QuickStat label="Reviews written"    value={stats.total_reviews ?? 0}           icon="📝" to="/history" />
                  <QuickStat label="Restaurants added"  value={stats.total_restaurants_added ?? 0} icon="🏪" to="/history" />
                  <QuickStat label="Saved favorites"    value="View"                               icon="❤️" to="/favorites" />
                </div>
              </div>
            )}

            <div className="card p-4">
              <h2 className="font-bold text-gray-900 mb-3">Quick Actions</h2>
              <nav className="space-y-1">
                {[
                  { to: '/explore',        label: '🔍 Explore restaurants' },
                  { to: '/add-restaurant', label: '➕ Add a restaurant' },
                  { to: '/favorites',      label: '❤️ My favorites' },
                  { to: '/history',        label: '📋 My history' },
                  ...(user.role === 'owner' ? [{ to: '/owner/dashboard', label: '📊 Owner dashboard' }] : []),
                ].map(({ to, label }) => (
                  <Link
                    key={to}
                    to={to}
                    className="flex items-center px-3 py-2.5 rounded-xl text-sm font-medium text-gray-700
                               hover:bg-brand-50 hover:text-brand-700 transition-colors"
                  >
                    {label}
                  </Link>
                ))}
              </nav>
            </div>
          </aside>
        </div>

        {/* Cuisine browse */}
        <section className="mt-10" aria-label="Browse by cuisine">
          <h2 className="font-bold text-gray-900 mb-3">Browse by Cuisine</h2>
          <div className="flex gap-2.5 overflow-x-auto pb-2 scrollbar-hide">
            {CUISINES.map((c) => (
              <Link key={c} to={`/explore?cuisine=${c}`} className="cuisine-chip">{c}</Link>
            ))}
          </div>
        </section>

        {/* Top rated */}
        <section className="mt-8" aria-label="Top rated restaurants">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-900">Top Rated Near You</h2>
            <Link to="/explore" className="text-brand-600 text-sm font-semibold hover:underline">View all →</Link>
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : featured.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {featured.map((r) => <RestaurantCard key={r.id} restaurant={r} />)}
            </div>
          ) : (
            <div className="text-center py-14 text-gray-500 card p-10">
              <div className="text-4xl mb-2">🍽️</div>
              <p>No restaurants yet. <Link to="/add-restaurant" className="text-brand-600 hover:underline">Add the first one!</Link></p>
            </div>
          )}
        </section>
      </div>
    )
  }

  // ── Guest / marketing layout ──────────────────────────────────────────────
  return (
    <div>
      {/* Hero */}
      <section
        className="relative text-white py-28 px-4 overflow-hidden"
        style={{ background: 'linear-gradient(135deg, #be123c 0%, #881337 55%, #4c0519 100%)' }}
        aria-label="Hero"
      >
        {/* Decorative circles */}
        <div className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute -bottom-32 -left-16 w-80 h-80 rounded-full bg-white/5 pointer-events-none" />

        <div className="relative max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 border border-white/20 text-sm font-medium text-brand-100 mb-6">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            AI-powered restaurant discovery
          </div>

          <h1 className="text-5xl md:text-6xl font-extrabold leading-tight tracking-tight text-balance">
            Find your next<br />
            <span className="text-brand-200">favorite restaurant</span>
          </h1>

          <p className="mt-5 text-lg text-brand-100 max-w-xl mx-auto leading-relaxed">
            Discover top-rated restaurants, honest reviews, and personalized recommendations powered by AI.
          </p>

          <form onSubmit={handleSearch} className="mt-9 flex gap-2 max-w-xl mx-auto" role="search">
            <label htmlFor="hero-search" className="sr-only">Search restaurants</label>
            <div className="relative flex-1">
              <svg className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
                fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <input
                id="hero-search"
                type="search"
                value={searchQ}
                onChange={(e) => setSearchQ(e.target.value)}
                placeholder="Cuisine, restaurant name, or city…"
                className="w-full pl-12 pr-5 py-4 rounded-2xl text-gray-900 text-sm
                           focus:outline-none focus:ring-2 focus:ring-brand-300 focus:ring-offset-0
                           placeholder:text-gray-400"
              />
            </div>
            <button
              type="submit"
              className="px-7 py-4 rounded-2xl bg-white text-brand-700 font-bold text-sm
                         hover:bg-brand-50 active:scale-[0.97] transition-all shadow-lg"
            >
              Search
            </button>
          </form>

          <div className="mt-5 flex items-center justify-center gap-6 text-sm text-brand-200">
            <span>🍕 1000+ restaurants</span>
            <span className="opacity-40">·</span>
            <span>⭐ Verified reviews</span>
            <span className="opacity-40">·</span>
            <span>🤖 AI recommendations</span>
          </div>
        </div>
      </section>

      {/* Cuisine chips */}
      <section className="py-8 px-4 bg-white border-b border-gray-100" aria-label="Browse by cuisine">
        <div className="max-w-7xl mx-auto">
          <div className="flex gap-2.5 overflow-x-auto pb-1 scrollbar-hide">
            {CUISINES.map((c) => (
              <Link key={c} to={`/explore?cuisine=${c}`} className="cuisine-chip">{c}</Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured restaurants */}
      <section className="py-14 px-4" aria-label="Featured restaurants">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-7">
            <div>
              <h2 className="section-title">Top Rated Restaurants</h2>
              <p className="text-sm text-gray-500 mt-1">Highly rated by our community</p>
            </div>
            <Link to="/explore" className="text-brand-600 text-sm font-semibold hover:underline shrink-0">
              View all →
            </Link>
          </div>
          {loading ? <LoadingSpinner /> : featured.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {featured.map((r) => <RestaurantCard key={r.id} restaurant={r} />)}
            </div>
          ) : (
            <div className="text-center py-16 text-gray-500 card p-12">
              <div className="text-5xl mb-3">🍽️</div>
              <p>No restaurants yet. <Link to="/add-restaurant" className="text-brand-600 hover:underline">Add one!</Link></p>
            </div>
          )}
        </div>
      </section>

      {/* AI teaser */}
      <section className="py-18 px-4 bg-gray-50 border-y border-gray-100" aria-label="AI dining guide">
        <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-12 items-center">
          <div>
            <span className="badge bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200 mb-4 inline-flex">
              ✨ AI-Powered
            </span>
            <h2 className="text-3xl font-bold text-gray-900 leading-tight">
              Meet Forky, your personal dining guide
            </h2>
            <p className="mt-4 text-gray-600 leading-relaxed">
              Tell Forky what you're craving and get personalized restaurant recommendations
              in seconds — tailored to your taste, budget, and mood.
            </p>
            <Link to="/register" className="btn-primary inline-flex mt-6 px-6 py-3 text-base">
              Try it free →
            </Link>
          </div>

          {/* Mock chat bubble */}
          <div className="card p-5 space-y-3.5 text-sm">
            {[
              { role: 'user',      text: 'I want something romantic under $50 for two.' },
              { role: 'assistant', text: "I'd recommend Osteria Stella — candlelit Italian, avg $45 for two, rated 4.8 ⭐. Shall I find more options?" },
              { role: 'user',      text: 'Yes! Something with a nice view?' },
              { role: 'assistant', text: 'Vista Rooftop has stunning city views, modern American cuisine, and rave reviews for date nights! 🌆' },
            ].map((m, i) => (
              <div key={i} className={`flex items-end gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {m.role === 'assistant' && (
                  <div className="w-6 h-6 rounded-full bg-brand-100 flex items-center justify-center text-xs shrink-0">🍴</div>
                )}
                <div className={`max-w-[82%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
                  ${m.role === 'user'
                    ? 'bg-brand-600 text-white rounded-br-sm'
                    : 'bg-gray-100 text-gray-800 rounded-bl-sm'
                  }`}>
                  {m.text}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section
        className="py-18 px-4 text-white"
        style={{ background: 'linear-gradient(135deg, #e11d48 0%, #881337 100%)' }}
        aria-label="Call to action"
      >
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold">Ready to explore?</h2>
          <p className="mt-3 text-brand-100">
            Sign up to save favorites, write reviews, and get AI-powered recommendations.
          </p>
          <div className="mt-7 flex gap-3 justify-center flex-wrap">
            <Link
              to="/register"
              className="px-7 py-3.5 bg-white text-brand-700 rounded-xl font-bold text-sm
                         hover:bg-brand-50 active:scale-[0.97] transition-all shadow-lg"
            >
              Get started free
            </Link>
            <Link
              to="/explore"
              className="px-7 py-3.5 border border-brand-300 text-white rounded-xl font-semibold text-sm
                         hover:bg-brand-700/50 active:scale-[0.97] transition-all"
            >
              Browse restaurants
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
