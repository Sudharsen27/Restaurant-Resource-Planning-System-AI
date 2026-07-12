import Card from '../ui/Card'
import { ChartSkeleton } from '../ui/Skeleton'
import EmptyState from '../ui/EmptyState'
import { BarChartCard, PieChartCard } from '../charts/ChartComponents'
import { chartColors } from '../../utils/format'
import { buildCountBarChartData, buildDistributionChartData } from '../../utils/staffPlanner'

export default function StaffChartsSection({ rows, loading }) {
  const pieData = buildDistributionChartData(rows)
  const barData = buildCountBarChartData(rows)

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card title="Staff Distribution" subtitle="Headcount share by role (Recharts)">
        {loading ? (
          <ChartSkeleton />
        ) : pieData.length ? (
          <PieChartCard data={pieData} />
        ) : (
          <EmptyState title="No distribution data" />
        )}
      </Card>

      <Card title="Staff Count by Role" subtitle="Recommended headcount (Recharts)">
        {loading ? (
          <ChartSkeleton />
        ) : barData.length ? (
          <BarChartCard
            data={barData}
            xKey="name"
            bars={[{ key: 'count', name: 'Staff', color: chartColors.primary }]}
            layout="vertical"
            height={300}
          />
        ) : (
          <EmptyState title="No staff counts" />
        )}
      </Card>
    </div>
  )
}
