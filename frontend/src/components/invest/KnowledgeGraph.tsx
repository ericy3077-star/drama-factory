'use client'

import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'
import { apiGet } from '@/lib/api'
import type { KnowledgeGraph as KGType } from '@/types/invest'

interface KnowledgeGraphProps {
  entityId?: string
}

const NODE_COLORS: Record<string, string> = {
  company: '#2563eb',
  person: '#7c3aed',
  event: '#dc2626',
  concept: '#059669',
  ticker: '#d97706',
}

export function KnowledgeGraph({ entityId }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const { data: graph, isLoading } = useQuery({
    queryKey: ['knowledge-graph', entityId],
    queryFn: () => apiGet<KGType>(`/api/v1/invest/graph${entityId ? `?entity_id=${entityId}` : ''}`),
    enabled: true,
  })

  useEffect(() => {
    if (!graph || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Simple force-directed layout (placeholder visual)
    const { nodes, edges } = graph
    const W = canvas.offsetWidth
    const H = canvas.offsetHeight
    canvas.width = W
    canvas.height = H

    // Position nodes in a circle
    const positions: Record<string, { x: number; y: number }> = {}
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2
      const r = Math.min(W, H) * 0.35
      positions[node.id] = {
        x: W / 2 + r * Math.cos(angle),
        y: H / 2 + r * Math.sin(angle),
      }
    })

    ctx.clearRect(0, 0, W, H)

    // Draw edges
    ctx.strokeStyle = '#94a3b8'
    ctx.lineWidth = 1
    edges.forEach((edge) => {
      const from = positions[edge.source]
      const to = positions[edge.target]
      if (!from || !to) return
      ctx.beginPath()
      ctx.moveTo(from.x, from.y)
      ctx.lineTo(to.x, to.y)
      ctx.globalAlpha = 0.4 + edge.weight * 0.6
      ctx.stroke()
      ctx.globalAlpha = 1

      // Edge label
      const mx = (from.x + to.x) / 2
      const my = (from.y + to.y) / 2
      ctx.fillStyle = '#64748b'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(edge.label, mx, my - 4)
    })

    // Draw nodes
    nodes.forEach((node) => {
      const pos = positions[node.id]
      if (!pos) return
      const color = NODE_COLORS[node.type] ?? '#64748b'

      ctx.beginPath()
      ctx.arc(pos.x, pos.y, 18, 0, 2 * Math.PI)
      ctx.fillStyle = color
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()

      ctx.fillStyle = '#fff'
      ctx.font = 'bold 9px sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(node.label.slice(0, 4), pos.x, pos.y)

      ctx.fillStyle = '#1e293b'
      ctx.font = '11px sans-serif'
      ctx.textBaseline = 'top'
      ctx.fillText(node.label, pos.x, pos.y + 22)
    })
  }, [graph])

  return (
    <Card>
      <CardHeader className="pb-3 flex-row items-center justify-between">
        <CardTitle className="text-base">知识图谱</CardTitle>
        <div className="flex flex-wrap gap-1">
          {Object.entries(NODE_COLORS).map(([type, color]) => (
            <Badge key={type} variant="outline" className="text-[10px] gap-1">
              <span className="h-2 w-2 rounded-full inline-block" style={{ backgroundColor: color }} />
              {type}
            </Badge>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : !graph || graph.nodes.length === 0 ? (
          <div className="flex h-64 items-center justify-center text-sm text-muted-foreground">
            暂无知识图谱数据
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            className="w-full h-64 rounded-md bg-slate-50 dark:bg-slate-900"
          />
        )}
      </CardContent>
    </Card>
  )
}
