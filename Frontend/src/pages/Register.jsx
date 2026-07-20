import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AuthLayout from '../components/auth/AuthLayout'
import { AuthCard } from '../components/auth/AuthCard'
import {
  AuthCheckbox,
  AuthInput,
  PasswordInput,
  PasswordStrength,
} from '../components/auth/AuthFields'
import { AuthPrimaryButton, FormFooter, AuthLink } from '../components/auth/AuthActions'
import { useToast } from '../context/ToastContext'

/**
 * Enterprise register UI — accounts are provisioned by admins.
 * No public register API; form validates and routes to verify screen.
 */
export default function Register() {
  const { success, error } = useToast()
  const navigate = useNavigate()
  const firstRef = useRef(null)
  const [loading, setLoading] = useState(false)
  const [accepted, setAccepted] = useState(false)
  const [form, setForm] = useState({
    restaurantName: '',
    ownerName: '',
    email: '',
    phone: '',
    password: '',
    confirm: '',
  })
  const [errors, setErrors] = useState({})

  function setField(key, value) {
    setForm((p) => ({ ...p, [key]: value }))
    if (errors[key]) setErrors((p) => ({ ...p, [key]: undefined }))
  }

  function validate() {
    const next = {}
    if (!form.restaurantName.trim()) next.restaurantName = 'Enter your restaurant name'
    if (!form.ownerName.trim()) next.ownerName = 'Enter the owner name'
    if (!form.email.trim()) next.email = 'Enter a business email'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) next.email = 'Enter a valid email address'
    if (!form.phone.trim()) next.phone = 'Enter a phone number'
    if (!form.password) next.password = 'Create a password'
    else if (form.password.length < 8) next.password = 'Use at least 8 characters'
    if (form.confirm !== form.password) next.confirm = 'Passwords do not match'
    if (!accepted) next.terms = 'Accept the terms to continue'
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
      await new Promise((r) => setTimeout(r, 700))
      success('Request received. Check your email to verify your workspace.')
      navigate(`/verify-email?email=${encodeURIComponent(form.email.trim())}`, { replace: true })
    } catch (err) {
      error(err.message || 'Could not submit registration')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout>
      <AuthCard
        wide
        title="Create your workspace"
        description="Tell us about your restaurant. Access is activated after email verification."
        footer={
          <FormFooter>
            Already have an account? <AuthLink to="/login">Sign in</AuthLink>
          </FormFooter>
        }
      >
        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          <AuthInput
            ref={firstRef}
            id="reg-restaurant"
            label="Restaurant name"
            value={form.restaurantName}
            onChange={(e) => setField('restaurantName', e.target.value)}
            error={errors.restaurantName}
            autoComplete="organization"
            required
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <AuthInput
              id="reg-owner"
              label="Owner name"
              value={form.ownerName}
              onChange={(e) => setField('ownerName', e.target.value)}
              error={errors.ownerName}
              autoComplete="name"
              required
            />
            <AuthInput
              id="reg-phone"
              label="Phone"
              type="tel"
              value={form.phone}
              onChange={(e) => setField('phone', e.target.value)}
              error={errors.phone}
              autoComplete="tel"
              required
            />
          </div>

          <AuthInput
            id="reg-email"
            label="Business email"
            type="email"
            value={form.email}
            onChange={(e) => setField('email', e.target.value)}
            error={errors.email}
            autoComplete="email"
            required
          />

          <div className="space-y-2">
            <PasswordInput
              id="reg-password"
              label="Password"
              autoComplete="new-password"
              value={form.password}
              onChange={(e) => setField('password', e.target.value)}
              error={errors.password}
              required
              minLength={8}
            />
            <PasswordStrength password={form.password} />
          </div>

          <PasswordInput
            id="reg-confirm"
            label="Confirm password"
            autoComplete="new-password"
            value={form.confirm}
            onChange={(e) => setField('confirm', e.target.value)}
            error={errors.confirm}
            required
          />

          <AuthCheckbox
            id="reg-terms"
            checked={accepted}
            onChange={(e) => {
              setAccepted(e.target.checked)
              if (errors.terms) setErrors((p) => ({ ...p, terms: undefined }))
            }}
            error={errors.terms}
          >
            I agree to the{' '}
            <span className="font-medium text-slate-800 dark:text-zinc-100">Terms</span> and{' '}
            <span className="font-medium text-slate-800 dark:text-zinc-100">Privacy Policy</span>.
          </AuthCheckbox>

          <div className="pt-1">
            <AuthPrimaryButton loading={loading}>
              {loading ? 'Creating workspace…' : 'Create account'}
            </AuthPrimaryButton>
          </div>
        </form>
      </AuthCard>
    </AuthLayout>
  )
}
