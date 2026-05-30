'use client'

import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import Link from 'next/link'
import { Check, ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

// ─── Feature list ─────────────────────────────────────────────────────────────

const PRO_FEATURES = [
  { icon: '💬', label: '无限 AI 对话，永不受限' },
  { icon: '🔬', label: '深度研究报告，一键生成' },
  { icon: '📚', label: '知识库容量扩展至 50GB' },
  { icon: '🎬', label: '数字人工作室优先渲染' },
  { icon: '🎯', label: '专属客服，7×24 小时支持' },
]

const ENTERPRISE_EXTRA = [
  { icon: '🏢', label: '私有部署，数据完全自主' },
  { icon: '📊', label: '团队协作，多成员管理' },
  { icon: '🔒', label: 'SLA 99.9% 可用性保障' },
  { icon: '🤝', label: '专属客户成功经理' },
  { icon: '⚙️', label: '自定义集成与 API 配额' },
]

// ─── Decorative background dots ───────────────────────────────────────────────

const DOT_POSITIONS = [
  { top: '8%', left: '6%', size: 10, opacity: 0.15, delay: '0s' },
  { top: '12%', left: '18%', size: 6, opacity: 0.2, delay: '0.3s' },
  { top: '5%', left: '35%', size: 14, opacity: 0.1, delay: '0.6s' },
  { top: '18%', left: '52%', size: 8, opacity: 0.18, delay: '0.2s' },
  { top: '6%', left: '70%', size: 12, opacity: 0.12, delay: '0.8s' },
  { top: '15%', left: '85%', size: 7, opacity: 0.22, delay: '0.4s' },
  { top: '30%', left: '3%', size: 9, opacity: 0.13, delay: '1s' },
  { top: '45%', left: '92%', size: 11, opacity: 0.17, delay: '0.7s' },
  { top: '60%', left: '5%', size: 7, opacity: 0.2, delay: '0.1s' },
  { top: '70%', left: '88%', size: 13, opacity: 0.11, delay: '0.5s' },
  { top: '80%', left: '15%', size: 8, opacity: 0.16, delay: '0.9s' },
  { top: '85%', left: '60%', size: 10, opacity: 0.14, delay: '0.3s' },
  { top: '90%', left: '78%', size: 6, opacity: 0.19, delay: '0.6s' },
  { top: '75%', left: '45%', size: 9, opacity: 0.15, delay: '1.1s' },
  { top: '55%', left: '72%', size: 12, opacity: 0.12, delay: '0.4s' },
  { top: '40%', left: '28%', size: 5, opacity: 0.25, delay: '0.8s' },
]

// ─── Inner component (uses useSearchParams) ───────────────────────────────────

function BillingSuccessContent() {
  const searchParams = useSearchParams()
  const plan = searchParams.get('plan') ?? 'Pro'
  const displayPlan = plan.charAt(0).toUpperCase() + plan.slice(1).toLowerCase()
  const isEnterprise = plan.toLowerCase() === 'enterprise'
  const features = isEnterprise ? ENTERPRISE_EXTRA : PRO_FEATURES

  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex items-center justify-center p-6 overflow-hidden">

      {/* ── Decorative dots ── */}
      {DOT_POSITIONS.map((dot, i) => (
        <span
          key={i}
          className="absolute rounded-full bg-gradient-to-br from-blue-400 to-purple-500 animate-pulse"
          style={{
            top: dot.top,
            left: dot.left,
            width: dot.size,
            height: dot.size,
            opacity: dot.opacity,
            animationDelay: dot.delay,
            animationDuration: `${2 + i * 0.15}s`,
          }}
        />
      ))}

      {/* ── Background gradient orbs ── */}
      <div className="absolute top-1/4 left-1/4 w-72 h-72 bg-blue-400/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-purple-400/10 rounded-full blur-3xl pointer-events-none" />

      {/* ── Main card ── */}
      <div className="relative z-10 w-full max-w-lg space-y-8 text-center">

        {/* Animated checkmark */}
        <div className="flex justify-center">
          <div className="relative">
            {/* Outer pulse ring */}
            <div className="absolute inset-0 rounded-full bg-green-500/20 animate-ping" />
            {/* Middle ring */}
            <div className="absolute -inset-2 rounded-full bg-green-500/10 animate-pulse" />
            {/* Checkmark circle */}
            <div className="relative h-24 w-24 rounded-full bg-gradient-to-br from-green-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-500/30">
              <Check className="h-12 w-12 text-white stroke-[3]" />
            </div>
          </div>
        </div>

        {/* Heading */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 rounded-full px-4 py-1.5 text-sm font-medium">
            <Sparkles className="h-3.5 w-3.5" />
            支付成功
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent leading-tight">
            欢迎加入 {displayPlan}！
          </h1>
          <p className="text-muted-foreground text-base">
            您的账户已升级，所有 {displayPlan} 专属功能立即生效
          </p>
        </div>

        {/* Feature list */}
        <div className="bg-card border rounded-2xl p-6 text-left shadow-sm">
          <p className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wide">
            已解锁功能
          </p>
          <ul className="space-y-3">
            {features.map((f, i) => (
              <li
                key={i}
                className="flex items-center gap-3"
                style={{ animationDelay: `${i * 0.08}s` }}
              >
                <span className="text-xl shrink-0" role="img" aria-hidden="true">
                  {f.icon}
                </span>
                <span className="text-sm font-medium">{f.label}</span>
                <Check className="ml-auto h-4 w-4 text-green-500 shrink-0" />
              </li>
            ))}
          </ul>
        </div>

        {/* CTA */}
        <div className="space-y-3">
          <Button
            asChild
            size="lg"
            className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shadow-lg shadow-blue-500/25 text-base h-12"
          >
            <Link href="/invest">
              开始探索
              <ArrowRight className="ml-2 h-5 w-5" />
            </Link>
          </Button>
          <p className="text-xs text-muted-foreground">
            订阅确认邮件已发送至您的注册邮箱
          </p>
        </div>
      </div>
    </div>
  )
}

// ─── Page export ──────────────────────────────────────────────────────────────

export default function BillingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center">
          <div className="h-8 w-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
        </div>
      }
    >
      <BillingSuccessContent />
    </Suspense>
  )
}
