import { useEffect } from 'react'
import { App } from 'antd'
import { useQueryClient } from '@tanstack/react-query'
import { create } from 'zustand'
import { LiveSocket } from './ws'
import { notificationApi } from '../api/app'
import { useAuth } from '../auth/store'

interface UnreadState {
  unread: number
  set: (n: number) => void
}

export const useUnread = create<UnreadState>((set) => ({ unread: 0, set: (unread) => set({ unread }) }))

/** Keeps /ws/events/ open: realtime notifications, XP and quest updates (same events the mobile app gets). */
export function useUserEvents() {
  const user = useAuth((s) => s.user)
  const { notification } = App.useApp()
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!user) return
    notificationApi.unread().then((n) => useUnread.getState().set(n)).catch(() => undefined)
    const socket = new LiveSocket('/ws/events/')
    socket.connect()
    const off = socket.on((e) => {
      if (e.event === 'notification') {
        useUnread.getState().set(useUnread.getState().unread + 1)
        // a new private message while the messages page is open needs no pop-up
        if (!(e.payload.kind === 'message' && window.location.pathname.startsWith('/messages')))
          notification.info({ message: String(e.payload.title ?? ''), description: String(e.payload.body ?? ''), placement: 'topRight' })
        queryClient.invalidateQueries({ queryKey: ['notifications'] })
      } else if (e.event === 'dm' || e.event === 'dm_read') {
        // the open conversation listens for this; the list of conversations just reloads
        window.dispatchEvent(new CustomEvent('lingoprism:dm', { detail: { event: e.event, payload: e.payload } }))
        queryClient.invalidateQueries({ queryKey: ['dm-threads'] })
      } else if (e.event === 'xp' || e.event === 'quest_completed') {
        queryClient.invalidateQueries({ queryKey: ['game-summary'] })
        queryClient.invalidateQueries({ queryKey: ['quests'] })
      }
    })
    return () => {
      off()
      socket.close()
    }
  }, [user, notification, queryClient])
}
