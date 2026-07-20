import { Link } from 'react-router-dom'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import { useNotifications } from '../context/NotificationContext'

export default function NotificationsPage() {
  const { allItems, markRead, markAllRead, unreadCount } = useNotifications()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Notifications</h1>
          <p className="text-sm text-slate-500">{unreadCount} unread</p>
        </div>
        <Button variant="secondary" onClick={markAllRead}>
          Mark all read
        </Button>
      </div>
      <Card>
        <ul className="divide-y divide-slate-100 dark:divide-zinc-900">
          {allItems.map((n) => (
            <li key={n.id} className="flex items-start justify-between gap-3 py-3">
              <div>
                <p className={`text-sm ${n.unread ? 'font-semibold' : 'font-medium'}`}>{n.title}</p>
                <p className="text-xs text-slate-500">{n.body}</p>
              </div>
              {n.unread && (
                <Button size="sm" variant="secondary" onClick={() => markRead(n.id)}>
                  Mark read
                </Button>
              )}
            </li>
          ))}
        </ul>
      </Card>
      <Link to="/" className="text-sm text-blue-600 hover:underline">
        Back to dashboard
      </Link>
    </div>
  )
}
