'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { AlertCircle, ArrowLeft, Loader2, Mail, CheckCircle2 } from 'lucide-react'

// ─── Email validation ─────────────────────────────────────────────────────────

function isValidEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

// ─── Success state ────────────────────────────────────────────────────────────

function SuccessCard({ email }: { email: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1 text-center pb-2">
          {/* Animated email icon */}
          <div className="flex justify-center mb-4">
            <div className="relative">
              <div className="h-20 w-20 rounded-full bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-200 dark:border-blue-800 flex items-center justify-center">
                <Mail className="h-9 w-9 text-blue-500" />
              </div>
              <div className="absolute -bottom-1 -right-1 h-7 w-7 rounded-full bg-green-500 flex items-center justify-center shadow-sm border-2 border-background">
                <CheckCircle2 className="h-4 w-4 text-white" />
              </div>
            </div>
          </div>
          <CardTitle className="text-2xl">邮件已发送！</CardTitle>
          <CardDescription className="text-base">
            重置链接已发送到
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5 text-center">
          {/* Email highlight */}
          <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg px-4 py-2.5">
            <p className="text-sm font-semibold text-blue-700 dark:text-blue-300 truncate">
              {email}
            </p>
          </div>

          {/* Instructions */}
          <div className="text-left space-y-3">
            <p className="text-sm font-medium text-muted-foreground">接下来请：</p>
            <ol className="space-y-2">
              {[
                '打开您的邮箱，查收来自 Drama Factory 的邮件',
                '点击邮件中的「重置密码」链接',
                '设置新密码后即可正常登录',
              ].map((step, i) => (
                <li key={i} className="flex items-start gap-3 text-sm">
                  <span className="h-5 w-5 rounded-full bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                    {i + 1}
                  </span>
                  <span className="text-muted-foreground">{step}</span>
                </li>
              ))}
            </ol>
          </div>

          <p className="text-xs text-muted-foreground bg-muted rounded-md px-3 py-2">
            链接有效期 30 分钟。若未收到邮件，请检查垃圾邮件文件夹。
          </p>
        </CardContent>

        <CardFooter className="flex flex-col gap-3">
          <Button asChild className="w-full bg-blue-600 hover:bg-blue-700 text-white">
            <Link href="/login">
              <ArrowLeft className="mr-2 h-4 w-4" />
              返回登录
            </Link>
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [isPending, setIsPending] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  if (submitted) return <SuccessCard email={email} />

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError('')

    if (!isValidEmail(email)) {
      setError('请输入有效的邮箱地址')
      return
    }

    setIsPending(true)
    try {
      // Mock API call — replace with: await apiPost('/api/v1/auth/forgot-password', { email })
      await new Promise((resolve) => setTimeout(resolve, 1200))
      setSubmitted(true)
    } catch {
      setError('发送失败，请稍后重试')
    } finally {
      setIsPending(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-slate-900 p-4">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader className="space-y-1">
          {/* Brand */}
          <div className="flex items-center gap-2 mb-3">
            <div className="h-8 w-8 rounded-lg bg-blue-500 flex items-center justify-center font-bold text-white text-sm">
              DF
            </div>
            <span className="font-semibold">Drama Factory</span>
          </div>

          {/* Icon */}
          <div className="flex items-center justify-center h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 border border-blue-200 dark:border-blue-800 mb-2">
            <Mail className="h-7 w-7 text-blue-500" />
          </div>

          <CardTitle className="text-2xl">忘记密码？</CardTitle>
          <CardDescription>
            输入您的注册邮箱，我们将发送密码重置链接
          </CardDescription>
        </CardHeader>

        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">注册邮箱</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value)
                  if (error) setError('')
                }}
                required
                autoComplete="email"
                autoFocus
                className={error ? 'border-destructive focus-visible:ring-destructive' : ''}
              />
            </div>
          </CardContent>

          <CardFooter className="flex flex-col gap-4">
            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white"
              disabled={isPending || !email}
            >
              {isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Mail className="mr-2 h-4 w-4" />
              )}
              {isPending ? '发送中...' : '发送重置链接'}
            </Button>

            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <ArrowLeft className="h-3.5 w-3.5" />
              返回登录
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
