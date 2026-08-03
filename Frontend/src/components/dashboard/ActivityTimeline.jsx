import { Package, UserCheck, ShoppingBag, Brain, FileCheck } from 'lucide-react'

const ICONS = {
  inventory: Package,
  employee: UserCheck,
  order: ShoppingBag,
  forecast: Brain,
  purchase: FileCheck,
}

function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

export default function ActivityTimeline({ items = [] }) {
  return (
    <ol className="relative space-y-0 border-l border-stone-200 pl-6 dark:border-white/10">
      {items.map((item) => {
        const Icon = ICONS[item.type] || Package
        return (
          <li key={item.id} className="relative pb-6 last:pb-0">
            <span className="absolute -left-[31px] flex h-7 w-7 items-center justify-center rounded-full border border-emerald-100 bg-emerald-50 dark:border-emerald-400/20 dark:bg-emerald-400/10">
              <Icon className="h-3.5 w-3.5 text-emerald-700 dark:text-emerald-300" />
            </span>
            <p className="text-sm font-semibold text-stone-900 dark:text-stone-100">{item.title}</p>
            <p className="text-xs text-stone-500">{item.detail}</p>
            <p className="mt-1 text-[10px] uppercase tracking-wide text-stone-400">{timeAgo(item.at)}</p>
          </li>
        )
      })}
    </ol>
  )
}
