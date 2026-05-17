'use client'

import { useQuery } from '@tanstack/react-query'
import { Users, BookOpen, TrendingUp, Clock } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { apiGet } from '@/lib/api'
import type { CourseAnalytics } from '@/types/edu'
import { useState } from 'react'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ElementType
  description?: string
  color?: string
}

function StatCard({ title, value, icon: Icon, description, color = 'text-primary' }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold mt-1">{value}</p>
            {description && <p className="text-xs text-muted-foreground mt-1">{description}</p>}
          </div>
          <div className={`h-10 w-10 rounded-lg bg-primary/10 flex items-center justify-center ${color}`}>
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export function LearnerDashboard() {
  const [courseId, setCourseId] = useState<string | undefined>(undefined)

  const { data: analytics } = useQuery({
    queryKey: ['course-analytics', courseId],
    queryFn: () => apiGet<CourseAnalytics>(`/api/v1/edu/analytics${courseId ? `?course_id=${courseId}` : ''}`),
    enabled: true,
  })

  return (
    <div className="space-y-6">
      {/* Summary stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="总学员数"
          value={analytics?.total_enrollments ?? 0}
          icon={Users}
          description="累计注册学员"
        />
        <StatCard
          title="活跃学员"
          value={analytics?.active_learners ?? 0}
          icon={TrendingUp}
          description="最近 30 天活跃"
          color="text-green-500"
        />
        <StatCard
          title="完成率"
          value={`${Math.round((analytics?.completion_rate ?? 0) * 100)}%`}
          icon={BookOpen}
          description="课程平均完成率"
          color="text-purple-500"
        />
        <StatCard
          title="平均观看时长"
          value={analytics ? `${Math.round(analytics.avg_watch_time_seconds / 60)} 分钟` : '0 分钟'}
          icon={Clock}
          description="每次访问"
          color="text-orange-500"
        />
      </div>

      {/* Lesson completion */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">课时完成率</CardTitle>
        </CardHeader>
        <CardContent>
          {!analytics || analytics.lesson_completion_rates.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">暂无数据</p>
          ) : (
            <div className="space-y-3">
              {analytics.lesson_completion_rates.map((l) => (
                <div key={l.lesson_id} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="truncate flex-1 pr-4">{l.lesson_title}</span>
                    <span className="text-muted-foreground shrink-0">
                      {Math.round(l.completion_rate * 100)}%
                    </span>
                  </div>
                  <Progress value={l.completion_rate * 100} className="h-2" />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Daily views chart placeholder */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">每日观看趋势</CardTitle>
        </CardHeader>
        <CardContent>
          {!analytics || analytics.daily_views.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">暂无数据</p>
          ) : (
            <div className="flex items-end gap-1 h-32">
              {analytics.daily_views.map((d) => {
                const maxViews = Math.max(...analytics.daily_views.map((v) => v.views))
                const heightPct = maxViews > 0 ? (d.views / maxViews) * 100 : 0
                return (
                  <div key={d.date} className="flex-1 flex flex-col items-center gap-1 group relative">
                    <div
                      className="w-full bg-primary/60 hover:bg-primary rounded-t transition-colors"
                      style={{ height: `${heightPct}%`, minHeight: 4 }}
                    />
                    <span className="text-[10px] text-muted-foreground hidden group-hover:block absolute -top-5">
                      {d.views}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
