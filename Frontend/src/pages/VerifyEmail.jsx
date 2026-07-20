import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CheckCircle2, Mail } from 'lucide-react'
import AuthLayout from '../components/auth/AuthLayout'
import { AuthCard } from '../components/auth/AuthCard'
import { AuthPrimaryButton, FormFooter, AuthLink } from '../components/auth/AuthActions'
import { useToast } from '../context/ToastContext'

export default function VerifyEmail() {
  const { success } = useToast()
  const [params] = useSearchParams()
  const email = useMemo(() => params.get('email') || '', [params])
  const [resending, setResending] = useState(false)

  async function onResend() {
    setResending(true)
    try {
      await new Promise((r) => setTimeout(r, 600))
      success('Verification email resent')
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthLayout>
      <AuthCard
        title="Check your email"
        description="We sent a verification link to activate your workspace."
        footer={
          <FormFooter>
            Wrong address? <AuthLink to="/register">Go back</AuthLink>
            <span className="mx-1.5 text-slate-300 dark:text-zinc-600" aria-hidden>
              ·
            </span>
            <AuthLink to="/login">Sign in</AuthLink>
          </FormFooter>
        }
      >
        <div className="flex flex-col items-center text-center">
          <div
            className="mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100 dark:bg-emerald-950/50 dark:text-emerald-400 dark:ring-emerald-900/60 auth-card-enter"
            aria-hidden
          >
            <CheckCircle2 className="h-7 w-7" strokeWidth={1.75} />
          </div>

          {email ? (
            <div className="mb-5 inline-flex max-w-full items-center gap-2 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-200">
              <Mail className="h-4 w-4 shrink-0 text-slate-400" aria-hidden />
              <span className="truncate font-medium">{email}</span>
            </div>
          ) : null}

          <p className="mb-6 max-w-sm text-sm leading-relaxed text-slate-500 dark:text-zinc-400">
            Open the link in that email to continue. If you don’t see it, check spam or resend below.
          </p>

          <AuthPrimaryButton type="button" loading={resending} onClick={onResend}>
            {resending ? 'Sending…' : 'Resend verification email'}
          </AuthPrimaryButton>
        </div>
      </AuthCard>
    </AuthLayout>
  )
}
