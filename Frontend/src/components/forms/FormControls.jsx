const base =
  'w-full min-h-11 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-base sm:text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 disabled:opacity-60 dark:border-zinc-600 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-emerald-400 dark:focus:ring-emerald-400/20'

function Field({ label, error, hint, children, htmlFor }) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={htmlFor} className="block text-sm font-medium text-slate-700 dark:text-zinc-200">
          {label}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-slate-500 dark:text-zinc-400">{hint}</p>}
      {error && <p className="text-xs font-medium text-rose-600 dark:text-rose-400">{error}</p>}
    </div>
  )
}

export function Input({ label, error, hint, id, className = '', ...props }) {
  const inputId = id || props.name
  return (
    <Field label={label} error={error} hint={hint} htmlFor={inputId}>
      <input id={inputId} className={`${base} ${className}`} {...props} />
    </Field>
  )
}

export function Textarea({ label, error, hint, id, className = '', rows = 4, ...props }) {
  const inputId = id || props.name
  return (
    <Field label={label} error={error} hint={hint} htmlFor={inputId}>
      <textarea id={inputId} rows={rows} className={`${base} ${className}`} {...props} />
    </Field>
  )
}

export function Select({ label, error, hint, id, options = [], className = '', ...props }) {
  const inputId = id || props.name
  return (
    <Field label={label} error={error} hint={hint} htmlFor={inputId}>
      <select id={inputId} className={`${base} ${className}`} {...props}>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </Field>
  )
}

export function Checkbox({ label, id, className = '', ...props }) {
  const inputId = id || props.name
  return (
    <label htmlFor={inputId} className={`inline-flex items-center gap-2 text-sm ${className}`}>
      <input id={inputId} type="checkbox" className="h-4 w-4 rounded border-slate-300" {...props} />
      <span>{label}</span>
    </label>
  )
}

export function Switch({ label, checked, onChange, id }) {
  return (
    <button
      type="button"
      id={id}
      role="switch"
      aria-checked={checked}
      onClick={() => onChange?.(!checked)}
      className="inline-flex items-center gap-3 text-sm"
    >
      <span
        className={`relative h-6 w-11 rounded-full transition ${
          checked ? 'bg-blue-600 dark:bg-zinc-100' : 'bg-slate-300 dark:bg-zinc-700'
        }`}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition dark:bg-zinc-900 ${
            checked ? 'left-5 dark:left-5' : 'left-0.5'
          }`}
        />
      </span>
      {label && <span>{label}</span>}
    </button>
  )
}

export function RadioGroup({ label, name, options = [], value, onChange }) {
  return (
    <fieldset className="space-y-2">
      {label && <legend className="text-sm font-medium">{label}</legend>}
      <div className="flex flex-wrap gap-3">
        {options.map((opt) => (
          <label key={opt.value} className="inline-flex items-center gap-2 text-sm">
            <input
              type="radio"
              name={name}
              value={opt.value}
              checked={value === opt.value}
              onChange={() => onChange?.(opt.value)}
            />
            {opt.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}

export function FileUpload({ label, accept, onChange, hint }) {
  return (
    <Field label={label} hint={hint}>
      <input
        type="file"
        accept={accept}
        onChange={(e) => onChange?.(e.target.files?.[0] || null)}
        className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-slate-900 file:px-3 file:py-2 file:text-sm file:font-medium file:text-white dark:file:bg-zinc-100 dark:file:text-zinc-900"
      />
    </Field>
  )
}
