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
const Register = lazy(() => import('./pages/Register'))
const ForgotPassword = lazy(() => import('./pages/ForgotPassword'))
const ResetPassword = lazy(() => import('./pages/ResetPassword'))
const VerifyEmail = lazy(() => import('./pages/VerifyEmail'))
const Profile = lazy(() => import('./pages/Profile'))
const Sessions = lazy(() => import('./pages/Sessions'))
const Unauthorized = lazy(() => import('./pages/Unauthorized'))
const PosPage = lazy(() => import('./pages/PosPage'))
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const SupportPage = lazy(() => import('./pages/SupportPage'))
const SystemStatusPage = lazy(() => import('./pages/SystemStatusPage'))
const RestaurantsPage = lazy(() => import('./pages/erp/ErpPages'))
const BranchesPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.BranchesManagePage })),
)
const OpsOverviewPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.OpsOverviewPage })),
)
const RestaurantDetailsPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.RestaurantDetailsPage })),
)
const DiningAreasPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.DiningAreasPage })),
)
const TablesPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.TablesPage })),
)
const DepartmentsPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.DepartmentsPage })),
)
const BusinessSettingsPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.BusinessSettingsPage })),
)
const DocumentsPage = lazy(() =>
  import('./pages/erp/OperationsPages').then((m) => ({ default: m.DocumentsPage })),
)
const CategoriesPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.CategoriesPage })),
)
const ProductsPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.ProductsPage })),
)
const StockPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.StockPage })),
)
const SuppliersPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.SuppliersPage })),
)
const OrdersPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.OrdersPage })),
)
const CustomersPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.CustomersPage })),
)
const EmployeesPage = lazy(() =>
  import('./pages/erp/ErpPages').then((m) => ({ default: m.EmployeesPage })),
)
const CatalogOverviewPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.CatalogOverviewPage })),
)
const PurchaseOrdersPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.PurchaseOrdersPage })),
)
const GoodsReceiptsPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.GoodsReceiptsPage })),
)
const RecipesPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.RecipesPage })),
)
const MenuManagePage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.MenuManagePage })),
)
const StockAlertsPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.StockAlertsPage })),
)
const StockTransfersPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.StockTransfersPage })),
)
const InventoryTransactionsPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.InventoryTransactionsPage })),
)

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<LoadingSpinner label="Loading page…" />}>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} />

          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route index element={<Dashboard />} />
              <Route path="ops" element={<OpsOverviewPage />} />
              <Route path="catalog" element={<CatalogOverviewPage />} />
              <Route path="restaurants" element={<RestaurantsPage />} />
              <Route path="restaurant-profile" element={<RestaurantDetailsPage />} />
              <Route path="branches" element={<BranchesPage />} />
              <Route path="dining-areas" element={<DiningAreasPage />} />
              <Route path="tables" element={<TablesPage />} />
              <Route path="departments" element={<DepartmentsPage />} />
              <Route path="business-settings" element={<BusinessSettingsPage />} />
              <Route path="documents" element={<DocumentsPage />} />
              <Route path="products" element={<ProductsPage />} />
              <Route path="categories" element={<CategoriesPage />} />
              <Route path="stock" element={<StockPage />} />
              <Route path="suppliers" element={<SuppliersPage />} />
              <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
              <Route path="goods-receipts" element={<GoodsReceiptsPage />} />
              <Route path="recipes" element={<RecipesPage />} />
              <Route path="menu" element={<MenuManagePage />} />
              <Route path="stock-alerts" element={<StockAlertsPage />} />
              <Route path="stock-transfers" element={<StockTransfersPage />} />
              <Route path="inventory-transactions" element={<InventoryTransactionsPage />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="pos" element={<PosPage />} />
              <Route path="customers" element={<CustomersPage />} />
              <Route path="employees" element={<EmployeesPage />} />
              <Route path="forecast" element={<Forecast />} />
              <Route path="staff" element={<StaffPlanner />} />
              <Route path="inventory" element={<InventoryPlanner />} />
              <Route path="feedback" element={<ManagerFeedback />} />
              <Route path="analytics" element={<ModelAnalytics />} />
              <Route path="history" element={<PredictionHistory />} />
              <Route path="notifications" element={<NotificationsPage />} />
              <Route path="settings" element={<Settings />} />
              <Route path="support" element={<SupportPage />} />
              <Route path="profile" element={<Profile />} />
              <Route path="sessions" element={<Sessions />} />
              <Route path="unauthorized" element={<Unauthorized />} />
              <Route path="403" element={<SystemStatusPage variant="403" />} />
              <Route path="500" element={<SystemStatusPage variant="500" />} />
              <Route path="offline" element={<SystemStatusPage variant="offline" />} />
              <Route path="*" element={<SystemStatusPage variant="404" />} />
            </Route>
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  )
}

export default App
