import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import toast from 'react-hot-toast'

const BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

function Avatar({ user, size = 8 }) {
  const dim = `w-${size} h-${size}`
  if (user.profile_photo_url) {
    return (
      <img
        src={`${BASE}${user.profile_photo_url}`}
        alt={user.name}
        className={`${dim} rounded-full object-cover`}
      />
    )
  }
  return (
    <div className={`${dim} rounded-full bg-gradient-to-br from-brand-400 to-brand-600
                    flex items-center justify-center font-bold text-white text-sm select-none shrink-0`}>
      {user.name?.[0]?.toUpperCase() ?? '?'}
    </div>
  )
}

function DropdownItem({ to, onClick, children, danger = false }) {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={`flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium transition-colors ${
        danger ? 'text-red-600 hover:bg-red-50' : 'text-gray-700 hover:bg-gray-50 hover:text-gray-900'
      }`}
    >
      {children}
    </Link>
  )
}

export default function Navbar() {
  const { user, logout }             = useAuth()
  const navigate                     = useNavigate()
  const [dropOpen, setDropOpen]      = useState(false)
  const [mobileOpen, setMobileOpen]  = useState(false)
  const dropRef                      = useRef(null)

  // Close dropdown on outside click
  useEffect(() => {
    if (!dropOpen) return
    const h = (e) => { if (!dropRef.current?.contains(e.target)) setDropOpen(false) }
    document.addEventListener('mousedown', h)
    return () => document.removeEventListener('mousedown', h)
  }, [dropOpen])

  // Close mobile on resize
  useEffect(() => {
    const h = () => { if (window.innerWidth >= 768) setMobileOpen(false) }
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [])

  const handleLogout = () => {
    logout()
    toast.success('Logged out successfully')
    navigate('/')
    setDropOpen(false)
    setMobileOpen(false)
  }

  const closeAll = () => { setDropOpen(false); setMobileOpen(false) }

  const linkCls = ({ isActive }) =>
    `text-sm font-medium transition-colors pb-px border-b-2 ${
      isActive
        ? 'text-brand-600 border-brand-600'
        : 'text-gray-600 hover:text-gray-900 border-transparent'
    }`

  return (
    <header
      className="sticky top-0 z-40 bg-white/95 backdrop-blur-sm border-b border-gray-100"
      style={{ boxShadow: '0 1px 0 0 rgb(0 0 0 / 0.05)' }}
    >
      <nav
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-6"
        aria-label="Main navigation"
      >
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 shrink-0" aria-label="ForkFinder home">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700
                          flex items-center justify-center shadow-sm">
            <span className="text-white text-sm" aria-hidden="true">🍴</span>
          </div>
          <span className="font-extrabold text-lg tracking-tight text-gray-900">
            Fork<span className="text-brand-600">Finder</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-7 flex-1">
          <NavLink to="/explore"  className={linkCls}>Explore</NavLink>
          {user && <NavLink to="/favorites" className={linkCls}>Favorites</NavLink>}
          {user && <NavLink to="/history"   className={linkCls}>History</NavLink>}
          {user?.role === 'owner' && (
            <NavLink to="/owner/dashboard" className={linkCls}>Dashboard</NavLink>
          )}
        </div>

        {/* Desktop right */}
        <div className="hidden md:flex items-center gap-3">
          {user ? (
            <>
              <Link
                to="/add-restaurant"
                className="btn-secondary text-xs px-3.5 py-2 gap-1.5 rounded-lg"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
                Add Restaurant
              </Link>

              {/* Avatar dropdown */}
              <div className="relative" ref={dropRef}>
                <button
                  onClick={() => setDropOpen(!dropOpen)}
                  aria-expanded={dropOpen}
                  aria-haspopup="menu"
                  className="flex items-center gap-2 pl-1.5 pr-3 py-1.5 rounded-full
                             border border-gray-200 hover:border-gray-300 hover:bg-gray-50
                             transition-all duration-150"
                >
                  <Avatar user={user} size={7} />
                  <span className="text-sm font-semibold text-gray-800 max-w-[96px] truncate">
                    {user.name?.split(' ')[0]}
                  </span>
                  <svg
                    className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${dropOpen ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>

                {dropOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 top-full mt-2 w-54 bg-white rounded-2xl border border-gray-100
                               py-1.5 z-50 animate-fade-up"
                    style={{ width: 216, boxShadow: '0 10px 30px -4px rgb(0 0 0 / 0.12), 0 4px 8px -4px rgb(0 0 0 / 0.08)' }}
                  >
                    {/* User info */}
                    <div className="px-4 py-3 border-b border-gray-100">
                      <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">{user.email}</p>
                    </div>

                    <div className="py-1">
                      <DropdownItem to="/profile"     onClick={closeAll}>👤 Profile</DropdownItem>
                      <DropdownItem to="/preferences" onClick={closeAll}>⚙️ Preferences</DropdownItem>
                    </div>

                    {user.role === 'owner' && (
                      <div className="border-t border-gray-100 py-1">
                        <p className="px-4 pt-2.5 pb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                          Owner Tools
                        </p>
                        <DropdownItem to="/owner/dashboard"   onClick={closeAll}>📊 Dashboard</DropdownItem>
                        <DropdownItem to="/owner/restaurants" onClick={closeAll}>🏪 My Restaurants</DropdownItem>
                        <DropdownItem to="/owner/reviews"     onClick={closeAll}>⭐ Reviews</DropdownItem>
                        <DropdownItem to="/claim-restaurant"  onClick={closeAll}>✅ Claim Restaurant</DropdownItem>
                      </div>
                    )}

                    <div className="border-t border-gray-100 pt-1">
                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium
                                   text-red-600 hover:bg-red-50 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round"
                            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Log out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login"    className="btn-ghost   px-4 py-2">Log in</Link>
              <Link to="/register" className="btn-primary px-4 py-2">Sign up free</Link>
            </>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded-xl hover:bg-gray-100 transition-colors"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle menu"
          aria-expanded={mobileOpen}
        >
          <svg className="w-5 h-5 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d={mobileOpen ? 'M6 18L18 6M6 6l12 12' : 'M4 6h16M4 12h16M4 18h16'} />
          </svg>
        </button>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-100 bg-white">
          {user && (
            <div className="flex items-center gap-3 px-4 py-4 border-b border-gray-100">
              <Avatar user={user} size={10} />
              <div className="min-w-0">
                <p className="text-sm font-semibold text-gray-900 truncate">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
          )}

          <nav className="px-2 py-2 space-y-0.5" aria-label="Mobile navigation">
            <MobileNavLink to="/explore"         onClick={closeAll}>🔍  Explore</MobileNavLink>
            {user && <MobileNavLink to="/favorites" onClick={closeAll}>❤️  Favorites</MobileNavLink>}
            {user && <MobileNavLink to="/history"   onClick={closeAll}>📋  History</MobileNavLink>}
            {user && <MobileNavLink to="/add-restaurant" onClick={closeAll}>➕  Add Restaurant</MobileNavLink>}

            {user?.role === 'owner' && (
              <>
                <p className="px-3 pt-3 pb-1 text-[10px] font-semibold text-gray-400 uppercase tracking-wider">
                  Owner Tools
                </p>
                <MobileNavLink to="/owner/dashboard"   onClick={closeAll}>📊  Dashboard</MobileNavLink>
                <MobileNavLink to="/owner/restaurants" onClick={closeAll}>🏪  My Restaurants</MobileNavLink>
                <MobileNavLink to="/owner/reviews"     onClick={closeAll}>⭐  Reviews</MobileNavLink>
                <MobileNavLink to="/claim-restaurant"  onClick={closeAll}>✅  Claim Restaurant</MobileNavLink>
              </>
            )}

            {user && (
              <>
                <div className="border-t border-gray-100 my-1.5" />
                <MobileNavLink to="/profile"     onClick={closeAll}>👤  Profile</MobileNavLink>
                <MobileNavLink to="/preferences" onClick={closeAll}>⚙️  Preferences</MobileNavLink>
                <button
                  onClick={handleLogout}
                  className="w-full text-left px-3 py-2.5 rounded-xl text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
                >
                  🚪  Log out
                </button>
              </>
            )}
          </nav>

          {!user && (
            <div className="flex gap-2 px-4 py-4 border-t border-gray-100">
              <Link to="/login"    onClick={closeAll} className="btn-secondary flex-1 justify-center">Log in</Link>
              <Link to="/register" onClick={closeAll} className="btn-primary  flex-1 justify-center">Sign up</Link>
            </div>
          )}
        </div>
      )}
    </header>
  )
}

function MobileNavLink({ to, onClick, children }) {
  return (
    <NavLink
      to={to}
      onClick={onClick}
      className={({ isActive }) =>
        `block px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
          isActive ? 'bg-brand-50 text-brand-700' : 'text-gray-700 hover:bg-gray-50'
        }`
      }
    >
      {children}
    </NavLink>
  )
}
