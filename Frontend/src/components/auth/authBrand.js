/** Auth experience brand — UI only, not API config. */
export const AUTH_BRAND = {
  name: 'RestoPlan',
  product: 'Restaurant ERP',
  tagline: 'Inventory, POS, and forecasting for multi-location restaurants — in one workspace.',
}

export function passwordStrength(password) {
  const p = password || ''
  let score = 0
  if (p.length >= 8) score += 1
  if (p.length >= 12) score += 1
  if (/[a-z]/.test(p) && /[A-Z]/.test(p)) score += 1
  if (/\d/.test(p)) score += 1
  if (/[^A-Za-z0-9]/.test(p)) score += 1
  const labels = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong']
  const colors = [
    'bg-rose-500',
    'bg-orange-500',
    'bg-amber-500',
    'bg-sky-500',
    'bg-emerald-500',
  ]
  const idx = Math.min(score, 4)
  return { score, label: p ? labels[idx] : '', color: colors[idx], percent: (score / 5) * 100 }
}
