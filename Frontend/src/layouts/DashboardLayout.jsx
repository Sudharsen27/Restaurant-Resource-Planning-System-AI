import { Outlet } from 'react-router-dom'
import Sidebar from '../components/layout/Sidebar'
import Navbar from '../components/layout/Navbar'
import Footer from '../components/layout/Footer'
import ToastContainer from '../components/ui/Toast'
import ErrorBoundary from '../components/ErrorBoundary'
import { SidebarProvider, useSidebar } from '../context/SidebarContext'
import { OrgProvider } from '../context/OrgContext'
import { NotificationProvider } from '../context/NotificationContext'

function Shell() {
  const { collapsed } = useSidebar()
  const pad = collapsed ? 'lg:pl-[72px]' : 'lg:pl-[260px]'

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-black">
      <Sidebar />
      <div className={`flex min-h-screen min-w-0 flex-col transition-[padding] duration-200 ${pad}`}>
        <Navbar />
        <main className="flex-1 overflow-auto p-4 lg:p-6">
          <ErrorBoundary>
            <div className="animate-in fade-in duration-200">
              <Outlet />
            </div>
          </ErrorBoundary>
        </main>
        <Footer />
      </div>
      <ToastContainer />
    </div>
  )
}

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <OrgProvider>
        <NotificationProvider>
          <Shell />
        </NotificationProvider>
      </OrgProvider>
    </SidebarProvider>
  )
}
