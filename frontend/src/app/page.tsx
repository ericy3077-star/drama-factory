import Link from 'next/link'
import { Button } from '@/components/ui/button'
import {
  TrendingUp, GraduationCap, Zap, Brain, Video,
  BarChart3, Shield, Users, Database, GitBranch,
  ArrowRight, CheckCircle2, Layers
} from 'lucide-react'

// ── 四大引擎 ──────────────────────────────────────────────────────
const engines = [
  {
    id: 'memory',
    name: 'MemoryOS',
    label: '记忆引擎',
    icon: Brain,
    color: 'text-cyan-400',
    bg: 'bg-cyan-500/10',
    border: 'border-cyan-500/20',
    desc: '用户知识永久沉淀，向量检索 + 知识图谱，越用越懂你',
  },
  {
    id: 'agent',
    name: 'AgentOS',
    label: 'Agent 引擎',
    icon: Zap,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/20',
    desc: 'LangGraph 状态机，多步骤任务自动执行，人机协作暂停',
  },
  {
    id: 'avatar',
    name: 'AvatarOS',
    label: '数字人引擎',
    icon: Video,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10',
    border: 'border-purple-500/20',
    desc: '15 分钟素材训练专属数字分身，脚本→视频全自动生成',
  },
  {
    id: 'percept',
    name: 'PerceptOS',
    label: '多模态引擎',
    icon: Layers,
    color: 'text-green-400',
    bg: 'bg-green-500/10',
    border: 'border-green-500/20',
    desc: 'PDF/视频/图表统一理解，智能模型路由降低 70% 成本',
  },
]

// ── 两大垂直产品 ──────────────────────────────────────────────────
const verticals = [
  {
    id: 'invest',
    name: 'InvestMind',
    label: '投资超级助手',
    href: '/invest',
    icon: TrendingUp,
    accent: 'blue',
    tagline: '让一个分析师的产出等于三个',
    pricing: '¥299 / 月起',
    features: [
      '智能信息流：财报 / 研报 / 新闻 AI 提炼日报',
      '研究工作台：多文档对比 + 一键生成投资备忘录',
      '投资 Agent：多步骤自动化研究任务',
      '知识图谱：所有研究自动关联，永不遗忘',
    ],
    moat: '投资偏好数据 + 历史研究积累形成不可迁移资产',
  },
  {
    id: 'edu',
    name: 'EduStar',
    label: '教育数字人平台',
    href: '/edu',
    icon: GraduationCap,
    accent: 'purple',
    tagline: '内容生产成本降低 90%，效果提升 3 倍',
    pricing: '¥599 / 月起',
    features: [
      '数字讲师克隆：15 分钟素材 → 永久数字分身',
      'AI 课程工厂：主题 → 大纲 → 脚本 → 视频全自动',
      '多语言扩展：同一形象，10 种语言同步输出',
      '学员数据：完课率 / 理解曲线 / 个性化推荐',
    ],
    moat: '讲师人格数据 + 学员行为数据双飞轮驱动',
  },
]

// ── 三层壁垒 ──────────────────────────────────────────────────────
const moatLayers = [
  {
    layer: 'L3',
    title: '壁垒资产层',
    subtitle: '数据 + 工作流 + 人格',
    color: 'from-amber-500/20 to-orange-500/10',
    border: 'border-amber-500/30',
    labelColor: 'text-amber-400',
    items: ['用户人格数据库', '行业知识图谱', '工作流深度嵌入'],
    desc: '用户迁移成本趋近无穷，数据资产持续增值',
  },
  {
    layer: 'L2',
    title: '平台产品层',
    subtitle: '网络效应',
    color: 'from-blue-500/15 to-cyan-500/10',
    border: 'border-blue-500/30',
    labelColor: 'text-blue-400',
    items: ['AI 员工市场（供需撮合）', '多模态感知 API（开发者生态）'],
    desc: '用户越多，AI 员工越多样，企业越愿意采购',
  },
  {
    layer: 'L1',
    title: '入口产品层',
    subtitle: '快速现金流',
    color: 'from-slate-700/50 to-slate-800/30',
    border: 'border-slate-600/30',
    labelColor: 'text-slate-400',
    items: ['InvestMind（投资助手）', 'EduStar（教育数字人）'],
    desc: '用户订阅付费，同时开始积累行为数据',
  },
]

// ── 数据飞轮 ──────────────────────────────────────────────────────
const flywheels = [
  {
    product: 'InvestMind',
    color: 'blue',
    steps: [
      '用户分析行为 → 偏好数据沉淀',
      '推荐越精准 → 用户依赖度提升',
      '口碑传播 → 更多用户加入',
      '知识图谱越丰富 → 产品能力领先',
    ],
  },
  {
    product: 'EduStar',
    color: 'purple',
    steps: [
      '讲师生产内容 → 学员行为数据',
      '内容效果优化 → 完课率提升',
      '学员推荐 → 更多讲师入驻',
      '内容生态丰富 → 网络效应形成',
    ],
  },
]

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-white">

      {/* ── Nav ─────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-slate-800/60 bg-slate-950/80 backdrop-blur">
        <div className="container mx-auto flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 text-sm font-bold">
              DF
            </div>
            <span className="font-semibold">Drama Factory</span>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-slate-400 md:flex">
            <a href="#matrix" className="hover:text-white transition-colors">产品矩阵</a>
            <a href="#engines" className="hover:text-white transition-colors">AI 引擎</a>
            <a href="#moat" className="hover:text-white transition-colors">竞争壁垒</a>
            <a href="#flywheel" className="hover:text-white transition-colors">数据飞轮</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost" size="sm" className="text-slate-400 hover:text-white">登录</Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="bg-blue-600 hover:bg-blue-500">免费注册</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section className="container mx-auto px-4 py-28 text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-slate-700 bg-slate-800/50 px-4 py-1.5 text-sm text-slate-400">
          <Database className="h-3.5 w-3.5 text-cyan-400" />
          数据飞轮驱动的 AI 垂直平台
        </div>
        <h1 className="mb-6 text-5xl font-bold tracking-tight md:text-7xl">
          <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">InvestMind</span>
          <span className="mx-3 text-slate-600">&</span>
          <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">EduStar</span>
        </h1>
        <p className="mx-auto mb-4 max-w-2xl text-lg text-slate-400">
          投资超级助手 + 教育数字人平台，共享四大 AI 引擎基础设施
        </p>
        <p className="mx-auto mb-10 max-w-xl text-sm text-slate-500">
          不是 AI 工具，而是 AI 原生的垂直行业操作系统——数据壁垒越深，竞争者越难追赶
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/register">
            <Button size="lg" className="h-12 bg-blue-600 px-8 hover:bg-blue-500">
              立即开始 <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </Link>
          <a href="#matrix">
            <Button size="lg" variant="outline" className="h-12 border-slate-700 px-8 text-slate-300 hover:text-white">
              查看产品矩阵
            </Button>
          </a>
        </div>
      </section>

      {/* ── 产品矩阵 ────────────────────────────────────────── */}
      <section id="matrix" className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">Product Matrix</div>
          <h2 className="text-3xl font-bold">产品矩阵</h2>
          <p className="mt-3 text-slate-400">三层架构，每一层为下一层建立壁垒</p>
        </div>

        <div className="mx-auto max-w-5xl space-y-4">
          {moatLayers.map((layer) => (
            <div
              key={layer.layer}
              className={`rounded-2xl border bg-gradient-to-r p-6 ${layer.color} ${layer.border}`}
            >
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-4">
                  <div className={`shrink-0 rounded-lg border px-2.5 py-1 text-xs font-bold ${layer.border} ${layer.labelColor}`}>
                    {layer.layer}
                  </div>
                  <div>
                    <div className="font-semibold">{layer.title}</div>
                    <div className="text-sm text-slate-400">{layer.subtitle}</div>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {layer.items.map((item) => (
                    <span key={item} className="rounded-full border border-slate-700 bg-slate-800/60 px-3 py-1 text-sm text-slate-300">
                      {item}
                    </span>
                  ))}
                </div>
              </div>
              <p className="mt-3 text-sm text-slate-500 md:pl-14">{layer.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 两大垂直产品 ────────────────────────────────────── */}
      <section className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">Verticals</div>
          <h2 className="text-3xl font-bold">双垂直入口产品</h2>
          <p className="mt-3 text-slate-400">先做深，再平台化</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-6 md:grid-cols-2">
          {verticals.map((v) => {
            const Icon = v.icon
            const isBlue = v.accent === 'blue'
            return (
              <div
                key={v.id}
                className={`group rounded-2xl border p-8 transition-all duration-300 hover:-translate-y-1 hover:shadow-xl ${
                  isBlue
                    ? 'border-blue-500/20 bg-blue-500/5 hover:border-blue-500/40 hover:shadow-blue-500/10'
                    : 'border-purple-500/20 bg-purple-500/5 hover:border-purple-500/40 hover:shadow-purple-500/10'
                }`}
              >
                <div className={`mb-4 flex h-14 w-14 items-center justify-center rounded-xl ${isBlue ? 'bg-blue-500/20' : 'bg-purple-500/20'}`}>
                  <Icon className={`h-7 w-7 ${isBlue ? 'text-blue-400' : 'text-purple-400'}`} />
                </div>

                <div className={`mb-1 text-xs font-medium ${isBlue ? 'text-blue-400' : 'text-purple-400'}`}>
                  {v.label}
                </div>
                <h3 className="mb-1 text-2xl font-bold">{v.name}</h3>
                <p className="mb-5 text-sm text-slate-400">{v.tagline}</p>

                <ul className="mb-6 space-y-2.5">
                  {v.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                      <CheckCircle2 className={`mt-0.5 h-4 w-4 shrink-0 ${isBlue ? 'text-blue-400' : 'text-purple-400'}`} />
                      {f}
                    </li>
                  ))}
                </ul>

                <div className={`mb-5 rounded-lg border p-3 text-xs text-slate-400 ${isBlue ? 'border-blue-500/15 bg-blue-500/5' : 'border-purple-500/15 bg-purple-500/5'}`}>
                  <span className="font-medium text-slate-300">护城河：</span>{v.moat}
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold text-white">{v.pricing}</span>
                  <Link href={v.href}>
                    <Button size="sm" className={isBlue ? 'bg-blue-600 hover:bg-blue-500' : 'bg-purple-600 hover:bg-purple-500'}>
                      进入产品 <ArrowRight className="ml-1 h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── 四大引擎 ────────────────────────────────────────── */}
      <section id="engines" className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">AI Platform</div>
          <h2 className="text-3xl font-bold">四大共享 AI 引擎</h2>
          <p className="mt-3 text-slate-400">两个垂直产品共享同一套基础设施，技术复用，壁垒叠加</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {engines.map((e) => {
            const Icon = e.icon
            return (
              <div key={e.id} className={`rounded-xl border p-5 ${e.bg} ${e.border}`}>
                <div className={`mb-3 flex h-10 w-10 items-center justify-center rounded-lg ${e.bg}`}>
                  <Icon className={`h-5 w-5 ${e.color}`} />
                </div>
                <div className={`mb-0.5 text-xs font-medium ${e.color}`}>{e.label}</div>
                <div className="mb-2 font-semibold">{e.name}</div>
                <p className="text-xs leading-relaxed text-slate-400">{e.desc}</p>
              </div>
            )
          })}
        </div>

        {/* 共享关系示意 */}
        <div className="mx-auto mt-8 max-w-5xl rounded-xl border border-slate-700/50 bg-slate-800/30 p-5">
          <div className="flex flex-wrap items-center justify-center gap-3 text-sm text-slate-400">
            <span className="font-medium text-blue-400">InvestMind</span>
            <span className="text-slate-600">使用</span>
            <span className="rounded bg-cyan-500/10 px-2 py-0.5 text-cyan-400">MemoryOS</span>
            <span className="rounded bg-yellow-500/10 px-2 py-0.5 text-yellow-400">AgentOS</span>
            <span className="rounded bg-green-500/10 px-2 py-0.5 text-green-400">PerceptOS</span>
            <span className="mx-4 text-slate-600">｜</span>
            <span className="font-medium text-purple-400">EduStar</span>
            <span className="text-slate-600">使用</span>
            <span className="rounded bg-purple-500/10 px-2 py-0.5 text-purple-400">AvatarOS</span>
            <span className="rounded bg-cyan-500/10 px-2 py-0.5 text-cyan-400">MemoryOS</span>
            <span className="rounded bg-yellow-500/10 px-2 py-0.5 text-yellow-400">AgentOS</span>
          </div>
        </div>
      </section>

      {/* ── 竞争壁垒 ────────────────────────────────────────── */}
      <section id="moat" className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">Competitive Moat</div>
          <h2 className="text-3xl font-bold">三重竞争壁垒</h2>
          <p className="mt-3 text-slate-400">随时间自动加深，竞争者越晚进入越难追赶</p>
        </div>

        <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-3">
          {[
            {
              icon: Database,
              title: '数据壁垒',
              color: 'text-cyan-400',
              bg: 'bg-cyan-500/10',
              border: 'border-cyan-500/20',
              points: ['用户知识图谱不可迁移', '行业专属数据积累', '模型持续 Fine-tune'],
            },
            {
              icon: GitBranch,
              title: '工作流嵌入',
              color: 'text-yellow-400',
              bg: 'bg-yellow-500/10',
              border: 'border-yellow-500/20',
              points: ['日常工作流全部在平台', '替换成本极高', '深度 API 集成企业系统'],
            },
            {
              icon: Users,
              title: '网络效应',
              color: 'text-purple-400',
              bg: 'bg-purple-500/10',
              border: 'border-purple-500/20',
              points: ['AI 员工市场供需双边', '内容生态越大越好用', '开发者生态锁定'],
            },
          ].map((m) => {
            const Icon = m.icon
            return (
              <div key={m.title} className={`rounded-xl border p-6 ${m.bg} ${m.border}`}>
                <Icon className={`mb-3 h-6 w-6 ${m.color}`} />
                <h3 className="mb-3 font-semibold">{m.title}</h3>
                <ul className="space-y-2">
                  {m.points.map((p) => (
                    <li key={p} className="flex items-start gap-2 text-sm text-slate-400">
                      <Shield className={`mt-0.5 h-3.5 w-3.5 shrink-0 ${m.color}`} />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── 数据飞轮 ────────────────────────────────────────── */}
      <section id="flywheel" className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">Data Flywheel</div>
          <h2 className="text-3xl font-bold">数据飞轮机制</h2>
          <p className="mt-3 text-slate-400">用户行为 → 产品更好 → 更多用户，自我强化的正向循环</p>
        </div>

        <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-2">
          {flywheels.map((fw) => {
            const isBlue = fw.color === 'blue'
            return (
              <div key={fw.product} className={`rounded-xl border p-6 ${isBlue ? 'border-blue-500/20 bg-blue-500/5' : 'border-purple-500/20 bg-purple-500/5'}`}>
                <div className={`mb-4 text-sm font-semibold ${isBlue ? 'text-blue-400' : 'text-purple-400'}`}>
                  {fw.product} 飞轮
                </div>
                <div className="space-y-3">
                  {fw.steps.map((step, i) => (
                    <div key={step} className="flex items-start gap-3">
                      <div className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${isBlue ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}`}>
                        {i + 1}
                      </div>
                      <span className="text-sm text-slate-300">{step}</span>
                    </div>
                  ))}
                  <div className={`mt-2 flex items-center gap-2 text-xs ${isBlue ? 'text-blue-500' : 'text-purple-500'}`}>
                    <ArrowRight className="h-3.5 w-3.5 rotate-[135deg]" />
                    循环加速，壁垒持续加深
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── 路线图 ──────────────────────────────────────────── */}
      <section className="container mx-auto px-4 py-20">
        <div className="mb-12 text-center">
          <div className="mb-2 text-sm font-medium uppercase tracking-widest text-slate-500">Roadmap</div>
          <h2 className="text-3xl font-bold">执行路线图</h2>
        </div>

        <div className="mx-auto max-w-3xl">
          {[
            {
              phase: 'Phase 1',
              time: '0 – 6 个月',
              title: '跑通 PMF',
              color: 'blue',
              items: ['InvestMind MVP 上线', '目标 50 个付费用户', 'MemoryOS 开始积累用户数据'],
            },
            {
              phase: 'Phase 2',
              time: '6 – 18 个月',
              title: '数据飞轮启动',
              color: 'purple',
              items: ['EduStar 上线', '两产品数据打通', '用户知识图谱足够丰富，黏性显著提升'],
            },
            {
              phase: 'Phase 3',
              time: '18 个月+',
              title: '平台化',
              color: 'amber',
              items: ['AI 员工市场上线', '开发者 API 开放', '三重壁垒形成，进入平台竞争阶段'],
            },
          ].map((r, i) => (
            <div key={r.phase} className="relative flex gap-6">
              {i < 2 && (
                <div className="absolute left-[19px] top-10 h-full w-px bg-slate-800" />
              )}
              <div className={`relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold ${
                r.color === 'blue' ? 'border-blue-500 bg-blue-500/20 text-blue-400'
                  : r.color === 'purple' ? 'border-purple-500 bg-purple-500/20 text-purple-400'
                  : 'border-amber-500 bg-amber-500/20 text-amber-400'
              }`}>
                {i + 1}
              </div>
              <div className="mb-8 flex-1 rounded-xl border border-slate-800 bg-slate-900/50 p-5">
                <div className="mb-1 flex items-center gap-3">
                  <span className={`text-xs font-medium ${r.color === 'blue' ? 'text-blue-400' : r.color === 'purple' ? 'text-purple-400' : 'text-amber-400'}`}>
                    {r.phase}
                  </span>
                  <span className="text-xs text-slate-500">{r.time}</span>
                </div>
                <div className="mb-3 font-semibold">{r.title}</div>
                <ul className="space-y-1.5">
                  {r.items.map((item) => (
                    <li key={item} className="flex items-center gap-2 text-sm text-slate-400">
                      <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-slate-600" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ─────────────────────────────────────────────── */}
      <section className="container mx-auto px-4 py-20">
        <div className="mx-auto max-w-2xl rounded-2xl border border-slate-700/50 bg-gradient-to-br from-slate-800/80 to-slate-900/80 p-12 text-center">
          <h2 className="mb-4 text-3xl font-bold">开始构建你的 AI 工作流</h2>
          <p className="mb-8 text-slate-400">
            越早开始，积累的数据壁垒越深。加入 Drama Factory，让 AI 成为你最强大的竞争优势。
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="h-12 bg-blue-600 px-8 hover:bg-blue-500">
                免费开始 <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
            <Link href="/invest">
              <Button size="lg" variant="outline" className="h-12 border-slate-600 px-8 text-slate-300 hover:text-white">
                体验 InvestMind
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-slate-800 py-8">
        <div className="container mx-auto flex flex-col items-center justify-between gap-4 px-4 text-sm text-slate-500 md:flex-row">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-gradient-to-br from-blue-500 to-purple-600 text-xs font-bold text-white">DF</div>
            <span>Drama Factory</span>
          </div>
          <div className="flex gap-6">
            <a href="#matrix" className="hover:text-slate-300 transition-colors">产品矩阵</a>
            <a href="#engines" className="hover:text-slate-300 transition-colors">AI 引擎</a>
            <a href="#moat" className="hover:text-slate-300 transition-colors">竞争壁垒</a>
          </div>
          <span>© 2026 Drama Factory. All rights reserved.</span>
        </div>
      </footer>
    </div>
  )
}
