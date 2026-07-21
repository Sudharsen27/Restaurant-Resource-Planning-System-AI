import api from './api'

export async function fetchCatalogDashboard(params = {}) {
  const { data } = await api.get('/catalog/dashboard', { params })
  return data
}

export async function listUnits(params = {}) {
  const { data } = await api.get('/units', { params })
  return data
}

export async function createUnit(payload) {
  const { data } = await api.post('/units', payload)
  return data
}

export async function listUnitConversions() {
  const { data } = await api.get('/units/conversions')
  return data
}

export async function createUnitConversion(payload) {
  const { data } = await api.post('/units/conversions', payload)
  return data
}

export async function seedDefaultUnits(params = {}) {
  const { data } = await api.post('/units/seed-defaults', null, { params })
  return data
}

export async function listPurchaseOrders(params = {}) {
  const { data } = await api.get('/purchase-orders', { params })
  return data
}

export async function createPurchaseOrder(payload) {
  const { data } = await api.post('/purchase-orders', payload)
  return data
}

export async function submitPurchaseOrder(id) {
  const { data } = await api.post(`/purchase-orders/${id}/submit`)
  return data
}

export async function approvePurchaseOrder(id) {
  const { data } = await api.post(`/purchase-orders/${id}/approve`)
  return data
}

export async function cancelPurchaseOrder(id) {
  const { data } = await api.post(`/purchase-orders/${id}/cancel`)
  return data
}

export async function listGoodsReceipts(params = {}) {
  const { data } = await api.get('/goods-receipts', { params })
  return data
}

export async function createGoodsReceipt(payload) {
  const { data } = await api.post('/goods-receipts', payload)
  return data
}

export async function listRecipes(params = {}) {
  const { data } = await api.get('/recipes', { params })
  return data
}

export async function createRecipe(payload) {
  const { data } = await api.post('/recipes', payload)
  return data
}

export async function listMenuCategories(params = {}) {
  const { data } = await api.get('/menu/categories', { params })
  return data
}

export async function createMenuCategory(payload) {
  const { data } = await api.post('/menu/categories', payload)
  return data
}

export async function listMenuItems(params = {}) {
  const { data } = await api.get('/menu/items', { params })
  return data
}

export async function createMenuItem(payload) {
  const { data } = await api.post('/menu/items', payload)
  return data
}

export async function listStockAlerts(params = {}) {
  const { data } = await api.get('/stock-alerts', { params })
  return data
}

export async function listInventoryTransactions(params = {}) {
  const { data } = await api.get('/inventory-transactions', { params })
  return data
}

export async function adjustInventory(payload) {
  const { data } = await api.post('/inventory-transactions/adjust', payload)
  return data
}

export async function listStockTransfers(params = {}) {
  const { data } = await api.get('/stock-transfers', { params })
  return data
}

export async function createStockTransfer(payload) {
  const { data } = await api.post('/stock-transfers', payload)
  return data
}

export async function submitStockTransfer(id) {
  const { data } = await api.post(`/stock-transfers/${id}/submit`)
  return data
}

export async function approveStockTransfer(id) {
  const { data } = await api.post(`/stock-transfers/${id}/approve`)
  return data
}

export async function completeStockTransfer(id) {
  const { data } = await api.post(`/stock-transfers/${id}/complete`)
  return data
}

export async function fetchInventoryValuation(params = {}) {
  const { data } = await api.get('/catalog/reports/inventory-valuation', { params })
  return data
}
