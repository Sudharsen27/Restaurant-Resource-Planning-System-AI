export default function Card({ title, subtitle, action, children, className = '' }) {
  return (
    <div
      className={`rounded-xl border border-stone-200/80 bg-white shadow-[0_1px_2px_rgba(28,35,30,0.04)] dark:border-white/10 dark:bg-[#1b2520] ${className}`}
    >
      {(title || action) && (
        <div className="flex items-start justify-between border-b border-stone-100 px-5 py-4 dark:border-white/10">
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
      <div className="p-5">{children}</div>
    </div>
  )
}
