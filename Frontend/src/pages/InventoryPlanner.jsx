import { useMemo, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import Card from '../components/ui/Card'
import EmptyState from '../components/ui/EmptyState'
import InventoryPlannerHeader from '../components/inventory/InventoryPlannerHeader'
import InventorySummaryCards from '../components/inventory/InventorySummaryCards'
import InventoryPlannerActions from '../components/inventory/InventoryPlannerActions'
import InventoryIngredientTable from '../components/inventory/InventoryIngredientTable'
import InventoryChartsSection from '../components/inventory/InventoryChartsSection'
import RecentInventoryPlansTable from '../components/inventory/RecentInventoryPlansTable'
import InventoryErrorCard from '../components/inventory/InventoryErrorCard'
import { useToast } from '../context/ToastContext'
import { getInventoryRecommendation } from '../services/recommendationService'
import { getLatestInventory } from '../services/persistenceService'
import { useDashboardRefresh } from '../hooks/useDashboard'
import {
  buildInventoryPayload,
  buildInventoryRows,
  buildRecentInventoryRows,
  countPurchaseItems,
  downloadCsv,
  inventoryPlanToCsv,
  normalizeInventoryPlan,
  validateInventoryForm,
} from '../utils/inventoryPlanner'

const INVENTORY_LATEST_KEY = ['inventory-latest']

export default function InventoryPlanner() {
  const toast = useToast()
  const refreshDashboard = useDashboardRefresh()
  const queryClient = useQueryClient()

  const [customersInput, setCustomersInput] = useState('')
  const [safetyRate, setSafetyRate] = useState(0.15)
  const [leadTime, setLeadTime] = useState(1)
  const [fieldErrors, setFieldErrors] = useState({})
  const [userPlan, setUserPlan] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [generateError, setGenerateError] = useState(null)

  const latestQuery = useQuery({
    queryKey: INVENTORY_LATEST_KEY,
    queryFn: async () => normalizeInventoryPlan((await getLatestInventory()).data),
    staleTime: 30_000,
    retry: 1,
  })

  const plan =
    userPlan ??
    (!generating && latestQuery.data
      ? normalizeInventoryPlan(latestQuery.data, {
          safety_stock_rate: safetyRate,
          supplier_lead_time_days: leadTime,
        })
      : null)
  const customers =
    customersInput ||
    (latestQuery.data?.predicted_customers != null
      ? String(latestQuery.data.predicted_customers)
      : '')

  const rows = useMemo(() => (plan ? buildInventoryRows(plan) : []), [plan])
  const purchaseItems = useMemo(() => countPurchaseItems(rows), [rows])
  const recentRows = useMemo(
    () => buildRecentInventoryRows(latestQuery.data ? [latestQuery.data] : []),
    [latestQuery.data],
  )

  const loading = generating || (latestQuery.isLoading && !plan)
  const hasPlan = Boolean(plan?.ingredients?.length)

  const handleGenerate = async () => {
    const { valid, errors } = validateInventoryForm({ customers, safetyRate, leadTime })
    setFieldErrors(errors)
    if (!valid) {
      toast.error('Please fix the highlighted fields')
      return
    }

    setGenerating(true)
    setGenerateError(null)
    try {
      const payload = buildInventoryPayload({
        predictedCustomers: customers,
        safetyRate,
        leadTime,
        currentInventory: {},
        predictionId: latestQuery.data?.prediction_id ?? null,
      })
      const res = await getInventoryRecommendation(payload)
      const normalized = normalizeInventoryPlan(res.data, {
        safety_stock_rate: payload.safety_stock_rate,
        supplier_lead_time_days: payload.supplier_lead_time_days,
        current_inventory: payload.current_inventory,
      })
      setUserPlan(normalized)
      queryClient.invalidateQueries({ queryKey: INVENTORY_LATEST_KEY })
      refreshDashboard()
      toast.success('Inventory plan generated successfully')

      const latest = await getLatestInventory().catch(() => null)
      if (latest?.data) {
        setUserPlan(
          normalizeInventoryPlan(latest.data, {
            safety_stock_rate: payload.safety_stock_rate,
            supplier_lead_time_days: payload.supplier_lead_time_days,
            current_inventory: payload.current_inventory,
          }),
        )
      }
    } catch (err) {
      const message = err?.message || 'Failed to generate inventory plan'
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
        setUserPlan(
          normalizeInventoryPlan(result.data, {
            safety_stock_rate: safetyRate,
            supplier_lead_time_days: leadTime,
            current_inventory: {},
          }),
        )
        setCustomersInput(String(result.data.predicted_customers))
        toast.success('Loaded latest inventory plan')
      } else {
        toast.error('No saved inventory plan found')
      }
    } catch (err) {
      toast.error(err?.message || 'Failed to refresh')
    }
  }

  const handleExport = () => {
    if (!plan) return
    const csv = inventoryPlanToCsv(plan, rows)
    const stamp = plan.created_at
      ? new Date(plan.created_at).toISOString().slice(0, 10)
      : 'export'
    downloadCsv(`inventory-plan-${stamp}.csv`, csv)
    toast.success('CSV exported')
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="inventory-planner-page space-y-8 print:space-y-4">
      <InventoryPlannerHeader />

      <InventoryPlannerActions
        customers={customers}
        safetyRate={safetyRate}
        leadTime={leadTime}
        onCustomersChange={setCustomersInput}
        onSafetyChange={setSafetyRate}
        onLeadTimeChange={setLeadTime}
        onGenerate={handleGenerate}
        onRefresh={handleRefresh}
        onExport={handleExport}
        onPrint={handlePrint}
        loading={generating || latestQuery.isFetching}
        disabled={!hasPlan}
        errors={fieldErrors}
      />

      {latestQuery.isError && !plan && (
        <InventoryErrorCard
          title="Could not load latest inventory plan"
          message={latestQuery.error?.message || 'No saved inventory plan in PostgreSQL yet.'}
          onRetry={handleRefresh}
        />
      )}

      {generateError && (
        <InventoryErrorCard
          title="Inventory plan generation failed"
          message={generateError}
          onRetry={handleGenerate}
        />
      )}

      {loading && !hasPlan && (
        <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 py-16 dark:border-slate-700">
          <Loader2 className="h-8 w-8 animate-spin text-amber-600" />
          <p className="text-sm text-slate-500">Loading inventory plan from API…</p>
        </div>
      )}

      {!loading && !hasPlan && !latestQuery.isError && !generateError && (
        <EmptyState
          title="No Inventory Plan Available"
          description="Enter forecasted customers and generate a procurement plan."
          action={
            <button
              type="button"
              onClick={handleGenerate}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Generate Inventory Plan
            </button>
          }
        />
      )}

      {hasPlan && (
        <div className="space-y-8 print:space-y-4">
          <InventorySummaryCards
            plan={plan}
            purchaseItems={purchaseItems}
            loading={generating}
          />

          <Card
            title="Ingredient Procurement"
            subtitle="Ingredient list from POST /recommendation/inventory"
          >
            <InventoryIngredientTable rows={rows} totalCost={plan.inventory_cost} />
          </Card>

          <InventoryChartsSection rows={rows} loading={generating} />

          <Card
            title="Recent Inventory Plans"
            subtitle="Latest saved plan from GET /inventory/latest"
          >
            <RecentInventoryPlansTable rows={recentRows} />
          </Card>
        </div>
      )}
    </div>
  )
}
