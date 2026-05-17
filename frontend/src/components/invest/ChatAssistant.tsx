'use client'

import { useRef, useEffect } from 'react'
import { Send, StopCircle, Bot, User, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { useChat } from '@/hooks/useChat'
import type { ChatMessage, ToolCallStep, MemoryFragment } from '@/types/invest'
import { useState } from 'react'

interface ChatAssistantProps {
  vertical: 'invest' | 'edu'
}

function ToolCallBadge({ step }: { step: ToolCallStep }) {
  const [open, setOpen] = useState(false)

  const statusColor =
    step.status === 'completed' ? 'text-green-600 dark:text-green-400' :
    step.status === 'failed' ? 'text-red-600 dark:text-red-400' :
    'text-yellow-600 dark:text-yellow-400'

  return (
    <div className="rounded-md border border-border bg-muted/50 text-xs overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left hover:bg-muted/80 transition-colors"
      >
        {step.status === 'running' ? (
          <Loader2 className="h-3 w-3 animate-spin text-yellow-500 shrink-0" />
        ) : open ? (
          <ChevronDown className="h-3 w-3 shrink-0" />
        ) : (
          <ChevronRight className="h-3 w-3 shrink-0" />
        )}
        <span className="font-mono font-medium">{step.name}</span>
        <span className={cn('ml-auto', statusColor)}>
          {step.status === 'running' ? '执行中' : step.status === 'completed' ? '完成' : '失败'}
        </span>
        {step.duration_ms && (
          <span className="text-muted-foreground">{step.duration_ms}ms</span>
        )}
      </button>
      {open && (
        <div className="px-3 py-2 border-t border-border space-y-2">
          <div>
            <p className="text-muted-foreground mb-1">输入:</p>
            <pre className="bg-background rounded p-2 overflow-x-auto text-[11px]">
              {JSON.stringify(step.input, null, 2)}
            </pre>
          </div>
          {step.output !== undefined && (
            <div>
              <p className="text-muted-foreground mb-1">输出:</p>
              <pre className="bg-background rounded p-2 overflow-x-auto text-[11px]">
                {JSON.stringify(step.output, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MemoryRef({ fragment }: { fragment: MemoryFragment }) {
  return (
    <div className="flex items-start gap-2 rounded-md border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/30 px-3 py-2 text-xs">
      <Badge variant="outline" className="text-[10px] shrink-0 mt-0.5">记忆</Badge>
      <p className="text-blue-700 dark:text-blue-300">{fragment.content}</p>
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === 'user'

  return (
    <div className={cn('flex gap-3 animate-fade-in', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex h-8 w-8 shrink-0 items-center justify-center rounded-full',
          isUser ? 'bg-primary text-primary-foreground' : 'bg-muted border',
        )}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={cn('flex max-w-[80%] flex-col gap-2', isUser && 'items-end')}>
        {/* Tool calls */}
        {message.tool_calls && message.tool_calls.length > 0 && (
          <div className="w-full space-y-1.5">
            {message.tool_calls.map((step) => (
              <ToolCallBadge key={step.id} step={step} />
            ))}
          </div>
        )}

        {/* Memory refs */}
        {message.memory_refs && message.memory_refs.length > 0 && (
          <div className="w-full space-y-1">
            {message.memory_refs.map((f) => (
              <MemoryRef key={f.id} fragment={f} />
            ))}
          </div>
        )}

        {/* Content */}
        {message.content && (
          <div
            className={cn(
              'rounded-2xl px-4 py-3 text-sm',
              isUser
                ? 'bg-primary text-primary-foreground rounded-tr-sm'
                : 'bg-muted rounded-tl-sm',
            )}
          >
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
              </div>
            )}
            {message.is_streaming && (
              <span className="inline-block w-0.5 h-4 bg-current ml-0.5 align-text-bottom animate-cursor-blink" />
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export function ChatAssistant({ vertical }: ChatAssistantProps) {
  const { messages, input, setInput, isStreaming, send, stop } = useChat(vertical)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (input.trim() && !isStreaming) send()
    }
  }

  const SUGGESTIONS = vertical === 'invest'
    ? ['分析苹果公司近期财报', '当前美联储政策对科技股的影响', '比较 NVDA 和 AMD 的竞争优势']
    : ['帮我写一段 5 分钟的 Python 入门课脚本', '如何提高课程完成率', '设计一个机器学习基础课程大纲']

  return (
    <div className="flex flex-col h-full border rounded-xl overflow-hidden bg-background">
      {/* Messages */}
      <ScrollArea className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-64 space-y-4">
            <Bot className="h-12 w-12 text-muted-foreground" />
            <div className="text-center">
              <p className="font-medium">
                {vertical === 'invest' ? 'InvestMind AI 助手' : 'EduStar AI 助手'}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {vertical === 'invest' ? '我可以帮您分析市场、研究个股、解读财报' : '我可以帮您创作课程脚本、设计课程结构'}
              </p>
            </div>
            <div className="grid gap-2 w-full max-w-sm">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => { setInput(s); textareaRef.current?.focus() }}
                  className="text-left text-xs rounded-lg border p-3 hover:bg-accent transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-6 pb-4">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex gap-2 items-end">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入问题... (Enter 发送，Shift+Enter 换行)"
            className="min-h-[44px] max-h-32 resize-none"
            rows={1}
          />
          {isStreaming ? (
            <Button variant="outline" size="icon" onClick={stop} className="shrink-0">
              <StopCircle className="h-4 w-4 text-red-500" />
            </Button>
          ) : (
            <Button
              size="icon"
              disabled={!input.trim()}
              onClick={send}
              className="shrink-0"
            >
              <Send className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}
