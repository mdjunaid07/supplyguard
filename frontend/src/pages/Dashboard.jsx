import { useState, useEffect } from 'react'
import { getOverviewStats, getScans, getPackages } from '../api/client'
import RiskCard from '../components/RiskCard'
import RiskTrend from '../components/RiskTrend'
import TrustGraph from '../components/TrustGraph'
import { RiskBadge } from '../components/RiskCard'
import {
  Shield, AlertTriangle, Package, Activity,
  ExternalLink, GitPullRequest, Clock,
} from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { Link } from 'react-router-dom'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [recentScans, setRecentScans] = useState([])
  const [topPackages, setTopPackages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getOverviewStats(),
      getScans({ limit: 5 }),
      getPackages({ limit: 5, sort_by: 'avg_risk_score' }),
    ]).then(([s, sc, pk]) => {
      setStats(s)
      setRecentScans(sc.scans || [])
      setTopPackages(pk.packages || [])
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">
          Supply Chain <span className="text-gradient">Intelligence</span>
        </h1>
        <p className="text-slate-400 mt-1.5">
          AI-powered risk analysis for your npm dependencies
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <RiskCard
          title="Total Scans"
          value={loading ? '—' : stats?.total_scans ?? 0}
          subtitle="All time PR scans"
          icon={Activity}
        />
        <RiskCard
          title="High Risk Packages"
          value={loading ? '—' : stats?.high_risk_packages ?? 0}
          subtitle="Require immediate review"
          icon={AlertTriangle}
          riskLevel="HIGH"
        />
        <RiskCard
          title="Packages Tracked"
          value={loading ? '—' : stats?.total_packages ?? 0}
          subtitle="Across all repositories"
          icon={Package}
        />
        <RiskCard
          title="Scans This Week"
          value={loading ? '—' : stats?.recent_scans_7d ?? 0}
          subtitle="Last 7 days"
          icon={Shield}
        />
      </div>

      {/* Risk Trend Chart + Graph */}
      <div className="grid lg:grid-cols-2 gap-6">
        <RiskTrend days={30} />
        <TrustGraph />
      </div>

      {/* Recent Scans + Top Risk Packages */}
      <div className="grid lg:grid-cols-2 gap-6">

        {/* Recent Scans */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white">🔍 Recent PR Scans</h2>
            <Link to="/scans" className="text-xs text-brand-400 hover:text-brand-300 transition-colors">
              View all →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-14 bg-surface-muted rounded-xl animate-pulse" />
              ))}
            </div>
          ) : !recentScans.length ? (
            <div className="text-center py-8 text-slate-500">
              <GitPullRequest className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No scans yet. Open a PR to trigger analysis.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {recentScans.map(scan => (
                <Link
                  key={scan._id}
                  to={`/scans/${scan._id}`}
                  className="flex items-center justify-between p-3 rounded-xl bg-surface-muted hover:bg-white/5 border border-surface-border/50 hover:border-brand-600/30 transition-all duration-200 group"
                  id={`scan-${scan._id}`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-brand-600/15 border border-brand-500/20 flex items-center justify-center flex-shrink-0">
                      <GitPullRequest className="w-4 h-4 text-brand-400" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">
                        {scan.repo_full_name} <span className="text-slate-500">#{scan.pr_number}</span>
                      </p>
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {format(parseISO(scan.scanned_at), 'MMM dd, HH:mm')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {scan.high_risk_count > 0 && (
                      <span className="badge-high">{scan.high_risk_count} HIGH</span>
                    )}
                    {scan.medium_risk_count > 0 && !scan.high_risk_count && (
                      <span className="badge-medium">{scan.medium_risk_count} MED</span>
                    )}
                    {!scan.high_risk_count && !scan.medium_risk_count && (
                      <span className="badge-low">CLEAN</span>
                    )}
                    <ExternalLink className="w-3 h-3 text-slate-600 group-hover:text-brand-400 transition-colors" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Top Risk Packages */}
        <div className="card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-lg font-semibold text-white">⚠️ Highest Risk Packages</h2>
            <Link to="/packages" className="text-xs text-brand-400 hover:text-brand-300 transition-colors">
              View all →
            </Link>
          </div>
          {loading ? (
            <div className="space-y-3">
              {[1,2,3].map(i => (
                <div key={i} className="h-14 bg-surface-muted rounded-xl animate-pulse" />
              ))}
            </div>
          ) : !topPackages.length ? (
            <div className="text-center py-8 text-slate-500">
              <Package className="w-8 h-8 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No packages tracked yet.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {topPackages.map(pkg => (
                <Link
                  key={pkg._id}
                  to={`/packages/${encodeURIComponent(pkg.package_name)}`}
                  className="block p-3 rounded-xl bg-surface-muted hover:bg-white/5 border border-surface-border/50 hover:border-brand-600/30 transition-all"
                  id={`pkg-${pkg.package_name}`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-mono font-medium text-slate-200">
                      {pkg.package_name}
                    </span>
                    <RiskBadge level={pkg.latest_risk_level} />
                  </div>
                  <div className="risk-bar">
                    <div
                      className="risk-bar-fill"
                      style={{
                        width: `${(pkg.avg_risk_score || 0) * 100}%`,
                        background: pkg.latest_risk_level === 'HIGH' ? '#ef4444' :
                                    pkg.latest_risk_level === 'MEDIUM' ? '#f59e0b' : '#22c55e',
                      }}
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">
                    Risk: {((pkg.avg_risk_score || 0) * 100).toFixed(1)}% · Scanned {pkg.scan_count}×
                  </p>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
