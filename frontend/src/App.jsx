import React from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import Navbar from './components/common/Navbar'
import Footer from './components/common/Footer'
import AIAssistant from './components/common/AIAssistant'
import { useAuth } from './context/AuthContext'
import LoadingSpinner from './components/common/LoadingSpinner'

// Pages
import Home from './pages/Home'
import Explore from './pages/Explore'
import Login from './pages/Login'
import Register from './pages/Register'
import RestaurantDetails from './pages/RestaurantDetails'
import AddRestaurant from './pages/AddRestaurant'
import Profile from './pages/Profile'
import Favorites from './pages/Favorites'
import History from './pages/History'
import Preferences from './pages/Preferences'
import OwnerDashboard from './pages/owner/OwnerDashboard'
import OwnerRestaurants from './pages/owner/OwnerRestaurants'
import OwnerRestaurantDetail from './pages/owner/OwnerRestaurantDetail'
import OwnerReviews from './pages/owner/OwnerReviews'
import ClaimRestaurant from './pages/ClaimRestaurant'

function RequireAuth({ children, ownerOnly = false }) {
  const { user, loading } = useAuth()
  if (loading) return <LoadingSpinner fullPage />
  if (!user) return <Navigate to="/login" replace />
  if (ownerOnly && user.role !== 'owner') return <Navigate to="/" replace />
  return children
}

export default function App() {
  const { loading } = useAuth()
  if (loading) return <LoadingSpinner fullPage />

  return (
    <div className="flex flex-col min-h-screen">
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/explore" element={<Explore />} />
          <Route path="/restaurants/:id" element={<RestaurantDetails />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected routes */}
          <Route path="/profile" element={<RequireAuth><Profile /></RequireAuth>} />
          <Route path="/add-restaurant" element={<RequireAuth><AddRestaurant /></RequireAuth>} />
          <Route path="/favorites" element={<RequireAuth><Favorites /></RequireAuth>} />
          <Route path="/history" element={<RequireAuth><History /></RequireAuth>} />
          <Route path="/preferences" element={<RequireAuth><Preferences /></RequireAuth>} />

          {/* Owner routes */}
          <Route path="/owner/dashboard" element={<RequireAuth ownerOnly><OwnerDashboard /></RequireAuth>} />
          <Route path="/owner/restaurants" element={<RequireAuth ownerOnly><OwnerRestaurants /></RequireAuth>} />
          <Route path="/owner/restaurants/:id" element={<RequireAuth ownerOnly><OwnerRestaurantDetail /></RequireAuth>} />
          <Route path="/owner/reviews" element={<RequireAuth ownerOnly><OwnerReviews /></RequireAuth>} />
          <Route path="/claim-restaurant" element={<RequireAuth ownerOnly><ClaimRestaurant /></RequireAuth>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
      <Footer />
      <AIAssistant />
    </div>
  )
}
