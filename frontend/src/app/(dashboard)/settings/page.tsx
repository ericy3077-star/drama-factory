'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import {
  User,
  Shield,
  CreditCard,
  Loader2,
  Check,
  Zap,
  Crown,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useAuthStore } from '@/store/authStore'
import { apiGet, apiPost } from '@/lib/api'

// ─── Types ────────────────────────────────────────────────────────────────────

interface SubscriptionData {
  plan: 'free' | 'pro' | 'enterprise'
  messages_used: number
  messages_limit: number
  storage_used_gb: number
  storage_limit_gb: number
  renewal_date?: string
}

interface CheckoutData {
  checkout_url: string
}

// ─── Constants ────────────────────────────────────────────────────────────────

const TIMEZONES = [
  { value: 'Asia/Shanghai', label: '中国标准时间 (CST, UTC+8)' },
  { value: 'Asia/Hong_Kong', label: '香港时间 (HKT, UTC+8)' },
  { value: 'Asia/Taipei', label: '台湾时间 (TST, UTC+8)' },
  { value: 'Asia/Tokyo', label: '日本标准时间 (JST, UTC+9)' },
  { value: 'Asia/Seoul', label: '韩国标准时间 (KST, UTC+9)' },
  { value: 'Asia/Singapore', label: '新加坡时间 (SGT, UTC+8)' },
  { value: 'America/New_York', label: '美国东部时间 (ET, UTC-5/-4)' },
  { value: 'America/Los_Angeles', label: '美国太平洋时间 (PT, UTC-8/-7)' },
  { value: 'Europe/London', label: '英国时间 (GMT/BST, UTC+0/+1)' },
  { value: 'Europe/Paris', label: '中欧时间 (CET, UTC+1/+2)' },
  { value: 'UTC', label: '协调世界时 (UTC)' },
]

const PLAN_FEATURES = {
  free: {
    label: '免费版',
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
    features: ['每月 100 条对话', '1GB 知识库', '标准响应速度'],
  },
  pro: {
    label: 'Pro 版',
    color: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    features: ['无限对话', '50GB 知识库', '深度研究报告', '数字人工作室', '优先响应'],
  },
  enterprise: {
    label: '企业版',
    color: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    features: ['Pro 所有功能', '私有部署选项', '专属客服经理', 'SLA 99.9%', '定制集成'],
  },
}

// ─── Avatar Initials ──────────────────────────────────────────────────────────

function AvatarInitials({ name, email }: { name?: string; email?: string }) {
  const initials = name
    ? name.slice(0, 2).toUpperCase()
    : email
    ? email.slice(0, 2).toUpperCase()
    : 'DF'

  return (
    <div className="relative">
      <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
        <span className="text-2xl font-bold text-white">{initials}</span>
      </div>
      <div className="absolute -bottom-1 -right-1 h-5 w-5 rounded-full bg-green-500 border-2 border-background" />
    </div>
  )
}

// ─── Account Tab ──────────────────────────────────────────────────────────────

function AccountTab() {
  const { user, setUser } = useAuthStore()
  const [displayName, setDisplayName] = useState(user?.display_name ?? '')
  const [bio, setBio] = useState(user?.bio ?? '')
  const [timezone, setTimezone] = useState(user?.timezone ?? 'Asia/Shanghai')

  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name)
      setBio(user.bio ?? '')
      setTimezone(user.timezone ?? 'Asia/Shanghai')
    }
  }, [user])

  const saveMutation = useMutation({
    mutationFn: () =>
      apiPost<typeof user>('/api/v1/users/me', { display_name: displayName, bio, timezone }),
    onSuccess: (data) => {
      if (data) setUser(data)
      toast.success('账户信息已保存')
    },
    onError: () => toast.error('保存失败，请稍后重试'),
  })

  return (
    <div className="space-y-6">
      {/* Profile header */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-5">
            <AvatarInitials name={user?.display_name} email={user?.email} />
            <div>
              <p className="text-lg font-semibold">{user?.display_name || '未设置姓名'}</p>
              <p className="text-sm text-muted-foreground">{user?.email}</p>
              <Badge
                variant="secondary"
                className={`mt-1.5 text-xs ${
                  PLAN_FEATURES[user?.subscription_tier ?? 'free'].color
                }`}
              >
                {PLAN_FEATURES[user?.subscription_tier ?? 'free'].label}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Edit form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">基本信息</CardTitle>
          <CardDescription>修改您的公开资料信息</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="display_name">显示名称</Label>
            <Input
              id="display_name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="您的名字"
              maxLength={50}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bio">个人简介</Label>
            <Textarea
              id="bio"
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="介绍一下自己..."
              className="resize-none"
              rows={3}
              maxLength={200}
            />
            <p className="text-xs text-muted-foreground text-right">{bio.length}/200</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone">时区</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger id="timezone">
                <SelectValue placeholder="选择时区" />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="pt-2">
            <Button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              {saveMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Check className="mr-2 h-4 w-4" />
              )}
              保存更改
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Security Tab ─────────────────────────────────────────────────────────────

function SecurityTab() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<Record<string, string>>({})

  const passwordMutation = useMutation({
    mutationFn: () =>
      apiPost('/api/v1/users/me/password', {
        current_password: currentPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      toast.success('密码已更新', { description: '请使用新密码登录' })
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
    },
    onError: () => toast.error('密码更新失败', { description: '当前密码可能不正确' }),
  })

  function validate() {
    const errs: Record<string, string> = {}
    if (!currentPassword) errs.current = '请输入当前密码'
    if (newPassword.length < 8) errs.new = '新密码至少 8 个字符'
    if (newPassword !== confirmPassword) errs.confirm = '两次密码输入不一致'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (validate()) passwordMutation.mutate()
  }

  const strengthScore = newPassword.length === 0
    ? 0
    : newPassword.length < 8
    ? 1
    : /[A-Z]/.test(newPassword) && /[0-9]/.test(newPassword) && /[^A-Za-z0-9]/.test(newPassword)
    ? 3
    : 2

  const strengthLabels = ['', '弱', '中等', '强']
  const strengthColors = ['', 'bg-red-500', 'bg-yellow-500', 'bg-green-500']

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">修改密码</CardTitle>
          <CardDescription>定期更换密码有助于保护您的账户安全</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="current_password">当前密码</Label>
              <Input
                id="current_password"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
              />
              {errors.current && <p className="text-xs text-destructive">{errors.current}</p>}
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="new_password">新密码</Label>
              <Input
                id="new_password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
                placeholder="至少 8 个字符"
              />
              {newPassword.length > 0 && (
                <div className="space-y-1">
                  <Progress value={strengthScore * 33.3} className="h-1.5" />
                  <p className={`text-xs font-medium ${
                    strengthScore === 1 ? 'text-red-500' :
                    strengthScore === 2 ? 'text-yellow-500' : 'text-green-500'
                  }`}>
                    密码强度：{strengthLabels[strengthScore]}
                  </p>
                </div>
              )}
              {errors.new && <p className="text-xs text-destructive">{errors.new}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm_password">确认新密码</Label>
              <Input
                id="confirm_password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
              />
              {errors.confirm && <p className="text-xs text-destructive">{errors.confirm}</p>}
            </div>

            <div className="pt-2">
              <Button
                type="submit"
                disabled={passwordMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {passwordMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Shield className="mr-2 h-4 w-4" />
                )}
                更新密码
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="border-amber-200 dark:border-amber-800 bg-amber-50/50 dark:bg-amber-950/20">
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <Shield className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <p className="text-sm font-medium text-amber-800 dark:text-amber-200">安全提示</p>
              <ul className="text-xs text-amber-700 dark:text-amber-300 space-y-1 list-disc list-inside">
                <li>使用大写字母、数字和特殊符号组合</li>
                <li>避免使用生日或常见词语</li>
                <li>不同网站使用不同密码</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// ─── Subscription Tab ─────────────────────────────────────────────────────────

function SubscriptionTab() {
  const { user } = useAuthStore()

  const { data: subscription, isLoading } = useQuery<SubscriptionData>({
    queryKey: ['subscription'],
    queryFn: () => apiGet<SubscriptionData>('/api/v1/billing/subscription'),
    retry: false,
    // Show mock data if API unavailable
    placeholderData: {
      plan: user?.subscription_tier ?? 'free',
      messages_used: 47,
      messages_limit: 100,
      storage_used_gb: 0.3,
      storage_limit_gb: 1,
      renewal_date: '2026-06-30',
    },
  })

  const upgradeMutation = useMutation({
    mutationFn: () => apiPost<CheckoutData>('/api/v1/billing/checkout', { plan: 'pro' }),
    onSuccess: (data) => {
      if (data?.checkout_url) window.location.href = data.checkout_url
    },
    onError: () => toast.error('跳转支付失败，请稍后重试'),
  })

  const plan = subscription?.plan ?? user?.subscription_tier ?? 'free'
  const planInfo = PLAN_FEATURES[plan]
  const messagesPercent = subscription
    ? (subscription.messages_used / subscription.messages_limit) * 100
    : 0
  const storagePercent = subscription
    ? (subscription.storage_used_gb / subscription.storage_limit_gb) * 100
    : 0

  return (
    <div className="space-y-6">
      {/* Current plan */}
      <Card className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">当前套餐</CardTitle>
            <Badge className={planInfo.color}>
              {plan === 'pro' || plan === 'enterprise' ? (
                <Crown className="mr-1 h-3 w-3" />
              ) : null}
              {planInfo.label}
            </Badge>
          </div>
          {subscription?.renewal_date && plan !== 'free' && (
            <CardDescription>下次续费：{subscription.renewal_date}</CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {planInfo.features.map((f) => (
              <li key={f} className="flex items-center gap-2 text-sm">
                <div className="h-4 w-4 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center shrink-0">
                  <Check className="h-2.5 w-2.5 text-blue-600 dark:text-blue-400" />
                </div>
                {f}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Usage stats */}
      {isLoading ? (
        <Card>
          <CardContent className="pt-6 flex items-center justify-center h-32">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">用量统计</CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">本月对话次数</span>
                <span className="font-medium">
                  {subscription?.messages_used} / {subscription?.messages_limit}
                </span>
              </div>
              <Progress value={messagesPercent} className="h-2" />
              {messagesPercent >= 80 && (
                <p className="text-xs text-amber-600 dark:text-amber-400">
                  用量已达 {Math.round(messagesPercent)}%，考虑升级套餐
                </p>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">知识库存储</span>
                <span className="font-medium">
                  {subscription?.storage_used_gb} GB / {subscription?.storage_limit_gb} GB
                </span>
              </div>
              <Progress value={storagePercent} className="h-2" />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Upgrade CTA — only for free plan */}
      {plan === 'free' && (
        <Card className="border-blue-200 dark:border-blue-800 bg-gradient-to-br from-blue-50 to-purple-50 dark:from-blue-950/30 dark:to-purple-950/30">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <div className="flex-1">
                <p className="font-semibold text-blue-900 dark:text-blue-100 flex items-center gap-2">
                  <Zap className="h-4 w-4 text-blue-600" />
                  升级到 Pro，解锁全部功能
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  无限对话、50GB 知识库、数字人工作室，仅需 ¥99/月
                </p>
              </div>
              <Button
                onClick={() => upgradeMutation.mutate()}
                disabled={upgradeMutation.isPending}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white shrink-0"
              >
                {upgradeMutation.isPending ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Crown className="mr-2 h-4 w-4" />
                )}
                立即升级
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">账户设置</h1>
        <p className="text-muted-foreground mt-1">管理您的个人信息、安全设置和订阅套餐</p>
      </div>

      <Tabs defaultValue="account" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="account" className="gap-2">
            <User className="h-4 w-4" />
            账户
          </TabsTrigger>
          <TabsTrigger value="security" className="gap-2">
            <Shield className="h-4 w-4" />
            安全
          </TabsTrigger>
          <TabsTrigger value="subscription" className="gap-2">
            <CreditCard className="h-4 w-4" />
            订阅
          </TabsTrigger>
        </TabsList>

        <TabsContent value="account">
          <AccountTab />
        </TabsContent>
        <TabsContent value="security">
          <SecurityTab />
        </TabsContent>
        <TabsContent value="subscription">
          <SubscriptionTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}
