import { Moon, Server, Sun } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { useTheme } from '../context/ThemeContext'
import { healthCheck } from '../services/forecastService'
import { getDatasetInfo } from '../services/datasetService'
import { formatDate, formatNumber } from '../utils/format'

export default function Settings() {
  const { darkMode, toggleTheme } = useTheme()
  const restaurantName = 'Spice Garden Restaurant'

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['api-health'],
    queryFn: async () => (await healthCheck()).data,
    staleTime: 60_000,
    retry: 1,
  })

  const { data: dataset, isLoading: dsLoading } = useQuery({
    queryKey: ['dataset-info'],
    queryFn: async () => (await getDatasetInfo()).data,
    staleTime: 60_000,
    retry: 1,
  })

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
          Settings
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Application preferences and system configuration
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Restaurant Profile">
          <dl className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-100 py-3 dark:border-slate-800">
              <dt className="text-slate-500">Restaurant Name</dt>
              <dd className="font-medium">{restaurantName}</dd>
            </div>
            <div className="flex justify-between border-b border-slate-100 py-3 dark:border-slate-800">
              <dt className="text-slate-500">Timezone</dt>
              <dd className="font-medium">Asia/Kolkata (IST)</dd>
            </div>
            <div className="flex justify-between py-3">
              <dt className="text-slate-500">Currency</dt>
              <dd className="font-medium">INR (₹)</dd>
            </div>
          </dl>
        </Card>

        <Card title="Appearance">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-900 dark:text-white">Dark Mode</p>
              <p className="text-xs text-slate-500">Toggle between light and dark themes</p>
            </div>
            <button
              type="button"
              onClick={toggleTheme}
              aria-pressed={darkMode}
              className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-medium dark:border-slate-700 dark:bg-slate-800"
            >
              {darkMode ? (
                <>
                  <Sun className="h-4 w-4" aria-hidden="true" /> Light
                </>
              ) : (
                <>
                  <Moon className="h-4 w-4" aria-hidden="true" /> Dark
                </>
              )}
            </button>
          </div>
        </Card>

        <Card title="API Connection">
          {healthLoading ? (
            <CardSkeleton />
          ) : health ? (
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Status</dt>
                <dd className="font-medium text-emerald-600">{health.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Base URL</dt>
                <dd className="font-mono text-xs">
                  {import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001'}
                </dd>
              </div>
              <div className="flex items-center gap-2 text-emerald-600">
                <Server className="h-4 w-4" aria-hidden="true" />
                <span className="text-sm">Backend connected</span>
              </div>
            </dl>
          ) : (
            <EmptyState title="Backend unreachable" description="Check API server on port 8001" />
          )}
        </Card>

        <Card title="Training Dataset">
          {dsLoading ? (
            <CardSkeleton />
          ) : dataset?.exists ? (
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Total Rows</dt>
                <dd className="font-medium">{formatNumber(dataset.total_rows)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Columns</dt>
                <dd className="font-medium">{dataset.columns?.length}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Date Range</dt>
                <dd className="font-medium">
                  {formatDate(dataset.min_date)} — {formatDate(dataset.max_date)}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Size</dt>
                <dd className="font-medium">{dataset.dataset_size_mb?.toFixed(2)} MB</dd>
              </div>
            </dl>
          ) : (
            <EmptyState title="Dataset not found" description="Run dataset generator on backend" />
          )}
        </Card>
      </div>
    </div>
  )
}
