import { Users } from 'lucide-react'

export default function StaffPlannerHeader() {
  return (
    <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
      <div>
        <div className="flex items-center gap-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600/10">
            <Users className="h-5 w-5 text-emerald-600" />
          </div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
            Staff Planner
          </h2>
        </div>
        <p className="mt-2 max-w-2xl text-sm text-slate-500">
          ML-driven workforce planning based on predicted customer demand.
        </p>
      </div>
    </div>
  )
}
