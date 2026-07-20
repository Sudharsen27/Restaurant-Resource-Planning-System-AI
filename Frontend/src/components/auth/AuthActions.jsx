import { Loader2 } from 'lucide-react'
import { Link } from 'react-router-dom'

export function AuthPrimaryButton({
  children,
  loading,
  className = '',
  disabled,
  type = 'submit',
  ...props
}) {
  return (
    <button
      type={type}
      className={`inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-500 active:bg-blue-700 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-blue-500/30 disabled:cursor-not-allowed disabled:opacity-55 dark:bg-blue-500 dark:hover:bg-blue-400 ${className}`}
      {...props}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : null}
      <span>{children}</span>
    </button>
  )
}

export function AuthSecondaryButton({ children, className = '', ...props }) {
  return (
    <button
      type="button"
      className={`inline-flex h-10 w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 text-sm font-semibold text-slate-800 transition hover:bg-slate-50 active:bg-slate-100 focus-visible:outline-none focus-visible:ring-4 focus-visible:ring-slate-400/25 disabled:opacity-55 dark:border-zinc-700 dark:bg-zinc-950 dark:text-zinc-100 dark:hover:bg-zinc-900 ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function SocialLoginButton({ provider = 'Google', onClick, disabled }) {
  return (
    <AuthSecondaryButton
      onClick={onClick}
      disabled={disabled}
      aria-label={`Continue with ${provider}`}
    >
      <svg className="h-4 w-4 shrink-0" viewBox="0 0 24 24" aria-hidden>
        <path
          fill="#EA4335"
          d="M12 10.2v3.6h5.1c-.2 1.2-.9 2.3-1.9 3l3.1 2.4c1.8-1.7 2.9-4.1 2.9-7 0-.7-.1-1.3-.2-1.9H12z"
        />
        <path
          fill="#34A853"
          d="M6.6 14.3l-.8.6-2.7 2.1C4.7 20 8.1 22 12 22c2.4 0 4.5-.8 6-2.2l-3.1-2.4c-.8.6-1.9.9-2.9.9-2.3 0-4.2-1.5-4.9-3.6z"
        />
        <path
          fill="#4A90E2"
          d="M3.1 7.1C2.4 8.5 2 10.2 2 12s.4 3.5 1.1 4.9l3.5-2.7C6.2 13.4 6 12.7 6 12s.2-1.4.5-2.1L3.1 7.1z"
        />
        <path
          fill="#FBBC05"
          d="M12 6c1.3 0 2.5.5 3.4 1.3l2.6-2.6C16.5 3.4 14.4 2.5 12 2.5 8.1 2.5 4.7 4.5 3.1 7.1l3.4 2.7C7.3 7.7 9.3 6 12 6z"
        />
      </svg>
      Continue with {provider}
    </AuthSecondaryButton>
  )
}

export function AuthDivider({ label = 'or' }) {
  return (
    <div className="relative flex items-center gap-3 py-0.5" role="separator" aria-label={label}>
      <div className="h-px flex-1 bg-slate-200 dark:bg-zinc-800" />
      <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400 dark:text-zinc-500">
        {label}
      </span>
      <div className="h-px flex-1 bg-slate-200 dark:bg-zinc-800" />
    </div>
  )
}

export function FormFooter({ children }) {
  return <p className="text-center text-sm text-slate-500 dark:text-zinc-400">{children}</p>
}

export function AuthLink({ to, children, className = '' }) {
  return (
    <Link
      to={to}
      className={`font-semibold text-blue-600 underline-offset-2 transition hover:text-blue-500 hover:underline focus-visible:rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 dark:text-blue-400 dark:hover:text-blue-300 ${className}`}
    >
      {children}
    </Link>
  )
}
