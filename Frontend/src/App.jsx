import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import DashboardLayout from './layouts/DashboardLayout'
import Dashboard from './pages/Dashboard'
import Forecast from './pages/Forecast'
import StaffPlanner from './pages/StaffPlanner'
import InventoryPlanner from './pages/InventoryPlanner'
import ManagerFeedback from './pages/ManagerFeedback'
import ModelAnalytics from './pages/ModelAnalytics'
import PredictionHistory from './pages/PredictionHistory'
import Settings from './pages/Settings'

function App() {
  return (
    <BrowserRouter>
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
    </BrowserRouter>
  )
}

export default App
