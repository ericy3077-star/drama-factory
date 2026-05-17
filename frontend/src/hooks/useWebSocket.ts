'use client'

import { useEffect, useCallback } from 'react'
import { wsClient } from '@/lib/websocket'
import type { WSMessageType } from '@/types/api'

/**
 * Subscribe to a WebSocket event. Auto-connects on mount.
 * Returns an emit function for sending messages.
 */
export function useWebSocket<T = unknown>(
  event: WSMessageType | string | undefined,
  handler?: (payload: T) => void,
) {
  useEffect(() => {
    if (!wsClient.isConnected) {
      wsClient.connect()
    }

    if (!event || !handler) return

    const unsubscribe = wsClient.subscribe<T>(event, handler)
    return unsubscribe
  }, [event, handler])

  const emit = useCallback(<P = unknown>(evt: string, payload: P) => {
    wsClient.emit(evt, payload)
  }, [])

  const joinRoom = useCallback((room: string) => {
    wsClient.joinRoom(room)
  }, [])

  const leaveRoom = useCallback((room: string) => {
    wsClient.leaveRoom(room)
  }, [])

  return { emit, joinRoom, leaveRoom, isConnected: wsClient.isConnected }
}
