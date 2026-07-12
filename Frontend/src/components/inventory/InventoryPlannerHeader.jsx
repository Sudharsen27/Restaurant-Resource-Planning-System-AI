import { Package } from 'lucide-react'

export default function InventoryPlannerHeader() {
  return (
    <div>
      <div className="flex items-center gap-2">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-600/10">
          <Package className="h-5 w-5 text-amber-600" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Inventory Planner
        </h2>
      </div>
      <p className="mt-2 max-w-2xl text-sm text-slate-500">
        ML-driven ingredient procurement planning based on predicted customer demand.
      </p>
    </div>
  )
}
