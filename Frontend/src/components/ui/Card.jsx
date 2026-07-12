export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <div
      className={`rounded-2xl border border-slate-200/80 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900/80 ${className}`}
    >
      {(title || action) && (
        <div className="flex items-start justify-between border-b border-slate-100 px-6 py-4 dark:border-slate-800">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{title}</h3>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
            )}
          </div>
          {action}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}
