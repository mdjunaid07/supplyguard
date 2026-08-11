import { useState, useEffect } from 'react'
import { getPackages } from '../api/client'
import { RiskBadge } from '../components/RiskCard'
import { Package, Search, ArrowUpDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import { format, parseISO } from 'date-fns'
import clsx from 'clsx'

export default function PackagesPage() {
  const [packages, setPackages] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [sortBy, setSortBy] = useState('avg_risk_score')

  useEffect(() => {
    setLoading(true)
    getPackages({ limit: 100, sort_by: sortBy })
      .then(r => setPackages(r.packages || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [sortBy])

  const filtered = packages.filter(p =>
    p.package_name?.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-white">Tracked <span className="text-gradient">Packages</span></h1>
        <p className="text-slate-400 mt-1.5">{packages.length} packages monitored across all repositories</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search packages..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-surface-card border border-surface-border rounded-xl
                       text-sm text-slate-200 placeholder-slate-500
                       focus:outline-none focus:border-brand-500 transition-colors"
            id="package-search"
          />
        </div>
        <div className="flex items-center gap-2">
          <ArrowUpDown className="w-4 h-4 text-slate-500" />
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="bg-surface-card border border-surface-border rounded-xl text-sm text-slate-200 px-3 py-2.5 focus:outline-none focus:border-brand-500 transition-colors"
            id="package-sort"
          >
            <option value="avg_risk_score">Sort: Risk Score</option>
            <option value="scan_count">Sort: Scan Count</option>
            <option value="last_scanned">Sort: Last Scanned</option>
          </select>
        </div>
      </div>

      {/* Package Grid */}
      {loading ? (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 bg-surface-card rounded-2xl border border-surface-border animate-pulse" />
          ))}
        </div>
      ) : !filtered.length ? (
        <div className="card text-center py-16 text-slate-500">
          <Package className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p>No packages found.</p>
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map(pkg => {
            const riskPct = ((pkg.avg_risk_score || 0) * 100).toFixed(1)
            const barColor =
              pkg.latest_risk_level === 'HIGH'   ? '#ef4444' :
              pkg.latest_risk_level === 'MEDIUM' ? '#f59e0b' : '#22c55e'

            return (
              <Link
                key={pkg._id}
                to={`/packages/${encodeURIComponent(pkg.package_name)}`}
                id={`pkg-card-${pkg.package_name}`}
                className={clsx(
                  'card group block hover:scale-[1.02] transition-all duration-200',
                  pkg.latest_risk_level === 'HIGH' && 'border-red-500/20 hover:border-red-500/40'
                )}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-xl bg-brand-600/10 border border-brand-500/20 flex items-center justify-center">
                    <Package className="w-5 h-5 text-brand-400" />
                  </div>
                  <RiskBadge level={pkg.latest_risk_level || 'UNKNOWN'} />
                </div>

                <h3 className="font-mono font-semibold text-white text-sm mb-1 group-hover:text-brand-300 transition-colors truncate">
                  {pkg.package_name}
                </h3>
                <p className="text-xs text-slate-500 mb-3">
                  Scanned {pkg.scan_count}× ·{' '}
                  {pkg.last_scanned ? format(parseISO(pkg.last_scanned), 'MMM dd') : '—'}
                </p>

                <div className="risk-bar mb-1.5">
                  <div
                    className="risk-bar-fill"
                    style={{ width: `${riskPct}%`, background: barColor }}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500">
                  <span>Risk</span>
                  <span className="font-semibold" style={{ color: barColor }}>{riskPct}%</span>
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
