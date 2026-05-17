import { io, type Socket } from 'socket.io-client'
import { tokenStorage } from './api'
import type { WSMessage, WSMessageType } from '@/types/api'

// ─── Types ────────────────────────────────────────────────────────────────────

type EventHandler<T = unknown> = (payload: T) => void

interface WSClientOptions {
  autoConnect?: boolean
  reconnectionAttempts?: number
  reconnectionDelay?: number
}

// ─── WebSocket Client ─────────────────────────────────────────────────────────

class WebSocketClient {
  private socket: Socket | null = null
  private handlers: Map<string, Set<EventHandler>> = new Map()
  private heartbeatInterval: ReturnType<typeof setInterval> | null = null
  private readonly HEARTBEAT_INTERVAL = 25_000

  connect(options: WSClientOptions = {}): void {
    if (this.socket?.connected) return

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000'
    const token = tokenStorage.getAccess()

    this.socket = io(wsUrl, {
      auth: { token },
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionAttempts: options.reconnectionAttempts ?? 10,
      reconnectionDelay: options.reconnectionDelay ?? 1000,
      reconnectionDelayMax: 10_000,
      autoConnect: options.autoConnect ?? true,
    })

    this.socket.on('connect', () => {
      console.log('[WS] Connected:', this.socket?.id)
      this.startHeartbeat()
    })

    this.socket.on('disconnect', (reason) => {
      console.log('[WS] Disconnected:', reason)
      this.stopHeartbeat()
    })

    this.socket.on('connect_error', (err) => {
      console.warn('[WS] Connection error:', err.message)
    })

    // Route all incoming messages to registered handlers
    this.socket.onAny((event: string, message: WSMessage) => {
      this.dispatch(event, message?.payload ?? message)
    })
  }

  disconnect(): void {
    this.stopHeartbeat()
    this.socket?.disconnect()
    this.socket = null
  }

  subscribe<T = unknown>(event: WSMessageType | string, handler: EventHandler<T>): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler as EventHandler)

    // Return unsubscribe function
    return () => {
      this.handlers.get(event)?.delete(handler as EventHandler)
    }
  }

  emit<T = unknown>(event: string, payload: T): void {
    if (!this.socket?.connected) {
      console.warn('[WS] Cannot emit: not connected')
      return
    }
    this.socket.emit(event, payload)
  }

  joinRoom(room: string): void {
    this.emit('join_room', { room })
  }

  leaveRoom(room: string): void {
    this.emit('leave_room', { room })
  }

  get isConnected(): boolean {
    return this.socket?.connected ?? false
  }

  private dispatch(event: string, payload: unknown): void {
    const eventHandlers = this.handlers.get(event)
    eventHandlers?.forEach((handler) => {
      try {
        handler(payload)
      } catch (err) {
        console.error(`[WS] Handler error for event "${event}":`, err)
      }
    })
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      this.emit('ping', { ts: Date.now() })
    }, this.HEARTBEAT_INTERVAL)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval)
      this.heartbeatInterval = null
    }
  }
}

// Singleton instance
export const wsClient = new WebSocketClient()

export default wsClient
