'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, BookOpen, ChevronRight, Loader2, GripVertical, Pencil } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from '@/components/ui/dialog'
import { apiGet, apiPost } from '@/lib/api'
import type { Course } from '@/types/edu'
import { toast } from 'sonner'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

const STATUS_CONFIG = {
  draft: { label: '草稿', variant: 'secondary' },
  published: { label: '已发布', variant: 'success' },
  archived: { label: '已归档', variant: 'outline' },
} as const

function CreateCourseDialog({ onCreated }: { onCreated: () => void }) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  const mutation = useMutation({
    mutationFn: () => apiPost<Course>('/api/v1/edu/courses', { title, description }),
    onSuccess: () => {
      toast.success('课程创建成功')
      setOpen(false); setTitle(''); setDescription('')
      onCreated()
    },
    onError: () => toast.error('创建失败'),
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className="gap-2"><Plus className="h-4 w-4" />新建课程</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader><DialogTitle>新建课程</DialogTitle></DialogHeader>
        <div className="space-y-4 py-2">
          <div className="space-y-2">
            <Label>课程标题</Label>
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例如：Python 零基础入门" />
          </div>
          <div className="space-y-2">
            <Label>课程简介</Label>
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="简单描述课程内容和目标学员" rows={3} />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>取消</Button>
          <Button onClick={() => mutation.mutate()} disabled={!title || mutation.isPending}>
            {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}创建
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function CourseRow({ course, onSelect, selected }: { course: Course; onSelect: () => void; selected: boolean }) {
  const config = STATUS_CONFIG[course.status]
  return (
    <button
      onClick={onSelect}
      className={`w-full text-left rounded-lg border p-4 transition-all ${
        selected ? 'border-primary bg-primary/5' : 'hover:bg-accent/50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="font-medium text-sm truncate">{course.title}</p>
            <Badge variant={config.variant as 'secondary' | 'success' | 'outline'} className="text-xs shrink-0">
              {config.label}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground line-clamp-1">{course.description}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
            <span>{course.chapters.length} 章节</span>
            <span>{course.learner_count} 学员</span>
            <span>更新于 {formatDistanceToNow(new Date(course.updated_at), { addSuffix: true, locale: zhCN })}</span>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0 mt-1" />
      </div>
    </button>
  )
}

export function CourseEditor() {
  const queryClient = useQueryClient()
  const [selectedCourse, setSelectedCourse] = useState<Course | null>(null)

  const { data: courses = [], refetch } = useQuery({
    queryKey: ['courses'],
    queryFn: () => apiGet<Course[]>('/api/v1/edu/courses'),
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
      {/* Course list */}
      <div className="md:col-span-2 space-y-4">
        <div className="flex items-center justify-between">
          <p className="font-semibold text-sm">{courses.length} 个课程</p>
          <CreateCourseDialog onCreated={refetch} />
        </div>
        <div className="space-y-2">
          {courses.length === 0 && (
            <div className="rounded-lg border-2 border-dashed border-border p-8 text-center space-y-2">
              <BookOpen className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">创建您的第一个课程</p>
            </div>
          )}
          {courses.map((c) => (
            <CourseRow key={c.id} course={c} selected={selectedCourse?.id === c.id} onSelect={() => setSelectedCourse(c)} />
          ))}
        </div>
      </div>

      {/* Chapter editor */}
      <div className="md:col-span-3">
        {selectedCourse ? (
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">{selectedCourse.title}</CardTitle>
                <Button variant="outline" size="sm" className="gap-1.5 h-8">
                  <Pencil className="h-3.5 w-3.5" /> 编辑信息
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium">章节列表</p>
                  <Button variant="outline" size="sm" className="gap-1.5 h-8">
                    <Plus className="h-3.5 w-3.5" /> 添加章节
                  </Button>
                </div>
                {selectedCourse.chapters.length === 0 ? (
                  <div className="rounded-lg border-2 border-dashed border-border p-6 text-center">
                    <p className="text-sm text-muted-foreground">暂无章节，点击添加</p>
                  </div>
                ) : (
                  selectedCourse.chapters.map((ch) => (
                    <div key={ch.id} className="rounded-lg border">
                      <div className="flex items-center gap-2 px-3 py-2 bg-muted/50">
                        <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
                        <span className="text-sm font-medium flex-1">{ch.title}</span>
                        <Badge variant="secondary" className="text-xs">{ch.lessons.length} 课时</Badge>
                      </div>
                      {ch.lessons.length > 0 && (
                        <div className="divide-y">
                          {ch.lessons.map((lesson) => (
                            <div key={lesson.id} className="flex items-center gap-2 px-4 py-2 text-sm">
                              <GripVertical className="h-3.5 w-3.5 text-muted-foreground cursor-grab" />
                              <span className="flex-1 text-muted-foreground">{lesson.title}</span>
                              <Badge variant="outline" className="text-xs">{lesson.type}</Badge>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="flex h-full min-h-64 items-center justify-center rounded-lg border-2 border-dashed border-border">
            <div className="text-center space-y-2">
              <BookOpen className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">选择一个课程开始编辑</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
