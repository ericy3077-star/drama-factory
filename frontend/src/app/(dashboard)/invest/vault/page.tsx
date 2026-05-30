'use client'

import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import {
  Brain,
  Search,
  Plus,
  Trash2,
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  Loader2,
  BookOpen,
  X,
  Tag,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Progress } from '@/components/ui/progress'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { KnowledgeGraph } from '@/components/invest/KnowledgeGraph'
import { apiPost, apiDelete, tokenStorage } from '@/lib/api'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { cn, formatBytes } from '@/lib/utils'
import axios from 'axios'

interface Memory {
  id: string
  content: string
  source: 'chat' | 'document' | 'manual'
  created_at: string
  score?: number
  metadata?: Record<string, unknown>
}

interface UploadResult {
  filename: string
  page_count?: number
  summary?: string
  entities?: string[]
  size: number
}

const SOURCE_LABELS: Record<string, string> = {
  chat: '对话',
  document: '文档',
  manual: '手动',
}

const SOURCE_COLORS: Record<string, string> = {
  chat: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  document: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  manual: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300',
}

function relativeTime(dateStr: string): string {
  try {
    return formatDistanceToNow(new Date(dateStr), { addSuffix: true, locale: zhCN })
  } catch {
    return dateStr
  }
}

export default function VaultPage() {
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [newMemoryOpen, setNewMemoryOpen] = useState(false)
  const [newMemoryContent, setNewMemoryContent] = useState('')
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [isUploading, setIsUploading] = useState(false)
  const [recentUploads, setRecentUploads] = useState<UploadResult[]>([])
  const [latestResult, setLatestResult] = useState<UploadResult | null>(null)

  // Fetch memories
  const { data: memories = [], isLoading } = useQuery<Memory[]>({
    queryKey: ['memories'],
    queryFn: async () => {
      try {
        const res = await axios.get('/api/v1/memories', {
          baseURL: process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000',
          headers: { Authorization: `Bearer ${tokenStorage.getAccess() ?? ''}` },
        })
        return res.data?.data ?? []
      } catch {
        return []
      }
    },
  })

  // Create memory
  const createMutation = useMutation({
    mutationFn: () => apiPost<Memory>('/api/v1/memories', { content: newMemoryContent, source: 'manual' }),
    onSuccess: () => {
      toast.success('记忆已添加')
      setNewMemoryContent('')
      setNewMemoryOpen(false)
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
    onError: () => toast.error('添加失败，请重试'),
  })

  // Delete memory
  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiDelete<void>(`/api/v1/memories/${id}`),
    onSuccess: () => {
      toast.success('记忆已删除')
      setDeletingId(null)
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    },
    onError: () => {
      toast.error('删除失败，请重试')
      setDeletingId(null)
    },
  })

  // File upload
  const uploadFile = useCallback(async (file: File) => {
    setIsUploading(true)
    setUploadProgress(0)
    setLatestResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)
      const token = tokenStorage.getAccess() ?? ''

      const xhr = new XMLHttpRequest()
      xhr.open('POST', `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/invest/vault/upload`)
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)

      await new Promise<void>((resolve, reject) => {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            setUploadProgress(Math.round((e.loaded / e.total) * 100))
          }
        }
        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
          } else {
            reject(new Error(`上传失败: ${xhr.status}`))
          }
        }
        xhr.onerror = () => reject(new Error('网络错误'))
        xhr.send(formData)
      })

      let parsed: Record<string, unknown> = {}
      try {
        parsed = JSON.parse(xhr.responseText)
      } catch {
        // ignore parse error
      }

      const result: UploadResult = {
        filename: file.name,
        size: file.size,
        page_count: (parsed?.data as Record<string, unknown>)?.page_count as number | undefined ?? (parsed?.page_count as number | undefined),
        summary: (parsed?.data as Record<string, unknown>)?.summary as string | undefined ?? (parsed?.summary as string | undefined),
        entities: (parsed?.data as Record<string, unknown>)?.entities as string[] | undefined ?? (parsed?.entities as string[] | undefined),
      }

      setLatestResult(result)
      setRecentUploads((prev) => [result, ...prev].slice(0, 3))
      toast.success(`${file.name} 上传成功`)
      queryClient.invalidateQueries({ queryKey: ['memories'] })
    } catch (err) {
      const msg = err instanceof Error ? err.message : '上传失败'
      toast.error(msg)
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }, [queryClient])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (files) => { if (files[0]) uploadFile(files[0]) },
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    maxSize: 50 * 1024 * 1024,
    maxFiles: 1,
    onDropRejected: (rejected) => {
      rejected.forEach((r) => r.errors.forEach((e) => toast.error(e.message)))
    },
  })

  const filteredMemories = memories.filter((m) =>
    search.trim() === '' || m.content.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-500" />
            记忆管理中心
          </h1>
          <p className="text-muted-foreground mt-1">管理 AI 的专属记忆库，上传文档并构建知识图谱</p>
        </div>
        <Button onClick={() => setNewMemoryOpen(true)} className="gap-2">
          <Plus className="h-4 w-4" />
          新建记忆
        </Button>
      </div>

      {/* Main two-column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left panel — Memory Library */}
        <Card className="flex flex-col">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Brain className="h-4 w-4 text-purple-500" />
                记忆库
              </CardTitle>
              <span className="text-xs text-muted-foreground">
                共 {filteredMemories.length} 条记忆
              </span>
            </div>
            <div className="relative mt-2">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="搜索记忆..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <ScrollArea className="h-[460px]">
              <div className="p-4 space-y-3">
                {isLoading ? (
                  <div className="flex justify-center py-10">
                    <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                  </div>
                ) : filteredMemories.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 space-y-3 text-center">
                    <Brain className="h-10 w-10 text-muted-foreground/40" />
                    <p className="text-sm font-medium text-muted-foreground">暂无记忆</p>
                    <p className="text-xs text-muted-foreground max-w-[220px]">
                      AI 助手会自动学习您的投资偏好，形成专属记忆
                    </p>
                  </div>
                ) : (
                  filteredMemories.map((memory) => (
                    <div
                      key={memory.id}
                      className="group rounded-lg border p-3 space-y-2 hover:border-border/80 transition-colors"
                    >
                      <div className="flex items-start justify-between gap-2">
                        <p className="text-sm leading-relaxed flex-1">
                          {memory.content.slice(0, 120)}
                          {memory.content.length > 120 && '…'}
                        </p>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-6 w-6 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive"
                          onClick={() => {
                            setDeletingId(memory.id)
                            deleteMutation.mutate(memory.id)
                          }}
                          disabled={deletingId === memory.id}
                        >
                          {deletingId === memory.id ? (
                            <Loader2 className="h-3.5 w-3.5 animate-spin" />
                          ) : (
                            <Trash2 className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span
                            className={cn(
                              'text-[10px] px-1.5 py-0.5 rounded font-medium',
                              SOURCE_COLORS[memory.source] ?? 'bg-muted text-muted-foreground',
                            )}
                          >
                            {SOURCE_LABELS[memory.source] ?? memory.source}
                          </span>
                          {memory.score !== undefined && (
                            <span className="flex items-center gap-1 text-xs text-muted-foreground">
                              <Tag className="h-3 w-3" />
                              {memory.score.toFixed(2)}
                            </span>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {relativeTime(memory.created_at)}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Right panel — Upload & Index */}
        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Upload className="h-4 w-4 text-blue-500" />
                上传文档
              </CardTitle>
              <CardDescription>支持 PDF、DOCX、TXT，最大 50MB</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Drop zone */}
              <div
                {...getRootProps()}
                className={cn(
                  'rounded-xl border-2 border-dashed p-8 text-center cursor-pointer transition-colors',
                  isDragActive
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50 hover:bg-accent/30',
                  isUploading && 'pointer-events-none opacity-60',
                )}
              >
                <input {...getInputProps()} />
                {isUploading ? (
                  <div className="space-y-3">
                    <Loader2 className="h-8 w-8 mx-auto text-primary animate-spin" />
                    <p className="text-sm font-medium">正在上传并解析...</p>
                    <Progress value={uploadProgress} className="h-1.5 max-w-[200px] mx-auto" />
                    <p className="text-xs text-muted-foreground">{uploadProgress}%</p>
                  </div>
                ) : (
                  <>
                    <Upload
                      className={cn(
                        'h-8 w-8 mx-auto mb-3',
                        isDragActive ? 'text-primary' : 'text-muted-foreground',
                      )}
                    />
                    <p className="text-sm font-medium">
                      {isDragActive ? '释放以上传' : '拖放文件到此处，或点击选择'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      PDF · DOCX · TXT · 最大 50MB
                    </p>
                  </>
                )}
              </div>

              {/* Latest upload result */}
              {latestResult && (
                <div className="rounded-lg border border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-950/30 p-4 space-y-3">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-600 dark:text-green-400 shrink-0" />
                    <p className="text-sm font-medium text-green-700 dark:text-green-300">
                      解析完成
                    </p>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-5 w-5 ml-auto"
                      onClick={() => setLatestResult(null)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="space-y-1.5 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <FileText className="h-3 w-3" />
                      <span className="font-medium text-foreground truncate">{latestResult.filename}</span>
                      <span>· {formatBytes(latestResult.size)}</span>
                      {latestResult.page_count && <span>· {latestResult.page_count} 页</span>}
                    </div>
                    {latestResult.summary && (
                      <p className="leading-relaxed text-foreground/80">{latestResult.summary}</p>
                    )}
                    {latestResult.entities && latestResult.entities.length > 0 && (
                      <div className="flex flex-wrap gap-1 pt-1">
                        {latestResult.entities.slice(0, 8).map((e) => (
                          <Badge key={e} variant="secondary" className="text-[10px]">
                            {e}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent uploads */}
          {recentUploads.length > 0 && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-muted-foreground">本次会话上传</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {recentUploads.map((upload, i) => (
                  <div key={i} className="flex items-center gap-3 rounded-md border p-2.5">
                    <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm truncate font-medium">{upload.filename}</p>
                      <p className="text-xs text-muted-foreground">{formatBytes(upload.size)}</p>
                    </div>
                    {upload.page_count && (
                      <span className="text-xs text-muted-foreground shrink-0">{upload.page_count}页</span>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      <Separator />

      {/* Knowledge Graph section */}
      <div className="space-y-3">
        <div>
          <h2 className="text-base font-semibold flex items-center gap-2">
            <BookOpen className="h-4 w-4 text-blue-500" />
            知识图谱预览
          </h2>
          <p className="text-sm text-muted-foreground mt-0.5">基于您的文档和对话自动构建的实体关系网络</p>
        </div>
        <KnowledgeGraph />
      </div>

      {/* New memory dialog */}
      <Dialog open={newMemoryOpen} onOpenChange={setNewMemoryOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-500" />
              新建记忆
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3 py-2">
            <Textarea
              placeholder="输入您想让 AI 记住的内容..."
              value={newMemoryContent}
              onChange={(e) => setNewMemoryContent(e.target.value)}
              className="min-h-[120px] resize-none"
            />
            <p className="text-xs text-muted-foreground">
              手动记忆将被标记为 "手动" 来源，AI 在后续对话中会优先参考这些内容
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setNewMemoryOpen(false)}>取消</Button>
            <Button
              disabled={!newMemoryContent.trim() || createMutation.isPending}
              onClick={() => createMutation.mutate()}
            >
              {createMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              保存记忆
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
