import { Link } from 'react-router-dom'

const EXPLORE_LINKS = [
  { to: '/explore',        label: 'Browse Restaurants' },
  { to: '/add-restaurant', label: 'Add a Restaurant' },
  { to: '/register',       label: 'Join ForkFinder' },
]

const ACCOUNT_LINKS = [
  { to: '/login',       label: 'Log in' },
  { to: '/register',    label: 'Sign up free' },
  { to: '/preferences', label: 'Dining Preferences' },
]

export default function Footer() {
  return (
    <footer
      className="bg-white border-t border-gray-100 mt-16"
      role="contentinfo"
      style={{ boxShadow: '0 -1px 0 0 rgb(0 0 0 / 0.04)' }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-10">

          {/* Brand */}
          <div>
            <Link to="/" className="flex items-center gap-2.5 mb-3">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700
                              flex items-center justify-center shadow-sm">
                <span className="text-white text-sm">🍴</span>
              </div>
              <span className="font-extrabold text-lg tracking-tight text-gray-900">
                Fork<span className="text-brand-600">Finder</span>
              </span>
            </Link>
            <p className="text-sm text-gray-500 leading-relaxed max-w-xs">
              Discover, review, and share the best restaurants near you — powered by AI.
            </p>
          </div>

          {/* Explore */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Explore</h3>
            <nav aria-label="Footer explore links">
              <ul className="space-y-2.5">
                {EXPLORE_LINKS.map(({ to, label }) => (
                  <li key={to}>
                    <Link to={to} className="text-sm text-gray-500 hover:text-brand-600 transition-colors">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>

          {/* Account */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4">Account</h3>
            <nav aria-label="Footer account links">
              <ul className="space-y-2.5">
                {ACCOUNT_LINKS.map(({ to, label }) => (
                  <li key={to}>
                    <Link to={to} className="text-sm text-gray-500 hover:text-brand-600 transition-colors">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </nav>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 pt-6 border-t border-gray-100 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-gray-400">
            © {new Date().getFullYear()} ForkFinder · Built for DATA 236 Lab 1
          </p>
          <div className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" aria-hidden="true" />
            AI-powered by Forky
          </div>
        </div>
      </div>
    </footer>
  )
}
