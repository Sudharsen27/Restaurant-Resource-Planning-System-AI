import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import LoadingSpinner from './components/ui/LoadingSpinner'

const Dashboard = lazy(() => import('./pages/Dashboard'))
const Forecast = lazy(() => import('./pages/Forecast'))
const StaffPlanner = lazy(() => import('./pages/StaffPlanner'))
const InventoryPlanner = lazy(() => import('./pages/InventoryPlanner'))
const ManagerFeedback = lazy(() => import('./pages/ManagerFeedback'))
const ModelAnalytics = lazy(() => import('./pages/ModelAnalytics'))
const PredictionHistory = lazy(() => import('./pages/PredictionHistory'))
const Settings = lazy(() => import('./pages/Settings'))

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner label="Loading page…" />}>
        <Routes>
          <Route element={<DashboardLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="forecast" element={<Forecast />} />
            <Route path="staff" element={<StaffPlanner />} />
            <Route path="inventory" element={<InventoryPlanner />} />
            <Route path="feedback" element={<ManagerFeedback />} />
            <Route path="analytics" element={<ModelAnalytics />} />
            <Route path="history" element={<PredictionHistory />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
