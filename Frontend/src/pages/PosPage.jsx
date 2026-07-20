import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { MonitorSmartphone } from 'lucide-react'

export default function PosPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">POS</h1>
        <p className="text-sm text-slate-500">Point of sale workspace (UI shell · API-ready)</p>
      </div>
      <Card>
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <div className="rounded-2xl bg-slate-100 p-4 dark:bg-zinc-900">
            <MonitorSmartphone className="h-8 w-8" />
          </div>
          <p className="max-w-md text-sm text-slate-500">
            Register UI, ticket queue, and tender flows will connect to the orders API. This shell is ready
            for integration.
          </p>
          <Button disabled>Open register (soon)</Button>
        </div>
      </Card>
    </div>
  )
}
