import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import toast from 'react-hot-toast'

export default function Login() {
  const { login }    = useAuth()
  const navigate     = useNavigate()
  const [form, setForm]     = useState({ email: '', password: '', role: 'user' })
  const [loading, setLoading] = useState(false)
  const [error, setError]   = useState('')

  const handle = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const user = await login(form.email, form.password, form.role)
      toast.success(`Welcome back, ${user.name?.split(' ')[0]}!`)
      navigate(user.role === 'owner' ? '/owner/dashboard' : '/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-16
                    bg-gradient-to-br from-brand-50 via-white to-gray-50">
      <div className="w-full max-w-md animate-fade-up">

        {/* Logo + heading */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2.5 mb-5" aria-label="ForkFinder home">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-brand-500 to-brand-700
                            flex items-center justify-center shadow-md mx-auto">
              <span className="text-white text-xl">🍴</span>
            </div>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
          <p className="text-gray-500 text-sm mt-1.5">Log in to your ForkFinder account</p>
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

          <form onSubmit={submit} noValidate className="space-y-5">
            {/* Role selector */}
            <fieldset>
              <legend className="label">I am a…</legend>
              <div className="grid grid-cols-2 gap-3">
                {[
                  { value: 'user',  icon: '🍽️', label: 'Diner' },
                  { value: 'owner', icon: '🏪', label: 'Restaurant Owner' },
                ].map(({ value, icon, label }) => (
                  <label
                    key={value}
                    className={`flex flex-col items-center gap-2 p-4 rounded-2xl border-2 cursor-pointer
                                transition-all duration-150 select-none
                                ${form.role === value
                                  ? 'border-brand-500 bg-brand-50'
                                  : 'border-gray-200 hover:border-gray-300 bg-white'
                                }`}
                  >
                    <input
                      type="radio"
                      name="role"
                      value={value}
                      checked={form.role === value}
                      onChange={handle}
                      className="sr-only"
                    />
                    <span className="text-2xl" aria-hidden="true">{icon}</span>
                    <span className={`font-semibold text-sm ${form.role === value ? 'text-brand-700' : 'text-gray-700'}`}>
                      {label}
                    </span>
                  </label>
                ))}
              </div>
            </fieldset>

            {/* Email */}
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <input
                id="email"
                type="email"
                name="email"
                autoComplete="email"
                required
                value={form.email}
                onChange={handle}
                className="input"
                placeholder="you@example.com"
              />
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                type="password"
                name="password"
                autoComplete="current-password"
                required
                value={form.password}
                onChange={handle}
                className="input"
                placeholder="••••••••"
              />
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full py-3 text-base">
              {loading
                ? <><span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />Signing in…</>
                : 'Sign in'
              }
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-500">
            Don't have an account?{' '}
            <Link to="/register" className="text-brand-600 font-semibold hover:underline">
              Sign up free
            </Link>
          </p>

          {/* Demo credentials */}
          <details className="mt-5">
            <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 transition-colors text-center select-none">
              Demo credentials
            </summary>
            <div className="mt-2 p-3.5 bg-gray-50 rounded-xl text-xs text-gray-600 space-y-1.5">
              <p className="font-semibold text-gray-700">Try these accounts:</p>
              <p>🍽️ Diner: <span className="font-mono">alice@example.com</span> / <span className="font-mono">password123</span></p>
              <p>🏪 Owner: <span className="font-mono">owner@pizzapalace.com</span> / <span className="font-mono">password123</span></p>
            </div>
          </details>
        </div>
      </div>
    </div>
  )
}
