import { useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import StaffPlannerHeader from '../components/staff/StaffPlannerHeader'
import StaffSummaryCards from '../components/staff/StaffSummaryCards'
import StaffPlannerActions from '../components/staff/StaffPlannerActions'
import StaffRecommendationTable from '../components/staff/StaffRecommendationTable'
import StaffChartsSection from '../components/staff/StaffChartsSection'
import RecentStaffPlansTable from '../components/staff/RecentStaffPlansTable'
import StaffErrorCard from '../components/staff/StaffErrorCard'
import { useToast } from '../context/ToastContext'
import { getStaffRecommendation } from '../services/recommendationService'
import { getLatestStaff } from '../services/persistenceService'
import { useDashboardRefresh } from '../hooks/useDashboard'
import {
  buildRecentPlansRows,
  buildStaffRows,
  computeShiftCoverage,
  downloadCsv,
  normalizeStaffPlan,
  staffPlanToCsv,
} from '../utils/staffPlanner'

const STAFF_LATEST_KEY = ['staff-latest']

export default function StaffPlanner() {
  const toast = useToast()
  const refreshDashboard = useDashboardRefresh()
  const queryClient = useQueryClient()
  const [customersInput, setCustomersInput] = useState('')
  const [userPlan, setUserPlan] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState(null)

  const latestQuery = useQuery({
    queryKey: STAFF_LATEST_KEY,
    queryFn: async () => normalizeStaffPlan((await getLatestStaff()).data),
    staleTime: 30_000,
    retry: 1,
  })

  const plan = userPlan ?? (!generating ? latestQuery.data ?? null : null)
  const customers =
    customersInput ||
    (latestQuery.data?.predicted_customers != null
      ? String(latestQuery.data.predicted_customers)
      : '')

  const rows = useMemo(() => (plan ? buildStaffRows(plan) : []), [plan])
  const shiftCoverage = useMemo(() => (plan ? computeShiftCoverage(plan) : null), [plan])
  const recentRows = useMemo(
    () => buildRecentPlansRows(latestQuery.data ? [latestQuery.data] : []),
    [latestQuery.data],
  )

  const loading = generating || (latestQuery.isLoading && !plan)
  const hasPlan = Boolean(plan?.staff)

  const handleGenerate = async () => {
    const n = Number(customers)
    if (!Number.isFinite(n) || n < 1) {
      toast.error('Enter forecasted customers (minimum 1)')
      return
    }

    setGenerating(true)
    setGenerateError(null)
    try {
      const payload = {
        predicted_customers: n,
        ...(latestQuery.data?.prediction_id ? { prediction_id: latestQuery.data.prediction_id } : {}),
      }
      const res = await getStaffRecommendation(payload)
      const normalized = normalizeStaffPlan({
        ...res.data,
        created_at: new Date().toISOString(),
      })
      setUserPlan(normalized)
      queryClient.invalidateQueries({ queryKey: STAFF_LATEST_KEY })
      refreshDashboard()
      toast.success('Staff plan generated successfully')

      const latest = await getLatestStaff().catch(() => null)
      if (latest?.data) {
        setUserPlan(normalizeStaffPlan(latest.data))
      }
    } catch (err) {
      const message = err?.message || 'Failed to generate staff plan'
      setGenerateError(message)
      toast.error(message)
    } finally {
      setGenerating(false)
    }
  }

  const handleRefresh = async () => {
    setGenerateError(null)
    try {
      const result = await latestQuery.refetch()
      if (result.data) {
        setUserPlan(result.data)
        setCustomersInput(String(result.data.predicted_customers))
        toast.success('Loaded latest staff plan')
      } else {
        toast.error('No saved staff plan found')
      }
    } catch (err) {
      toast.error(err?.message || 'Failed to refresh')
    }
  }

  const handleExport = () => {
    if (!plan) return
    const csv = staffPlanToCsv(plan, rows)
    const stamp = plan.created_at
      ? new Date(plan.created_at).toISOString().slice(0, 10)
      : 'export'
    downloadCsv(`staff-plan-${stamp}.csv`, csv)
    toast.success('CSV exported')
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="staff-planner-page space-y-8 print:space-y-4">
      <StaffPlannerHeader />

      <StaffPlannerActions
        customers={customers}
        onCustomersChange={setCustomersInput}
        onGenerate={handleGenerate}
        onRefresh={handleRefresh}
        onExport={handleExport}
        onPrint={handlePrint}
        loading={generating || latestQuery.isFetching}
        disabled={!hasPlan}
      />

      {latestQuery.isError && !plan && (
        <StaffErrorCard
          title="Could not load latest staff plan"
          message={latestQuery.error?.message || 'No saved staff plan in PostgreSQL yet.'}
          onRetry={handleRefresh}
        />
      )}

      {generateError && (
        <StaffErrorCard
          title="Staff plan generation failed"
          message={generateError}
          onRetry={handleGenerate}
        />
      )}

      {loading && !hasPlan && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 py-16 dark:border-slate-700">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          <p className="text-sm text-slate-500">Loading staff plan from API…</p>
        </div>
      )}

      {!loading && !hasPlan && !latestQuery.isError && !generateError && (
        <EmptyState
          title="No Staff Plan Available"
          description="Enter forecasted customers and generate a workforce plan."
          action={
            <button
              type="button"
              onClick={handleGenerate}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Generate Staff Plan
            </button>
          }
        />
      )}

      {hasPlan && (
        <div className="space-y-8 print:space-y-4">
          <StaffSummaryCards plan={plan} shiftCoverage={shiftCoverage} loading={generating} />

          <Card
            title="Staff Recommendation"
            subtitle="Role breakdown from POST /recommendation/staff"
          >
            <StaffRecommendationTable
              rows={rows}
              totalStaff={plan.total_staff}
              totalCost={plan.staff_cost}
            />
          </Card>

          <StaffChartsSection rows={rows} loading={generating} />

          <Card
            title="Recent Staff Plans"
            subtitle="Latest saved plan from GET /staff/latest"
          >
            <RecentStaffPlansTable rows={recentRows} />
          </Card>
        </div>
      )}
    </div>
  )
}
