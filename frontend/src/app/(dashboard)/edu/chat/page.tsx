import type { Metadata } from 'next'
import { GraduationCap } from 'lucide-react'
import { ChatAssistant } from '@/components/invest/ChatAssistant'

export const metadata: Metadata = { title: 'EduStar — AI 教学助手' }

export default function EduChatPage() {
  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto">
      <div className="mb-4 shrink-0">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <GraduationCap className="h-6 w-6 text-purple-500" />
          EduStar AI 助手
        </h1>
        <p className="text-muted-foreground mt-1">
          帮您创作课程脚本、设计学习路径、优化教学内容
        </p>
      </div>
      <div className="flex-1 min-h-0">
        <ChatAssistant vertical="edu" />
      </div>
    </div>
  )
}
