import { Bell, Menu, Moon, Sun } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { useSidebar } from '../../context/SidebarContext'
import { useOrg } from '../../context/OrgContext'
import { useNotifications } from '../../context/NotificationContext'
import ProfileMenu from './ProfileMenu'
import NotificationPanel from './NotificationPanel'
import Breadcrumb from './Breadcrumb'

export default function Navbar() {
  const { darkMode, toggleTheme } = useTheme()
  const { openMobile } = useSidebar()
  const { restaurants, branches, restaurant, branch, selectRestaurant, selectBranch, branchesLoading } =
    useOrg()
  const { unreadCount, setPanelOpen, panelOpen } = useNotifications()

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 backdrop-blur-md dark:border-zinc-800 dark:bg-black/90">
      <div className="flex h-16 items-center gap-3 px-4 lg:px-6">
        <button
          type="button"
          onClick={openMobile}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden dark:text-zinc-400 dark:hover:bg-zinc-900"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>

        <div className="hidden min-w-0 flex-1 md:block">
          <Breadcrumb />
        </div>

        <div className="ml-auto flex items-center gap-2">
          <select
            value={restaurant?.id || ''}
            onChange={(e) => selectRestaurant(e.target.value)}
            className="hidden max-w-[160px] truncate rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs sm:block dark:border-zinc-700 dark:bg-zinc-950"
            aria-label="Restaurant"
          >
            {restaurants.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
          <select
            value={branch?.id || ''}
            onChange={(e) => selectBranch(e.target.value)}
            disabled={!branches.length || branchesLoading}
            title={
              !branches.length && !branchesLoading
                ? 'No location for this restaurant yet'
                : 'Branch / location'
            }
            className="hidden max-w-[150px] truncate rounded-lg border border-slate-200 bg-white px-2 py-1.5 text-xs disabled:cursor-not-allowed disabled:opacity-60 md:block dark:border-zinc-700 dark:bg-zinc-950"
            aria-label="Branch location"
          >
            {branchesLoading && <option value="">Loading…</option>}
            {!branchesLoading && !branches.length && (
              <option value="">No location</option>
            )}
            {branches.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={toggleTheme}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
            aria-label="Toggle theme"
          >
            {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>

          <div className="relative">
            <button
              type="button"
              onClick={() => setPanelOpen(!panelOpen)}
              className="relative rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-zinc-400 dark:hover:bg-zinc-900"
              aria-label="Notifications"
            >
              <Bell className="h-5 w-5" />
              {unreadCount > 0 && (
                <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-rose-500" />
              )}
            </button>
            <NotificationPanel />
          </div>

          <ProfileMenu />
        </div>
      </div>
    </header>
  )
}
