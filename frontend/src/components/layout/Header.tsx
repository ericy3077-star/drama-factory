'use client'

import { usePathname } from 'next/navigation'
import { Moon, Sun, Bell } from 'lucide-react'
import { useTheme } from 'next-themes'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

const PAGE_TITLES: Record<string, string> = {
  '/invest': 'InvestMind · 信息流',
  '/invest/research': 'InvestMind · 深度研究',
  '/invest/assistant': 'InvestMind · AI 助手',
  '/invest/vault': 'InvestMind · 知识库',
  '/edu': 'EduStar · 数字人工作室',
  '/edu/courses': 'EduStar · 课程管理',
  '/edu/analytics': 'EduStar · 数据分析',
}

export function Header() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  const title = PAGE_TITLES[pathname] ?? 'Drama Factory'

  return (
    <header className="h-16 border-b bg-background flex items-center justify-between px-6 shrink-0">
      <h2 className="text-sm font-semibold text-foreground">{title}</h2>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-4 w-4" />
          <Badge className="absolute -top-1 -right-1 h-4 w-4 p-0 flex items-center justify-center text-[10px]">
            3
          </Badge>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          aria-label="Toggle theme"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-transform dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-transform dark:rotate-0 dark:scale-100" />
        </Button>
      </div>
    </header>
  )
}
