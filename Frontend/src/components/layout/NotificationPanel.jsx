import { Bell, CheckCheck } from 'lucide-react'
import { useNotifications } from '../../context/NotificationContext'

function timeAgo(iso) {
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.round(hrs / 24)}d ago`
}

export default function NotificationPanel() {
  const {
    items,
    panelOpen,
    setPanelOpen,
    unreadCount,
    markRead,
    markAllRead,
    filter,
    setFilter,
  } = useNotifications()

  if (!panelOpen) return null

  return (
    <>
      <button
        type="button"
        className="fixed inset-0 z-[55] cursor-default bg-transparent"
        aria-label="Close notifications"
        onClick={() => setPanelOpen(false)}
      />
      <div
        role="dialog"
        aria-label="Notifications"
        className="absolute right-0 top-12 z-[60] w-[360px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl dark:border-zinc-800 dark:bg-zinc-950"
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4" />
            <h2 className="text-sm font-semibold">Notifications</h2>
            {unreadCount > 0 && (
              <span className="rounded-full bg-rose-500 px-1.5 text-[10px] font-bold text-white">
                {unreadCount}
              </span>
            )}
          </div>
          <button
            type="button"
            onClick={markAllRead}
            className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-slate-800 dark:hover:text-zinc-200"
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Mark all read
          </button>
        </div>
        <div className="flex gap-2 border-b border-slate-100 px-4 py-2 dark:border-zinc-800">
          {['all', 'unread'].map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`rounded-lg px-2.5 py-1 text-xs font-medium capitalize ${
                filter === f
                  ? 'bg-slate-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                  : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-zinc-900'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
        <ul className="max-h-80 overflow-y-auto">
          {items.length === 0 ? (
            <li className="px-4 py-8 text-center text-sm text-slate-500">No notifications</li>
          ) : (
            items.map((n) => (
              <li key={n.id}>
                <button
                  type="button"
                  onClick={() => markRead(n.id)}
                  className={`flex w-full flex-col gap-0.5 border-b border-slate-50 px-4 py-3 text-left hover:bg-slate-50 dark:border-zinc-900 dark:hover:bg-zinc-900 ${
                    n.unread ? 'bg-blue-50/40 dark:bg-zinc-900/60' : ''
                  }`}
                >
                  <span className="text-sm font-medium text-slate-900 dark:text-zinc-100">{n.title}</span>
                  <span className="text-xs text-slate-500">{n.body}</span>
                  <span className="text-[10px] text-slate-400">{timeAgo(n.at)}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </>
  )
}
