import StatCard from '../ui/StatCard'
import { Activity, Brain, Target, TrendingUp } from 'lucide-react'
import { formatNumber, formatPercent } from '../../utils/format'

export default function ModelMetricsCards({ current, accuracy }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <StatCard
        label="Accuracy"
        value={formatPercent(current?.accuracy ?? accuracy?.overall_accuracy)}
        change={
          accuracy
            ? `Today ${formatPercent(accuracy.todays_accuracy)} · 30d ${formatPercent(accuracy.last_30_days_accuracy)}`
            : undefined
        }
        icon={Target}
        accent="emerald"
      />
      <StatCard
        label="MAE"
        value={current?.mae != null ? current.mae.toFixed(4) : '—'}
        change={
          accuracy?.average_error != null
            ? `Avg error: ${accuracy.average_error.toFixed(2)}`
            : undefined
        }
        icon={Activity}
        accent="amber"
      />
      <StatCard
        label="RMSE"
        value={current?.rmse != null ? current.rmse.toFixed(4) : '—'}
        change={
          accuracy?.average_mape != null
            ? `Avg MAPE: ${accuracy.average_mape.toFixed(2)}%`
            : undefined
        }
        icon={Brain}
        accent="blue"
      />
      <StatCard
        label="R²"
        value={current?.r2 != null ? current.r2.toFixed(4) : '—'}
        change={
          accuracy?.feedback_count != null
            ? `${formatNumber(accuracy.feedback_count)} feedback samples`
            : undefined
        }
        icon={TrendingUp}
        accent="violet"
      />
    </div>
  )
}
