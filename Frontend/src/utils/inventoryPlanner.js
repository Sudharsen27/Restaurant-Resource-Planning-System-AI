export function buildInventoryPayload({
  predictedCustomers,
  safetyRate,
  leadTime,
  wastageRate,
  currentInventory = {},
  predictionId = null,
}) {
  const payload = {
    predicted_customers: Number(predictedCustomers),
    safety_stock_rate: Number(safetyRate),
    supplier_lead_time_days: Number(leadTime),
    current_inventory: currentInventory,
  }
  if (wastageRate != null && wastageRate !== '') {
    payload.wastage_rate = Number(wastageRate)
  }
  if (predictionId) {
    payload.prediction_id = predictionId
  }
  return payload
}

export function normalizeInventoryPlan(apiData, meta = {}) {
  if (!apiData) return null
  return {
    id: apiData.id ?? null,
    prediction_id: apiData.prediction_id ?? null,
    predicted_customers: apiData.predicted_customers,
    ingredients: apiData.ingredients ?? [],
    inventory_cost: apiData.inventory_cost,
    ingredient_count: apiData.ingredient_count,
    created_at: apiData.created_at ?? null,
    safety_stock_rate: meta.safety_stock_rate ?? apiData.safety_stock_rate ?? null,
    supplier_lead_time_days: meta.supplier_lead_time_days ?? apiData.supplier_lead_time_days ?? null,
    current_inventory: meta.current_inventory ?? apiData.current_inventory ?? {},
  }
}

export function buildInventoryRows(plan) {
  if (!plan?.ingredients?.length) return []

  const currentInventory = plan.current_inventory || {}
  const leadTime = plan.supplier_lead_time_days

  return plan.ingredients.map((ing) => {
    const currentStock = Number(currentInventory[ing.name] ?? 0)
    const purchaseQty = Number(ing.purchase ?? 0)
    const required = Number(ing.required ?? 0)

    let status = 'In stock'
    if (purchaseQty > 0) status = 'Purchase needed'
    if (required > 0 && purchaseQty === 0 && currentStock < required) status = 'Review'

    return {
      name: ing.name,
      unit: ing.unit,
      required,
      currentStock,
      purchaseQty,
      estimatedCost: Number(ing.estimated_cost ?? 0),
      leadTime: leadTime != null ? leadTime : null,
      shelfLife: ing.shelf_life_days != null ? `${ing.shelf_life_days} days` : null,
      status,
    }
  })
}

export function countPurchaseItems(rows) {
  return rows.filter((r) => r.purchaseQty > 0).length
}

export function buildCostBreakdownChartData(rows, limit = 12) {
  return [...rows]
    .sort((a, b) => b.estimatedCost - a.estimatedCost)
    .slice(0, limit)
    .map((r) => ({
      name: r.name.length > 14 ? `${r.name.slice(0, 14)}…` : r.name,
      cost: r.estimatedCost,
    }))
}

export function buildQuantityBarChartData(rows, limit = 12) {
  return [...rows]
    .sort((a, b) => b.purchaseQty - a.purchaseQty)
    .slice(0, limit)
    .map((r) => ({
      name: r.name.length > 14 ? `${r.name.slice(0, 14)}…` : r.name,
      purchase: r.purchaseQty,
      required: r.required,
    }))
}

export function buildRecentInventoryRows(plans) {
  return (plans || [])
    .filter(Boolean)
    .map((plan) => ({
      id: plan.id,
      date: plan.created_at
        ? new Date(plan.created_at).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })
        : '—',
      forecast: plan.predicted_customers,
      ingredients: plan.ingredient_count,
      inventoryCost: plan.inventory_cost,
      createdTime: plan.created_at
        ? new Date(plan.created_at).toLocaleString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
          })
        : '—',
      created_at: plan.created_at,
    }))
}

export function inventoryPlanToCsv(plan, rows) {
  const header = [
    'Ingredient Name',
    'Required Quantity',
    'Current Stock',
    'Purchase Quantity',
    'Unit',
    'Estimated Cost',
    'Supplier Lead Time',
    'Shelf Life',
    'Status',
  ]
  const lines = rows.map((r) =>
    [
      r.name,
      r.required,
      r.currentStock,
      r.purchaseQty,
      r.unit,
      r.estimatedCost,
      r.leadTime ?? '',
      r.shelfLife ?? '',
      r.status,
    ].join(','),
  )
  const meta = [
    `Predicted Customers,${plan.predicted_customers}`,
    `Ingredient Count,${plan.ingredient_count}`,
    `Inventory Cost,${plan.inventory_cost}`,
    `Safety Stock Rate,${plan.safety_stock_rate ?? ''}`,
    `Supplier Lead Time,${plan.supplier_lead_time_days ?? ''}`,
    `Created,${plan.created_at || ''}`,
    '',
  ]
  return [...meta, header.join(','), ...lines].join('\n')
}

export function downloadCsv(filename, content) {
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

export function validateInventoryForm({ customers, safetyRate, leadTime }) {
  const errors = {}
  const n = Number(customers)
  if (!Number.isFinite(n) || n < 1) {
    errors.customers = 'Forecasted customers must be at least 1'
  }
  const safety = Number(safetyRate)
  if (!Number.isFinite(safety) || safety < 0 || safety > 1) {
    errors.safetyRate = 'Safety stock rate must be between 0 and 100%'
  }
  const lead = Number(leadTime)
  if (!Number.isFinite(lead) || lead < 0) {
    errors.leadTime = 'Lead time must be 0 or greater'
  }
  return { valid: Object.keys(errors).length === 0, errors }
}
