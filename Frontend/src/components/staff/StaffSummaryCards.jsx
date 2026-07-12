import { Briefcase, IndianRupee, ShieldCheck, Users } from 'lucide-react'
import StatCard from '../ui/StatCard'
import { CardSkeleton } from '../ui/Skeleton'
import { formatCurrency, formatNumber, formatPercent } from '../../utils/format'

export default function StaffSummaryCards({ plan, shiftCoverage, loading }) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <CardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!plan) return null

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Total Recommended Staff"
        value={formatNumber(plan.total_staff)}
        change={`${plan.staff ? Object.keys(plan.staff).length : 0} role types`}
        icon={Users}
        accent="blue"
      />
      <StatCard
        label="Total Staff Cost"
        value={formatCurrency(plan.staff_cost)}
        change={
          plan.predicted_customers != null
            ? `Demand: ${formatNumber(plan.predicted_customers)} customers`
            : undefined
        }
        icon={IndianRupee}
        accent="emerald"
      />
      <StatCard
        label="Estimated Shift Coverage"
        value={shiftCoverage != null ? formatPercent(shiftCoverage, 0) : '—'}
        change="Roles staffed vs total role types"
        icon={ShieldCheck}
        accent="amber"
      />
      <StatCard
        label="Forecasted Customers"
        value={formatNumber(plan.predicted_customers)}
        change="Demand input for this plan"
        icon={Briefcase}
        accent="violet"
      />
    </div>
  )
}
