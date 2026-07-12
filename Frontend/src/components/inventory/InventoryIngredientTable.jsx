import { formatCurrency } from '../../utils/format'

function Qty({ value, unit }) {
  return (
    <span>
      {Number(value).toFixed(2)}
      <span className="ml-1 text-xs text-slate-400">{unit}</span>
    </span>
  )
}

function StatusBadge({ status }) {
  const styles = {
    'Purchase needed': 'bg-blue-100 text-blue-800 dark:bg-blue-950/50 dark:text-blue-300',
    'In stock': 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950/50 dark:text-emerald-300',
    Review: 'bg-amber-100 text-amber-800 dark:bg-amber-950/50 dark:text-amber-300',
  }
  return (
    <span
      className={`inline-flex shrink-0 items-center whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[status] || 'bg-slate-100 text-slate-600'
      }`}
    >
      {status}
    </span>
  )
}

export default function InventoryIngredientTable({ rows, totalCost }) {
  if (!rows.length) return null

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[960px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-left text-xs uppercase tracking-wider text-slate-500 dark:border-slate-700">
            <th className="pb-3 pr-4 font-medium">Ingredient Name</th>
            <th className="pb-3 pr-4 font-medium">Required Quantity</th>
            <th className="pb-3 pr-4 font-medium">Current Stock</th>
            <th className="pb-3 pr-4 font-medium">Purchase Quantity</th>
            <th className="pb-3 pr-4 font-medium">Unit</th>
            <th className="pb-3 pr-4 font-medium text-right">Estimated Cost</th>
            <th className="pb-3 pr-4 font-medium">Supplier Lead Time</th>
            <th className="pb-3 pr-4 font-medium">Shelf Life</th>
            <th className="min-w-[8.5rem] pb-3 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.name}
              className="border-b border-slate-100 transition hover:bg-slate-50/80 dark:border-slate-800 dark:hover:bg-slate-800/50"
            >
              <td className="py-3.5 pr-4 font-medium text-slate-900 dark:text-white">
                {row.name}
              </td>
              <td className="py-3.5 pr-4 text-slate-700 dark:text-slate-300">
                <Qty value={row.required} unit={row.unit} />
              </td>
              <td className="py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                <Qty value={row.currentStock} unit={row.unit} />
              </td>
              <td className="py-3.5 pr-4">
                <span
                  className={
                    row.purchaseQty > 0
                      ? 'font-semibold text-blue-600 dark:text-blue-400'
                      : 'text-slate-400'
                  }
                >
                  <Qty value={row.purchaseQty} unit={row.unit} />
                </span>
              </td>
              <td className="py-3.5 pr-4 text-slate-500">{row.unit}</td>
              <td className="py-3.5 pr-4 text-right font-medium text-slate-900 dark:text-white">
                {formatCurrency(row.estimatedCost)}
              </td>
              <td className="py-3.5 pr-4 text-slate-600 dark:text-slate-400">
                {row.leadTime != null
                  ? `${row.leadTime} day${Number(row.leadTime) !== 1 ? 's' : ''}`
                  : '—'}
              </td>
              <td className="py-3.5 pr-4 text-slate-500">{row.shelfLife ?? '—'}</td>
              <td className="min-w-[8.5rem] py-3.5">
                <StatusBadge status={row.status} />
              </td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr className="border-t-2 border-slate-200 dark:border-slate-700">
            <td colSpan={5} className="pt-4 font-semibold text-slate-900 dark:text-white">
              Total purchase cost
            </td>
            <td className="pt-4 text-right font-bold text-emerald-600 dark:text-emerald-400">
              {formatCurrency(totalCost)}
            </td>
            <td colSpan={3} className="pt-4" />
          </tr>
        </tfoot>
      </table>
    </div>
  )
}
