'use client'

import { useState, useCallback, useRef } from 'react'
import { generateId } from '@/lib/utils'
import { streamChat } from '@/lib/api'
import type { ChatMessage, ToolCallStep } from '@/types/invest'

const ENDPOINT = {
  invest: '/api/v1/invest/chat',
  edu: '/api/v1/edu/chat',
}

export function useChat(vertical: 'invest' | 'edu') {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const abortRef = useRef<AbortController | null>(null)

  const send = useCallback(async () => {
    const content = input.trim()
    if (!content || isStreaming) return

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content,
      created_at: new Date().toISOString(),
    }

    const assistantId = generateId()
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      tool_calls: [],
      memory_refs: [],
      created_at: new Date().toISOString(),
      is_streaming: true,
    }

    setMessages((prev) => [...prev, userMsg, assistantMsg])
    setInput('')
    setIsStreaming(true)

    const controller = new AbortController()
    abortRef.current = controller

    try {
      await streamChat(
        ENDPOINT[vertical],
        {
          message: content,
          history: messages.map((m) => ({ role: m.role, content: m.content })),
        },
        {
          signal: controller.signal,
          onDelta: (text) => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: m.content + text } : m,
              ),
            )
          },
          onToolUse: (event) => {
            const toolEvent = event as {
              id: string
              name: string
              input: Record<string, unknown>
              status: 'running' | 'completed' | 'failed'
              output?: unknown
              duration_ms?: number
            }
            const step: ToolCallStep = {
              id: toolEvent.id ?? generateId(),
              name: toolEvent.name,
              input: toolEvent.input ?? {},
              status: toolEvent.status ?? 'running',
              output: toolEvent.output,
              duration_ms: toolEvent.duration_ms,
            }
            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m
                const existingCalls = m.tool_calls ?? []
                const idx = existingCalls.findIndex((s) => s.id === step.id)
                const updated =
                  idx >= 0
                    ? existingCalls.map((s, i) => (i === idx ? step : s))
                    : [...existingCalls, step]
                return { ...m, tool_calls: updated }
              }),
            )
          },
          onDone: () => {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, is_streaming: false } : m,
              ),
            )
            setIsStreaming(false)
          },
          onError: (err) => {
            console.error('[useChat] stream error:', err)
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? { ...m, content: m.content || '抱歉，出现了错误，请重试。', is_streaming: false }
                  : m,
              ),
            )
            setIsStreaming(false)
          },
        },
      )
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('[useChat] unexpected error:', err)
      }
      setIsStreaming(false)
    }
  }, [input, isStreaming, messages, vertical])

  const stop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setMessages((prev) =>
      prev.map((m) => (m.is_streaming ? { ...m, is_streaming: false } : m)),
    )
  }, [])

  const clear = useCallback(() => {
    stop()
    setMessages([])
  }, [stop])

  return { messages, input, setInput, isStreaming, send, stop, clear }
}
