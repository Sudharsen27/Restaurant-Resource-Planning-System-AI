const variants = {
  primary:
    'bg-emerald-600 text-white shadow-sm shadow-emerald-950/15 hover:bg-emerald-700 focus-visible:ring-emerald-500 disabled:bg-emerald-400 dark:bg-emerald-500 dark:text-white dark:hover:bg-emerald-400 dark:focus-visible:ring-emerald-400 dark:disabled:bg-emerald-900 dark:disabled:text-emerald-200',
  secondary:
    'border border-stone-200 bg-white text-stone-700 shadow-sm hover:bg-stone-50 dark:border-white/10 dark:bg-[#1b2520] dark:text-stone-100 dark:hover:bg-white/10',
  danger: 'bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-500',
  ghost:
    'bg-transparent text-stone-700 hover:bg-stone-100 dark:text-stone-200 dark:hover:bg-white/10',
}

const sizes = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2 text-sm',
  lg: 'px-5 py-2.5 text-base',
}

export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  type = 'button',
  disabled = false,
  ...props
}) {
  return (
    <button
      type={type}
      disabled={disabled}
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}
