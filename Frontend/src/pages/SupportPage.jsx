import Card from '../components/ui/Card'
import { LifeBuoy, Mail, MessageCircle } from 'lucide-react'

export default function SupportPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Support</h1>
        <p className="text-sm text-slate-500">Help center and contact channels</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[
          { icon: LifeBuoy, title: 'Docs', body: 'Architecture, auth, and ERP UI guides in /docs' },
          { icon: Mail, title: 'Email', body: 'support@restaurant-erp.local (placeholder)' },
          { icon: MessageCircle, title: 'Status', body: 'All systems operational (mock)' },
        ].map(({ icon: Icon, title, body }) => (
          <Card key={title}>
            <Icon className="mb-3 h-5 w-5" />
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-1 text-sm text-slate-500">{body}</p>
          </Card>
        ))}
      </div>
    </div>
  )
}
