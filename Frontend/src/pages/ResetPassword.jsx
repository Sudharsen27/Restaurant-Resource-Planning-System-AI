import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import Button from '../components/ui/Button'
import { resetPassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function ResetPassword() {
  const { success, error } = useToast()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [token, setToken] = useState(params.get('token') || '')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    try {
      await resetPassword(token.trim(), password)
      success('Password reset successful. Please sign in.')
      navigate('/login', { replace: true })
    } catch (err) {
      error(err.message || 'Reset failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 dark:bg-black">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-lg font-semibold text-slate-900 dark:text-white">Reset password</h1>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="text"
            required
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Reset token"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="New password (Aa1!…)"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Saving…' : 'Reset password'}
          </Button>
        </form>
        <Link to="/login" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Back to login
        </Link>
      </div>
    </div>
  )
}
