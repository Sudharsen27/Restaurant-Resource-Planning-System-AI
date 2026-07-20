import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../services/notificationService'

const NotificationContext = createContext(null)

export function NotificationProvider({ children }) {
  const queryClient = useQueryClient()
  const [panelOpen, setPanelOpen] = useState(false)
  const [filter, setFilter] = useState('all')

  const { data: items = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => (await listNotifications()).data || [],
    staleTime: 30_000,
  })

  const unreadCount = useMemo(() => items.filter((n) => n.unread).length, [items])
  const visible = useMemo(() => {
    if (filter === 'unread') return items.filter((n) => n.unread)
    return items
  }, [items, filter])

  const markRead = useCallback(
    async (id) => {
      await markNotificationRead(id)
      await queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
    [queryClient],
  )

  const markAllRead = useCallback(async () => {
    await markAllNotificationsRead()
    await queryClient.invalidateQueries({ queryKey: ['notifications'] })
  }, [queryClient])

  const value = useMemo(
    () => ({
      items: visible,
      allItems: items,
      unreadCount,
      panelOpen,
      setPanelOpen,
      filter,
      setFilter,
      markRead,
      markAllRead,
    }),
    [visible, items, unreadCount, panelOpen, filter, markRead, markAllRead],
  )

  return (
    <NotificationContext.Provider value={value}>{children}</NotificationContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useNotifications() {
  const ctx = useContext(NotificationContext)
  if (!ctx) throw new Error('useNotifications must be used within NotificationProvider')
  return ctx
}
