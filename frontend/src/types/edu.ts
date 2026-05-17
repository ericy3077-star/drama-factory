// ─── Digital Avatar ───────────────────────────────────────────────────────────

export type AvatarStatus = 'creating' | 'training' | 'ready' | 'failed'

export interface DigitalAvatar {
  id: string
  name: string
  description?: string
  thumbnail_url?: string
  status: AvatarStatus
  voice_id?: string
  created_at: string
  updated_at: string
}

export interface CreateAvatarRequest {
  name: string
  description?: string
  photo_asset_id: string
  voice_sample_asset_id?: string
}

// ─── Video Generation ─────────────────────────────────────────────────────────

export type VideoStatus = 'queued' | 'processing' | 'completed' | 'failed'

export interface VideoJob {
  id: string
  avatar_id: string
  script: string
  status: VideoStatus
  progress: number
  video_url?: string
  thumbnail_url?: string
  duration_seconds?: number
  created_at: string
  updated_at: string
}

export interface GenerateVideoRequest {
  avatar_id: string
  script: string
  background_url?: string
  voice_speed?: number
}

// ─── Course ───────────────────────────────────────────────────────────────────

export type CourseStatus = 'draft' | 'published' | 'archived'

export interface Course {
  id: string
  title: string
  description: string
  thumbnail_url?: string
  status: CourseStatus
  chapters: Chapter[]
  learner_count: number
  avg_rating: number
  created_at: string
  updated_at: string
}

export interface Chapter {
  id: string
  course_id: string
  title: string
  order: number
  lessons: Lesson[]
}

export interface Lesson {
  id: string
  chapter_id: string
  title: string
  order: number
  type: 'video' | 'text' | 'quiz'
  video_job_id?: string
  content?: string
  duration_seconds?: number
}

// ─── Analytics ─────────────────────────────────────────────────────────────────

export interface CourseAnalytics {
  course_id: string
  total_enrollments: number
  active_learners: number
  completion_rate: number
  avg_watch_time_seconds: number
  lesson_completion_rates: LessonCompletionRate[]
  daily_views: DailyView[]
}

export interface LessonCompletionRate {
  lesson_id: string
  lesson_title: string
  completion_rate: number
}

export interface DailyView {
  date: string
  views: number
  unique_learners: number
}

// ─── Learner ─────────────────────────────────────────────────────────────────

export interface LearnerProgress {
  course_id: string
  learner_id: string
  progress_pct: number
  completed_lessons: string[]
  last_accessed_at: string
  certificate_issued?: boolean
}
