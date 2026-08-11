import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getPackage } from '../api/client'
import { RiskBadge } from '../components/RiskCard'
import { ArrowLeft, Package, Shield, Clock, GitCommit, Star, AlertTriangle } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, ResponsiveContainer, Tooltip,
} from 'recharts'

export default function PackageDetailPage() {
  const { name } = useParams()
  const [pkg, setPkg] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getPackage(decodeURIComponent(name))
      .then(setPkg)
      .catch(() => setError('Package not found'))
      .finally(() => setLoading(false))
  }, [name])

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 flex justify-center">
        <div className="w-10 h-10 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (error || !pkg) {
    return (
      <div className="max-w-5xl mx-auto px-6 py-8 text-center text-slate-400">
        <Package className="w-10 h-10 mx-auto mb-2 opacity-30" />
        <p>{error || 'Package not found'}</p>
        <Link to="/packages" className="btn-ghost mt-4 inline-flex">← Back</Link>
      </div>
    )
  }

  const history = pkg.features_history || []
  const latest = history[history.length - 1] || {}

  const radarData = [
    { subject: 'Age',         value: Math.min((latest.package_age_days || 0) / 3650, 1) * 100 },
    { subject: 'Maintainers', value: Math.min((latest.maintainer_count || 0) / 10, 1) * 100 },
    { subject: 'Activity',    value: Math.min((latest.commits_per_month || 0) / 30, 1) * 100 },
    { subject: 'Popularity',  value: (latest.repo_popularity_score || 0) * 100 },
    { subject: 'Safety',      value: (1 - (latest.cve_severity_score || 0)) * 100 },
    { subject: 'Trust',       value: (1 - (pkg.avg_risk_score || 0)) * 100 },
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      <Link to="/packages" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-brand-300 transition-colors">
        <ArrowLeft className="w-4 h-4" /> All Packages
      </Link>

      {/* Header */}
      <div className="card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-brand-600/15 border border-brand-500/20 flex items-center justify-center">
              <Package className="w-7 h-7 text-brand-400" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-mono text-white">{pkg.package_name}</h1>
              <p className="text-sm text-slate-400 mt-0.5">Scanned {pkg.scan_count}× · Last seen {pkg.last_scanned ? format(parseISO(pkg.last_scanned), 'MMM dd, yyyy') : '—'}</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-3xl font-bold text-white">{((pkg.avg_risk_score || 0) * 100).toFixed(1)}%</p>
              <p className="text-xs text-slate-400">Risk Score</p>
            </div>
            <RiskBadge level={pkg.latest_risk_level || 'UNKNOWN'} />
          </div>
        </div>

        {/* Risk bar */}
        <div className="mt-4">
          <div className="risk-bar h-3">
            <div
              className="risk-bar-fill"
              style={{
                width: `${(pkg.avg_risk_score || 0) * 100}%`,
                background: pkg.latest_risk_level === 'HIGH' ? 'linear-gradient(90deg,#dc2626,#ef4444)' :
                            pkg.latest_risk_level === 'MEDIUM' ? 'linear-gradient(90deg,#d97706,#f59e0b)' :
                            'linear-gradient(90deg,#16a34a,#22c55e)',
              }}
            />
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Radar Chart */}
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">📡 Health Radar</h2>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radarData}>
              <PolarGrid stroke="#2a2a45" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Radar
                name="Score"
                dataKey="value"
                stroke="#6366f1"
                fill="#6366f1"
                fillOpacity={0.25}
                strokeWidth={2}
              />
              <Tooltip
                formatter={(v) => [`${v.toFixed(1)}%`]}
                contentStyle={{ background: '#16162a', border: '1px solid #2a2a45', borderRadius: '12px', color: '#e2e8f0' }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Key Metrics */}
        <div className="card space-y-4">
          <h2 className="text-lg font-semibold text-white">📊 Key Metrics</h2>
          {[
            { icon: Clock,        label: 'Package Age',       value: `${(latest.package_age_days || 0).toFixed(0)} days` },
            { icon: Shield,       label: 'Maintainers',       value: latest.maintainer_count ?? '—' },
            { icon: GitCommit,    label: 'Commits / Month',   value: (latest.commits_per_month || 0).toFixed(1) },
            { icon: Star,         label: 'Popularity Score',  value: ((latest.repo_popularity_score || 0) * 100).toFixed(1) + '%' },
            { icon: AlertTriangle,label: 'CVE Count',         value: latest.cve_count ?? 0 },
            { icon: AlertTriangle,label: 'CVE Severity',      value: (latest.cve_severity_score || 0).toFixed(2) },
          ].map(({ icon: Icon, label, value }) => (
            <div key={label} className="flex items-center justify-between py-2 border-b border-surface-border/50 last:border-0">
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <Icon className="w-4 h-4 text-brand-400" />
                {label}
              </div>
              <span className="text-sm font-mono font-semibold text-white">{value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Feature History */}
      {history.length > 1 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-white mb-4">📜 Scan History ({history.length} records)</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  <th className="table-head text-left">#</th>
                  <th className="table-head text-left">Version</th>
                  <th className="table-head text-center">Risk Score</th>
                  <th className="table-head text-center">CVEs</th>
                  <th className="table-head text-center">Maintainers</th>
                  <th className="table-head text-center">Spike</th>
                </tr>
              </thead>
              <tbody>
                {history.slice().reverse().map((h, i) => (
                  <tr key={i} className="table-row">
                    <td className="table-cell text-slate-500">{history.length - i}</td>
                    <td className="table-cell font-mono text-slate-300">{h.version || '—'}</td>
                    <td className="table-cell text-center">
                      <span className="font-semibold text-white">
                        {((h.historical_risk_score || 0) * 100).toFixed(1)}%
                      </span>
                    </td>
                    <td className="table-cell text-center text-slate-300">{h.cve_count ?? 0}</td>
                    <td className="table-cell text-center text-slate-300">{h.maintainer_count ?? '—'}</td>
                    <td className="table-cell text-center text-slate-300">{(h.version_spike_ratio || 0).toFixed(2)}×</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
