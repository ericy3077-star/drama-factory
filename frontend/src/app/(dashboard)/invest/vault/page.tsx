import type { Metadata } from 'next'
import { FileUpload } from '@/components/shared/FileUpload'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export const metadata: Metadata = { title: 'InvestMind — 知识库' }

export default function VaultPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">知识库</h1>
        <p className="text-muted-foreground mt-1">上传文件，让 AI 助手理解您的私有数据</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>上传文档</CardTitle>
          <CardDescription>支持 PDF、Word、TXT 格式，或直接粘贴 URL</CardDescription>
        </CardHeader>
        <CardContent>
          <FileUpload
            accept={{ 'application/pdf': ['.pdf'], 'application/msword': ['.doc', '.docx'], 'text/plain': ['.txt'] }}
            maxSize={50 * 1024 * 1024}
            uploadUrl="/api/v1/invest/vault/upload"
          />
        </CardContent>
      </Card>
    </div>
  )
}
