/**
 * ProfileForm
 *
 * Reusable profile edit form. Controlled — parent manages `profile` state.
 *
 * Props:
 *   profile      object              — { name, email, phone, about_me, city, state, country, languages, gender }
 *   onChange     (field, value) => void
 *   onSubmit     (e) => void
 *   saving       boolean
 *   photoPreview string              — URL for the avatar preview
 *   onPhotoFile  (File) => void      — called when user picks a new photo
 *   userName     string              — displayed in the card header
 *   userRole     string              — 'owner' | 'diner'
 *   error        string              — form-level error
 *   className    string
 */
import ImageUpload from './ImageUpload'
import ErrorAlert from '../common/ErrorAlert'

const COUNTRIES = [
  'United States','Canada','United Kingdom','Australia','Germany',
  'France','Japan','India','Brazil','Mexico','Italy','Spain',
  'South Korea','China','Other',
]
const US_STATES = [
  'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN',
  'IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV',
  'NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN',
  'TX','UT','VT','VA','WA','WV','WI','WY',
]

export default function ProfileForm({
  profile = {},
  onChange,
  onSubmit,
  saving = false,
  photoPreview,
  onPhotoFile,
  userName,
  userRole,
  error,
  className = '',
}) {
  const field = (name) => ({
    name,
    id: `profile-${name}`,
    value: profile[name] ?? '',
    onChange: (e) => onChange?.(name, e.target.value),
    disabled: saving,
    className: 'input',
  })

  return (
    <form onSubmit={onSubmit} className={`space-y-6 ${className}`} noValidate>
      <ErrorAlert message={error} />

      {/* Photo + identity card */}
      <div className="card p-6 flex items-center gap-5">
        <ImageUpload
          preview={photoPreview}
          onFile={onPhotoFile}
          label="Change photo"
          shape="circle"
          size={80}
        />
        <div>
          <p className="font-semibold text-gray-900">{userName || profile.name}</p>
          <p className="text-sm text-gray-500 mt-0.5">
            {userRole === 'owner' ? 'Restaurant Owner' : 'Diner'}
          </p>
        </div>
      </div>

      {/* Name + email */}
      <div className="card p-6 space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="profile-name" className="label">Full name</label>
            <input type="text" {...field('name')} />
          </div>
          <div>
            <label htmlFor="profile-email" className="label">Email</label>
            <input type="email" {...field('email')} />
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="profile-phone" className="label">Phone</label>
            <input type="tel" {...field('phone')} placeholder="+1 (555) 000-0000" />
          </div>
          <div>
            <label htmlFor="profile-gender" className="label">Gender</label>
            <select {...field('gender')}>
              <option value="">Prefer not to say</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="non-binary">Non-binary</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="profile-about_me" className="label">About me</label>
          <textarea
            id="profile-about_me"
            name="about_me"
            rows={3}
            value={profile.about_me ?? ''}
            onChange={(e) => onChange?.('about_me', e.target.value)}
            disabled={saving}
            placeholder="Tell us about your food adventures…"
            className="input resize-none"
          />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label htmlFor="profile-city" className="label">City</label>
            <input type="text" {...field('city')} placeholder="San Francisco" />
          </div>
          <div>
            <label htmlFor="profile-state" className="label">State</label>
            <select {...field('state')}>
              <option value="">—</option>
              {US_STATES.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="profile-country" className="label">Country</label>
            <select {...field('country')}>
              <option value="">Select country</option>
              {COUNTRIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>

        <div>
          <label htmlFor="profile-languages" className="label">Languages spoken</label>
          <input
            type="text"
            {...field('languages')}
            placeholder="English, Spanish, French"
          />
          <p className="mt-1 text-xs text-gray-400">Comma-separated</p>
        </div>
      </div>

      <button type="submit" disabled={saving} className="btn-primary px-8 py-3">
        {saving ? 'Saving…' : 'Save Profile'}
      </button>
    </form>
  )
}
