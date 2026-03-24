import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

function PasswordStrength({ password }) {
  if (!password) return null
  const len    = password.length >= 8
  const mixed  = /[A-Z]/.test(password) && /[a-z]/.test(password)
  const num    = /\d/.test(password)
  const score  = [len, mixed, num].filter(Boolean).length

  const levels = [
    { label: 'Weak',   color: 'bg-red-400',   bars: 1 },
    { label: 'Fair',   color: 'bg-amber-400',  bars: 2 },
    { label: 'Strong', color: 'bg-green-500',  bars: 3 },
  ]
  const level = levels[Math.min(score - 1, 2)] || levels[0]

  return (
    <div className="flex items-center gap-2 mt-2">
      <div className="flex gap-1 flex-1">
        {[1, 2, 3].map((n) => (
          <div
            key={n}
            className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
              n <= level.bars ? level.color : 'bg-gray-200'
            }`}
          />
        ))}
      </div>
      <span className="text-xs text-gray-500">{level.label}</span>
    </div>
  )
}

export default function Register() {
  const { register } = useAuth()
  const navigate     = useNavigate()
  const [form, setForm]     = useState({ name: '', email: '', password: '', confirm: '', role: 'user' })
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    if (form.password.length < 8)          { setError('Password must be at least 8 characters.'); return }
    if (form.password !== form.confirm)    { setError('Passwords do not match.'); return }
    setLoading(true)
    try {
      const user = await register(form.name, form.email, form.password, form.role)
      toast.success(`Welcome to ForkFinder, ${user.name?.split(' ')[0]}!`)
      navigate(user.role === 'owner' ? '/owner/dashboard' : '/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const ROLES = [
    { value: 'user',  icon: '🍽️', label: 'Diner',            desc: 'Discover & review restaurants' },
    { value: 'owner', icon: '🏪', label: 'Restaurant Owner',  desc: 'Manage your listings' },
  ]

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16
                    bg-gradient-to-br from-brand-50 via-white to-gray-50">
      <div className="w-full max-w-md animate-fade-up">

        <div className="text-center mb-8">
          <Link to="/" aria-label="ForkFinder home" className="inline-block mb-4">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700
                            flex items-center justify-center shadow-md mx-auto">
              <span className="text-white text-xl">🍴</span>
            </div>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 text-sm mt-1.5">Join ForkFinder and discover great food</p>
        </div>

        <div className="card p-8">
          {error && (
            <div role="alert"
              className="mb-5 flex items-start gap-2.5 p-3.5 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl">
              <svg className="w-4 h-4 mt-px shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round"
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              {error}
            </div>
          )}

          <form onSubmit={submit} noValidate className="space-y-4">
            {/* Role selector */}
            <fieldset>
              <legend className="label">I want to…</legend>
              <div className="grid grid-cols-2 gap-3">
                {ROLES.map(({ value, icon, label, desc }) => (
                  <label
                    key={value}
                    className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 cursor-pointer
                                transition-all duration-150 select-none text-center
                                ${form.role === value
                                  ? 'border-brand-500 bg-brand-50'
                                  : 'border-gray-200 hover:border-gray-300 bg-white'
                                }`}
                  >
                    <input type="radio" name="role" value={value} checked={form.role === value} onChange={handle} className="sr-only" />
                    <span className="text-2xl" aria-hidden="true">{icon}</span>
                    <div>
                      <p className={`font-semibold text-sm leading-tight ${form.role === value ? 'text-brand-700' : 'text-gray-800'}`}>
                        {label}
                      </p>
                      <p className="text-[11px] text-gray-500 mt-0.5 leading-tight">{desc}</p>
                    </div>
                  </label>
                ))}
              </div>
            </fieldset>

            <div>
              <label htmlFor="name" className="label">Full name</label>
              <input
                id="name" type="text" name="name" autoComplete="name" required
                value={form.name} onChange={handle} className="input" placeholder="Jane Smith"
              />
            </div>

            <div>
              <label htmlFor="reg-email" className="label">Email address</label>
              <input
                id="reg-email" type="email" name="email" autoComplete="email" required
                value={form.email} onChange={handle} className="input" placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="reg-password" className="label">Password</label>
              <input
                id="reg-password" type="password" name="password" autoComplete="new-password" required
                value={form.password} onChange={handle} className="input" placeholder="Min. 8 characters"
              />
              <PasswordStrength password={form.password} />
            </div>

            <div>
              <label htmlFor="confirm" className="label">Confirm password</label>
              <input
                id="confirm" type="password" name="confirm" autoComplete="new-password" required
                value={form.confirm} onChange={handle} className="input" placeholder="Re-enter password"
              />
              {form.confirm && form.password !== form.confirm && (
                <p className="text-xs text-red-500 mt-1.5">Passwords don't match</p>
              )}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base mt-1">
              {loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Creating account…</>
                : 'Create account'
              }
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="text-brand-600 font-semibold hover:underline">Log in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
