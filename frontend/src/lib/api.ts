import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosError } from 'axios'
import type { ApiResponse, AuthTokens } from '@/types/api'

// ─── Token Storage ────────────────────────────────────────────────────────────

const TOKEN_KEY = 'df_access_token'
const REFRESH_KEY = 'df_refresh_token'

export const tokenStorage = {
  getAccess: () =>
    typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null,
  getRefresh: () =>
    typeof window !== 'undefined' ? localStorage.getItem(REFRESH_KEY) : null,
  set: (tokens: AuthTokens) => {
    if (typeof window === 'undefined') return
    localStorage.setItem(TOKEN_KEY, tokens.access_token)
    localStorage.setItem(REFRESH_KEY, tokens.refresh_token)
  },
  clear: () => {
    if (typeof window === 'undefined') return
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

// ─── Axios Instance ───────────────────────────────────────────────────────────

const api: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
  timeout: 30_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = tokenStorage.getAccess()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Flag to prevent parallel refresh races
let isRefreshing = false
let refreshSubscribers: Array<(token: string) => void> = []

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

function onRefreshComplete(token: string) {
  refreshSubscribers.forEach((cb) => cb(token))
  refreshSubscribers = []
}

// Response interceptor: handle 401 → refresh → retry
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      if (isRefreshing) {
        // Queue this request until the ongoing refresh completes
        return new Promise((resolve) => {
          subscribeTokenRefresh((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers['Authorization'] = `Bearer ${token}`
            }
            resolve(api(originalRequest))
          })
        })
      }

      isRefreshing = true
      const refreshToken = tokenStorage.getRefresh()

      if (!refreshToken) {
        tokenStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      }

      try {
        const { data } = await axios.post<ApiResponse<AuthTokens>>(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/refresh`,
          { refresh_token: refreshToken },
        )
        const tokens = data.data
        tokenStorage.set(tokens)
        onRefreshComplete(tokens.access_token)

        if (originalRequest.headers) {
          originalRequest.headers['Authorization'] = `Bearer ${tokens.access_token}`
        }
        return api(originalRequest)
      } catch {
        tokenStorage.clear()
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default api

// ─── Typed Helpers ────────────────────────────────────────────────────────────

export async function apiGet<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const { data } = await api.get<ApiResponse<T>>(url, { params })
  return data.data
}

export async function apiPost<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await api.post<ApiResponse<T>>(url, body)
  return data.data
}

export async function apiPut<T>(url: string, body?: unknown): Promise<T> {
  const { data } = await api.put<ApiResponse<T>>(url, body)
  return data.data
}

export async function apiDelete<T>(url: string): Promise<T> {
  const { data } = await api.delete<ApiResponse<T>>(url)
  return data.data
}

// ─── SSE Streaming ────────────────────────────────────────────────────────────

export interface StreamOptions {
  onDelta: (text: string) => void
  onToolUse?: (event: unknown) => void
  onDone?: () => void
  onError?: (err: Error) => void
  signal?: AbortSignal
}

export async function streamChat(
  url: string,
  body: unknown,
  options: StreamOptions,
): Promise<void> {
  const token = tokenStorage.getAccess()
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${url}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    signal: options.signal,
  })

  if (!response.ok) {
    options.onError?.(new Error(`HTTP ${response.status}: ${response.statusText}`))
    return
  }

  const reader = response.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (raw === '[DONE]') {
          options.onDone?.()
          return
        }
        try {
          const event = JSON.parse(raw)
          if (event.type === 'content_delta') {
            options.onDelta(event.delta?.text ?? '')
          } else if (event.type === 'tool_use') {
            options.onToolUse?.(event)
          } else if (event.type === 'message_stop') {
            options.onDone?.()
            return
          }
        } catch {
          // skip malformed lines
        }
      }
    }
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      options.onError?.(err as Error)
    }
  } finally {
    reader.releaseLock()
  }
}
