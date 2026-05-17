'use client'

import { useState, useEffect, useCallback } from 'react'
import { useWebSocket } from './useWebSocket'
import { apiGet } from '@/lib/api'
import type { Task, TaskStatus, TaskProgressPayload } from '@/types/api'

interface UseTaskStatusResult {
  status: TaskStatus | undefined
  progress: number | undefined
  message: string | undefined
  result: unknown
  error: string | undefined
  refresh: () => void
}

/**
 * Track an async task via WebSocket events + optional HTTP polling fallback.
 * Pass undefined for taskId to disable tracking.
 */
export function useTaskStatus(taskId: string | undefined, pollIntervalMs = 5000): UseTaskStatusResult {
  const [task, setTask] = useState<Task | undefined>(undefined)

  // Initial load
  useEffect(() => {
    if (!taskId) { setTask(undefined); return }
    apiGet<Task>(`/api/v1/tasks/${taskId}`).then(setTask).catch(console.error)
  }, [taskId])

  // WebSocket updates
  useWebSocket<TaskProgressPayload>('task_progress', (payload) => {
    if (payload.task_id !== taskId) return
    setTask((prev) =>
      prev
        ? { ...prev, status: payload.status, progress: payload.progress }
        : undefined,
    )
  })

  useWebSocket<TaskProgressPayload>('task_completed', (payload) => {
    if (payload.task_id !== taskId) return
    apiGet<Task>(`/api/v1/tasks/${taskId}`).then(setTask).catch(console.error)
  })

  useWebSocket<TaskProgressPayload>('task_failed', (payload) => {
    if (payload.task_id !== taskId) return
    setTask((prev) =>
      prev ? { ...prev, status: 'failed', error: payload.message } : undefined,
    )
  })

  // Polling fallback for tasks not yet WebSocket-connected
  useEffect(() => {
    if (!taskId) return
    if (task?.status === 'completed' || task?.status === 'failed' || task?.status === 'cancelled') return

    const interval = setInterval(() => {
      apiGet<Task>(`/api/v1/tasks/${taskId}`)
        .then((t) => {
          setTask(t)
          if (t.status === 'completed' || t.status === 'failed') clearInterval(interval)
        })
        .catch(console.error)
    }, pollIntervalMs)

    return () => clearInterval(interval)
  }, [taskId, task?.status, pollIntervalMs])

  const refresh = useCallback(() => {
    if (!taskId) return
    apiGet<Task>(`/api/v1/tasks/${taskId}`).then(setTask).catch(console.error)
  }, [taskId])

  return {
    status: task?.status,
    progress: task?.progress,
    message: undefined,
    result: task?.result,
    error: task?.error,
    refresh,
  }
}
