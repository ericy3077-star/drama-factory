'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Video, Loader2, Upload, Play, Download, CheckCircle2,
  AlertCircle, Clock, Wand2, User
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { apiGet, apiPost } from '@/lib/api'
import { useTaskStatus } from '@/hooks/useTaskStatus'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { DigitalAvatar, VideoJob, GenerateVideoRequest } from '@/types/edu'
import { toast } from 'sonner'
import { formatDuration } from '@/lib/utils'

const AVATAR_STATUS_CONFIG = {
  creating: { label: '创建中', icon: Loader2, color: 'warning', spin: true },
  training: { label: '训练中', icon: Loader2, color: 'warning', spin: true },
  ready: { label: '就绪', icon: CheckCircle2, color: 'success', spin: false },
  failed: { label: '失败', icon: AlertCircle, color: 'destructive', spin: false },
} as const

const VIDEO_STATUS_CONFIG = {
  queued: { label: '排队中', color: 'secondary' },
  processing: { label: '生成中', color: 'warning' },
  completed: { label: '完成', color: 'success' },
  failed: { label: '失败', color: 'destructive' },
} as const

function AvatarCard({ avatar, onSelect, selected }: { avatar: DigitalAvatar; onSelect: () => void; selected: boolean }) {
  const config = AVATAR_STATUS_CONFIG[avatar.status]
  const StatusIcon = config.icon

  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-xl border p-4 transition-all ${
        selected ? 'border-primary bg-primary/5 ring-2 ring-primary/20' : 'hover:border-primary/50 hover:bg-accent/50'
      }`}
    >
      <div className="flex items-start gap-3">
        <div className="h-14 w-14 rounded-lg overflow-hidden bg-muted shrink-0 flex items-center justify-center">
          {avatar.thumbnail_url ? (
            <img src={avatar.thumbnail_url} alt={avatar.name} className="object-cover w-full h-full" />
          ) : (
            <User className="h-6 w-6 text-muted-foreground" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2">
            <p className="font-medium text-sm truncate">{avatar.name}</p>
            <Badge variant={config.color as 'warning' | 'success' | 'destructive'} className="shrink-0 flex items-center gap-1 text-xs">
              <StatusIcon className={`h-3 w-3 ${config.spin ? 'animate-spin' : ''}`} />
              {config.label}
            </Badge>
          </div>
          {avatar.description && (
            <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{avatar.description}</p>
          )}
        </div>
      </div>
    </button>
  )
}

function VideoJobRow({ job }: { job: VideoJob }) {
  const config = VIDEO_STATUS_CONFIG[job.status]
  const { progress } = useTaskStatus(job.status !== 'completed' && job.status !== 'failed' ? job.id : undefined)
  const currentProgress = progress ?? job.progress

  return (
    <div className="rounded-lg border p-3 space-y-2">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium line-clamp-2">{job.script.slice(0, 80)}...</p>
        <Badge variant={config.color as 'secondary' | 'warning' | 'success' | 'destructive'} className="shrink-0 text-xs">
          {config.label}
        </Badge>
      </div>
      {(job.status === 'processing' || job.status === 'queued') && (
        <Progress value={currentProgress} className="h-1.5" />
      )}
      {job.status === 'completed' && job.video_url && (
        <div className="flex items-center gap-2">
          {job.duration_seconds && (
            <span className="text-xs text-muted-foreground">{formatDuration(job.duration_seconds)}</span>
          )}
          <a href={job.video_url} target="_blank" rel="noopener noreferrer" className="ml-auto">
            <Button variant="outline" size="sm" className="h-7 gap-1.5">
              <Play className="h-3 w-3" /> 预览
            </Button>
          </a>
          <a href={job.video_url} download>
            <Button variant="outline" size="sm" className="h-7 gap-1.5">
              <Download className="h-3 w-3" /> 下载
            </Button>
          </a>
        </div>
      )}
    </div>
  )
}

function CreateAvatarDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [photoAssetId, setPhotoAssetId] = useState('')

  const mutation = useMutation({
    mutationFn: () =>
      apiPost<DigitalAvatar>('/api/v1/edu/avatars', {
        name,
        description,
        photo_asset_id: photoAssetId,
      }),
    onSuccess: () => {
      toast.success('数字人创建任务已提交，训练中...')
      setOpen(false)
      setName(''); setDescription(''); setPhotoAssetId('')
      onCreated()
    },
    onError: () => toast.error('创建失败，请稍后重试'),
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2">
          <Plus className="h-4 w-4" /> 新建数字人
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>创建数字分身</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label>名称</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="例如：王老师数字人" />
          </div>
          <div className="space-y-2">
            <Label>简介（可选）</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="简单描述这个数字人的用途" rows={2} />
          </div>
          <div className="space-y-2">
            <Label>照片素材</Label>
            <div className="rounded-lg border-2 border-dashed border-border p-6 text-center space-y-2">
              <Upload className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">点击上传正面照片（建议高清免冠照）</p>
              <Button variant="outline" size="sm">选择文件</Button>
            </div>
            <Input
              placeholder="或输入已上传的素材 ID"
              value={photoAssetId}
              onChange={(e) => setPhotoAssetId(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={() => mutation.mutate()} disabled={!name || !photoAssetId || mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            开始创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function AvatarStudio() {
  const queryClient = useQueryClient()
  const [selectedAvatar, setSelectedAvatar] = useState<DigitalAvatar | null>(null)
  const [script, setScript] = useState('')

  const { data: avatars = [], refetch: refetchAvatars } = useQuery({
    queryKey: ['avatars'],
    queryFn: () => apiGet<DigitalAvatar[]>('/api/v1/edu/avatars'),
  })

  const { data: videoJobs = [], refetch: refetchJobs } = useQuery({
    queryKey: ['video-jobs', selectedAvatar?.id],
    queryFn: () => apiGet<VideoJob[]>(`/api/v1/edu/videos?avatar_id=${selectedAvatar!.id}`),
    enabled: !!selectedAvatar,
  })

  // Subscribe to task updates via WebSocket
  useWebSocket('task_progress', () => {
    refetchJobs()
  })

  const generateMutation = useMutation({
    mutationFn: (req: GenerateVideoRequest) => apiPost<VideoJob>('/api/v1/edu/videos', req),
    onSuccess: () => {
      toast.success('视频生成任务已提交')
      setScript('')
      refetchJobs()
    },
    onError: () => toast.error('提交失败，请稍后重试'),
  })

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: avatar list */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">我的数字人</h3>
          <CreateAvatarDialog onCreated={refetchAvatars} />
        </div>
        <ScrollArea className="h-[480px] pr-1">
          <div className="space-y-3">
            {avatars.length === 0 && (
              <div className="rounded-xl border-2 border-dashed border-border p-8 text-center space-y-2">
                <User className="h-8 w-8 mx-auto text-muted-foreground" />
                <p className="text-sm text-muted-foreground">还没有数字人，立即创建</p>
              </div>
            )}
            {avatars.map((a) => (
              <AvatarCard
                key={a.id}
                avatar={a}
                selected={selectedAvatar?.id === a.id}
                onSelect={() => setSelectedAvatar(a)}
              />
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Right: generate + jobs */}
      <div className="lg:col-span-2 space-y-4">
        {selectedAvatar ? (
          <>
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Wand2 className="h-4 w-4 text-purple-500" />
                  生成视频 · {selectedAvatar.name}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <Label>课程脚本</Label>
                  <Textarea
                    value={script}
                    onChange={(e) => setScript(e.target.value)}
                    placeholder="输入数字人要朗读的脚本内容，支持 SSML 标签控制语速和停顿..."
                    rows={6}
                  />
                  <p className="text-xs text-muted-foreground text-right">{script.length} 字</p>
                </div>
                <div className="flex justify-end">
                  <Button
                    disabled={!script.trim() || generateMutation.isPending || selectedAvatar.status !== 'ready'}
                    onClick={() =>
                      generateMutation.mutate({
                        avatar_id: selectedAvatar.id,
                        script,
                      })
                    }
                    className="gap-2"
                  >
                    {generateMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Video className="h-4 w-4" />
                    )}
                    生成视频
                  </Button>
                </div>
                {selectedAvatar.status !== 'ready' && (
                  <p className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
                    <Clock className="h-3.5 w-3.5" />
                    数字人尚未就绪，就绪后可生成视频
                  </p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">生成记录</CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-72">
                  <div className="space-y-3">
                    {videoJobs.length === 0 && (
                      <p className="text-sm text-muted-foreground text-center py-8">暂无生成记录</p>
                    )}
                    {videoJobs.map((job) => (
                      <VideoJobRow key={job.id} job={job} />
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </>
        ) : (
          <div className="flex h-full min-h-64 items-center justify-center rounded-xl border-2 border-dashed border-border">
            <div className="text-center space-y-2">
              <Video className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">请先选择一个数字人</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
