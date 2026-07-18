/** Application constants — no secrets. */

export const APP_NAME = 'Spice Garden Restaurant'
export const APP_TIMEZONE = 'Asia/Kolkata'
export const APP_CURRENCY = 'INR'

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api/v1'

export const API_TIMEOUT_MS = Number(import.meta.env.VITE_API_TIMEOUT_MS || 120000)

export const QUERY_STALE_TIME_MS = 30_000
export const THEME_STORAGE_KEY = 'rrps-theme'
