import { useCallback, useEffect, useState } from 'react'
import Card from '../components/ui/Card'
import Button from '../components/ui/Button'
import LoadingSpinner from '../components/ui/LoadingSpinner'
import { listSessions, revokeAllSessions, revokeSession } from '../services/authService'
import { useToast } from '../context/ToastContext'

export default function Sessions() {
  const { success, error } = useToast()
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listSessions()
      setSessions(res?.data || [])
    } catch (err) {
      error(err.message || 'Failed to load sessions')
    } finally {
      setLoading(false)
    }
  }, [error])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await listSessions()
        if (!cancelled) setSessions(res?.data || [])
      } catch (err) {
        if (!cancelled) error(err.message || 'Failed to load sessions')
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [error])

  async function onRevoke(id) {
    try {
      await revokeSession(id)
      success('Session terminated')
      await load()
    } catch (err) {
      error(err.message || 'Could not terminate session')
    }
  }

  async function onRevokeAll() {
    try {
      await revokeAllSessions()
      success('Other sessions terminated')
      await load()
    } catch (err) {
      error(err.message || 'Could not terminate sessions')
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">Sessions</h1>
          <p className="text-sm text-slate-500">Active devices and force logout</p>
        </div>
        <Button variant="secondary" onClick={onRevokeAll}>
          Terminate other sessions
        </Button>
      </div>

      <Card title="Active sessions">
        {loading ? (
          <LoadingSpinner />
        ) : sessions.length === 0 ? (
          <p className="text-sm text-slate-500">No active sessions.</p>
        ) : (
          <ul className="divide-y divide-slate-200 dark:divide-slate-800">
            {sessions.map((s) => (
              <li key={s.id} className="flex flex-wrap items-center justify-between gap-3 py-3 text-sm">
                <div>
                  <p className="font-medium text-slate-900 dark:text-white">
                    {s.browser || 'Unknown browser'} · {s.os || 'Unknown OS'}
                    {s.is_current ? (
                      <span className="ml-2 rounded bg-emerald-100 px-1.5 py-0.5 text-xs text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300">
                        Current
                      </span>
                    ) : null}
                  </p>
                  <p className="text-xs text-slate-500">
                    {s.device || 'Device'} · IP {s.ip_address || '—'} · Last activity{' '}
                    {s.last_activity_at ? new Date(s.last_activity_at).toLocaleString() : '—'}
                  </p>
                </div>
                {!s.is_current && (
                  <Button variant="danger" size="sm" onClick={() => onRevoke(s.id)}>
                    Terminate
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}
