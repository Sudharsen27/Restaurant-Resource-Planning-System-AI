import { Link, useNavigate } from 'react-router-dom'
import { LogOut, MonitorSmartphone, Settings, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'
import { useEffect, useRef, useState } from 'react'

export default function ProfileMenu() {
  const { user, logout } = useAuth()
  const { success, error } = useToast()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef(null)

  useEffect(() => {
    function onDoc(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

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

  const initials = (user?.full_name || 'U')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 rounded-xl border border-slate-200 px-2 py-1.5 dark:border-zinc-700"
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-zinc-900 text-[10px] font-bold text-white dark:bg-zinc-100 dark:text-zinc-900">
          {initials}
        </div>
        <span className="hidden max-w-[120px] truncate text-sm font-medium text-slate-700 sm:block dark:text-zinc-300">
          {user?.full_name || 'User'}
        </span>
      </button>
      {open && (
        <div
          role="menu"
          className="absolute right-0 top-11 z-[60] w-56 overflow-hidden rounded-xl border border-slate-200 bg-white py-1 shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
        >
          <div className="border-b border-slate-100 px-3 py-2 dark:border-zinc-800">
            <p className="truncate text-sm font-semibold">{user?.full_name}</p>
            <p className="truncate text-xs text-slate-500">{user?.email}</p>
            <p className="mt-1 text-[10px] uppercase tracking-wide text-slate-400">{user?.role}</p>
          </div>
          <Link
            role="menuitem"
            to="/profile"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-zinc-900"
          >
            <User className="h-4 w-4" /> Profile
          </Link>
          <Link
            role="menuitem"
            to="/sessions"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-zinc-900"
          >
            <MonitorSmartphone className="h-4 w-4" /> Sessions
          </Link>
          <Link
            role="menuitem"
            to="/settings"
            onClick={() => setOpen(false)}
            className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-zinc-900"
          >
            <Settings className="h-4 w-4" /> Settings
          </Link>
          <button
            type="button"
            role="menuitem"
            onClick={onLogout}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30"
          >
            <LogOut className="h-4 w-4" /> Sign out
          </button>
        </div>
      )}
    </div>
  )
}
