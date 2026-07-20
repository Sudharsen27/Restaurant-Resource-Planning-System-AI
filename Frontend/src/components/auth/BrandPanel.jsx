import { Brain, ClipboardList, Moon, Sun, UtensilsCrossed, Warehouse } from 'lucide-react'
import { AUTH_BRAND } from './authBrand'
import { useTheme } from '../../context/ThemeContext'

const HIGHLIGHTS = [
  { icon: Warehouse, title: 'Inventory & procurement', desc: 'Stock, POs, and transfers across locations' },
  { icon: ClipboardList, title: 'POS & order flow', desc: 'Floor to kitchen with live status' },
  { icon: Brain, title: 'Forecast & staffing AI', desc: 'Demand plans your managers can trust' },
]

export function ThemeToggle({ className = '', variant = 'light' }) {
  const { darkMode, toggleTheme } = useTheme()
  const light =
    'text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:ring-slate-400/30 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-zinc-100'
  const dark = 'text-slate-300 hover:bg-white/10 hover:text-white focus-visible:ring-white/25'

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`inline-flex h-9 w-9 items-center justify-center rounded-lg transition focus-visible:outline-none focus-visible:ring-4 ${
        variant === 'dark' ? dark : light
      } ${className}`}
      aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
      title={darkMode ? 'Light mode' : 'Dark mode'}
    >
      {darkMode ? <Sun className="h-4 w-4" aria-hidden /> : <Moon className="h-4 w-4" aria-hidden />}
    </button>
  )
}

export function BrandPanel({ compact = false }) {
  if (compact) {
    return (
      <div className="flex items-center justify-between gap-3 border-b border-slate-200/70 bg-white/90 px-4 py-3 backdrop-blur-sm dark:border-zinc-800 dark:bg-zinc-950/90 sm:px-6">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white">
            <UtensilsCrossed className="h-3.5 w-3.5" aria-hidden />
          </div>
          <div>
            <p className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white">
              {AUTH_BRAND.name}
            </p>
            <p className="text-[11px] leading-none text-slate-500 dark:text-zinc-400">
              {AUTH_BRAND.product}
            </p>
          </div>
        </div>
        <ThemeToggle />
      </div>
    )
  }

  return (
    <aside
      className="relative flex min-h-0 w-full shrink-0 flex-col overflow-hidden bg-[#0A0F1A] text-white md:h-full md:w-[46%] lg:w-[40%]"
      aria-label="Product overview"
    >
      <div
        className="pointer-events-none absolute inset-0"
        aria-hidden
        style={{
          background:
            'radial-gradient(ellipse 90% 55% at 0% 0%, rgba(37,99,235,0.28), transparent 55%), radial-gradient(ellipse 60% 40% at 100% 100%, rgba(56,189,248,0.08), transparent 50%)',
        }}
      />

      <div className="relative z-10 flex min-h-0 flex-1 flex-col overflow-y-auto px-8 py-8 lg:px-10 lg:py-10 xl:px-12">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-500">
            <UtensilsCrossed className="h-4 w-4" aria-hidden />
          </div>
          <div>
            <p className="text-[15px] font-semibold tracking-tight">{AUTH_BRAND.name}</p>
            <p className="text-xs text-slate-400">{AUTH_BRAND.product}</p>
          </div>
        </div>

        <div className="mt-14 max-w-sm auth-fade-up lg:mt-16">
          <h2 className="text-[1.75rem] font-semibold leading-[1.2] tracking-tight lg:text-[2rem]">
            Run every location with clarity.
          </h2>
          <p className="mt-4 text-sm leading-relaxed text-slate-400 lg:text-[15px]">
            {AUTH_BRAND.tagline}
          </p>
        </div>

        <ul className="mt-10 space-y-4 auth-fade-up lg:mt-12" style={{ animationDelay: '60ms' }}>
          {HIGHLIGHTS.map((item) => {
            const Icon = item.icon
            return (
              <li key={item.title} className="flex gap-3">
                <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-white/5 text-blue-300 ring-1 ring-white/10">
                  <Icon className="h-4 w-4" aria-hidden />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-100">{item.title}</p>
                  <p className="mt-0.5 text-xs leading-relaxed text-slate-400">{item.desc}</p>
                </div>
              </li>
            )
          })}
        </ul>

        <div
          className="mt-auto hidden pt-12 auth-fade-up xl:block"
          style={{ animationDelay: '120ms' }}
        >
          <div className="rounded-xl border border-white/10 bg-white/[0.04] p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs font-medium text-slate-300">Today across locations</p>
              <span className="text-[10px] font-medium uppercase tracking-wider text-emerald-400/90">
                Live
              </span>
            </div>
            <div className="grid grid-cols-3 gap-3">
              {[
                { label: 'Orders', value: '1,284' },
                { label: 'Revenue', value: '₹2.4L' },
                { label: 'Fill rate', value: '98%' },
              ].map((m) => (
                <div key={m.label}>
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">{m.label}</p>
                  <p className="mt-1 text-lg font-semibold tracking-tight tabular-nums">{m.value}</p>
                </div>
              ))}
            </div>
          </div>
          <p className="mt-6 text-[11px] text-slate-500">
            Trusted by restaurant groups that need ERP depth without ERP clutter.
          </p>
        </div>
      </div>
    </aside>
  )
}
