import api from '../api/client'
import { API_BASE_URL } from '../constants/config'
import { getAccessToken } from '../store'

export async function listOrders(params = {}) {
  const { data } = await api.get('/orders', { params })
  return data
}

export async function getOrder(id) {
  const { data } = await api.get(`/orders/${id}`)
  return data
}

export async function createOrder(payload) {
  const { data } = await api.post('/orders', payload)
  return data
}

export async function updateOrder(id, payload) {
  const { data } = await api.put(`/orders/${id}`, payload)
  return data
}

export async function payOrder(id, payload) {
  const { data } = await api.post(`/orders/${id}/pay`, payload)
  return data
}

export async function refundOrder(id, paymentId = null) {
  const { data } = await api.post(`/orders/${id}/refund`, null, {
    params: paymentId ? { payment_id: paymentId } : {},
  })
  return data
}

export async function getInvoice(id) {
  const { data } = await api.get(`/orders/${id}/invoice`)
  return data
}

export async function updateKitchenItem(orderId, itemId, kitchen_status) {
  const { data } = await api.patch(`/orders/${orderId}/items/${itemId}/kitchen`, {
    kitchen_status,
  })
  return data
}

export async function deleteOrder(id) {
  const { data } = await api.delete(`/orders/${id}`)
  return data
}

export async function fetchPosDashboard(params = {}) {
  const { data } = await api.get('/pos/dashboard', { params })
  return data
}

export async function fetchKitchenQueue(params = {}) {
  const { data } = await api.get('/pos/kitchen', { params })
  return data
}

export async function fetchFloorPlan(branchId) {
  const { data } = await api.get('/pos/floor', { params: { branch_id: branchId } })
  return data
}

export async function updateTablePosition(tableId, pos_x, pos_y) {
  const { data } = await api.patch(`/pos/tables/${tableId}/position`, null, {
    params: { pos_x, pos_y },
  })
  return data
}

export async function mergeTables(primary_table_id, secondary_table_ids) {
  const { data } = await api.post('/pos/tables/merge', {
    primary_table_id,
    secondary_table_ids,
  })
  return data
}

export async function splitTables(primary_table_id) {
  const { data } = await api.post('/pos/tables/split', { primary_table_id })
  return data
}

/** Live ops WebSocket (falls back to polling if connection fails). */
export function connectPosSocket(onEvent) {
  const base = API_BASE_URL.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '')
  const url = `${base}/api/v1/pos/ws`
  let ws
  try {
    ws = new WebSocket(url)
  } catch {
    return () => {}
  }
  ws.onmessage = (ev) => {
    try {
      const msg = JSON.parse(ev.data)
      onEvent?.(msg)
    } catch {
      /* ignore */
    }
  }
  const ping = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) ws.send('ping')
  }, 25000)
  return () => {
    clearInterval(ping)
    ws.close()
  }
}

export function posWsAuthHint() {
  return Boolean(getAccessToken())
}
