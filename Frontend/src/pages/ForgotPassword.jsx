import { useState } from 'react'
import { Link } from 'react-router-dom'
import Button from '../components/ui/Button'
import { forgotPassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function ForgotPassword() {
  const { success, error } = useToast()
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [resetToken, setResetToken] = useState('')

  async function onSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setResetToken('')
    try {
      const res = await forgotPassword(email.trim())
      setResetToken(res?.data?.reset_token || '')
      success(res.message || 'If the account exists, reset instructions were generated')
    } catch (err) {
      error(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4 dark:bg-black">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-950">
        <h1 className="text-lg font-semibold text-slate-900 dark:text-white">Forgot password</h1>
        <p className="mt-1 text-sm text-slate-500">Enter your account email to generate a reset token.</p>
        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@restaurant.com"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
          <Button type="submit" className="w-full" disabled={loading}>
            {loading ? 'Sending…' : 'Request reset'}
          </Button>
        </form>
        {resetToken && (
          <div className="mt-4 rounded-lg bg-slate-50 p-3 text-xs break-all dark:bg-slate-800 dark:text-slate-200">
            Dev reset token: {resetToken}
            <div className="mt-2">
              <Link className="text-blue-600 hover:underline" to={`/reset-password?token=${encodeURIComponent(resetToken)}`}>
                Continue to reset
              </Link>
            </div>
          </div>
        )}
        <Link to="/login" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          Back to login
        </Link>
      </div>
    </div>
  )
}
