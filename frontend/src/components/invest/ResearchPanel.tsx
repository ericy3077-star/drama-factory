'use client'

import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Search, FileText, Loader2, Clock, CheckCircle2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { apiGet, apiPost } from '@/lib/api'
import type { ResearchReport } from '@/types/invest'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import { toast } from 'sonner'

const REPORT_TYPE_LABELS = {
  fundamental: '基本面',
  technical: '技术面',
  sector: '行业',
  macro: '宏观',
}

export function ResearchPanel() {
  const [ticker, setTicker] = useState('')
  const [reportType, setReportType] = useState<'fundamental' | 'technical' | 'sector' | 'macro'>('fundamental')
  const [selectedReport, setSelectedReport] = useState<ResearchReport | null>(null)

  const { data: reports = [], refetch } = useQuery({
    queryKey: ['research-reports'],
    queryFn: () => apiGet<ResearchReport[]>('/api/v1/invest/research'),
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      apiPost<ResearchReport>('/api/v1/invest/research', {
        ticker: ticker.toUpperCase(),
        report_type: reportType,
      }),
    onSuccess: (report) => {
      toast.success(`${report.ticker} 研究报告生成中...`)
      refetch()
      setTicker('')
    },
    onError: () => toast.error('报告生成失败，请稍后重试'),
  })

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Left: generate + list */}
      <div className="md:col-span-1 space-y-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">生成研究报告</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9 font-mono uppercase"
                placeholder="输入股票代码 AAPL"
                value={ticker}
                onChange={(e) => setTicker(e.target.value.toUpperCase())}
                onKeyDown={(e) => e.key === 'Enter' && ticker && generateMutation.mutate()}
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {(Object.keys(REPORT_TYPE_LABELS) as Array<keyof typeof REPORT_TYPE_LABELS>).map((t) => (
                <button
                  key={t}
                  onClick={() => setReportType(t)}
                  className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${
                    reportType === t
                      ? 'bg-primary text-primary-foreground border-primary'
                      : 'border-border text-muted-foreground hover:border-primary'
                  }`}
                >
                  {REPORT_TYPE_LABELS[t]}
                </button>
              ))}
            </div>
            <Button
              className="w-full"
              disabled={!ticker || generateMutation.isPending}
              onClick={() => generateMutation.mutate()}
            >
              {generateMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              生成报告
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">历史报告</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-80">
              <div className="p-3 space-y-2">
                {reports.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-8">暂无报告</p>
                )}
                {reports.map((r) => (
                  <button
                    key={r.id}
                    onClick={() => setSelectedReport(r)}
                    className={`w-full text-left rounded-md p-3 text-sm transition-colors ${
                      selectedReport?.id === r.id ? 'bg-accent' : 'hover:bg-accent/50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-semibold">{r.ticker}</span>
                      {r.status === 'completed' ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                      ) : (
                        <Clock className="h-3.5 w-3.5 text-yellow-500" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground truncate">{r.title}</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {formatDistanceToNow(new Date(r.created_at), { addSuffix: true, locale: zhCN })}
                    </p>
                  </button>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Right: report content */}
      <div className="md:col-span-2">
        {selectedReport ? (
          <Card className="h-full">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-lg font-bold">{selectedReport.ticker}</span>
                    <Badge variant="outline">{REPORT_TYPE_LABELS[selectedReport.report_type]}</Badge>
                    <Badge variant={selectedReport.status === 'completed' ? 'success' : 'warning'}>
                      {selectedReport.status === 'completed' ? '完成' : '生成中'}
                    </Badge>
                  </div>
                  <CardTitle className="text-base">{selectedReport.title}</CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-sm">{selectedReport.content}</pre>
                </div>
              </ScrollArea>
              {selectedReport.sources.length > 0 && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs font-medium mb-2">参考来源</p>
                  <div className="space-y-1">
                    {selectedReport.sources.map((s) => (
                      <a
                        key={s.id}
                        href={s.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-xs text-muted-foreground hover:text-primary truncate"
                      >
                        {s.title}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="flex h-full min-h-64 items-center justify-center rounded-lg border-2 border-dashed border-border">
            <div className="text-center space-y-2">
              <FileText className="h-8 w-8 mx-auto text-muted-foreground" />
              <p className="text-sm text-muted-foreground">选择一个报告或生成新报告</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
