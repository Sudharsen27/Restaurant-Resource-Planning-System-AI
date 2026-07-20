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
          className="group flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-4 transition hover:-translate-y-0.5 hover:shadow-md dark:border-zinc-800 dark:bg-zinc-950"
        >
          <div className="rounded-xl bg-slate-100 p-2.5 dark:bg-zinc-900">
            <Icon className="h-4 w-4 text-slate-700 dark:text-zinc-200" />
          </div>
          <span className="text-sm font-semibold text-slate-800 dark:text-zinc-100">{label}</span>
        </Link>
      ))}
    </div>
  )
}
