import Card from '../ui/Card'
import { ChartSkeleton } from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'
import { BarChartCard } from '../charts/ChartComponents'
import { chartColors } from '../../utils/format'
import { buildCostBreakdownChartData, buildQuantityBarChartData } from '../../utils/inventoryPlanner'

export default function InventoryChartsSection({ rows, loading }) {
  const costData = buildCostBreakdownChartData(rows)
  const qtyData = buildQuantityBarChartData(rows)

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Inventory Cost Breakdown" subtitle="Estimated cost by ingredient (Recharts)">
        {loading ? (
          <ChartSkeleton />
        ) : costData.length ? (
          <BarChartCard
            data={costData}
            xKey="name"
            bars={[{ key: 'cost', name: 'Cost (INR)', color: chartColors.secondary }]}
            layout="vertical"
            height={320}
          />
        ) : (
          <EmptyState title="No cost data" />
        )}
      </Card>

      <Card title="Ingredient Quantity" subtitle="Required vs purchase quantities (Recharts)">
        {loading ? (
          <ChartSkeleton />
        ) : qtyData.length ? (
          <BarChartCard
            data={qtyData}
            xKey="name"
            bars={[
              { key: 'required', name: 'Required', color: chartColors.primary },
              { key: 'purchase', name: 'Purchase', color: chartColors.warning },
            ]}
            layout="vertical"
            height={320}
          />
        ) : (
          <EmptyState title="No quantity data" />
        )}
      </Card>
    </div>
  )
}
