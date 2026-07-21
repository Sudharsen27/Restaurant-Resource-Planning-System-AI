import api from '../api/client'

// ── CRM ──────────────────────────────────────────────────────────────────────

export async function fetchCrmDashboard(params = {}) {
  const { data } = await api.get('/crm/dashboard', { params })
  return data
}

export async function fetchCustomerProfile(customerId) {
  const { data } = await api.get(`/hrms/customers/${customerId}/profile`)
  return data
}

// ── Loyalty ──────────────────────────────────────────────────────────────────

export async function getLoyaltyRules(restaurantId) {
  const { data } = await api.get(`/loyalty/rules/${restaurantId}`)
  return data
}

export async function updateLoyaltyRules(restaurantId, payload) {
  const { data } = await api.put(`/loyalty/rules/${restaurantId}`, payload)
  return data
}

export async function listLoyaltyTransactions(params = {}) {
  const { data } = await api.get('/loyalty/transactions', { params })
  return data
}

export async function redeemLoyaltyPoints(payload) {
  const { data } = await api.post('/loyalty/redeem', payload)
  return data
}

export async function awardBirthdayBonus(payload) {
  const { data } = await api.post('/loyalty/birthday-bonus', payload)
  return data
}

export async function awardReferralBonus(payload) {
  const { data } = await api.post('/loyalty/referral-bonus', payload)
  return data
}

export async function listCoupons(params = {}) {
  const { data } = await api.get('/loyalty/coupons', { params })
  return data
}

export async function createCoupon(payload) {
  const { data } = await api.post('/loyalty/coupons', payload)
  return data
}

export async function fetchLoyaltyDashboard(params = {}) {
  const { data } = await api.get('/loyalty/dashboard', { params })
  return data
}

export async function fetchCustomerLoyaltyDashboard(customerId) {
  const { data } = await api.get(`/loyalty/customers/${customerId}/dashboard`)
  return data
}

// ── Reservations ─────────────────────────────────────────────────────────────

export async function listReservations(params = {}) {
  const { data } = await api.get('/reservations', { params })
  return data
}

export async function listWaitlist(params = {}) {
  const { data } = await api.get('/reservations/waitlist', { params })
  return data
}

export async function getReservation(id) {
  const { data } = await api.get(`/reservations/${id}`)
  return data
}

export async function createReservation(payload) {
  const { data } = await api.post('/reservations', payload)
  return data
}

export async function updateReservation(id, payload) {
  const { data } = await api.put(`/reservations/${id}`, payload)
  return data
}

export async function updateReservationStatus(id, payload) {
  const { data } = await api.patch(`/reservations/${id}/status`, payload)
  return data
}

export async function promoteWaitlistReservation(id) {
  const { data } = await api.post(`/reservations/${id}/promote`)
  return data
}

export async function deleteReservation(id) {
  const { data } = await api.delete(`/reservations/${id}`)
  return data
}

// ── Shifts ───────────────────────────────────────────────────────────────────

export async function listShiftTemplates(params = {}) {
  const { data } = await api.get('/shifts/templates', { params })
  return data
}

export async function createShiftTemplate(payload) {
  const { data } = await api.post('/shifts/templates', payload)
  return data
}

export async function updateShiftTemplate(id, payload) {
  const { data } = await api.put(`/shifts/templates/${id}`, payload)
  return data
}

export async function deleteShiftTemplate(id) {
  const { data } = await api.delete(`/shifts/templates/${id}`)
  return data
}

export async function listShiftAssignments(params = {}) {
  const { data } = await api.get('/shifts/assignments', { params })
  return data
}

export async function assignShift(payload) {
  const { data } = await api.post('/shifts/assignments', payload)
  return data
}

export async function assignWeeklyShifts(payload) {
  const { data } = await api.post('/shifts/assignments/weekly', payload)
  return data
}

// ── Attendance ───────────────────────────────────────────────────────────────

export async function clockIn(payload) {
  const { data } = await api.post('/attendance/clock-in', payload)
  return data
}

export async function clockOut(payload) {
  const { data } = await api.post('/attendance/clock-out', payload)
  return data
}

export async function attendanceBreak(payload) {
  const { data } = await api.post('/attendance/break', payload)
  return data
}

export async function listAttendance(params = {}) {
  const { data } = await api.get('/attendance', { params })
  return data
}

// ── Leave ────────────────────────────────────────────────────────────────────

export async function listLeaveBalances(employeeId, params = {}) {
  const { data } = await api.get(`/leaves/balances/${employeeId}`, { params })
  return data
}

export async function createLeaveRequest(payload) {
  const { data } = await api.post('/leaves/requests', payload)
  return data
}

export async function listLeaveRequests(params = {}) {
  const { data } = await api.get('/leaves/requests', { params })
  return data
}

export async function reviewLeaveRequest(requestId, payload) {
  const { data } = await api.patch(`/leaves/requests/${requestId}/review`, payload)
  return data
}

// ── Payroll ──────────────────────────────────────────────────────────────────

export async function generatePayroll(payload) {
  const { data } = await api.post('/payroll/generate', payload)
  return data
}

export async function listPayrollRuns(params = {}) {
  const { data } = await api.get('/payroll/runs', { params })
  return data
}

export async function lockPayrollRun(runId) {
  const { data } = await api.post(`/payroll/runs/${runId}/lock`)
  return data
}

export async function listPayslips(runId) {
  const { data } = await api.get(`/payroll/runs/${runId}/payslips`)
  return data
}

export async function fetchPayslipPrint(payslipId) {
  const { data } = await api.get(`/payroll/payslips/${payslipId}/print`)
  return data
}

// ── HRMS ─────────────────────────────────────────────────────────────────────

export async function fetchHrmsDashboard(params = {}) {
  const { data } = await api.get('/hrms/dashboard', { params })
  return data
}
