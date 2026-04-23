import { createSlice } from '@reduxjs/toolkit'

/**
 * Auth slice — mirrors AuthContext state in Redux.
 *
 * Populated by AuthContext on every login, logout, register, and rehydration.
 * Components can still use useAuth() from AuthContext; this slice exists so
 * Redux DevTools shows meaningful auth state transitions for Lab 2 Part 4.
 */

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginSuccess(state, action) {
      state.user = action.payload.user
      state.token = action.payload.token
      state.isAuthenticated = true
    },
    logout(state) {
      state.user = null
      state.token = null
      state.isAuthenticated = false
    },
    updateUser(state, action) {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
    rehydrate(state, action) {
      state.user = action.payload.user
      state.token = action.payload.token
      state.isAuthenticated = true
    },
  },
})

export const {
  loginSuccess,
  logout,
  updateUser,
  rehydrate,
} = authSlice.actions

// ── Selectors ──────────────────────────────────────────────────────────────────
export const selectUser            = (state) => state.auth.user
export const selectToken           = (state) => state.auth.token
export const selectIsAuthenticated = (state) => state.auth.isAuthenticated
export const selectIsOwner         = (state) => state.auth.user?.role === 'owner'

export default authSlice.reducer
