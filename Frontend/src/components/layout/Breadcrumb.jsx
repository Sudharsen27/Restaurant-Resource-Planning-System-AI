import { useMemo } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { ChevronRight, Home } from 'lucide-react'
import { BREADCRUMB_LABELS } from '../../constants/navigation'

export default function Breadcrumb() {
  const { pathname } = useLocation()
  const parts = useMemo(() => pathname.split('/').filter(Boolean), [pathname])

  if (parts.length === 0) {
    return (
      <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-xs text-slate-500">
        <Home className="h-3.5 w-3.5" />
        <span className="font-medium text-slate-700 dark:text-zinc-300">Dashboard</span>
      </nav>
    )
  }

  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-1 text-xs text-slate-500">
      <Link to="/" className="inline-flex items-center gap-1 hover:text-slate-800 dark:hover:text-zinc-200">
        <Home className="h-3.5 w-3.5" />
        <span>Home</span>
      </Link>
      {parts.map((part, i) => {
        const href = `/${parts.slice(0, i + 1).join('/')}`
        const label = BREADCRUMB_LABELS[part] || part
        const last = i === parts.length - 1
        return (
          <span key={href} className="inline-flex items-center gap-1">
            <ChevronRight className="h-3 w-3 opacity-50" />
            {last ? (
              <span className="font-medium text-slate-700 dark:text-zinc-300">{label}</span>
            ) : (
              <Link to={href} className="hover:text-slate-800 dark:hover:text-zinc-200">
                {label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
