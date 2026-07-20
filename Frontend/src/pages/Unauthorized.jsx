import { Link } from 'react-router-dom'
import Button from '../components/ui/Button'

export default function Unauthorized() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center px-4 text-center">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">403 — Unauthorized</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        You do not have permission to view this page. Contact an administrator if you need access.
      </p>
      <div className="mt-6 flex gap-3">
        <Link to="/">
          <Button>Go to dashboard</Button>
        </Link>
        <Link to="/profile">
          <Button variant="secondary">Profile</Button>
        </Link>
      </div>
    </div>
  )
}
