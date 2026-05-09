import { useEffect, useState } from 'react'
import { fetchBacklogItems } from '../lib/api'
import type { BacklogItem } from '@shared/types'
import { Badge } from '../components/Badge'
import { Loader2, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

export function RoutingHealthView() {
  const [items, setItems] = useState<BacklogItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      setLoading(true)
      const response = await fetchBacklogItems()
      const routingItems = response.items.filter(
        item => item.status !== 'DONE' && 
        (item.entry_point === 'ROUTING_MISSING' || item.entry_point === 'ROUTING_BLOCKED')
      )
      setItems(routingItems)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load items')
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

  const blockedCount = items.filter(item => item.entry_point === 'ROUTING_BLOCKED').length
  const missingCount = items.filter(item => item.entry_point === 'ROUTING_MISSING').length

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-foreground">Routing Health</h2>
        <p className="text-muted-foreground mt-2">Items requiring routing attention</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-red-500/10">
              <XCircle className="w-6 h-6 text-red-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Routing Blocked</p>
              <p className="text-3xl font-bold text-foreground">{blockedCount}</p>
            </div>
          </div>
        </div>

        <div className="bg-card border border-border rounded-lg p-6">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-lg bg-yellow-500/10">
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Routing Missing</p>
              <p className="text-3xl font-bold text-foreground">{missingCount}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-foreground">Items Requiring Attention</h3>
        
        {items.length === 0 ? (
          <div className="bg-card border border-border rounded-lg p-8 text-center">
            <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
            <p className="text-muted-foreground">All items have proper routing</p>
          </div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="bg-card border border-border rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h4 className="text-lg font-semibold text-foreground">{item.title}</h4>
                  <p className="text-sm text-muted-foreground mt-1">{item.id}</p>
                </div>
                <Badge 
                  variant={item.entry_point === 'ROUTING_BLOCKED' ? 'destructive' : 'secondary'}
                >
                  {item.entry_point}
                </Badge>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Status</p>
                  <p className="text-sm font-medium text-foreground">{item.status}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wide">Routing Reason</p>
                  <p className="text-sm font-medium text-foreground">{item.routing_reason || 'Not set'}</p>
                </div>
              </div>

              {item.routing_reason && (
                <div className="mt-4 p-3 bg-accent rounded">
                  <p className="text-xs text-muted-foreground uppercase tracking-wide mb-1">Routing Reason</p>
                  <p className="text-sm text-accent-foreground">{item.routing_reason}</p>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
