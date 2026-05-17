'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  TrendingUp,
  GraduationCap,
  Rss,
  FlaskConical,
  MessageSquare,
  Archive,
  Video,
  BookOpen,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
} from 'lucide-react'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { useAuthStore } from '@/store/authStore'
import { signOut } from 'next-auth/react'

type NavItem = {
  label: string
  href: string
  icon: React.ElementType
}

const investNav: NavItem[] = [
  { label: '信息流', href: '/invest', icon: Rss },
  { label: '深度研究', href: '/invest/research', icon: FlaskConical },
  { label: 'AI 助手', href: '/invest/assistant', icon: MessageSquare },
  { label: '知识库', href: '/invest/vault', icon: Archive },
]

const eduNav: NavItem[] = [
  { label: '数字人工作室', href: '/edu', icon: Video },
  { label: '课程管理', href: '/edu/courses', icon: BookOpen },
  { label: '数据分析', href: '/edu/analytics', icon: BarChart3 },
]

function NavGroup({
  title,
  icon: Icon,
  color,
  items,
  collapsed,
  pathname,
}: {
  title: string
  icon: React.ElementType
  color: string
  items: NavItem[]
  collapsed: boolean
  pathname: string
}) {
  return (
    <div className="space-y-1">
      {!collapsed && (
        <div className={cn('flex items-center gap-2 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider', color)}>
          <Icon className="h-3.5 w-3.5" />
          {title}
        </div>
      )}
      {collapsed && (
        <div className={cn('flex justify-center py-1', color)}>
          <Icon className="h-4 w-4" />
        </div>
      )}
      {items.map((item) => {
        const active = pathname === item.href || (pathname.startsWith(item.href) && item.href !== '/')
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              'flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors',
              collapsed && 'justify-center px-2',
              active
                ? 'bg-accent text-accent-foreground font-medium'
                : 'text-muted-foreground hover:bg-accent/50 hover:text-foreground',
            )}
            title={collapsed ? item.label : undefined}
          >
            <item.icon className="h-4 w-4 shrink-0" />
            {!collapsed && item.label}
          </Link>
        )
      })}
    </div>
  )
}

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()
  const user = useAuthStore((s) => s.user)
  const clearAuth = useAuthStore((s) => s.clearAuth)

  async function handleSignOut() {
    clearAuth()
    await signOut({ callbackUrl: '/login' })
  }

  return (
    <aside
      className={cn(
        'relative flex h-screen flex-col border-r bg-background transition-all duration-300',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Logo */}
      <div className={cn('flex h-16 items-center border-b px-4', collapsed && 'justify-center px-2')}>
        <div className="flex items-center gap-2 min-w-0">
          <div className="h-8 w-8 shrink-0 rounded-lg bg-blue-500 flex items-center justify-center font-bold text-white text-sm">
            DF
          </div>
          {!collapsed && <span className="font-semibold truncate">Drama Factory</span>}
        </div>
      </div>

      {/* Collapse toggle */}
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-3 top-[72px] h-6 w-6 rounded-full border bg-background shadow-sm z-10"
        onClick={() => setCollapsed((c) => !c)}
      >
        {collapsed ? <ChevronRight className="h-3 w-3" /> : <ChevronLeft className="h-3 w-3" />}
      </Button>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-4">
        <NavGroup
          title="InvestMind"
          icon={TrendingUp}
          color="text-blue-500"
          items={investNav}
          collapsed={collapsed}
          pathname={pathname}
        />
        <Separator />
        <NavGroup
          title="EduStar"
          icon={GraduationCap}
          color="text-purple-500"
          items={eduNav}
          collapsed={collapsed}
          pathname={pathname}
        />
      </nav>

      {/* Footer */}
      <div className="border-t p-3 space-y-1">
        <Link
          href="/settings"
          className={cn(
            'flex items-center gap-3 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent/50 hover:text-foreground transition-colors',
            collapsed && 'justify-center px-2',
          )}
          title={collapsed ? '设置' : undefined}
        >
          <Settings className="h-4 w-4 shrink-0" />
          {!collapsed && '设置'}
        </Link>

        <div className={cn('flex items-center gap-3 px-3 py-2', collapsed && 'justify-center px-2')}>
          <Avatar className="h-7 w-7 shrink-0">
            <AvatarImage src={user?.avatar_url} alt={user?.name} />
            <AvatarFallback className="text-xs">
              {user?.name?.charAt(0).toUpperCase() ?? 'U'}
            </AvatarFallback>
          </Avatar>
          {!collapsed && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name ?? '用户'}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={handleSignOut}>
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>
    </aside>
  )
}
