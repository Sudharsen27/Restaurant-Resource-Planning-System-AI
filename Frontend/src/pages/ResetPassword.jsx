import { useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import { AuthCard } from '../components/auth/AuthCard'
import { AuthInput, PasswordInput, PasswordStrength } from '../components/auth/AuthFields'
import { AuthPrimaryButton, FormFooter, AuthLink } from '../components/auth/AuthActions'
import { resetPassword } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function ResetPassword() {
  const { success, error } = useToast()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const hasTokenParam = Boolean(params.get('token'))
  const firstRef = useRef(null)
  const [token, setToken] = useState(params.get('token') || '')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})

  function validate() {
    const next = {}
    if (!token.trim()) next.token = 'Reset token is required'
    if (!password) next.password = 'Enter a new password'
    else if (password.length < 8) next.password = 'Use at least 8 characters'
    else if (!/[A-Z]/.test(password) || !/[a-z]/.test(password) || !/\d/.test(password)) {
      next.password = 'Include upper, lower, and a number'
    }
    if (confirm !== password) next.confirm = 'Passwords do not match'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!validate()) {
      firstRef.current?.focus()
      return
    }
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
    <AuthLayout>
      <AuthCard
        title="Choose a new password"
        description="Use a strong password you haven’t used here before."
        footer={
          <FormFooter>
            <AuthLink to="/login">← Back to sign in</AuthLink>
          </FormFooter>
        }
      >
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          {!hasTokenParam && (
            <AuthInput
              ref={firstRef}
              id="reset-token"
              label="Reset token"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              error={errors.token}
              required
            />
          )}
          <div className="space-y-2">
            <PasswordInput
              ref={hasTokenParam ? firstRef : undefined}
              id="reset-password"
              label="New password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              error={errors.password}
              required
              minLength={8}
            />
            <PasswordStrength password={password} />
          </div>
          <PasswordInput
            id="reset-confirm"
            label="Confirm password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            error={errors.confirm}
            required
          />
          <AuthPrimaryButton loading={loading}>
            {loading ? 'Saving…' : 'Update password'}
          </AuthPrimaryButton>
        </form>
      </AuthCard>
    </AuthLayout>
  )
}
