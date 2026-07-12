/** All roles returned by POST /recommendation/staff */
export const STAFF_ROLE_KEYS = [
  'chef',
  'waiter',
  'kitchen_helper',
  'cashier',
  'cleaner',
  'host',
  'manager',
]

export const ROLE_LABELS = {
  chef: 'Chef',
  waiter: 'Waiter',
  kitchen_helper: 'Kitchen Helper',
  cashier: 'Cashier',
  cleaner: 'Cleaner',
  host: 'Host',
  manager: 'Manager',
}

/** Infer shift label from plan created_at (API timestamp). */
export function shiftLabelFromTimestamp(iso) {
  if (!iso) return '—'
  const hour = new Date(iso).getHours()
  if (hour < 12) return 'Morning'
  if (hour < 17) return 'Afternoon'
  if (hour < 21) return 'Evening'
  return 'Night'
}

/** Role shift cost allocated from API staff_cost by headcount share. */
export function allocateRoleDailyCost(staffCost, count, totalStaff) {
  if (!totalStaff || !staffCost || !count) return 0
  return Math.round((staffCost * count) / totalStaff * 100) / 100
}

export function buildStaffRows(apiResponse) {
  if (!apiResponse?.staff) return []

  const { staff, staff_cost: staffCost = 0, total_staff: totalStaff = 0 } = apiResponse
  const shiftLabel = shiftLabelFromTimestamp(apiResponse.created_at)

  return STAFF_ROLE_KEYS.map((role) => {
    const count = Number(staff[role] ?? 0)
    const dailyCost = allocateRoleDailyCost(staffCost, count, totalStaff)
    const hourlyCost =
      count > 0 && totalStaff > 0 && staffCost > 0
        ? Math.round((staffCost / totalStaff / 8) * 100) / 100
        : 0

    return {
      role,
      roleLabel: ROLE_LABELS[role] || role,
      count,
      shift: count > 0 ? shiftLabel : '—',
      hourlyCost,
      dailyCost,
      status: count > 0 ? 'Staffed' : 'Not required',
      share: totalStaff > 0 ? (count / totalStaff) * 100 : 0,
    }
  })
}

export function buildDistributionChartData(rows) {
  return rows
    .filter((r) => r.count > 0)
    .map((r) => ({
      name: r.roleLabel,
      value: r.count,
    }))
}

export function buildCountBarChartData(rows) {
  return rows.map((r) => ({
    name: r.roleLabel,
    count: r.count,
  }))
}

/** % of role types with at least one staff member (from API staff counts). */
export function computeShiftCoverage(apiResponse) {
  if (!apiResponse?.staff) return null
  const staffedRoles = STAFF_ROLE_KEYS.filter((k) => (apiResponse.staff[k] ?? 0) > 0).length
  return Math.round((staffedRoles / STAFF_ROLE_KEYS.length) * 100)
}

export function normalizeStaffPlan(apiData) {
  if (!apiData) return null
  return {
    id: apiData.id ?? null,
    prediction_id: apiData.prediction_id ?? null,
    predicted_customers: apiData.predicted_customers,
    staff: apiData.staff,
    staff_cost: apiData.staff_cost,
    total_staff: apiData.total_staff,
    created_at: apiData.created_at ?? null,
  }
}

export function buildRecentPlansRows(plans) {
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
      totalStaff: plan.total_staff,
      staffCost: plan.staff_cost,
      createdTime: plan.created_at
        ? new Date(plan.created_at).toLocaleString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
          })
        : '—',
      created_at: plan.created_at,
    }))
}

export function staffPlanToCsv(plan, rows) {
  const header = [
    'Role',
    'Recommended Count',
    'Shift',
    'Hourly Cost',
    'Daily Cost',
    'Status',
  ]
  const lines = rows.map((r) =>
    [r.roleLabel, r.count, r.shift, r.hourlyCost, r.dailyCost, r.status].join(','),
  )
  const meta = [
    `Predicted Customers,${plan.predicted_customers}`,
    `Total Staff,${plan.total_staff}`,
    `Staff Cost,${plan.staff_cost}`,
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
