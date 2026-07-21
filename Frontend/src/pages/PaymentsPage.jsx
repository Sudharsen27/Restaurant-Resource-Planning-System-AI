import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CreditCard, FileText, Printer } from 'lucide-react'
import EntityListPage from '../components/pages/EntityListPage'
import AppModal from '../components/modals/AppModal'
import Button from '../components/ui/Button'
import { Select, Input } from '../components/forms/FormControls'
import { useOrg } from '../context/OrgContext'
import { useToast } from '../context/ToastContext'
import { formatCurrency, formatDateTime } from '../utils/format'
import {
  getInvoice,
  listOrders,
  payOrder,
  refundOrder,
} from '../services/orderService'

const PAY_METHODS = [
  { value: 'CASH', label: 'Cash' },
  { value: 'CARD', label: 'Card' },
  { value: 'UPI', label: 'UPI' },
  { value: 'WALLET', label: 'Wallet' },
]

export default function PaymentsPage() {
  const { restaurant, branch } = useOrg()
  const { success, error: toastError } = useToast()
  const queryClient = useQueryClient()
  const [payOpen, setPayOpen] = useState(false)
  const [invoiceOpen, setInvoiceOpen] = useState(false)
  const [selected, setSelected] = useState(null)
  const [invoice, setInvoice] = useState(null)
  const [method, setMethod] = useState('CASH')
  const [amount, setAmount] = useState('')
  const [tip, setTip] = useState(0)

  const { data: orders = [], isLoading, isError, error } = useQuery({
    queryKey: ['payments-orders', restaurant?.id, branch?.id],
    enabled: !!restaurant?.id,
    queryFn: async () => {
      const res = await listOrders({
        restaurant_id: restaurant.id,
        branch_id: branch?.id,
        limit: 100,
      })
      return res.data || []
    },
  })

  const openPay = (row) => {
    setSelected(row)
    setAmount(String(row.balance_due ?? row.total ?? ''))
    setTip(0)
    setMethod('CASH')
    setPayOpen(true)
  }

  const payMutation = useMutation({
    mutationFn: () =>
      payOrder(selected.uuid, {
        amount: amount === '' ? null : Number(amount),
        tip_amount: Number(tip) || 0,
        method,
        split: Number(amount) > 0 && Number(amount) < Number(selected.balance_due || selected.total),
      }),
    onSuccess: () => {
      success('Payment recorded')
      setPayOpen(false)
      queryClient.invalidateQueries({ queryKey: ['payments-orders'] })
      queryClient.invalidateQueries({ queryKey: ['orders'] })
      queryClient.invalidateQueries({ queryKey: ['pos-dashboard'] })
    },
    onError: (e) => toastError(e.message),
  })

  const refundMutation = useMutation({
    mutationFn: (row) => refundOrder(row.uuid),
    onSuccess: () => {
      success('Refund issued')
      queryClient.invalidateQueries({ queryKey: ['payments-orders'] })
    },
    onError: (e) => toastError(e.message),
  })

  const openInvoice = async (row) => {
    try {
      const res = await getInvoice(row.uuid)
      setInvoice(res.data || res)
      setSelected(row)
      setInvoiceOpen(true)
    } catch (e) {
      toastError(e.message)
    }
  }

  const printInvoice = () => {
    if (!invoice) return
    const w = window.open('', '_blank', 'width=480,height=720')
    if (!w) return
    w.document.write(`<!doctype html><html><head><title>${invoice.invoice_number}</title>
      <style>body{font-family:ui-monospace,monospace;padding:24px;font-size:13px}
      h1{font-size:18px;margin:0 0 8px}table{width:100%;border-collapse:collapse;margin:12px 0}
      td,th{text-align:left;padding:4px 0;border-bottom:1px dashed #ccc}
      .tot{font-weight:700;font-size:15px}</style></head><body>
      <h1>GST Invoice ${invoice.invoice_number}</h1>
      <div>Order ${invoice.order_number} · ${invoice.customer}</div>
      <div>${invoice.order_type}${invoice.table_number ? ` · Table ${invoice.table_number}` : ''}</div>
      <table><thead><tr><th>Item</th><th>Qty</th><th>Amt</th></tr></thead><tbody>
      ${(invoice.items || [])
        .map(
          (i) =>
            `<tr><td>${i.item_name}</td><td>${i.quantity}</td><td>${Number(i.line_total).toFixed(2)}</td></tr>`,
        )
        .join('')}
      </tbody></table>
      <div>Subtotal: ${Number(invoice.subtotal).toFixed(2)}</div>
      <div>Discount: ${Number(invoice.discount_amount).toFixed(2)}</div>
      <div>CGST: ${Number(invoice.cgst).toFixed(2)} · SGST: ${Number(invoice.sgst).toFixed(2)}</div>
      <div>Tip: ${Number(invoice.tip_amount).toFixed(2)}</div>
      <div class="tot">Total: ₹${Number(invoice.total).toFixed(2)}</div>
      <div style="margin-top:16px;font-size:11px">QR: ${invoice.qr_payload}</div>
      <script>window.print()</script></body></html>`)
    w.document.close()
  }

  const rows = orders.map((o) => ({
    ...o,
    paid_label: formatCurrency(o.amount_paid),
    due_label: formatCurrency(o.balance_due),
    total_label: formatCurrency(o.total),
    when: formatDateTime(o.createdAt),
  }))

  return (
    <>
      {isError && <p className="mb-3 text-sm text-rose-600">{error?.message}</p>}
      <EntityListPage
        title="Payments & receipts"
        description="Tender, split/partial pay, refunds, GST invoices"
        entity="payments"
        rows={rows}
        loading={isLoading}
        columns={[
          { key: 'order_number', label: 'Order' },
          { key: 'customer', label: 'Customer' },
          { key: 'total_label', label: 'Total' },
          { key: 'paid_label', label: 'Paid' },
          { key: 'due_label', label: 'Due' },
          { key: 'status', label: 'Status' },
          {
            key: 'actions',
            label: '',
            render: (_, row) => (
              <div className="flex flex-wrap gap-1">
                {Number(row.balance_due) > 0 && (
                  <Button size="sm" onClick={() => openPay(row)}>
                    <CreditCard className="h-3.5 w-3.5" /> Pay
                  </Button>
                )}
                <Button size="sm" variant="secondary" onClick={() => openInvoice(row)}>
                  <FileText className="h-3.5 w-3.5" /> Invoice
                </Button>
                {(row.payments || []).some((p) => p.status === 'PAID') && (
                  <Button size="sm" variant="danger" onClick={() => refundMutation.mutate(row)}>
                    Refund
                  </Button>
                )}
              </div>
            ),
          },
        ]}
        headerActions={
          <Link to="/pos">
            <Button variant="secondary">Open POS</Button>
          </Link>
        }
      />

      <AppModal open={payOpen} onClose={() => setPayOpen(false)} title={`Pay ${selected?.order_number || ''}`} hideFooter>
        <div className="space-y-3">
          <p className="text-sm text-slate-500">
            Due {formatCurrency(selected?.balance_due)} · enter less for partial / split
          </p>
          <Select label="Method" value={method} onChange={(e) => setMethod(e.target.value)} options={PAY_METHODS} />
          <Input label="Amount" type="number" value={amount} onChange={(e) => setAmount(e.target.value)} />
          <Input label="Tip" type="number" value={tip} onChange={(e) => setTip(e.target.value)} />
          <Button className="w-full" disabled={payMutation.isPending} onClick={() => payMutation.mutate()}>
            Confirm payment
          </Button>
        </div>
      </AppModal>

      <AppModal
        open={invoiceOpen}
        onClose={() => setInvoiceOpen(false)}
        title={invoice?.invoice_number || 'Invoice'}
        hideFooter
      >
        {invoice && (
          <div className="space-y-2 text-sm">
            <p>
              {invoice.customer} · {invoice.order_number}
            </p>
            <p>
              Tax CGST {formatCurrency(invoice.cgst)} · SGST {formatCurrency(invoice.sgst)}
            </p>
            <p className="text-lg font-bold">{formatCurrency(invoice.total)}</p>
            <p className="break-all text-xs text-slate-500">{invoice.qr_payload}</p>
            <p className="text-xs text-slate-400">
              Email receipt: use Print → Save as PDF / mailto from the print dialog.
            </p>
            <Button onClick={printInvoice}>
              <Printer className="h-4 w-4" /> Print / PDF
            </Button>
          </div>
        )}
      </AppModal>
    </>
  )
}
