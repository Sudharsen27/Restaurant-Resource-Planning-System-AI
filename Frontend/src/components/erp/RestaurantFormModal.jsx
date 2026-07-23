import { useState } from 'react'
import AppModal from '../modals/AppModal'
import { Input, Textarea, Switch } from '../forms/FormControls'

const EMPTY = {
  name: '',
  code: '',
  city: '',
  state: '',
  country: 'India',
  legal_name: '',
  tax_id: '',
  gst_number: '',
  pan_number: '',
  phone: '',
  email: '',
  website: '',
  logo_url: '',
  address: '',
  timezone: 'Asia/Kolkata',
  currency: 'INR',
  is_active: true,
}

function toForm(row) {
  if (!row) return { ...EMPTY }
  return {
    name: row.name || '',
    code: row.code || '',
    city: row.city || '',
    state: row.state || '',
    country: row.country || 'India',
    legal_name: row.legal_name || '',
    tax_id: row.tax_id || '',
    gst_number: row.gst_number || '',
    pan_number: row.pan_number || '',
    phone: row.phone || '',
    email: row.email || '',
    website: row.website || '',
    logo_url: row.logo_url || '',
    address: row.address || '',
    timezone: row.timezone || 'Asia/Kolkata',
    currency: row.currency || 'INR',
    is_active: row.is_active !== false,
  }
}

/** Build API payload; empty optional strings become null. */
export function restaurantPayloadFromForm(form) {
  const trim = (v) => (typeof v === 'string' ? v.trim() : v)
  const optional = (v) => {
    const t = trim(v)
    return t ? t : null
  }
  return {
    name: trim(form.name),
    code: trim(form.code),
    city: optional(form.city),
    state: optional(form.state),
    country: optional(form.country) || 'India',
    legal_name: optional(form.legal_name),
    tax_id: optional(form.tax_id),
    gst_number: optional(form.gst_number),
    pan_number: optional(form.pan_number),
    phone: optional(form.phone),
    email: optional(form.email),
    website: optional(form.website),
    logo_url: optional(form.logo_url),
    address: optional(form.address),
    timezone: trim(form.timezone) || 'Asia/Kolkata',
    currency: trim(form.currency) || 'INR',
    is_active: Boolean(form.is_active),
  }
}

export default function RestaurantFormModal({
  open,
  mode = 'create',
  initial,
  busy = false,
  onClose,
  onSubmit,
}) {
  const [form, setForm] = useState(() => toForm(initial))
  const [error, setError] = useState('')
  const [resetKey, setResetKey] = useState({ open: false, initial })

  // Reset form when the modal opens or the edited row changes (render-time adjust; no effect).
  if (open !== resetKey.open || (open && initial !== resetKey.initial)) {
    setResetKey({ open, initial })
    if (open) {
      setForm(toForm(initial))
      setError('')
    }
  }

  function setField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function handleConfirm() {
    if (!form.name?.trim() || form.name.trim().length < 2) {
      setError('Name must be at least 2 characters')
      return
    }
    if (!form.code?.trim() || form.code.trim().length < 2) {
      setError('Code must be at least 2 characters')
      return
    }
    setError('')
    onSubmit?.(restaurantPayloadFromForm(form))
  }

  return (
    <AppModal
      open={open}
      size="lg"
      title={mode === 'edit' ? 'Edit restaurant' : 'Add restaurant'}
      onClose={onClose}
      onConfirm={handleConfirm}
      confirmLabel={mode === 'edit' ? 'Save changes' : 'Create restaurant'}
      busy={busy}
    >
      <div className="max-h-[65vh] space-y-4 overflow-y-auto pr-1">
        <p className="text-xs text-slate-500">
          Fields marked * are required. Code must be unique (e.g. SG-01, MC-04).
        </p>
        {error && (
          <p className="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
            {error}
          </p>
        )}

        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Basics</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="Name *"
              name="name"
              value={form.name}
              onChange={(e) => setField('name', e.target.value)}
              placeholder="Mountain Cafe"
              disabled={busy}
            />
            <Input
              label="Code *"
              name="code"
              value={form.code}
              onChange={(e) => setField('code', e.target.value)}
              placeholder="MC-03"
              disabled={busy}
            />
            <Input
              label="City"
              name="city"
              value={form.city}
              onChange={(e) => setField('city', e.target.value)}
              placeholder="Pune"
              disabled={busy}
            />
            <Input
              label="State"
              name="state"
              value={form.state}
              onChange={(e) => setField('state', e.target.value)}
              disabled={busy}
            />
            <Input
              label="Country"
              name="country"
              value={form.country}
              onChange={(e) => setField('country', e.target.value)}
              disabled={busy}
            />
            <Input
              label="Legal name"
              name="legal_name"
              value={form.legal_name}
              onChange={(e) => setField('legal_name', e.target.value)}
              disabled={busy}
            />
            <Input
              label="GST number"
              name="gst_number"
              value={form.gst_number}
              onChange={(e) => setField('gst_number', e.target.value)}
              disabled={busy}
            />
            <Input
              label="PAN number"
              name="pan_number"
              value={form.pan_number}
              onChange={(e) => setField('pan_number', e.target.value)}
              disabled={busy}
            />
          </div>
        </section>

        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Contact</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="Phone"
              name="phone"
              value={form.phone}
              onChange={(e) => setField('phone', e.target.value)}
              placeholder="+91-…"
              disabled={busy}
            />
            <Input
              label="Email"
              name="email"
              type="email"
              value={form.email}
              onChange={(e) => setField('email', e.target.value)}
              placeholder="hello@example.com"
              disabled={busy}
            />
            <Input
              label="Website"
              name="website"
              value={form.website}
              onChange={(e) => setField('website', e.target.value)}
              disabled={busy}
            />
            <Input
              label="Logo URL"
              name="logo_url"
              value={form.logo_url}
              onChange={(e) => setField('logo_url', e.target.value)}
              disabled={busy}
            />
          </div>
          <Textarea
            label="Address"
            name="address"
            rows={2}
            value={form.address}
            onChange={(e) => setField('address', e.target.value)}
            disabled={busy}
          />
        </section>

        <section className="space-y-3">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Settings</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <Input
              label="Tax ID"
              name="tax_id"
              value={form.tax_id}
              onChange={(e) => setField('tax_id', e.target.value)}
              disabled={busy}
            />
            <Input
              label="Currency"
              name="currency"
              value={form.currency}
              onChange={(e) => setField('currency', e.target.value)}
              disabled={busy}
            />
            <Input
              label="Timezone"
              name="timezone"
              value={form.timezone}
              onChange={(e) => setField('timezone', e.target.value)}
              disabled={busy}
            />
          </div>
          <div className="rounded-xl border border-slate-200 px-3 py-3 dark:border-zinc-700">
            <Switch
              label="Active restaurant"
              checked={form.is_active}
              onChange={(v) => setField('is_active', v)}
            />
          </div>
        </section>
      </div>
    </AppModal>
  )
}
