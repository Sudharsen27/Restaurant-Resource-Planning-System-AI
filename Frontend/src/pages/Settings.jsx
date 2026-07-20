import { useState } from 'react'
import { Moon, Monitor, Server, Sun } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import { CardSkeleton } from '../components/ui/Skeleton'
import EmptyState from '../components/ui/EmptyState'
import { Select, Input } from '../components/forms/FormControls'
import { API_BASE_URL, APP_NAME } from '../constants/config'
import { useTheme } from '../context/ThemeContext'
import { healthCheck } from '../services/forecastService'
import { getDatasetInfo } from '../services/datasetService'
import { formatDate, formatNumber } from '../utils/format'

export default function Settings() {
  const { darkMode, preference, setTheme } = useTheme()
  const restaurantName = APP_NAME
  const [language, setLanguage] = useState('en-IN')
  const [timezone, setTimezone] = useState('Asia/Kolkata')
  const [currency, setCurrency] = useState('INR')
  const [taxRate, setTaxRate] = useState('5')

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
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">Settings</h2>
        <p className="mt-1 text-sm text-slate-500">Restaurant, appearance, locale, and tax configuration</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Restaurant settings">
          <dl className="space-y-4 text-sm">
            <div className="flex justify-between border-b border-slate-100 py-3 dark:border-zinc-800">
              <dt className="text-slate-500">Restaurant name</dt>
              <dd className="font-medium">{restaurantName}</dd>
            </div>
            <div className="py-2">
              <Select
                label="Language"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                options={[
                  { value: 'en-IN', label: 'English (India)' },
                  { value: 'hi-IN', label: 'Hindi' },
                ]}
              />
            </div>
            <div className="py-2">
              <Select
                label="Time zone"
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                options={[
                  { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST)' },
                  { value: 'UTC', label: 'UTC' },
                ]}
              />
            </div>
            <div className="py-2">
              <Select
                label="Currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                options={[
                  { value: 'INR', label: 'INR (₹)' },
                  { value: 'USD', label: 'USD ($)' },
                ]}
              />
            </div>
          </dl>
        </Card>

        <Card title="Appearance / theme">
          <p className="mb-3 text-xs text-slate-500">
            Current: {preference} {darkMode ? '(rendering dark)' : '(rendering light)'}
          </p>
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'light', label: 'Light', icon: Sun },
              { id: 'dark', label: 'Dark', icon: Moon },
              { id: 'system', label: 'System', icon: Monitor },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                type="button"
                onClick={() => setTheme(id)}
                className={`flex flex-col items-center gap-2 rounded-xl border px-3 py-4 text-sm font-medium transition ${
                  preference === id
                    ? 'border-slate-900 bg-slate-900 text-white dark:border-zinc-100 dark:bg-zinc-100 dark:text-zinc-900'
                    : 'border-slate-200 hover:bg-slate-50 dark:border-zinc-700 dark:hover:bg-zinc-900'
                }`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </Card>

        <Card title="Tax configuration">
          <Input
            label="Default tax rate (%)"
            type="number"
            min="0"
            step="0.1"
            value={taxRate}
            onChange={(e) => setTaxRate(e.target.value)}
            hint="UI preference — persist via settings API when available"
          />
        </Card>

        <Card title="API connection">
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
                <dd className="font-mono text-xs">{API_BASE_URL}</dd>
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

        <Card title="Training dataset" className="lg:col-span-2">
          {dsLoading ? (
            <CardSkeleton />
          ) : dataset?.exists ? (
            <dl className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-slate-500">Total rows</dt>
                <dd className="font-medium">{formatNumber(dataset.total_rows)}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Columns</dt>
                <dd className="font-medium">{dataset.columns?.length}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Date range</dt>
                <dd className="font-medium">
                  {formatDate(dataset.min_date)} — {formatDate(dataset.max_date)}
                </dd>
              </div>
              <div>
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
