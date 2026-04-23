import React, { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { useDispatch } from 'react-redux'
import api, { tokenStore } from '../services/api'
import { authApi } from '../services/auth'
import {
  loginSuccess,
  logout as authLogout,
  updateUser as authUpdateUser,
  rehydrate,
} from '../store/slices/authSlice'
import { clearFavorites } from '../store/slices/favoritesSlice'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const dispatch = useDispatch()
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // ── Re-hydrate from localStorage on app mount ─────────────────────────────
  useEffect(() => {
    const token  = tokenStore.get()
    const stored = localStorage.getItem('user')
    if (token && stored) {
      try {
        const parsed = JSON.parse(stored)
        setUser(parsed)
        // Also set on the Axios default so requests made before the first
        // interceptor run already have the token.
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
        dispatch(rehydrate({ user: parsed, token }))
      } catch {
        // Corrupted storage — start fresh
        tokenStore.clear()
      }
    }
    setLoading(false)
  }, [dispatch])

  // ── Persist a successful auth response ───────────────────────────────────
  const _persist = useCallback((data) => {
    const user = { ...data, id: data.user_id }
    tokenStore.set(data.access_token, user)
    api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
    setUser(user)
    dispatch(loginSuccess({ user, token: data.access_token }))
  }, [dispatch])

  // ── Public methods ────────────────────────────────────────────────────────

  /**
   * Log in with email + password.
   * role defaults to 'user'; pass 'owner' to hit /auth/owner/login.
   *
   * @param {string} email
   * @param {string} password
   * @param {'user'|'owner'} role
   * @returns {Promise<TokenResponse>}
   */
  const login = useCallback(async (email, password, role = 'user') => {
    const data = await authApi.login(email, password, role)
    _persist(data)
    return data
  }, [_persist])

  /**
   * Register a new account.
   * role defaults to 'user'; pass 'owner' to hit /auth/owner/signup.
   *
   * @param {string} name
   * @param {string} email
   * @param {string} password
   * @param {'user'|'owner'} role
   * @returns {Promise<TokenResponse>}
   */
  const register = useCallback(async (name, email, password, role = 'user') => {
    const data = await authApi.register(name, email, password, role)
    _persist(data)
    return data
  }, [_persist])

  /**
   * Clear all auth state.
   * JWT is stateless — no server call needed.
   */
  const logout = useCallback(() => {
    tokenStore.clear()
    setUser(null)
    dispatch(authLogout())
    dispatch(clearFavorites())
  }, [dispatch])

  /**
   * Merge updates into the stored user object without a full reload.
   * Use after profile photo upload, name change, etc.
   *
   * @param {Partial<TokenResponse>} updates
   */
  const updateUser = useCallback((updates) => {
    setUser((prev) => {
      const next = { ...prev, ...updates }
      // Keep localStorage in sync
      localStorage.setItem('user', JSON.stringify(next))
      return next
    })
    dispatch(authUpdateUser(updates))
  }, [dispatch])

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
