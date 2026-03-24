/**
 * AnalyticsCard
 *
 * KPI / stats card for the owner dashboard.
 *
 * Props:
 *   label        string         — metric name (e.g. "Total Reviews")
 *   value        string|number  — main figure
 *   icon         string         — emoji icon
 *   trend        number         — % change vs prior period (optional, + or -)
 *   trendLabel   string         — context label (e.g. "vs last month")
 *   to           string         — react-router link (makes the card clickable)
 *   loading      boolean        — show skeleton
 *   color        'brand'|'green'|'amber'|'red'|'purple'  — accent color (default: 'brand')
 *   className    string
 */
import { Link } from 'react-router-dom'

const COLOR_MAP = {
  brand:  { bg: 'bg-brand-50',  text: 'text-brand-600',  badge: 'bg-brand-100 text-brand-700'  },
  green:  { bg: 'bg-green-50',  text: 'text-green-600',  badge: 'bg-green-100 text-green-700'  },
  amber:  { bg: 'bg-amber-50',  text: 'text-amber-600',  badge: 'bg-amber-100 text-amber-700'  },
  red:    { bg: 'bg-red-50',    text: 'text-red-600',    badge: 'bg-red-100 text-red-700'      },
  purple: { bg: 'bg-purple-50', text: 'text-purple-600', badge: 'bg-purple-100 text-purple-700'},
}

function TrendBadge({ trend, trendLabel }) {
  if (trend == null) return null
  const isPos = trend >= 0
  return (
    <div className="flex items-center gap-1 mt-2">
      <span className={`text-xs font-semibold ${isPos ? 'text-green-600' : 'text-red-500'}`}>
        {isPos ? '▲' : '▼'} {Math.abs(trend).toFixed(1)}%
      </span>
      {trendLabel && <span className="text-xs text-gray-400">{trendLabel}</span>}
    </div>
  )
}

function CardContent({ label, value, icon, trend, trendLabel, color = 'brand', loading }) {
  const c = COLOR_MAP[color] || COLOR_MAP.brand

  if (loading) {
    return (
      <div className="card p-5 space-y-3 animate-pulse">
        <div className="flex items-center gap-3">
          <div className={`w-10 h-10 rounded-xl ${c.bg}`} />
          <div className="flex-1 space-y-1.5">
            <div className="h-5 w-16 bg-gray-200 rounded" />
            <div className="h-3 w-24 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex items-start gap-4">
      <div className={`w-11 h-11 rounded-xl ${c.bg} flex items-center justify-center text-xl flex-shrink-0`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-medium uppercase tracking-wide truncate">{label}</p>
        <p className={`text-2xl font-bold mt-0.5 ${c.text}`}>{value ?? '—'}</p>
        <TrendBadge trend={trend} trendLabel={trendLabel} />
      </div>
    </div>
  )
}

export default function AnalyticsCard({
  label,
  value,
  icon,
  trend,
  trendLabel,
  to,
  loading = false,
  color = 'brand',
  className = '',
}) {
  const inner = (
    <CardContent
      label={label}
      value={value}
      icon={icon}
      trend={trend}
      trendLabel={trendLabel}
      color={color}
      loading={loading}
    />
  )

  const baseClass = `card p-5 transition ${to ? 'hover:shadow-md cursor-pointer' : ''} ${className}`

  if (to) {
    return (
      <Link to={to} className={baseClass}>
        {inner}
      </Link>
    )
  }

  return <div className={baseClass}>{inner}</div>
}
