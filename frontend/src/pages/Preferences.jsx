import { useEffect, useState } from 'react'
import { preferencesApi } from '../services/preferences'
import LoadingSpinner from '../components/common/LoadingSpinner'
import toast from 'react-hot-toast'

const CUISINES = [
  'American', 'Italian', 'Mexican', 'Japanese', 'Chinese', 'Indian', 'Thai',
  'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek', 'Spanish',
  'Middle Eastern', 'Caribbean', 'Ethiopian', 'Seafood', 'BBQ', 'Pizza',
  'Burgers', 'Sushi', 'Vegan', 'Vegetarian',
]

const DIETARY = [
  'Vegetarian', 'Vegan', 'Gluten-Free', 'Halal', 'Kosher',
  'Dairy-Free', 'Nut-Free', 'Low-Carb', 'Keto', 'Paleo',
  'Shellfish-Free', 'Soy-Free',
]

const AMBIANCES = [
  'Casual', 'Fine Dining', 'Family-Friendly', 'Romantic', 'Outdoor Seating',
  'Sports Bar', 'Live Music', 'Quick Bite', 'Brunch Spot', 'Late Night',
  'Rooftop', 'Waterfront',
]

const PRICE_RANGES = [
  { value: '$', label: '$ · Budget' },
  { value: '$$', label: '$$ · Mid-range' },
  { value: '$$$', label: '$$$ · Upscale' },
  { value: '$$$$', label: '$$$$ · Fine dining' },
]

const SORT_OPTIONS = [
  { value: 'rating', label: 'Highest rated' },
  { value: 'newest', label: 'Newest' },
  { value: 'most_reviewed', label: 'Most reviewed' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
]

function ToggleChip({ label, selected, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={selected}
      className={`px-3 py-1.5 rounded-full text-sm font-medium border transition-all
        ${selected
          ? 'bg-brand-600 text-white border-brand-600'
          : 'bg-white text-gray-600 border-gray-200 hover:border-brand-400 hover:text-brand-600'
        }`}
    >
      {label}
    </button>
  )
}

export default function Preferences() {
  const [prefs, setPrefs] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  // Local form state
  const [cuisines, setCuisines] = useState([])
  const [dietary, setDietary] = useState([])
  const [ambiance, setAmbiance] = useState([])
  const [priceRange, setPriceRange] = useState('')
  const [searchRadius, setSearchRadius] = useState(10)
  const [locations, setLocations] = useState([])
  const [locationInput, setLocationInput] = useState('')
  const [sortPref, setSortPref] = useState('rating')

  useEffect(() => {
    preferencesApi.get()
      .then((data) => {
        setPrefs(data)
        setCuisines(data.cuisine_preferences || [])
        setDietary(data.dietary_restrictions || [])
        setAmbiance(data.ambiance_preferences || [])
        setPriceRange(data.price_range || '')
        setSearchRadius(data.search_radius || 10)
        setLocations(data.preferred_locations || [])
        setSortPref(data.sort_preference || 'rating')
      })
      .catch(() => toast.error('Failed to load preferences'))
      .finally(() => setLoading(false))
  }, [])

  const toggle = (list, setList, value) => {
    setList((prev) =>
      prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]
    )
  }

  const addLocation = () => {
    const v = locationInput.trim()
    if (v && !locations.includes(v)) {
      setLocations((prev) => [...prev, v])
    }
    setLocationInput('')
  }

  const save = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await preferencesApi.update({
        cuisine_preferences: cuisines,
        dietary_restrictions: dietary,
        ambiance_preferences: ambiance,
        price_range: priceRange || null,
        search_radius: searchRadius,
        preferred_locations: locations,
        sort_preference: sortPref,
      })
      toast.success('Preferences saved!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingSpinner />

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-8">
        <h1 className="section-title">Dining Preferences</h1>
        <p className="text-gray-500 text-sm mt-1">
          Tell us what you love — the AI assistant uses these to personalize recommendations.
        </p>
      </div>

      <form onSubmit={save} className="space-y-8">

        {/* Cuisine preferences */}
        <section className="card p-6" aria-labelledby="cuisine-heading">
          <h2 id="cuisine-heading" className="font-semibold text-gray-900 mb-1">Favourite Cuisines</h2>
          <p className="text-xs text-gray-400 mb-4">Select all that apply</p>
          <div className="flex flex-wrap gap-2">
            {CUISINES.map((c) => (
              <ToggleChip
                key={c}
                label={c}
                selected={cuisines.includes(c)}
                onClick={() => toggle(cuisines, setCuisines, c)}
              />
            ))}
          </div>
        </section>

        {/* Dietary restrictions */}
        <section className="card p-6" aria-labelledby="dietary-heading">
          <h2 id="dietary-heading" className="font-semibold text-gray-900 mb-1">Dietary Needs</h2>
          <p className="text-xs text-gray-400 mb-4">The AI will always respect these — restaurants that can't accommodate them won't be recommended</p>
          <div className="flex flex-wrap gap-2">
            {DIETARY.map((d) => (
              <ToggleChip
                key={d}
                label={d}
                selected={dietary.includes(d)}
                onClick={() => toggle(dietary, setDietary, d)}
              />
            ))}
          </div>
        </section>

        {/* Ambiance */}
        <section className="card p-6" aria-labelledby="ambiance-heading">
          <h2 id="ambiance-heading" className="font-semibold text-gray-900 mb-1">Preferred Ambiance</h2>
          <p className="text-xs text-gray-400 mb-4">What kind of atmosphere do you enjoy?</p>
          <div className="flex flex-wrap gap-2">
            {AMBIANCES.map((a) => (
              <ToggleChip
                key={a}
                label={a}
                selected={ambiance.includes(a)}
                onClick={() => toggle(ambiance, setAmbiance, a)}
              />
            ))}
          </div>
        </section>

        {/* Price range + Sort */}
        <div className="grid sm:grid-cols-2 gap-6">
          <section className="card p-6" aria-labelledby="price-heading">
            <h2 id="price-heading" className="font-semibold text-gray-900 mb-4">Preferred Price Range</h2>
            <div className="space-y-2">
              {PRICE_RANGES.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="price_range"
                    value={value}
                    checked={priceRange === value}
                    onChange={() => setPriceRange(value)}
                    className="accent-brand-600"
                  />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="radio"
                  name="price_range"
                  value=""
                  checked={priceRange === ''}
                  onChange={() => setPriceRange('')}
                  className="accent-brand-600"
                />
                <span className="text-sm text-gray-700">No preference</span>
              </label>
            </div>
          </section>

          <section className="card p-6" aria-labelledby="sort-heading">
            <h2 id="sort-heading" className="font-semibold text-gray-900 mb-4">Default Sort Order</h2>
            <div className="space-y-2">
              {SORT_OPTIONS.map(({ value, label }) => (
                <label key={value} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="radio"
                    name="sort_pref"
                    value={value}
                    checked={sortPref === value}
                    onChange={() => setSortPref(value)}
                    className="accent-brand-600"
                  />
                  <span className="text-sm text-gray-700">{label}</span>
                </label>
              ))}
            </div>
          </section>
        </div>

        {/* Search radius */}
        <section className="card p-6" aria-labelledby="radius-heading">
          <h2 id="radius-heading" className="font-semibold text-gray-900 mb-1">Search Radius</h2>
          <p className="text-xs text-gray-400 mb-4">How far are you willing to travel? ({searchRadius} miles)</p>
          <input
            type="range"
            min={1}
            max={100}
            value={searchRadius}
            onChange={(e) => setSearchRadius(Number(e.target.value))}
            className="w-full accent-brand-600"
            aria-label="Search radius in miles"
          />
          <div className="flex justify-between text-xs text-gray-400 mt-1">
            <span>1 mi</span>
            <span className="font-semibold text-brand-600">{searchRadius} mi</span>
            <span>100 mi</span>
          </div>
        </section>

        {/* Preferred locations */}
        <section className="card p-6" aria-labelledby="locations-heading">
          <h2 id="locations-heading" className="font-semibold text-gray-900 mb-1">Preferred Locations</h2>
          <p className="text-xs text-gray-400 mb-4">Cities or neighbourhoods you frequently visit</p>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={locationInput}
              onChange={(e) => setLocationInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addLocation())}
              placeholder="e.g. San Francisco"
              className="input flex-1"
              aria-label="Add location"
            />
            <button type="button" onClick={addLocation} className="btn-secondary px-4">
              Add
            </button>
          </div>
          {locations.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {locations.map((loc) => (
                <span key={loc} className="inline-flex items-center gap-1.5 px-3 py-1 bg-brand-50 text-brand-700 text-sm rounded-full border border-brand-100">
                  {loc}
                  <button
                    type="button"
                    onClick={() => setLocations((prev) => prev.filter((l) => l !== loc))}
                    aria-label={`Remove ${loc}`}
                    className="text-brand-400 hover:text-brand-700 transition leading-none"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </section>

        {/* Save */}
        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="btn-secondary"
          >
            Reset
          </button>
          <button type="submit" disabled={saving} className="btn-primary px-8">
            {saving ? 'Saving…' : 'Save preferences'}
          </button>
        </div>
      </form>
    </div>
  )
}
