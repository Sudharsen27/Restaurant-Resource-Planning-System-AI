import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import { AuthCard } from '../components/auth/AuthCard'
import { AuthAlert, AuthInput } from '../components/auth/AuthFields'
import { AuthPrimaryButton, FormFooter, AuthLink } from '../components/auth/AuthActions'
import { forgotPassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function ForgotPassword() {
  const { success, error } = useToast()
  const emailRef = useRef(null)
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [resetToken, setResetToken] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [sent, setSent] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    if (!email.trim()) {
      setFieldError('Enter your email')
      emailRef.current?.focus()
      return
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setFieldError('Enter a valid email address')
      emailRef.current?.focus()
      return
    }
    setFieldError('')
    setLoading(true)
    setResetToken('')
    setSent(false)
    try {
      const res = await forgotPassword(email.trim())
      setResetToken(res?.data?.reset_token || '')
      setSent(true)
      success(res.message || 'If the account exists, reset instructions were generated')
    } catch (err) {
      error(err.message || 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <AuthCard
        title="Reset your password"
        description="Enter your account email and we’ll send a reset link if it exists."
        footer={
          <FormFooter>
            <AuthLink to="/login">← Back to sign in</AuthLink>
          </FormFooter>
        }
      >
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          <AuthInput
            ref={emailRef}
            id="forgot-email"
            label="Email"
            type="email"
            autoComplete="email"
            autoFocus
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (fieldError) setFieldError('')
            }}
            error={fieldError}
            required
          />
          <AuthPrimaryButton loading={loading}>
            {loading ? 'Sending…' : 'Send reset link'}
          </AuthPrimaryButton>
        </form>

        {sent && (
          <div className="mt-6 space-y-3">
            <AuthAlert variant="success">
              <p className="font-medium">Check your inbox</p>
              <p className="mt-1 text-xs opacity-90">
                If an account exists for that address, reset instructions are on the way.
              </p>
            </AuthAlert>
            {resetToken && (
              <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-3 text-xs text-slate-600 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-300">
                <p className="font-medium text-slate-800 dark:text-zinc-200">Dev only · Reset token</p>
                <p className="mt-1 break-all font-mono text-[11px] leading-relaxed">{resetToken}</p>
                <Link
                  className="mt-2 inline-flex font-semibold text-blue-600 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 dark:text-blue-400"
                  to={`/reset-password?token=${encodeURIComponent(resetToken)}`}
                >
                  Continue to reset password
                </Link>
              </div>
            )}
          </div>
        )}
      </AuthCard>
    </AuthLayout>
  )
}
