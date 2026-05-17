// ─── Feed / Research ─────────────────────────────────────────────────────────

export type FeedCategory =
  | 'market_news'
  | 'earnings'
  | 'macro'
  | 'crypto'
  | 'ipo'
  | 'analysis'

export interface FeedItem {
  id: string
  title: string
  summary: string
  source: string
  source_url: string
  category: FeedCategory
  tickers: string[]
  sentiment: 'positive' | 'negative' | 'neutral'
  sentiment_score: number
  published_at: string
  image_url?: string
  ai_insights?: string
}

export interface ResearchReport {
  id: string
  title: string
  ticker: string
  company_name: string
  report_type: 'fundamental' | 'technical' | 'sector' | 'macro'
  status: 'draft' | 'completed'
  content: string
  sources: ResearchSource[]
  created_at: string
  updated_at: string
}

export interface ResearchSource {
  id: string
  title: string
  url: string
  snippet: string
  relevance_score: number
}

// ─── Chat / Assistant ─────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant' | 'system'

export interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  tool_calls?: ToolCallStep[]
  memory_refs?: MemoryFragment[]
  created_at: string
  is_streaming?: boolean
}

export interface ToolCallStep {
  id: string
  name: string
  input: Record<string, unknown>
  output?: unknown
  status: 'running' | 'completed' | 'failed'
  duration_ms?: number
}

export interface ChatSession {
  id: string
  title: string
  messages: ChatMessage[]
  created_at: string
  updated_at: string
}

// ─── Memory ───────────────────────────────────────────────────────────────────

export interface MemoryFragment {
  id: string
  content: string
  source: string
  category: 'preference' | 'fact' | 'context' | 'portfolio'
  relevance_score: number
  created_at: string
}

// ─── Knowledge Graph ─────────────────────────────────────────────────────────

export interface GraphNode {
  id: string
  label: string
  type: 'company' | 'person' | 'event' | 'concept' | 'ticker'
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label: string
  weight: number
}

export interface KnowledgeGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ─── Vault ─────────────────────────────────────────────────────────────────────

export interface VaultDocument {
  id: string
  name: string
  type: 'pdf' | 'docx' | 'txt' | 'url'
  size_bytes: number
  status: 'indexing' | 'ready' | 'failed'
  chunk_count: number
  created_at: string
}
