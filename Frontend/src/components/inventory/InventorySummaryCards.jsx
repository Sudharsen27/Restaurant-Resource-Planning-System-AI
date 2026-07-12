import { Briefcase, Package, Shield, Wallet } from 'lucide-react'
import StatCard from '../ui/StatCard'
import { CardSkeleton } from '../ui/Skeleton'
import { formatCurrency, formatNumber, formatPercent } from '../../utils/format'

export default function InventorySummaryCards({ plan, purchaseItems, loading }) {
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

  const safetyLabel =
    plan.safety_stock_rate != null
      ? formatPercent(plan.safety_stock_rate * 100, 0)
      : purchaseItems != null
        ? `${formatNumber(purchaseItems)} items to order`
        : '—'

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Total Ingredients"
        value={formatNumber(plan.ingredient_count)}
        change={`${purchaseItems ?? 0} require purchase`}
        icon={Package}
        accent="blue"
      />
      <StatCard
        label="Total Purchase Cost"
        value={formatCurrency(plan.inventory_cost)}
        change="Sum of estimated ingredient costs"
        icon={Wallet}
        accent="emerald"
      />
      <StatCard
        label="Safety Stock"
        value={safetyLabel}
        change={
          plan.safety_stock_rate != null
            ? 'Rate sent with inventory request'
            : 'Purchase buffer from API plan'
        }
        icon={Shield}
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
