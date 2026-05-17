'use client'

import { CheckCircle2, XCircle, Loader2, Clock, Ban } from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { TaskStatus as TaskStatusType } from '@/types/api'

interface TaskStatusProps {
  status: TaskStatusType
  progress?: number
  message?: string
  className?: string
  compact?: boolean
}

const STATUS_CONFIG: Record<TaskStatusType, { icon: React.ElementType; label: string; color: string; spin: boolean }> = {
  pending: { icon: Clock, label: '等待中', color: 'text-slate-500', spin: false },
  running: { icon: Loader2, label: '执行中', color: 'text-blue-500', spin: true },
  completed: { icon: CheckCircle2, label: '已完成', color: 'text-green-500', spin: false },
  failed: { icon: XCircle, label: '失败', color: 'text-red-500', spin: false },
  cancelled: { icon: Ban, label: '已取消', color: 'text-slate-400', spin: false },
}

export function TaskStatus({ status, progress, message, className, compact = false }: TaskStatusProps) {
  const config = STATUS_CONFIG[status]
  const Icon = config.icon

  if (compact) {
    return (
      <div className={cn('flex items-center gap-1.5', className)}>
        <Icon className={cn('h-3.5 w-3.5 shrink-0', config.color, config.spin && 'animate-spin')} />
        <span className={cn('text-xs', config.color)}>{config.label}</span>
      </div>
    )
  }

  return (
    <div className={cn('rounded-lg border p-4 space-y-3', className)}>
      <div className="flex items-center gap-2">
        <Icon className={cn('h-4 w-4 shrink-0', config.color, config.spin && 'animate-spin')} />
        <span className="text-sm font-medium">{config.label}</span>
        {message && <span className="text-xs text-muted-foreground ml-1">{message}</span>}
      </div>
      {(status === 'running' || status === 'pending') && progress !== undefined && (
        <div className="space-y-1">
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-muted-foreground text-right">{progress}%</p>
        </div>
      )}
    </div>
  )
}
