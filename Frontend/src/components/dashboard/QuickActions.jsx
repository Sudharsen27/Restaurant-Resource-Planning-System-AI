import {
  Package,
  ShoppingCart,
  UserPlus,
  Brain,
  Truck,
  PlusCircle,
} from 'lucide-react'
import { Link } from 'react-router-dom'

const ACTIONS = [
  { to: '/orders', label: 'Create Order', icon: ShoppingCart },
  { to: '/products', label: 'New Product', icon: PlusCircle },
  { to: '/inventory', label: 'Add Inventory', icon: Package },
  { to: '/forecast', label: 'Generate Forecast', icon: Brain },
  { to: '/employees', label: 'Add Employee', icon: UserPlus },
  { to: '/suppliers', label: 'Create Supplier', icon: Truck },
]

export default function QuickActions() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {ACTIONS.map(({ to, label, icon: Icon }) => (
        <Link
          key={to + label}
          to={to}
          className="group flex items-center gap-3 rounded-xl border border-stone-200 bg-white p-4 shadow-[0_1px_2px_rgba(28,35,30,0.04)] transition hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-md dark:border-white/10 dark:bg-[#1b2520] dark:hover:border-emerald-400/30"
        >
          <div className="rounded-lg bg-emerald-50 p-2.5 dark:bg-emerald-400/10">
            <Icon className="h-4 w-4 text-emerald-700 dark:text-emerald-300" />
          </div>
          <span className="text-sm font-semibold text-stone-800 dark:text-stone-100">{label}</span>
        </Link>
      ))}
    </div>
  )
}
