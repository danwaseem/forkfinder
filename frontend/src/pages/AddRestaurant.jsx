import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import api from '../services/api'
import toast from 'react-hot-toast'
import PhotoPicker from '../components/common/PhotoPicker'

const DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
const CUISINES = ['Italian', 'Japanese', 'Chinese', 'Mexican', 'Indian', 'Thai', 'American', 'French', 'Mediterranean', 'Korean', 'Vietnamese', 'Greek', 'Spanish', 'Other']
const PRICE_RANGES = ['$', '$$', '$$$', '$$$$']

const COUNTRIES = [
  'United States', 'Canada', 'United Kingdom', 'Australia', 'Germany', 'France',
  'Japan', 'India', 'Brazil', 'Mexico', 'Italy', 'Spain', 'South Korea', 'China',
]
const US_STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

export default function AddRestaurant() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const editId = searchParams.get('edit')

  const [form, setForm] = useState({
    name: '', description: '', cuisine_type: '', price_range: '',
    address: '', city: '', state: '', country: 'United States', zip_code: '',
    phone: '', website: '',
    latitude: '', longitude: '',
  })
  const [hours, setHours] = useState({ monday: '', tuesday: '', wednesday: '', thursday: '', friday: '', saturday: '', sunday: '' })
  const [photos, setPhotos]           = useState([])    // File[] — pending uploads
  const [existingPhotos, setExistingPhotos] = useState([]) // string[] — already saved URLs
  const [loading, setLoading] = useState(false)
  const [fetchLoading, setFetchLoading] = useState(false)

  useEffect(() => {
    if (!editId) return
    setFetchLoading(true)
    api.get(`/restaurants/${editId}`)
      .then(({ data }) => {
        const { photos: existingP, hours: h, ...rest } = data
        if (Array.isArray(existingP)) setExistingPhotos(existingP)
        setForm({
          name: rest.name || '', description: rest.description || '',
          cuisine_type: rest.cuisine_type || '', price_range: rest.price_range || '',
          address: rest.address || '', city: rest.city || '', state: rest.state || '',
          country: rest.country || 'United States', zip_code: rest.zip_code || '',
          phone: rest.phone || '', website: rest.website || '',
          latitude: rest.latitude || '', longitude: rest.longitude || '',
        })
        if (h && typeof h === 'object') setHours({ ...hours, ...h })
      })
      .catch(() => toast.error('Could not load restaurant'))
      .finally(() => setFetchLoading(false))
  }, [editId])

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })
  const handleHours = (day, val) => setHours({ ...hours, [day]: val })

  const submit = async (e) => {
    e.preventDefault()
    if (!form.name.trim()) { toast.error('Restaurant name is required'); return }
    setLoading(true)

    const payload = { ...form }
    Object.keys(payload).forEach((k) => { if (payload[k] === '') delete payload[k] })
    if (payload.latitude) payload.latitude = parseFloat(payload.latitude)
    if (payload.longitude) payload.longitude = parseFloat(payload.longitude)
    const filteredHours = Object.fromEntries(Object.entries(hours).filter(([, v]) => v.trim()))
    if (Object.keys(filteredHours).length) payload.hours = filteredHours

    try {
      let restaurantId
      if (editId) {
        await api.put(`/restaurants/${editId}`, payload)
        restaurantId = editId
        toast.success('Restaurant updated!')
      } else {
        const { data } = await api.post('/restaurants', payload)
        restaurantId = data.id
        toast.success('Restaurant added!')
      }

      // Upload photos
      for (const file of photos) {
        const fd = new FormData()
        fd.append('file', file)
        await api.post(`/restaurants/${restaurantId}/photos`, fd)
      }

      navigate(`/restaurants/${restaurantId}`)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save restaurant')
    } finally {
      setLoading(false)
    }
  }

  if (fetchLoading) return <div className="max-w-3xl mx-auto px-4 py-8">Loading...</div>

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <h1 className="section-title mb-6">{editId ? 'Edit Restaurant' : 'Add New Restaurant'}</h1>

      <form onSubmit={submit} className="space-y-6" noValidate>
        {/* Basic Info */}
        <fieldset className="card p-6 space-y-4">
          <legend className="font-bold text-gray-900 text-lg -mt-1 mb-2">Basic Information</legend>

          <div>
            <label htmlFor="name" className="label">Restaurant name <span className="text-red-500">*</span></label>
            <input id="name" name="name" type="text" required value={form.name} onChange={handle} className="input" placeholder="e.g. The Golden Fork" />
          </div>

          <div>
            <label htmlFor="description" className="label">Description</label>
            <textarea id="description" name="description" rows={3} value={form.description} onChange={handle} className="input resize-none" placeholder="What makes this place special?" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="cuisine_type" className="label">Cuisine type</label>
              <select id="cuisine_type" name="cuisine_type" value={form.cuisine_type} onChange={handle} className="input">
                <option value="">Select cuisine</option>
                {CUISINES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="price_range" className="label">Price range</label>
              <select id="price_range" name="price_range" value={form.price_range} onChange={handle} className="input">
                <option value="">Select range</option>
                {PRICE_RANGES.map((p) => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>
          </div>
        </fieldset>

        {/* Location */}
        <fieldset className="card p-6 space-y-4">
          <legend className="font-bold text-gray-900 text-lg -mt-1 mb-2">Location</legend>

          <div>
            <label htmlFor="address" className="label">Street address</label>
            <input id="address" name="address" type="text" value={form.address} onChange={handle} className="input" placeholder="123 Main Street" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="city" className="label">City</label>
              <input id="city" name="city" type="text" value={form.city} onChange={handle} className="input" placeholder="San Francisco" />
            </div>
            <div>
              <label htmlFor="state" className="label">State / Province</label>
              <select id="state" name="state" value={form.state} onChange={handle} className="input">
                <option value="">Select state</option>
                {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="country" className="label">Country</label>
              <select id="country" name="country" value={form.country} onChange={handle} className="input">
                {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="zip_code" className="label">ZIP / Postal code</label>
              <input id="zip_code" name="zip_code" type="text" value={form.zip_code} onChange={handle} className="input" placeholder="94105" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="latitude" className="label">Latitude (optional)</label>
              <input id="latitude" name="latitude" type="number" step="any" value={form.latitude} onChange={handle} className="input" placeholder="37.7749" />
            </div>
            <div>
              <label htmlFor="longitude" className="label">Longitude (optional)</label>
              <input id="longitude" name="longitude" type="number" step="any" value={form.longitude} onChange={handle} className="input" placeholder="-122.4194" />
            </div>
          </div>
        </fieldset>

        {/* Contact */}
        <fieldset className="card p-6 space-y-4">
          <legend className="font-bold text-gray-900 text-lg -mt-1 mb-2">Contact & Web</legend>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="phone" className="label">Phone number</label>
              <input id="phone" name="phone" type="tel" value={form.phone} onChange={handle} className="input" placeholder="+1 (555) 000-0000" />
            </div>
            <div>
              <label htmlFor="website" className="label">Website</label>
              <input id="website" name="website" type="url" value={form.website} onChange={handle} className="input" placeholder="https://example.com" />
            </div>
          </div>
        </fieldset>

        {/* Hours */}
        <fieldset className="card p-6">
          <legend className="font-bold text-gray-900 text-lg -mt-1 mb-4">Hours (optional)</legend>
          <div className="space-y-2">
            {DAYS.map((day) => (
              <div key={day} className="flex items-center gap-4">
                <span className="capitalize text-sm text-gray-700 w-24">{day}</span>
                <input
                  type="text"
                  value={hours[day]}
                  onChange={(e) => handleHours(day, e.target.value)}
                  className="input flex-1"
                  placeholder="e.g. 11am – 10pm or Closed"
                  aria-label={`${day} hours`}
                />
              </div>
            ))}
          </div>
        </fieldset>

        {/* Photos */}
        <fieldset className="card p-6">
          <legend className="font-bold text-gray-900 text-lg -mt-1 mb-4">
            Photos <span className="text-gray-400 font-normal text-sm">(optional)</span>
          </legend>
          <PhotoPicker
            files={photos}
            onChange={setPhotos}
            existingUrls={existingPhotos}
            maxFiles={10}
            label=""
            hint="Drag & drop or click + to add photos · JPEG, PNG, WEBP · Max 5 MB each · Up to 10 photos"
          />
        </fieldset>

        <div className="flex gap-3">
          <button type="submit" disabled={loading} className="btn-primary px-8 py-3">
            {loading ? 'Saving...' : editId ? 'Update Restaurant' : 'Add Restaurant'}
          </button>
          <button type="button" onClick={() => navigate(-1)} className="btn-secondary px-8 py-3">
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}
