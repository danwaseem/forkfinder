import { useState } from 'react'

/**
 * FilterPanel
 *
 * A collapsible filter sidebar / panel for restaurant search.
 *
 * Props:
 *   filters      object        — current filter state (see defaultFilters shape below)
 *   onChange     (filters) => void  — called with the full updated filters object
 *   onReset      () => void    — called when "Clear all" is clicked
 *   cuisines     string[]      — list of cuisine options to show
 *   priceRanges  string[]      — list of price range options (default ['$','$$','$$$','$$$$'])
 *   collapsed    boolean       — start collapsed on mobile (default: false)
 *   className    string        — extra wrapper classes
 *
 * Filter shape:
 *   { cuisine: string, priceRange: string, minRating: number, city: string, claimed: boolean|null }
 */

const DEFAULT_CUISINES = [
  'Italian', 'Japanese', 'Mexican', 'Indian', 'American',
  'Thai', 'Chinese', 'Mediterranean', 'Korean', 'Vietnamese',
  'Greek', 'French', 'BBQ', 'Seafood', 'Vegan',
]
const DEFAULT_PRICES = ['$', '$$', '$$$', '$$$$']
const RATINGS = [4, 3, 2, 1]

function SectionTitle({ children }) {
  return <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">{children}</h3>
}

function Chip({ label, active, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`px-3 py-1.5 rounded-full text-sm font-medium border transition
        ${active
          ? 'bg-brand-600 text-white border-brand-600'
          : 'border-gray-200 text-gray-600 hover:border-brand-300 hover:text-brand-700 bg-white'
        }`}
    >
      {label}
    </button>
  )
}

export default function FilterPanel({
  filters = {},
  onChange,
  onReset,
  cuisines = DEFAULT_CUISINES,
  priceRanges = DEFAULT_PRICES,
  collapsed: initialCollapsed = false,
  className = '',
}) {
  const [isOpen, setIsOpen] = useState(typeof window !== 'undefined' && window.innerWidth >= 1024 ? true : !initialCollapsed)

  const set = (key, value) => onChange?.({ ...filters, [key]: value })

  const hasActiveFilters = (
    filters.cuisine ||
    filters.priceRange ||
    filters.minRating ||
    filters.city ||
    filters.claimed != null
  )

  return (
    <aside className={`bg-white rounded-2xl border border-gray-100 shadow-sm ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
          </svg>
          <span className="font-semibold text-sm text-gray-800">Filters</span>
          {hasActiveFilters && (
            <span className="w-2 h-2 rounded-full bg-brand-500" aria-label="Filters active" />
          )}
        </div>

        <div className="flex items-center gap-2">
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onReset}
              className="text-xs text-brand-600 hover:underline font-medium"
            >
              Clear all
            </button>
          )}
          {/* Mobile toggle */}
          <button
            type="button"
            onClick={() => setIsOpen((v) => !v)}
            aria-expanded={isOpen}
            aria-label={isOpen ? 'Collapse filters' : 'Expand filters'}
            className="lg:hidden p-1 rounded text-gray-400 hover:text-gray-600"
          >
            <svg className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
              fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Body */}
      {isOpen && (
        <div className="p-4 space-y-6">
          {/* Cuisine */}
          <div>
            <SectionTitle>Cuisine</SectionTitle>
            <div className="flex flex-wrap gap-2">
              {cuisines.map((c) => (
                <Chip
                  key={c}
                  label={c}
                  active={filters.cuisine === c}
                  onClick={() => set('cuisine', filters.cuisine === c ? '' : c)}
                />
              ))}
            </div>
          </div>

          {/* Price range */}
          <div>
            <SectionTitle>Price Range</SectionTitle>
            <div className="flex gap-2">
              {priceRanges.map((p) => (
                <Chip
                  key={p}
                  label={p}
                  active={filters.priceRange === p}
                  onClick={() => set('priceRange', filters.priceRange === p ? '' : p)}
                />
              ))}
            </div>
          </div>

          {/* Min rating */}
          <div>
            <SectionTitle>Minimum Rating</SectionTitle>
            <div className="flex flex-col gap-1.5">
              {RATINGS.map((r) => (
                <label key={r} className="flex items-center gap-2 cursor-pointer group">
                  <input
                    type="radio"
                    name="minRating"
                    checked={filters.minRating === r}
                    onChange={() => set('minRating', filters.minRating === r ? null : r)}
                    className="sr-only"
                  />
                  <span className={`w-4 h-4 rounded-full border-2 flex items-center justify-center transition
                    ${filters.minRating === r ? 'border-brand-600 bg-brand-600' : 'border-gray-300 group-hover:border-brand-400'}`}>
                    {filters.minRating === r && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                  </span>
                  <span className="text-sm text-gray-700 flex items-center gap-1">
                    {Array.from({ length: r }).map((_, i) => (
                      <span key={i} className="text-amber-400 text-sm">★</span>
                    ))}
                    <span className="text-gray-500 text-xs">& up</span>
                  </span>
                </label>
              ))}
              {filters.minRating && (
                <button
                  type="button"
                  onClick={() => set('minRating', null)}
                  className="text-xs text-gray-400 hover:text-gray-600 text-left mt-0.5"
                >
                  Clear rating
                </button>
              )}
            </div>
          </div>

          {/* City */}
          <div>
            <SectionTitle>City</SectionTitle>
            <input
              type="text"
              value={filters.city || ''}
              onChange={(e) => set('city', e.target.value)}
              placeholder="e.g. San Francisco"
              className="input text-sm py-2"
            />
          </div>

          {/* Claimed only */}
          <div>
            <label className="flex items-center gap-3 cursor-pointer group">
              <button
                type="button"
                role="switch"
                aria-checked={!!filters.claimed}
                onClick={() => set('claimed', filters.claimed ? null : true)}
                className={`relative w-9 h-5 rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-brand-400 focus:ring-offset-1
                  ${filters.claimed ? 'bg-brand-600' : 'bg-gray-200'}`}
              >
                <span className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform
                  ${filters.claimed ? 'translate-x-4' : 'translate-x-0'}`} />
              </button>
              <span className="text-sm text-gray-700">Claimed restaurants only</span>
            </label>
          </div>
        </div>
      )}
    </aside>
  )
}

