import { Eye, EyeOff } from 'lucide-react'
import { forwardRef, useId, useState } from 'react'
import { passwordStrength } from './authBrand'

const inputBase =
  'w-full rounded-lg border bg-white px-3 py-2.5 text-[15px] leading-snug text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/15 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-zinc-950 dark:text-zinc-50 dark:placeholder:text-zinc-500 dark:focus:border-blue-400 dark:focus:ring-blue-400/20'

const inputOk = 'border-slate-300 hover:border-slate-400 dark:border-zinc-700 dark:hover:border-zinc-600'
const inputErr =
  'border-rose-400 focus:border-rose-500 focus:ring-rose-500/15 dark:border-rose-500/70'

export const AuthInput = forwardRef(function AuthInput(
  { id, label, type = 'text', error, hint, className = '', ...props },
  ref,
) {
  const autoId = useId()
  const inputId = id || autoId
  const errId = `${inputId}-err`
  const hintId = `${inputId}-hint`

  return (
    <div className={`space-y-1.5 ${className}`}>
      <label
        htmlFor={inputId}
        className="block text-[13px] font-medium text-slate-700 dark:text-zinc-300"
      >
        {label}
      </label>
      <input
        ref={ref}
        id={inputId}
        type={type}
        aria-invalid={Boolean(error) || undefined}
        aria-describedby={error ? errId : hint ? hintId : undefined}
        className={`${inputBase} ${error ? inputErr : inputOk}`}
        {...props}
      />
      {hint && !error && (
        <p id={hintId} className="text-xs text-slate-500 dark:text-zinc-400">
          {hint}
        </p>
      )}
      {error && (
        <p id={errId} role="alert" className="text-xs font-medium text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}
    </div>
  )
})

export const PasswordInput = forwardRef(function PasswordInput(
  { id, label = 'Password', error, hint, className = '', ...props },
  ref,
) {
  const [show, setShow] = useState(false)
  const autoId = useId()
  const inputId = id || autoId
  const errId = `${inputId}-err`

  return (
    <div className={`space-y-1.5 ${className}`}>
      <label
        htmlFor={inputId}
        className="block text-[13px] font-medium text-slate-700 dark:text-zinc-300"
      >
        {label}
      </label>
      <div className="relative">
        <input
          ref={ref}
          id={inputId}
          type={show ? 'text' : 'password'}
          autoComplete={props.autoComplete || 'current-password'}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={error ? errId : undefined}
          className={`${inputBase} pr-11 ${error ? inputErr : inputOk}`}
          {...props}
        />
        <button
          type="button"
          onClick={() => setShow((v) => !v)}
          aria-pressed={show}
          aria-label={show ? 'Hide password' : 'Show password'}
          className="absolute right-1.5 top-1/2 inline-flex h-8 w-8 -translate-y-1/2 items-center justify-center rounded-md text-slate-400 transition hover:bg-slate-100 hover:text-slate-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/40 dark:hover:bg-zinc-800 dark:hover:text-zinc-200"
        >
          {show ? <EyeOff className="h-4 w-4" aria-hidden /> : <Eye className="h-4 w-4" aria-hidden />}
        </button>
      </div>
      {hint && !error && <p className="text-xs text-slate-500 dark:text-zinc-400">{hint}</p>}
      {error && (
        <p id={errId} role="alert" className="text-xs font-medium text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}
    </div>
  )
})

export function PasswordStrength({ password }) {
  const { label, score } = passwordStrength(password)
  if (!password) return null

  const segments = 5
  const filled = Math.min(score, segments)

  return (
    <div className="space-y-1.5" aria-live="polite">
      <div className="flex gap-1" role="meter" aria-valuemin={0} aria-valuemax={5} aria-valuenow={score} aria-label="Password strength">
        {Array.from({ length: segments }).map((_, i) => {
          let tone = 'bg-slate-200 dark:bg-zinc-800'
          if (i < filled) {
            if (score <= 1) tone = 'bg-rose-500'
            else if (score === 2) tone = 'bg-orange-500'
            else if (score === 3) tone = 'bg-amber-500'
            else if (score === 4) tone = 'bg-sky-500'
            else tone = 'bg-emerald-500'
          }
          return <div key={i} className={`h-1 flex-1 rounded-full transition-colors ${tone}`} />
        })}
      </div>
      <p className="text-xs text-slate-500 dark:text-zinc-400">
        Strength:{' '}
        <span className="font-medium text-slate-700 dark:text-zinc-200">{label}</span>
        {score < 3 ? ' · Use 8+ characters with mixed case, a number, and a symbol' : ''}
      </p>
    </div>
  )
}

export function AuthCheckbox({ id, checked, onChange, children, error }) {
  const autoId = useId()
  const inputId = id || autoId

  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="flex cursor-pointer items-start gap-2.5 text-sm text-slate-600 dark:text-zinc-300">
        <input
          id={inputId}
          type="checkbox"
          checked={checked}
          onChange={onChange}
          className="mt-0.5 h-4 w-4 shrink-0 rounded border-slate-300 text-blue-600 focus:ring-2 focus:ring-blue-500/30 focus:ring-offset-0 dark:border-zinc-600 dark:bg-zinc-950"
        />
        <span className="leading-snug">{children}</span>
      </label>
      {error && (
        <p role="alert" className="pl-6 text-xs font-medium text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}
    </div>
  )
}

export function AuthAlert({ children, variant = 'error' }) {
  const styles =
    variant === 'success'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200'
      : 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200'

  return (
    <div role="alert" aria-live="assertive" className={`rounded-lg border px-3.5 py-2.5 text-sm leading-snug ${styles}`}>
      {children}
    </div>
  )
}
