export function AuthCard({ title, description, children, footer, wide = false }) {
  return (
    <div className={`auth-card-enter w-full ${wide ? 'max-w-[440px]' : ''}`}>
      <header className="mb-7">
        <h1 className="text-[1.375rem] font-semibold tracking-tight text-slate-900 dark:text-white sm:text-[1.5rem]">
          {title}
        </h1>
        {description && (
          <p className="mt-2 text-sm leading-relaxed text-slate-500 dark:text-zinc-400">
            {description}
          </p>
        )}
      </header>

      {children}

      {footer && (
        <div className="mt-6 border-t border-slate-200/80 pt-5 dark:border-zinc-800">{footer}</div>
      )}
    </div>
  )
}
