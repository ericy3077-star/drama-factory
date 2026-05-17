import type { Metadata } from 'next'
import { LearnerDashboard } from '@/components/edu/LearnerDashboard'

export const metadata: Metadata = { title: 'EduStar — 数据分析' }

export default function AnalyticsPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">学员数据</h1>
        <p className="text-muted-foreground mt-1">课程完成率、学习时长和用户行为分析</p>
      </div>
      <LearnerDashboard />
    </div>
  )
}
