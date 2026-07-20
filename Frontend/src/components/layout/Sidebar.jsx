import { NavLink } from 'react-router-dom'
import {
  BarChart3,
  Brain,
  History,
  LayoutDashboard,
  MessageSquare,
  MonitorSmartphone,
  Package,
  Settings,
  TrendingUp,
  UserCircle2,
  Users,
} from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/forecast', label: 'Forecast', icon: TrendingUp },
  { to: '/staff', label: 'Staff', icon: Users },
  { to: '/inventory', label: 'Inventory', icon: Package },
  { to: '/feedback', label: 'Feedback', icon: MessageSquare },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/history', label: 'History', icon: History },
  { to: '/settings', label: 'Settings', icon: Settings },
  { to: '/profile', label: 'Profile', icon: UserCircle2 },
  { to: '/sessions', label: 'Sessions', icon: MonitorSmartphone },
]

export default function Sidebar({ mobileOpen, onClose }) {
  const { canAccessPath } = useAuth()
  const items = navItems.filter((item) => canAccessPath(item.to))

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={onClose}
          aria-label="Close sidebar"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col border-r border-slate-200 bg-white transition-transform dark:border-zinc-800 dark:bg-black lg:static lg:translate-x-0 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-16 items-center gap-3 border-b border-slate-200 px-6 dark:border-zinc-800">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-zinc-900 dark:bg-zinc-100">
            <Brain className="h-5 w-5 text-white dark:text-zinc-900" />
          </div>
          <div>
            <p className="text-sm font-bold text-slate-900 dark:text-white">RRPS</p>
            <p className="text-[10px] font-medium uppercase tracking-widest text-slate-500">
              ML Forecaster
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-4" aria-label="Main navigation">
          {items.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                  isActive
                    ? 'bg-blue-600 text-white dark:bg-zinc-100 dark:text-zinc-900 dark:shadow-none'
                    : 'text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-900'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="h-4 w-4" aria-hidden="true" />
                  <span aria-current={isActive ? 'page' : undefined}>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
