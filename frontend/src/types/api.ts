// ─── Generic API Response ────────────────────────────────────────────────────

export interface ApiResponse<T = unknown> {
  data: T
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_next: boolean
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, unknown>
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  display_name: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
  expires_in: number
}

export interface User {
  id: string
  email: string
  display_name: string
  name?: string          // alias — some components use this
  avatar_url?: string
  bio?: string
  timezone?: string
  is_active?: boolean
  created_at: string
  subscription_tier?: 'free' | 'pro' | 'enterprise'
}

// ─── SSE / Streaming ─────────────────────────────────────────────────────────

export type SSEEventType =
  | 'message_start'
  | 'content_delta'
  | 'tool_use'
  | 'tool_result'
  | 'message_stop'
  | 'error'

export interface SSEEvent {
  type: SSEEventType
  data: unknown
}

export interface ContentDeltaEvent {
  type: 'content_delta'
  delta: { text: string }
  index: number
}

export interface ToolUseEvent {
  type: 'tool_use'
  id: string
  name: string
  input: Record<string, unknown>
  status: 'running' | 'completed' | 'failed'
  output?: unknown
}

// ─── Task ─────────────────────────────────────────────────────────────────────

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'

export interface Task {
  id: string
  type: string
  status: TaskStatus
  progress: number
  result?: unknown
  error?: string
  created_at: string
  updated_at: string
}

// ─── WebSocket Messages ───────────────────────────────────────────────────────

export type WSMessageType =
  | 'task_progress'
  | 'task_completed'
  | 'task_failed'
  | 'notification'
  | 'ping'
  | 'pong'

export interface WSMessage<T = unknown> {
  type: WSMessageType
  payload: T
  timestamp: string
}

export interface TaskProgressPayload {
  task_id: string
  progress: number
  message?: string
  status: TaskStatus
}
