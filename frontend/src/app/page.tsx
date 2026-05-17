import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, GraduationCap, Zap, Shield, BarChart3, Video } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Nav */}
      <header className="container mx-auto flex items-center justify-between py-6 px-4">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-lg bg-blue-500 flex items-center justify-center font-bold text-sm">
            DF
          </div>
          <span className="font-semibold text-lg">Drama Factory</span>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" className="text-slate-300 hover:text-white">
              登录
            </Button>
          </Link>
          <Link href="/register">
            <Button className="bg-blue-500 hover:bg-blue-600">免费注册</Button>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="container mx-auto px-4 py-24 text-center">
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-sm text-blue-300 mb-6">
          <Zap className="h-3.5 w-3.5" />
          AI 驱动的投资研究与教育平台
        </div>
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
          <span className="text-blue-400">InvestMind</span>
          {' & '}
          <span className="text-purple-400">EduStar</span>
        </h1>
        <p className="text-xl text-slate-400 max-w-2xl mx-auto mb-10">
          智能投资研究助手 + 数字人课程创作平台。让 AI 成为您最强大的工作伙伴。
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link href="/register">
            <Button size="lg" className="bg-blue-500 hover:bg-blue-600 h-12 px-8">
              立即开始
            </Button>
          </Link>
          <Link href="/login">
            <Button size="lg" variant="outline" className="h-12 px-8 border-slate-600 text-slate-300 hover:text-white">
              查看演示
            </Button>
          </Link>
        </div>
      </section>

      {/* Products */}
      <section className="container mx-auto px-4 py-16">
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          <Card className="bg-slate-800/50 border-blue-500/20 hover:border-blue-500/50 transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-xl bg-blue-500/20 flex items-center justify-center mb-2">
                <TrendingUp className="h-6 w-6 text-blue-400" />
              </div>
              <CardTitle className="text-white text-2xl">InvestMind</CardTitle>
              <CardDescription className="text-slate-400">
                AI 驱动的投资研究平台
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { icon: BarChart3, text: '实时财经信息流，AI 情感分析' },
                { icon: Zap, text: '深度研究报告一键生成' },
                { icon: Shield, text: '知识图谱，关联分析' },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-3 text-slate-300">
                  <Icon className="h-4 w-4 text-blue-400 shrink-0" />
                  <span className="text-sm">{text}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="bg-slate-800/50 border-purple-500/20 hover:border-purple-500/50 transition-colors">
            <CardHeader>
              <div className="h-12 w-12 rounded-xl bg-purple-500/20 flex items-center justify-center mb-2">
                <GraduationCap className="h-6 w-6 text-purple-400" />
              </div>
              <CardTitle className="text-white text-2xl">EduStar</CardTitle>
              <CardDescription className="text-slate-400">
                数字人课程创作平台
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                { icon: Video, text: '上传照片即可克隆数字分身' },
                { icon: Zap, text: '输入脚本，AI 生成课程视频' },
                { icon: BarChart3, text: '学员数据分析，优化内容' },
              ].map(({ icon: Icon, text }) => (
                <div key={text} className="flex items-center gap-3 text-slate-300">
                  <Icon className="h-4 w-4 text-purple-400 shrink-0" />
                  <span className="text-sm">{text}</span>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  )
}
