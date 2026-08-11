import { useState, useEffect, useRef } from 'react'
import { getGraphData } from '../api/client'
import { AlertCircle, RefreshCw } from 'lucide-react'

const RISK_COLORS = {
  HIGH:    '#ef4444',
  MEDIUM:  '#f59e0b',
  LOW:     '#22c55e',
  UNKNOWN: '#6366f1',
}

export default function TrustGraph() {
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const canvasRef = useRef(null)
  const animRef = useRef(null)
  const nodesRef = useRef([])

  useEffect(() => {
    loadGraph()
  }, [])

  const loadGraph = async () => {
    try {
      setLoading(true)
      const data = await getGraphData()
      setGraphData(data)
      initCanvas(data.nodes)
    } catch (e) {
      setError('Failed to load graph data')
    } finally {
      setLoading(false)
    }
  }

  const initCanvas = (nodes) => {
    const canvas = canvasRef.current
    if (!canvas || !nodes?.length) return
    const W = canvas.width = canvas.offsetWidth
    const H = canvas.height = canvas.offsetHeight

    // Assign random positions with physics
    nodesRef.current = nodes.map((n, i) => ({
      ...n,
      x: W / 2 + (Math.random() - 0.5) * W * 0.7,
      y: H / 2 + (Math.random() - 0.5) * H * 0.7,
      vx: 0, vy: 0,
      r: 8 + (n.scan_count || 1) * 2,
    }))
    animate(canvas)
  }

  const animate = (canvas) => {
    if (animRef.current) cancelAnimationFrame(animRef.current)
    const ctx = canvas.getContext('2d')

    const step = () => {
      const W = canvas.width, H = canvas.height
      ctx.clearRect(0, 0, W, H)

      const nodes = nodesRef.current
      // Simple repulsion
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const dx = nodes[j].x - nodes[i].x
          const dy = nodes[j].y - nodes[i].y
          const dist = Math.sqrt(dx * dx + dy * dy) || 1
          const force = Math.min(500 / (dist * dist), 3)
          nodes[i].vx -= (dx / dist) * force
          nodes[i].vy -= (dy / dist) * force
          nodes[j].vx += (dx / dist) * force
          nodes[j].vy += (dy / dist) * force
        }
        // Gravity to center
        nodes[i].vx += (W / 2 - nodes[i].x) * 0.001
        nodes[i].vy += (H / 2 - nodes[i].y) * 0.001
        // Damping
        nodes[i].vx *= 0.9
        nodes[i].vy *= 0.9
        nodes[i].x += nodes[i].vx
        nodes[i].y += nodes[i].vy
        nodes[i].x = Math.max(nodes[i].r, Math.min(W - nodes[i].r, nodes[i].x))
        nodes[i].y = Math.max(nodes[i].r, Math.min(H - nodes[i].r, nodes[i].y))
      }

      // Draw nodes
      nodes.forEach(n => {
        const color = RISK_COLORS[n.risk_level] || RISK_COLORS.UNKNOWN
        // Glow
        ctx.shadowColor = color
        ctx.shadowBlur = 12
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fillStyle = color + '33'
        ctx.fill()
        ctx.strokeStyle = color
        ctx.lineWidth = 2
        ctx.stroke()
        ctx.shadowBlur = 0

        // Label
        ctx.fillStyle = '#e2e8f0'
        ctx.font = '10px Inter'
        ctx.textAlign = 'center'
        const label = n.name?.length > 12 ? n.name.slice(0, 12) + '…' : (n.name || n.id)
        ctx.fillText(label, n.x, n.y + n.r + 14)
      })

      animRef.current = requestAnimationFrame(step)
    }
    step()
  }

  useEffect(() => () => { if (animRef.current) cancelAnimationFrame(animRef.current) }, [])

  const isEmpty = !graphData.nodes?.length

  return (
    <div className="card h-[420px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">🕸️ Trust Graph</h2>
          <p className="text-xs text-slate-400 mt-0.5">{graphData.nodes?.length || 0} packages tracked</p>
        </div>
        <button onClick={loadGraph} className="btn-ghost p-2" title="Refresh">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="flex items-center gap-4 mb-3">
        {Object.entries(RISK_COLORS).map(([level, color]) => (
          <span key={level} className="flex items-center gap-1.5 text-xs text-slate-400">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {level}
          </span>
        ))}
      </div>

      <div className="flex-1 rounded-xl overflow-hidden bg-surface/50 border border-surface-border relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
        {error && !loading && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-400">
            <AlertCircle className="w-8 h-8 text-red-400" />
            <p className="text-sm">{error}</p>
          </div>
        )}
        {!loading && isEmpty && !error && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-500">
            <p className="text-sm">No packages scanned yet.</p>
            <p className="text-xs">Open a PR with package.json changes to populate this graph.</p>
          </div>
        )}
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ display: isEmpty ? 'none' : 'block' }}
        />
      </div>
    </div>
  )
}
