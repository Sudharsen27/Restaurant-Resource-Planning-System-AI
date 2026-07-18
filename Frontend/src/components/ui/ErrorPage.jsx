import { AlertTriangle } from 'lucide-react'
import { Link } from 'react-router-dom'
import Button from './Button'

export default function ErrorPage({
  title = 'Something went wrong',
  message = 'An unexpected error occurred. Please try again.',
  homeTo = '/',
}) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center px-4 text-center">
      <AlertTriangle className="mb-4 h-12 w-12 text-amber-500" />
      <h1 className="text-xl font-semibold text-slate-900 dark:text-white">{title}</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500 dark:text-slate-400">{message}</p>
      <Link to={homeTo} className="mt-6">
        <Button>Back to Dashboard</Button>
      </Link>
    </div>
  )
}
