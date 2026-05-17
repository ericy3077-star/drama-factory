import type { Metadata } from 'next'
import { ChatAssistant } from '@/components/invest/ChatAssistant'

export const metadata: Metadata = { title: 'InvestMind — AI 助手' }

export default function AssistantPage() {
  return (
    <div className="h-full flex flex-col max-w-4xl mx-auto">
      <div className="mb-4 shrink-0">
        <h1 className="text-2xl font-bold">AI 投资助手</h1>
        <p className="text-muted-foreground mt-1">与 AI 实时对话，获取投资洞见</p>
      </div>
      <div className="flex-1 min-h-0">
        <ChatAssistant vertical="invest" />
      </div>
    </div>
  )
}
