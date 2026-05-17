'use client'

import { Brain, RefreshCw, Tag } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { apiGet } from '@/lib/api'
import type { MemoryFragment } from '@/types/invest'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const CATEGORY_LABELS = {
  preference: '偏好',
  fact: '事实',
  context: '上下文',
  portfolio: '持仓',
}

const CATEGORY_COLORS: Record<string, string> = {
  preference: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  fact: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  context: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
  portfolio: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
}

interface MemoryPanelProps {
  vertical?: 'invest' | 'edu'
}

export function MemoryPanel({ vertical = 'invest' }: MemoryPanelProps) {
  const { data: memories = [], refetch, isFetching } = useQuery({
    queryKey: ['memories', vertical],
    queryFn: () => apiGet<MemoryFragment[]>(`/api/v1/${vertical}/memory`),
  })

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between">
        <CardTitle className="text-base flex items-center gap-2">
          <Brain className="h-4 w-4 text-purple-500" />
          记忆面板
        </CardTitle>
        <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-80">
          <div className="p-3 space-y-2">
            {memories.length === 0 && (
              <div className="text-center py-8 space-y-2">
                <Brain className="h-6 w-6 mx-auto text-muted-foreground" />
                <p className="text-sm text-muted-foreground">暂无记忆片段</p>
                <p className="text-xs text-muted-foreground">与 AI 对话后，系统会自动提取关键记忆</p>
              </div>
            )}
            {memories.map((m) => (
              <div key={m.id} className="rounded-md border p-3 space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm leading-relaxed">{m.content}</p>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${CATEGORY_COLORS[m.category]}`}>
                    {CATEGORY_LABELS[m.category]}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Tag className="h-3 w-3" />
                    {m.source}
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(m.created_at), { addSuffix: true, locale: zhCN })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
