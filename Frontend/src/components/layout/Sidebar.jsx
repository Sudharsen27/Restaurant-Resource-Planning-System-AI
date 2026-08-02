import { NavLink, useNavigate } from 'react-router-dom'
import { Brain, ChevronLeft, ChevronRight } from 'lucide-react'
import { NAV_SECTIONS, SIDEBAR_LOGOUT } from '../../constants/navigation'
import { useAuth } from '../../context/AuthContext'
import { useSidebar } from '../../context/SidebarContext'
import { useToast } from '../../context/ToastContext'
import { ROLE_PATHS } from '../../constants/navigation'

function canAccess(role, path) {
  const allowed = ROLE_PATHS[role] || ROLE_PATHS.EMPLOYEE
  if (allowed.includes('*')) return true
  return allowed.some((p) => (p === '/' ? path === '/' : path === p || path.startsWith(`${p}/`)))
}

export default function Sidebar() {
  const { collapsed, toggleCollapsed, mobileOpen, closeMobile } = useSidebar()
  const { user, logout, canAccessPath } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()

  async function onLogout() {
    try {
      await logout(false)
      success('Signed out')
      navigate('/login', { replace: true })
    } catch (err) {
      error(err.message || 'Logout failed')
      navigate('/login', { replace: true })
    }
  }

  const widthClass = collapsed ? 'lg:w-[72px]' : 'lg:w-[260px]'

  return (
    <>
      {mobileOpen && (
        <button
          type="button"
          className="fixed inset-0 z-[55] bg-black/50 lg:hidden"
          onClick={closeMobile}
          aria-label="Close navigation"
        />
      )}
      <aside
        className={`fixed inset-y-0 left-0 z-50 flex flex-col border-r border-white/10 bg-[#17201d] text-stone-100 transition-all duration-200 dark:border-white/10 dark:bg-[#111815] ${widthClass} w-[260px] ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
        aria-label="Primary"
      >
        <div className="flex h-16 items-center gap-3 border-b border-white/10 px-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-500 shadow-sm shadow-emerald-950/30">
            <Brain className="h-5 w-5 text-white" />
          </div>
          {!collapsed && (
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-bold text-white">RestoPlan</p>
              <p className="truncate text-[10px] font-medium uppercase tracking-widest text-stone-400">
                Restaurant ERP
              </p>
            </div>
          )}
          <button
            type="button"
            onClick={toggleCollapsed}
            className="hidden rounded-lg p-1.5 text-stone-400 hover:bg-white/10 hover:text-white lg:inline-flex"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        <nav className="flex-1 space-y-4 overflow-y-auto p-3" aria-label="Main">
          {NAV_SECTIONS.map((section) => {
            const items = section.items.filter(
              (item) =>
                !item.hiddenInSidebar &&
                (canAccessPath?.(item.to) ?? canAccess(user?.role, item.to)),
            )
            if (!items.length) return null
            return (
              <div key={section.id}>
                {!collapsed && (
                  <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-wider text-stone-500">
                    {section.label}
                  </p>
                )}
                <ul className="space-y-0.5">
                  {items.map(({ to, label, icon: Icon, end }) => (
                    <li key={to}>
                      <NavLink
                        to={to}
                        end={end || to === '/'}
                        onClick={closeMobile}
                        title={collapsed ? label : undefined}
                        className={({ isActive }) =>
                          `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                            isActive
                              ? 'bg-emerald-500 text-white shadow-sm shadow-emerald-950/30'
                              : 'text-stone-300 hover:bg-white/10 hover:text-white'
                          } ${collapsed ? 'justify-center px-2' : ''}`
                        }
                      >
                        <Icon className="h-4 w-4 shrink-0" aria-hidden />
                        {!collapsed && <span>{label}</span>}
                      </NavLink>
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </nav>

        <div className="border-t border-white/10 p-3">
          <button
            type="button"
            onClick={onLogout}
            title="Logout"
            className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-rose-300 hover:bg-rose-400/10 hover:text-rose-200 ${
              collapsed ? 'justify-center px-2' : ''
            }`}
          >
            <SIDEBAR_LOGOUT.icon className="h-4 w-4" />
            {!collapsed && <span>{SIDEBAR_LOGOUT.label}</span>}
          </button>
        </div>
      </aside>
    </>
  )
}
