import type { Metadata } from 'next'
import { ResearchPanel } from '@/components/invest/ResearchPanel'

export const metadata: Metadata = { title: 'InvestMind — 深度研究' }

export default function ResearchPage() {
  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold">深度研究</h1>
        <p className="text-muted-foreground mt-1">AI 生成个股/行业深度研究报告</p>
      </div>
      <ResearchPanel />
    </div>
  )
}
