import { useState, useEffect } from 'react'
import { getScans } from '../api/client'
import { RiskBadge } from '../components/RiskCard'
import { GitPullRequest, Search, Filter, ExternalLink, Clock } from 'lucide-react'
import { format, parseISO } from 'date-fns'
import { Link } from 'react-router-dom'
import clsx from 'clsx'

const FILTERS = ['ALL', 'HIGH', 'MEDIUM', 'LOW']

export default function ScanHistory() {
  const [scans, setScans] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const LIMIT = 15

  useEffect(() => {
    setLoading(true)
    const params = { limit: LIMIT, skip: page * LIMIT }
    if (filter !== 'ALL') params.risk_level = filter
    getScans(params)
      .then(r => { setScans(r.scans || []); setTotal(r.total || 0) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [page, filter])

  const filtered = search
    ? scans.filter(s =>
        s.repo_full_name?.toLowerCase().includes(search.toLowerCase()) ||
        String(s.pr_number).includes(search)
      )
    : scans

  const totalPages = Math.ceil(total / LIMIT)

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 animate-fade-in">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Scan <span className="text-gradient">History</span></h1>
        <p className="text-slate-400 mt-1.5">{total} PR scans recorded</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            placeholder="Search by repo or PR number..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-surface-card border border-surface-border rounded-xl
                       text-sm text-slate-200 placeholder-slate-500
                       focus:outline-none focus:border-brand-500 transition-colors"
            id="scan-search"
          />
        </div>
        <div className="flex gap-2">
          <Filter className="w-4 h-4 text-slate-500 self-center" />
          {FILTERS.map(f => (
            <button
              key={f}
              onClick={() => { setFilter(f); setPage(0) }}
              className={clsx(
                'px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-200',
                filter === f
                  ? f === 'HIGH'   ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                  : f === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  : f === 'LOW'    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                  :                  'bg-brand-600/20 text-brand-300 border border-brand-500/20'
                  : 'btn-ghost text-xs'
              )}
              id={`filter-${f.toLowerCase()}`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="border-b border-surface-border bg-surface-muted/50">
              <tr>
                <th className="table-head text-left">Repository / PR</th>
                <th className="table-head text-center">Packages</th>
                <th className="table-head text-center">🔴 HIGH</th>
                <th className="table-head text-center">🟡 MEDIUM</th>
                <th className="table-head text-center">🟢 LOW</th>
                <th className="table-head text-left">Scanned At</th>
                <th className="table-head text-center">Comment</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <tr key={i} className="border-b border-surface-border/40">
                    {[...Array(7)].map((_, j) => (
                      <td key={j} className="table-cell">
                        <div className="h-4 bg-surface-muted rounded animate-pulse" />
                      </td>
                    ))}
                  </tr>
                ))
              ) : !filtered.length ? (
                <tr>
                  <td colSpan={7} className="py-16 text-center text-slate-500">
                    <GitPullRequest className="w-8 h-8 mx-auto mb-2 opacity-30" />
                    <p className="text-sm">No scans found.</p>
                  </td>
                </tr>
              ) : filtered.map(scan => (
                <tr key={scan._id} className="table-row">
                  <td className="table-cell">
                    <Link
                      to={`/scans/${scan._id}`}
                      className="group flex items-center gap-2 hover:text-brand-300 transition-colors"
                      id={`scan-link-${scan._id}`}
                    >
                      <GitPullRequest className="w-4 h-4 text-brand-400 flex-shrink-0" />
                      <div>
                        <p className="text-sm font-medium text-slate-200 group-hover:text-brand-300">
                          {scan.repo_full_name}
                        </p>
                        <p className="text-xs text-slate-500">PR #{scan.pr_number}</p>
                      </div>
                    </Link>
                  </td>
                  <td className="table-cell text-center">
                    <span className="text-sm font-mono text-slate-300">{scan.packages_scanned}</span>
                  </td>
                  <td className="table-cell text-center">
                    {scan.high_risk_count > 0
                      ? <span className="badge-high">{scan.high_risk_count}</span>
                      : <span className="text-slate-600 text-sm">—</span>}
                  </td>
                  <td className="table-cell text-center">
                    {scan.medium_risk_count > 0
                      ? <span className="badge-medium">{scan.medium_risk_count}</span>
                      : <span className="text-slate-600 text-sm">—</span>}
                  </td>
                  <td className="table-cell text-center">
                    {scan.low_risk_count > 0
                      ? <span className="badge-low">{scan.low_risk_count}</span>
                      : <span className="text-slate-600 text-sm">—</span>}
                  </td>
                  <td className="table-cell">
                    <div className="flex items-center gap-1.5 text-xs text-slate-400">
                      <Clock className="w-3.5 h-3.5" />
                      {scan.scanned_at ? format(parseISO(scan.scanned_at), 'MMM dd, HH:mm') : '—'}
                    </div>
                  </td>
                  <td className="table-cell text-center">
                    {scan.comment_url ? (
                      <a
                        href={scan.comment_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300"
                        id={`comment-link-${scan._id}`}
                      >
                        <ExternalLink className="w-3.5 h-3.5" /> View
                      </a>
                    ) : (
                      <span className="text-slate-600 text-xs">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-surface-border">
            <p className="text-xs text-slate-500">
              Showing {page * LIMIT + 1}–{Math.min((page + 1) * LIMIT, total)} of {total}
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => setPage(p => Math.max(0, p - 1))}
                disabled={page === 0}
                className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-40"
                id="prev-page"
              >
                ← Prev
              </button>
              <button
                onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="btn-ghost text-xs px-3 py-1.5 disabled:opacity-40"
                id="next-page"
              >
                Next →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
