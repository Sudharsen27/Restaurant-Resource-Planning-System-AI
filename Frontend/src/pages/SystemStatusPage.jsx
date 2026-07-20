import { Link } from 'react-router-dom'
import Button from '../components/ui/Button'
import { Home, ShieldAlert, WifiOff, ServerCrash } from 'lucide-react'

const CONFIG = {
  404: {
    code: '404',
    title: 'Page not found',
    body: 'The page you requested does not exist or was moved.',
    icon: Home,
  },
  403: {
    code: '403',
    title: 'Access denied',
    body: 'You do not have permission to view this resource.',
    icon: ShieldAlert,
  },
  500: {
    code: '500',
    title: 'Something went wrong',
    body: 'An unexpected server error occurred. Try again shortly.',
    icon: ServerCrash,
  },
  offline: {
    code: 'Offline',
    title: 'You are offline',
    body: 'Check your connection and retry when you are back online.',
    icon: WifiOff,
  },
}

export default function SystemStatusPage({ variant = '404' }) {
  const cfg = CONFIG[variant] || CONFIG['404']
  const Icon = cfg.icon

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <div className="mb-4 rounded-2xl bg-slate-100 p-4 dark:bg-zinc-900">
        <Icon className="h-8 w-8" />
      </div>
      <p className="text-sm font-semibold uppercase tracking-widest text-slate-400">{cfg.code}</p>
      <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">{cfg.title}</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">{cfg.body}</p>
      <div className="mt-6 flex gap-3">
        <Link to="/">
          <Button>Go to dashboard</Button>
        </Link>
        <Link to="/support">
          <Button variant="secondary">Support</Button>
        </Link>
      </div>
    </div>
  )
}
