import clsx from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

const RISK_CONFIG = {
  HIGH:    { dot: 'bg-red-500',    text: 'text-red-400',    bar: 'bg-gradient-to-r from-red-600 to-red-400',    badge: 'badge-high' },
  MEDIUM:  { dot: 'bg-amber-500',  text: 'text-amber-400',  bar: 'bg-gradient-to-r from-amber-600 to-amber-400', badge: 'badge-medium' },
  LOW:     { dot: 'bg-emerald-500',text: 'text-emerald-400',bar: 'bg-gradient-to-r from-emerald-600 to-emerald-400', badge: 'badge-low' },
  UNKNOWN: { dot: 'bg-slate-500',  text: 'text-slate-400',  bar: 'bg-slate-600', badge: '' },
}

export function RiskBadge({ level }) {
  const cfg = RISK_CONFIG[level] || RISK_CONFIG.UNKNOWN
  return (
    <span className={cfg.badge}>
      <span className={clsx('w-1.5 h-1.5 rounded-full inline-block', cfg.dot)} />
      {level}
    </span>
  )
}

export default function RiskCard({ title, value, subtitle, icon: Icon, trend, riskLevel, className }) {
  const cfg = RISK_CONFIG[riskLevel] || {}
  const trendIcon =
    trend > 0 ? <TrendingUp className="w-3.5 h-3.5 text-red-400" /> :
    trend < 0 ? <TrendingDown className="w-3.5 h-3.5 text-emerald-400" /> :
                <Minus className="w-3.5 h-3.5 text-slate-500" />

  return (
    <div className={clsx('stat-card group', className)}>
      <div className="flex items-start justify-between">
        <div className="flex flex-col gap-1">
          <p className="stat-label">{title}</p>
          <p className={clsx('stat-value', cfg.text)}>{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        {Icon && (
          <div className={clsx(
            'w-11 h-11 rounded-xl flex items-center justify-center',
            'bg-white/5 border border-surface-border',
            'group-hover:scale-110 transition-transform duration-200'
          )}>
            <Icon className={clsx('w-5 h-5', cfg.text || 'text-brand-400')} />
          </div>
        )}
      </div>
      {trend !== undefined && (
        <div className="flex items-center gap-1 mt-2">
          {trendIcon}
          <span className="text-xs text-slate-500">
            {Math.abs(trend)}% vs last period
          </span>
        </div>
      )}
    </div>
  )
}
