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
const KitchenPage = lazy(() => import('./pages/KitchenPage'))
const FloorPlanPage = lazy(() => import('./pages/FloorPlanPage'))
const PaymentsPage = lazy(() => import('./pages/PaymentsPage'))
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
const WarehousesPage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.WarehousesPage })),
)
const UnitsManagePage = lazy(() =>
  import('./pages/erp/CatalogPages').then((m) => ({ default: m.UnitsManagePage })),
)
const CrmDashboardPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.CrmDashboardPage })),
)
const LoyaltyPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.LoyaltyPage })),
)
const ReservationsPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.ReservationsPage })),
)
const HrmsDashboardPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.HrmsDashboardPage })),
)
const ShiftsPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.ShiftsPage })),
)
const AttendancePage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.AttendancePage })),
)
const LeavesPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.LeavesPage })),
)
const PayrollPage = lazy(() =>
  import('./pages/erp/CrmHrmsPages').then((m) => ({ default: m.PayrollPage })),
)
const ExecutiveDashboardPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.ExecutiveDashboardPage })),
)
const AnalyticsCenterPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.AnalyticsCenterPage })),
)
const ForecastDashboardPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.ForecastDashboardPage })),
)
const InsightsAlertsPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.InsightsAlertsPage })),
)
const ReportsCenterPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.ReportsCenterPage })),
)
const AiAssistantPage = lazy(() =>
  import('./pages/bi/BiPages').then((m) => ({ default: m.AiAssistantPage })),
)
const AdminOverviewPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.AdminOverviewPage })),
)
const WorkflowBuilderPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.WorkflowBuilderPage })),
)
const NotificationCenterPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.NotificationCenterPage })),
)
const JobSchedulerPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.JobSchedulerPage })),
)
const ReportSchedulerPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.ReportSchedulerPage })),
)
const SystemSettingsPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.SystemSettingsPage })),
)
const AuditCenterPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.AuditCenterPage })),
)
const FileManagementPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.FileManagementPage })),
)
const ApiManagementPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.ApiManagementPage })),
)
const IntegrationsPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.IntegrationsPage })),
)
const HealthDashboardPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.HealthDashboardPage })),
)
const SecurityCenterPage = lazy(() =>
  import('./pages/admin/AdminPages').then((m) => ({ default: m.SecurityCenterPage })),
)
const OrganizationDashboardPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.OrganizationDashboardPage })),
)
const OrganizationsListPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.OrganizationsListPage })),
)
const PlanComparisonPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.PlanComparisonPage })),
)
const SubscriptionCenterPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.SubscriptionCenterPage })),
)
const BillingPortalPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.BillingPortalPage })),
)
const UsageDashboardPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.UsageDashboardPage })),
)
const OnboardingWizardPage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.OnboardingWizardPage })),
)
const SuperAdminConsolePage = lazy(() =>
  import('./pages/saas/SaasPages').then((m) => ({ default: m.SuperAdminConsolePage })),
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
              <Route path="warehouses" element={<WarehousesPage />} />
              <Route path="units" element={<UnitsManagePage />} />
              <Route path="purchase-orders" element={<PurchaseOrdersPage />} />
              <Route path="goods-receipts" element={<GoodsReceiptsPage />} />
              <Route path="recipes" element={<RecipesPage />} />
              <Route path="menu" element={<MenuManagePage />} />
              <Route path="stock-alerts" element={<StockAlertsPage />} />
              <Route path="stock-transfers" element={<StockTransfersPage />} />
              <Route path="inventory-transactions" element={<InventoryTransactionsPage />} />
              <Route path="orders" element={<OrdersPage />} />
              <Route path="pos" element={<PosPage />} />
              <Route path="kitchen" element={<KitchenPage />} />
              <Route path="floor" element={<FloorPlanPage />} />
              <Route path="payments" element={<PaymentsPage />} />
              <Route path="customers" element={<CustomersPage />} />
              <Route path="employees" element={<EmployeesPage />} />
              <Route path="crm" element={<CrmDashboardPage />} />
              <Route path="loyalty" element={<LoyaltyPage />} />
              <Route path="reservations" element={<ReservationsPage />} />
              <Route path="hrms" element={<HrmsDashboardPage />} />
              <Route path="shifts" element={<ShiftsPage />} />
              <Route path="attendance" element={<AttendancePage />} />
              <Route path="leaves" element={<LeavesPage />} />
              <Route path="payroll" element={<PayrollPage />} />
              <Route path="executive" element={<ExecutiveDashboardPage />} />
              <Route path="analytics-center" element={<AnalyticsCenterPage />} />
              <Route path="forecast-bi" element={<ForecastDashboardPage />} />
              <Route path="insights" element={<InsightsAlertsPage />} />
              <Route path="reports-center" element={<ReportsCenterPage />} />
              <Route path="ai-assistant" element={<AiAssistantPage />} />
              <Route path="admin-console" element={<AdminOverviewPage />} />
              <Route path="workflow-builder" element={<WorkflowBuilderPage />} />
              <Route path="notification-center" element={<NotificationCenterPage />} />
              <Route path="job-scheduler" element={<JobSchedulerPage />} />
              <Route path="report-scheduler" element={<ReportSchedulerPage />} />
              <Route path="system-settings" element={<SystemSettingsPage />} />
              <Route path="audit-center" element={<AuditCenterPage />} />
              <Route path="file-management" element={<FileManagementPage />} />
              <Route path="api-management" element={<ApiManagementPage />} />
              <Route path="integrations" element={<IntegrationsPage />} />
              <Route path="health-dashboard" element={<HealthDashboardPage />} />
              <Route path="security-center" element={<SecurityCenterPage />} />
              <Route path="organizations" element={<OrganizationsListPage />} />
              <Route path="organization-dashboard" element={<OrganizationDashboardPage />} />
              <Route path="plans" element={<PlanComparisonPage />} />
              <Route path="subscription-center" element={<SubscriptionCenterPage />} />
              <Route path="billing-portal" element={<BillingPortalPage />} />
              <Route path="usage-dashboard" element={<UsageDashboardPage />} />
              <Route path="onboarding" element={<OnboardingWizardPage />} />
              <Route path="super-admin" element={<SuperAdminConsolePage />} />
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
