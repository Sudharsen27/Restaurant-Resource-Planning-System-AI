import { Bell, Menu, Moon, Sun, User } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'

export default function Navbar({ onMenuClick }) {
  const { darkMode, toggleTheme } = useTheme()
  const today = new Date().toLocaleDateString('en-IN', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/80 lg:px-8">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onMenuClick}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden dark:text-slate-400 dark:hover:bg-slate-800"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div>
          <h1 className="text-sm font-semibold text-slate-900 dark:text-white">
            Spice Garden Restaurant
          </h1>
          <p className="text-xs text-slate-500">{today}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleTheme}
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          aria-label="Toggle theme"
        >
          {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
        </button>
        <button
          type="button"
          className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          <Bell className="h-5 w-5" />
        </button>
        <div className="ml-1 flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-1.5 dark:border-slate-700">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600">
            <User className="h-4 w-4 text-white" />
          </div>
          <span className="hidden text-sm font-medium text-slate-700 sm:block dark:text-slate-300">
            Manager
          </span>
        </div>
      </div>
    </header>
  )
}
