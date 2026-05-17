import type { Metadata } from 'next'
import { AvatarStudio } from '@/components/edu/AvatarStudio'

export const metadata: Metadata = { title: 'EduStar — 创作工作室' }

export default function EduPage() {
  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">数字人工作室</h1>
        <p className="text-muted-foreground mt-1">创建您的数字分身，生成 AI 课程视频</p>
      </div>
      <AvatarStudio />
    </div>
  )
}
