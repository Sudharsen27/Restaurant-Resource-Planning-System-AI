import { useEffect, useRef, useState } from 'react'
import { Navigate, useLocation, useNavigate } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import { AuthCard } from '../components/auth/AuthCard'
import { AuthAlert, AuthCheckbox, AuthInput, PasswordInput } from '../components/auth/AuthFields'
import {
  AuthPrimaryButton,
  SocialLoginButton,
  AuthDivider,
  FormFooter,
  AuthLink,
} from '../components/auth/AuthActions'
import { GOOGLE_CLIENT_ID } from '../constants/config'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { requestGoogleIdToken } from '../utils/googleIdentity'

export default function Login() {
  const { login, loginWithGoogle, isAuthenticated, bootstrapping } = useAuth()
  const { success, error: toastError } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const emailRef = useRef(null)
  const [email, setEmail] = useState(() => {
    try {
      return localStorage.getItem('rrps_remember_email') || ''
    } catch {
      return ''
    }
  })
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(() => {
    try {
      return Boolean(localStorage.getItem('rrps_remember_email'))
    } catch {
      return true
    }
  })
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [errors, setErrors] = useState({})
  // Enterprise rule: never show Google SSO without a build-time VITE client ID.
  const googleClientId = GOOGLE_CLIENT_ID
  const googleSignInEnabled = Boolean(googleClientId)

  useEffect(() => {
    emailRef.current?.focus()
  }, [])

  if (!bootstrapping && isAuthenticated) {
    return <Navigate to={location.state?.from || '/'} replace />
  }

  function validate() {
    const next = {}
    if (!email.trim()) next.email = 'Enter your email'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) next.email = 'Enter a valid email address'
    if (!password) next.password = 'Enter your password'
    else if (password.length < 8) next.password = 'Password must be at least 8 characters'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  async function onSubmit(e) {
    e.preventDefault()
    if (!validate()) {
      emailRef.current?.focus()
      return
    }
    setLoading(true)
    setErrors({})
    try {
      await login(email.trim(), password)
      try {
        if (remember) localStorage.setItem('rrps_remember_email', email.trim())
        else localStorage.removeItem('rrps_remember_email')
      } catch {
        /* ignore */
      }
      success('Welcome back')
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      setErrors({ form: err.message || 'Invalid email or password' })
    } finally {
      setLoading(false)
    }
  }

  async function onGoogleSignIn() {
    if (!googleClientId) {
      toastError('Google sign-in is not configured for this environment')
      return
    }
    setGoogleLoading(true)
    setErrors({})
    try {
      const idToken = await requestGoogleIdToken(googleClientId)
      await loginWithGoogle(idToken)
      success('Welcome back')
      navigate(location.state?.from || '/', { replace: true })
    } catch (err) {
      const message = err.message || 'Google sign-in failed'
      setErrors({ form: message })
      toastError(message)
    } finally {
      setGoogleLoading(false)
    }
  }

  return (
    <AuthLayout>
      <AuthCard
        title="Sign in"
        description="Access your restaurant workspace."
        footer={
          <FormFooter>
            New here? <AuthLink to="/register">Create an account</AuthLink>
          </FormFooter>
        }
      >
        <form onSubmit={onSubmit} className="space-y-5" noValidate>
          <AuthInput
            ref={emailRef}
            id="login-email"
            label="Email"
            type="email"
            autoComplete="email"
            inputMode="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (errors.email || errors.form) setErrors((p) => ({ ...p, email: undefined, form: undefined }))
            }}
            error={errors.email}
            required
          />
          <PasswordInput
            id="login-password"
            label="Password"
            autoComplete="current-password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              if (errors.password || errors.form) setErrors((p) => ({ ...p, password: undefined, form: undefined }))
            }}
            error={errors.password}
            required
            minLength={8}
          />

          <div className="flex items-center justify-between gap-3">
            <AuthCheckbox
              id="login-remember"
              checked={remember}
              onChange={(e) => setRemember(e.target.checked)}
            >
              Remember me
            </AuthCheckbox>
            <AuthLink to="/forgot-password" className="shrink-0 text-sm">
              Forgot password?
            </AuthLink>
          </div>

          {errors.form && <AuthAlert>{errors.form}</AuthAlert>}

          <div className="space-y-3 pt-1">
            <AuthPrimaryButton loading={loading} disabled={googleLoading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </AuthPrimaryButton>
            {googleSignInEnabled ? (
              <>
                <AuthDivider />
                <SocialLoginButton
                  onClick={() => void onGoogleSignIn()}
                  disabled={loading || googleLoading}
                  loading={googleLoading}
                />
              </>
            ) : null}
          </div>
        </form>
      </AuthCard>
    </AuthLayout>
  )
}
