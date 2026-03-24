/**
 * PreferencesForm
 *
 * Reusable dining preferences editor. Fully controlled.
 *
 * Props:
 *   prefs       object   — { cuisine_preferences, price_range, search_radius,
 *                            dietary_restrictions, ambiance_preferences, sort_preference }
 *   onChange    (prefs) => void  — called with the full updated prefs object
 *   onSubmit    (e) => void
 *   saving      boolean
 *   error       string
 *   className   string
 */
import ErrorAlert from '../common/ErrorAlert'

const CUISINES = [
  'Italian','Japanese','Chinese','Mexican','Indian','Thai','American',
  'French','Mediterranean','Korean','Vietnamese','Greek','Spanish',
  'Middle Eastern','African','BBQ','Seafood','Vegan','Vegetarian',
]
const PRICE_RANGES = ['$', '$$', '$$$', '$$$$']
const DIETARY = [
  'None','Vegetarian','Vegan','Gluten-Free','Halal','Kosher','Dairy-Free','Nut-Free',
]
const AMBIANCE = [
  'Casual','Fine Dining','Romantic','Family-Friendly','Trendy',
  'Outdoor','Sports Bar','Cozy','Fast Casual',
]
const SORT_OPTIONS = [
  { value: 'rating',   label: 'Highest Rated' },
  { value: 'distance', label: 'Nearest' },
  { value: 'newest',   label: 'Newest' },
]

function SectionCard({ title, children }) {
  return (
    <div className="card p-6">
      <h2 className="font-bold text-gray-900 mb-3">{title}</h2>
      {children}
    </div>
  )
}

function ToggleChip({ label, active, onToggle }) {
  return (
    <button
      type="button"
      onClick={onToggle}
      aria-pressed={active}
      className={`px-3 py-1.5 rounded-full text-sm font-medium border transition
        ${active
          ? 'bg-brand-600 text-white border-brand-600'
          : 'border-gray-200 text-gray-600 hover:border-brand-300 bg-white'
        }`}
    >
      {label}
    </button>
  )
}

export default function PreferencesForm({
  prefs = {},
  onChange,
  onSubmit,
  saving = false,
  error,
  className = '',
}) {
  const toggleArr = (key, val) => {
    const arr = prefs[key] || []
    onChange?.({
      ...prefs,
      [key]: arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val],
    })
  }

  const set = (key, val) => onChange?.({ ...prefs, [key]: val })

  return (
    <form onSubmit={onSubmit} className={`space-y-6 ${className}`}>
      <ErrorAlert message={error} />

      {/* Cuisines */}
      <SectionCard title="Preferred Cuisines">
        <div className="flex flex-wrap gap-2">
          {CUISINES.map((c) => (
            <ToggleChip
              key={c}
              label={c}
              active={prefs.cuisine_preferences?.includes(c)}
              onToggle={() => toggleArr('cuisine_preferences', c)}
            />
          ))}
        </div>
      </SectionCard>

      {/* Price + radius */}
      <div className="card p-6 grid sm:grid-cols-2 gap-6">
        <div>
          <h2 className="font-bold text-gray-900 mb-3">Price Range</h2>
          <div className="flex gap-2">
            {PRICE_RANGES.map((p) => (
              <button
                key={p}
                type="button"
                onClick={() => set('price_range', prefs.price_range === p ? '' : p)}
                aria-pressed={prefs.price_range === p}
                className={`px-4 py-2 rounded-xl font-semibold text-sm border transition
                  ${prefs.price_range === p
                    ? 'bg-brand-600 text-white border-brand-600'
                    : 'border-gray-200 text-gray-600 hover:border-brand-300'
                  }`}
              >
                {p}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="prefs-search-radius" className="font-bold text-gray-900 block mb-3">
            Search Radius: <span className="text-brand-600">{prefs.search_radius ?? 10} mi</span>
          </label>
          <input
            id="prefs-search-radius"
            type="range"
            min={1}
            max={100}
            value={prefs.search_radius ?? 10}
            onChange={(e) => set('search_radius', parseInt(e.target.value))}
            className="w-full accent-brand-600"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1 mi</span>
            <span>100 mi</span>
          </div>
        </div>
      </div>

      {/* Dietary restrictions */}
      <SectionCard title="Dietary Restrictions">
        <div className="flex flex-wrap gap-2">
          {DIETARY.map((d) => (
            <ToggleChip
              key={d}
              label={d}
              active={prefs.dietary_restrictions?.includes(d)}
              onToggle={() => toggleArr('dietary_restrictions', d)}
            />
          ))}
        </div>
      </SectionCard>

      {/* Ambiance */}
      <SectionCard title="Ambiance Preferences">
        <div className="flex flex-wrap gap-2">
          {AMBIANCE.map((a) => (
            <ToggleChip
              key={a}
              label={a}
              active={prefs.ambiance_preferences?.includes(a)}
              onToggle={() => toggleArr('ambiance_preferences', a)}
            />
          ))}
        </div>
      </SectionCard>

      {/* Default sort */}
      <SectionCard title="Default Sort">
        <div className="flex gap-3 flex-wrap">
          {SORT_OPTIONS.map((o) => (
            <label
              key={o.value}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl border cursor-pointer transition
                ${prefs.sort_preference === o.value
                  ? 'border-brand-500 bg-brand-50 text-brand-700'
                  : 'border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
            >
              <input
                type="radio"
                name="sort_preference"
                value={o.value}
                checked={prefs.sort_preference === o.value}
                onChange={() => set('sort_preference', o.value)}
                className="sr-only"
              />
              {o.label}
            </label>
          ))}
        </div>
      </SectionCard>

      <button type="submit" disabled={saving} className="btn-primary px-8 py-3">
        {saving ? 'Saving…' : 'Save Preferences'}
      </button>
    </form>
  )
}
