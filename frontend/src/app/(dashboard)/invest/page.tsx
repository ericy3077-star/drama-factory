'use client'

import { useQuery } from '@tanstack/react-query'
import type { Metadata } from 'next'
import { FeedCard } from '@/components/invest/FeedCard'
import { apiPost } from '@/lib/api'
import { useInvestStore } from '@/store/investStore'
import type { FeedItem } from '@/types/invest'
import { Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'

async function fetchFeed(tickers: string[]): Promise<FeedItem[]> {
  return apiPost<FeedItem[]>('/api/v1/invest/feed', {
    tickers,
    topics: ['A股', '宏观经济', '科技', 'AI'],
    limit: 30,
  })
}

export default function InvestPage() {
  const watchlistTickers = useInvestStore((s) => s.watchlistTickers)

  const { data: items = [], isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['feed', watchlistTickers],
    queryFn: () => fetchFeed(watchlistTickers),
    staleTime: 5 * 60 * 1000,  // 5 min
    refetchInterval: 10 * 60 * 1000,  // auto-refresh every 10 min
  })

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">信息流</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            AI 实时分析 · 情感评分 · 每 10 分钟刷新
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
        >
          {isFetching ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-2">刷新</span>
        </Button>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-20 text-muted-foreground">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          正在获取最新资讯...
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive text-center">
          获取信息流失败，请检查网络连接或重新刷新。
          <Button variant="link" size="sm" onClick={() => refetch()} className="ml-2 h-auto p-0">
            重试
          </Button>
        </div>
      )}

      {!isLoading && !isError && items.length === 0 && (
        <div className="text-center py-16 text-muted-foreground">
          <p>暂无信息，请先在自选股中添加关注标的。</p>
        </div>
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <FeedCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  )
}
