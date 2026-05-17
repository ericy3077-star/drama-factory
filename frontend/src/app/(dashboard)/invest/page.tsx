import type { Metadata } from 'next'
import { FeedCard } from '@/components/invest/FeedCard'

export const metadata: Metadata = { title: 'InvestMind — 信息流' }

// Server Component — data fetched server-side in real app
async function getFeedItems() {
  // Placeholder data; replace with actual API call
  return [
    {
      id: '1',
      title: '美联储维持利率不变，暗示年内可能降息两次',
      summary:
        'FOMC 会议纪要显示委员们对通胀回落轨迹持谨慎乐观态度，市场预期 9 月为首次降息窗口。',
      source: 'Reuters',
      source_url: 'https://reuters.com',
      category: 'macro' as const,
      tickers: ['SPY', 'QQQ', 'TLT'],
      sentiment: 'positive' as const,
      sentiment_score: 0.65,
      published_at: new Date().toISOString(),
    },
    {
      id: '2',
      title: 'NVIDIA Q1 业绩超预期，数据中心收入同比增长 427%',
      summary:
        'NVDA 财报季再次亮眼，AI 芯片需求持续强劲。公司同时宣布 100 亿美元回购计划，盘后股价涨逾 8%。',
      source: 'Bloomberg',
      source_url: 'https://bloomberg.com',
      category: 'earnings' as const,
      tickers: ['NVDA'],
      sentiment: 'positive' as const,
      sentiment_score: 0.92,
      published_at: new Date(Date.now() - 3600_000).toISOString(),
    },
    {
      id: '3',
      title: '比特币跌破 6 万美元关口，市场情绪趋于谨慎',
      summary: '链上数据显示大额持仓者持续减持，现货 ETF 周净流出达 4.2 亿美元。',
      source: 'CoinDesk',
      source_url: 'https://coindesk.com',
      category: 'crypto' as const,
      tickers: ['BTC', 'ETH'],
      sentiment: 'negative' as const,
      sentiment_score: -0.55,
      published_at: new Date(Date.now() - 7200_000).toISOString(),
    },
  ]
}

export default async function InvestPage() {
  const items = await getFeedItems()

  return (
    <div className="max-w-4xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">信息流</h1>
        <p className="text-sm text-muted-foreground">AI 实时分析 · 情感评分</p>
      </div>
      <div className="space-y-3">
        {items.map((item) => (
          <FeedCard key={item.id} item={item} />
        ))}
      </div>
    </div>
  )
}
