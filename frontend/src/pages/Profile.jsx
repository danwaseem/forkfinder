import { useEffect, useState } from 'react'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ImageUpload from '../components/profile/ImageUpload'
import { imgUrl } from '../utils/format'

const COUNTRIES = ['United States','Canada','United Kingdom','Australia','Germany','France','Japan','India','Brazil','Mexico','Italy','Spain','South Korea','China','Other']
const US_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']
const CUISINES = ['Italian','Japanese','Chinese','Mexican','Indian','Thai','American','French','Mediterranean','Korean','Vietnamese','Greek','Spanish','Middle Eastern','African','BBQ','Seafood','Vegan','Vegetarian']
const DIETARY = ['None','Vegetarian','Vegan','Gluten-Free','Halal','Kosher','Dairy-Free','Nut-Free']
const AMBIANCE = ['Casual','Fine Dining','Romantic','Family-Friendly','Trendy','Outdoor','Sports Bar','Cozy','Fast Casual']
const SORT_OPTS = [{ value: 'rating', label: 'Highest Rated' },{ value: 'distance', label: 'Nearest' },{ value: 'newest', label: 'Newest' }]
const PRICE_RANGES = ['$','$$','$$$','$$$$']

export default function Profile() {
  const { user, updateUser } = useAuth()
  const [tab, setTab]             = useState('profile')
  const [loading, setLoading]     = useState(true)
  const [saving, setSaving]       = useState(false)
  const [photoUploading, setPhotoUploading] = useState(false)

  // Profile form
  const [profile, setProfile] = useState({ name: '', email: '', phone: '', about_me: '', city: '', state: '', country: '', languages: '', gender: '' })
  const [photoPreview, setPhotoPreview] = useState(null)

  // Preferences form
  const [prefs, setPrefs] = useState({ cuisine_preferences: [], price_range: '', search_radius: 10, dietary_restrictions: [], ambiance_preferences: [], sort_preference: 'rating' })

  useEffect(() => {
    Promise.all([api.get('/users/me'), api.get('/preferences/me')])
      .then(([uRes, pRes]) => {
        const u = uRes.data
        setProfile({ name: u.name || '', email: u.email || '', phone: u.phone || '', about_me: u.about_me || '', city: u.city || '', state: u.state || '', country: u.country || '', languages: u.languages || '', gender: u.gender || '' })
        setPhotoPreview(u.profile_photo_url ? `${import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'}${u.profile_photo_url}` : null)
        setPrefs({ ...pRes.data })
      })
      .catch(() => toast.error('Failed to load profile'))
      .finally(() => setLoading(false))
  }, [])

  const handleProfile = (e) => setProfile({ ...profile, [e.target.name]: e.target.value })

  const saveProfile = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      const { data } = await api.put('/users/me', profile)
      updateUser({ name: data.name, email: data.email })
      toast.success('Profile saved!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const uploadPhoto = async (file) => {
    // Optimistic preview
    const objectUrl = URL.createObjectURL(file)
    setPhotoPreview(objectUrl)
    setPhotoUploading(true)
    const fd = new FormData()
    fd.append('file', file)
    try {
      const { data } = await api.post('/users/me/photo', fd)
      updateUser({ profile_photo_url: data.profile_photo_url })
      // Replace object URL with the real server path
      setPhotoPreview(imgUrl(data.profile_photo_url))
      toast.success('Profile photo updated!')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Photo upload failed')
      // Roll back preview to the saved server photo
      setPhotoPreview(user?.profile_photo_url ? imgUrl(user.profile_photo_url) : null)
    } finally {
      URL.revokeObjectURL(objectUrl)
      setPhotoUploading(false)
    }
  }

  const togglePref = (key, val) => {
    setPrefs((prev) => {
      const arr = prev[key] || []
      return { ...prev, [key]: arr.includes(val) ? arr.filter((v) => v !== val) : [...arr, val] }
    })
  }

  const savePrefs = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.put('/preferences/me', prefs)
      toast.success('Preferences saved!')
    } catch {
      toast.error('Failed to save preferences')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <LoadingSpinner fullPage />

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="section-title mb-6">My Account</h1>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6" role="tablist">
        {[{ id: 'profile', label: 'Profile' }, { id: 'preferences', label: 'Dining Preferences' }].map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => setTab(t.id)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 transition -mb-px ${
              tab === t.id ? 'border-brand-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Profile Tab */}
      {tab === 'profile' && (
        <form onSubmit={saveProfile} className="space-y-6" noValidate>
          {/* Photo */}
          <div className="card p-6 flex items-center gap-6">
            <ImageUpload
              preview={photoPreview}
              onFile={uploadPhoto}
              label="Change photo"
              shape="circle"
              size={80}
              uploading={photoUploading}
            />
            <div>
              <p className="font-semibold text-gray-900">{profile.name}</p>
              <p className="text-sm text-gray-500">{user?.role === 'owner' ? 'Restaurant Owner' : 'Diner'}</p>
              <p className="text-xs text-gray-400 mt-1">Click the photo to change it</p>
            </div>
          </div>

          {/* Fields */}
          <div className="card p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="name" className="label">Full name</label>
                <input id="name" name="name" type="text" value={profile.name} onChange={handleProfile} className="input" />
              </div>
              <div>
                <label htmlFor="email" className="label">Email</label>
                <input id="email" name="email" type="email" value={profile.email} onChange={handleProfile} className="input" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label htmlFor="phone" className="label">Phone</label>
                <input id="phone" name="phone" type="tel" value={profile.phone} onChange={handleProfile} className="input" placeholder="+1 (555) 000-0000" />
              </div>
              <div>
                <label htmlFor="gender" className="label">Gender</label>
                <select id="gender" name="gender" value={profile.gender} onChange={handleProfile} className="input">
                  <option value="">Prefer not to say</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="non-binary">Non-binary</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="about_me" className="label">About me</label>
              <textarea id="about_me" name="about_me" rows={3} value={profile.about_me} onChange={handleProfile} className="input resize-none" placeholder="Tell us about your food adventures..." />
            </div>
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label htmlFor="city" className="label">City</label>
                <input id="city" name="city" type="text" value={profile.city} onChange={handleProfile} className="input" placeholder="San Francisco" />
              </div>
              <div>
                <label htmlFor="state" className="label">State</label>
                <select id="state" name="state" value={profile.state} onChange={handleProfile} className="input">
                  <option value="">—</option>
                  {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div>
                <label htmlFor="country" className="label">Country</label>
                <select id="country" name="country" value={profile.country} onChange={handleProfile} className="input">
                  <option value="">Select country</option>
                  {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label htmlFor="languages" className="label">Languages spoken (comma-separated)</label>
              <input id="languages" name="languages" type="text" value={profile.languages} onChange={handleProfile} className="input" placeholder="English, Spanish, French" />
            </div>
          </div>

          <button type="submit" disabled={saving} className="btn-primary px-8 py-3">
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      )}

      {/* Preferences Tab */}
      {tab === 'preferences' && (
        <form onSubmit={savePrefs} className="space-y-6">
          {/* Cuisines */}
          <div className="card p-6">
            <h2 className="font-bold text-gray-900 mb-3">Preferred Cuisines</h2>
            <div className="flex flex-wrap gap-2">
              {CUISINES.map((c) => (
                <button key={c} type="button" onClick={() => togglePref('cuisine_preferences', c)}
                  aria-pressed={prefs.cuisine_preferences?.includes(c)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition ${prefs.cuisine_preferences?.includes(c) ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-200 text-gray-600 hover:border-brand-300'}`}>
                  {c}
                </button>
              ))}
            </div>
          </div>

          {/* Price + radius */}
          <div className="card p-6 grid grid-cols-2 gap-4">
            <div>
              <h2 className="font-bold text-gray-900 mb-3">Price Range</h2>
              <div className="flex gap-2">
                {PRICE_RANGES.map((p) => (
                  <button key={p} type="button" onClick={() => setPrefs({ ...prefs, price_range: prefs.price_range === p ? '' : p })}
                    aria-pressed={prefs.price_range === p}
                    className={`px-4 py-2 rounded-xl font-semibold text-sm border transition ${prefs.price_range === p ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-200 text-gray-600 hover:border-brand-300'}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label htmlFor="search_radius" className="font-bold text-gray-900 block mb-3">Search Radius: {prefs.search_radius} miles</label>
              <input id="search_radius" type="range" min={1} max={100} value={prefs.search_radius} onChange={(e) => setPrefs({ ...prefs, search_radius: parseInt(e.target.value) })} className="w-full accent-brand-600" />
            </div>
          </div>

          {/* Dietary restrictions */}
          <div className="card p-6">
            <h2 className="font-bold text-gray-900 mb-3">Dietary Restrictions</h2>
            <div className="flex flex-wrap gap-2">
              {DIETARY.map((d) => (
                <button key={d} type="button" onClick={() => togglePref('dietary_restrictions', d)}
                  aria-pressed={prefs.dietary_restrictions?.includes(d)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition ${prefs.dietary_restrictions?.includes(d) ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-200 text-gray-600 hover:border-brand-300'}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Ambiance */}
          <div className="card p-6">
            <h2 className="font-bold text-gray-900 mb-3">Ambiance Preferences</h2>
            <div className="flex flex-wrap gap-2">
              {AMBIANCE.map((a) => (
                <button key={a} type="button" onClick={() => togglePref('ambiance_preferences', a)}
                  aria-pressed={prefs.ambiance_preferences?.includes(a)}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium border transition ${prefs.ambiance_preferences?.includes(a) ? 'bg-brand-600 text-white border-brand-600' : 'border-gray-200 text-gray-600 hover:border-brand-300'}`}>
                  {a}
                </button>
              ))}
            </div>
          </div>

          {/* Sort preference */}
          <div className="card p-6">
            <h2 className="font-bold text-gray-900 mb-3">Default Sort</h2>
            <div className="flex gap-3">
              {SORT_OPTS.map((o) => (
                <label key={o.value} className={`flex items-center gap-2 px-4 py-2 rounded-xl border cursor-pointer transition ${prefs.sort_preference === o.value ? 'border-brand-500 bg-brand-50 text-brand-700' : 'border-gray-200 text-gray-600 hover:border-gray-300'}`}>
                  <input type="radio" name="sort_preference" value={o.value} checked={prefs.sort_preference === o.value} onChange={(e) => setPrefs({ ...prefs, sort_preference: e.target.value })} className="sr-only" />
                  {o.label}
                </label>
              ))}
            </div>
          </div>

          <button type="submit" disabled={saving} className="btn-primary px-8 py-3">
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </form>
      )}
    </div>
  )
}
