'use client'

import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { ExternalLink, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { FeedItem } from '@/types/invest'

const CATEGORY_LABELS: Record<string, string> = {
  market_news: '市场',
  earnings: '财报',
  macro: '宏观',
  crypto: '加密',
  ipo: 'IPO',
  analysis: '分析',
}

interface FeedCardProps {
  item: FeedItem
}

export function FeedCard({ item }: FeedCardProps) {
  const sentimentIcon =
    item.sentiment === 'positive' ? TrendingUp :
    item.sentiment === 'negative' ? TrendingDown : Minus

  const SentimentIcon = sentimentIcon

  const sentimentColor =
    item.sentiment === 'positive' ? 'text-green-500' :
    item.sentiment === 'negative' ? 'text-red-500' : 'text-slate-400'

  const sentimentBadge =
    item.sentiment === 'positive' ? 'success' :
    item.sentiment === 'negative' ? 'destructive' : 'secondary'

  return (
    <Card className="hover:shadow-md transition-shadow group">
      <CardContent className="p-4">
        <div className="flex gap-4">
          {item.image_url && (
            <div className="shrink-0 hidden sm:block">
              <img
                src={item.image_url}
                alt={item.title}
                className="h-20 w-32 rounded-md object-cover"
              />
            </div>
          )}
          <div className="flex-1 min-w-0 space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-2 flex-wrap">
                <Badge variant="outline" className="text-xs shrink-0">
                  {CATEGORY_LABELS[item.category] ?? item.category}
                </Badge>
                {item.tickers.map((t) => (
                  <Badge key={t} variant="secondary" className="text-xs font-mono">
                    {t}
                  </Badge>
                ))}
              </div>
              <Badge variant={sentimentBadge as 'success' | 'destructive' | 'secondary'} className="shrink-0 flex items-center gap-1">
                <SentimentIcon className="h-3 w-3" />
                {Math.round(Math.abs(item.sentiment_score) * 100)}%
              </Badge>
            </div>

            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="group/link"
            >
              <h3 className="text-sm font-semibold leading-snug group-hover/link:text-primary transition-colors line-clamp-2">
                {item.title}
              </h3>
            </a>

            <p className="text-xs text-muted-foreground line-clamp-2">{item.summary}</p>

            {item.ai_insights && (
              <div className="rounded-md bg-blue-50 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900 px-3 py-2">
                <p className="text-xs text-blue-700 dark:text-blue-300">
                  <span className="font-medium">AI 洞察: </span>
                  {item.ai_insights}
                </p>
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <span className="font-medium">{item.source}</span>
                <span>·</span>
                <span>
                  {formatDistanceToNow(new Date(item.published_at), { addSuffix: true, locale: zhCN })}
                </span>
              </div>
              <a
                href={item.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <ExternalLink className="h-3.5 w-3.5 text-muted-foreground hover:text-foreground" />
              </a>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
