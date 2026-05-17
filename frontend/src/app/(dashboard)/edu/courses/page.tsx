import type { Metadata } from 'next'
import { CourseEditor } from '@/components/edu/CourseEditor'

export const metadata: Metadata = { title: 'EduStar — 课程管理' }

export default function CoursesPage() {
  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold">课程管理</h1>
        <p className="text-muted-foreground mt-1">创建和管理您的在线课程</p>
      </div>
      <CourseEditor />
    </div>
  )
}
