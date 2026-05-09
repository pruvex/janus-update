import { useEffect, useState } from 'react'
import { fetchBacklogItems } from '../lib/api'
import type { BacklogCounts } from '@shared/types'
import { Loader2, LayoutDashboard, CheckCircle, AlertCircle, Clock, Ban } from 'lucide-react'

export function KPIView() {
  const [counts, setCounts] = useState<BacklogCounts | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadCounts()
  }, [])

  const loadCounts = async () => {
    try {
      setLoading(true)
      const response = await fetchBacklogItems()
      setCounts(response.counts)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load counts')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-destructive">{error}</p>
      </div>
    )
  }

  if (!counts) {
    return null
  }

  const kpiCards = [
    {
      label: 'Total Items',
      value: counts.total,
      icon: LayoutDashboard,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Active',
      value: counts.active,
      icon: Clock,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
    {
      label: 'Done',
      value: counts.done,
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
    {
      label: 'Needs Info',
      value: counts.needs_info,
      icon: AlertCircle,
      color: 'text-orange-500',
      bgColor: 'bg-orange-500/10',
    },
    {
      label: 'Blocked',
      value: counts.blocked,
      icon: Ban,
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
    },
  ]

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground">KPI Overview</h2>
        <p className="text-muted-foreground mt-2">Backlog metrics and statistics</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {kpiCards.map((kpi) => {
          const Icon = kpi.icon
          return (
            <div key={kpi.label} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-lg ${kpi.bgColor}`}>
                  <Icon className={`w-6 h-6 ${kpi.color}`} />
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">{kpi.label}</p>
                  <p className="text-3xl font-bold text-foreground">{kpi.value}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      <div className="mt-8 bg-card border border-border rounded-lg p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Additional Metrics</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-muted-foreground">Ready</p>
            <p className="text-2xl font-bold text-foreground">{counts.ready}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">In Progress</p>
            <p className="text-2xl font-bold text-foreground">{counts.in_progress}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Routing Missing</p>
            <p className="text-2xl font-bold text-foreground">{counts.routing_missing}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Routing Blocked</p>
            <p className="text-2xl font-bold text-foreground">{counts.routing_blocked}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
