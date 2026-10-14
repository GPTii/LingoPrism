import { useAuth } from '../auth/store'

export interface WsEvent {
  event: string
  payload: Record<string, unknown>
}

/**
 * WebSocket to Django Channels with JWT auth (?token=) and exponential-backoff reconnect.
 * In dev the Vite server proxies /ws to the backend.
 */
export class LiveSocket {
  private ws: WebSocket | null = null
  private attempt = 0
  private closed = false
  private timer: number | undefined
  private listeners = new Set<(e: WsEvent) => void>()
  connected = false

  private path: string

  constructor(path: string) {
    this.path = path
  }

  connect() {
    this.closed = false
    const token = useAuth.getState().tokens?.access
    if (!token) return
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    this.ws = new WebSocket(`${proto}://${window.location.host}${this.path}?token=${token}`)
    this.ws.onopen = () => {
      this.attempt = 0
      this.connected = true
    }
    this.ws.onmessage = (m) => {
      try {
        const data = JSON.parse(m.data) as WsEvent
        this.listeners.forEach((l) => l(data))
      } catch {
        /* ignore malformed */
      }
    }
    this.ws.onclose = () => {
      this.connected = false
      if (this.closed) return
      const delay = Math.min(30_000, 1000 * 2 ** this.attempt++)
      this.timer = window.setTimeout(() => this.connect(), delay)
    }
  }

  on(listener: (e: WsEvent) => void) {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  send(message: Record<string, unknown>): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false
    this.ws.send(JSON.stringify(message))
    return true
  }

  close() {
    this.closed = true
    window.clearTimeout(this.timer)
    this.ws?.close()
  }
}
