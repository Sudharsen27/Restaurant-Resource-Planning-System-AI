import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import LoadingSpinner from './components/ui/LoadingSpinner'
import ProtectedRoute from './components/auth/ProtectedRoute'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Forecast = lazy(() => import('./pages/Forecast'))
const StaffPlanner = lazy(() => import('./pages/StaffPlanner'))
const InventoryPlanner = lazy(() => import('./pages/InventoryPlanner'))
const ManagerFeedback = lazy(() => import('./pages/ManagerFeedback'))
const ModelAnalytics = lazy(() => import('./pages/ModelAnalytics'))
const PredictionHistory = lazy(() => import('./pages/PredictionHistory'))
const Settings = lazy(() => import('./pages/Settings'))
const Login = lazy(() => import('./pages/Login'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const Profile = lazy(() => import('./pages/Profile'))
const Sessions = lazy(() => import('./pages/Sessions'))
const Unauthorized = lazy(() => import('./pages/Unauthorized'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner label="Loading page…" />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="forecast" element={<Forecast />} />
              <Route path="staff" element={<StaffPlanner />} />
              <Route path="inventory" element={<InventoryPlanner />} />
              <Route path="feedback" element={<ManagerFeedback />} />
              <Route path="analytics" element={<ModelAnalytics />} />
              <Route path="history" element={<PredictionHistory />} />
              <Route path="settings" element={<Settings />} />
              <Route path="profile" element={<Profile />} />
              <Route path="sessions" element={<Sessions />} />
              <Route path="unauthorized" element={<Unauthorized />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
