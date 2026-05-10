import { useEffect, useState } from 'react'
import { fetchBacklogItems } from '../lib/api'
import type { BacklogItem } from '@shared/types'
import { KanbanCard } from '../components/KanbanCard'
import { Loader2, AlertTriangle, Info, CheckCircle, XCircle } from 'lucide-react'

const COLUMNS = [
  'BUG',
  'ÄNDERUNG',
  'ERWEITERUNG',
  'VERBESSERUNG',
  'TECHNISCHE SCHULDEN',
  'UNKLAR',
  'SPEC FEATURE'
] as const

const COLUMN_TYPE_MAPPING: Record<string, string> = {
  'BUG': 'BUG',
  'ÄNDERUNG': 'CHANGE',
  'ERWEITERUNG': 'ENHANCEMENT',
  'VERBESSERUNG': 'IMPROVEMENT',
  'TECHNISCHE SCHULDEN': 'TECH_DEBT',
  'UNKLAR': 'UNCLEAR',
  'SPEC FEATURE': 'SPEC FEATURE'
}

const IMPORTANCE_WEIGHTS: Record<string, number> = {
  'CRITICAL': 4,
  'HIGH': 3,
  'MEDIUM': 2,
  'LOW': 1
}

const RISK_WEIGHTS: Record<string, number> = {
  'HIGH': 3,
  'MEDIUM': 2,
  'LOW': 1
}

const EFFORT_WEIGHTS: Record<string, number> = {
  'XL': 5,
  'L': 4,
  'M': 3,
  'S': 2,
  'XS': 1
}

const CONFIDENCE_WEIGHTS: Record<string, number> = {
  'HIGH': 3,
  'MEDIUM': 2,
  'LOW': 1,
  'null': 0
}

function calculatePriorityScore(item: BacklogItem): number {
  const importance = IMPORTANCE_WEIGHTS[item.importance] || 0
  const risk = RISK_WEIGHTS[item.implementation_risk] || 0
  const effort = EFFORT_WEIGHTS[item.effort] || 0
  const confidence = item.routing_confidence ? CONFIDENCE_WEIGHTS[item.routing_confidence] || 0 : 0
  
  return importance + confidence - risk - effort
}

export function ActiveView() {
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
      const activeItems = response.items.filter(item => item.status !== 'DONE')
      setItems(activeItems)
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

  const getColumnItems = (columnType: string) => {
    const englishType = COLUMN_TYPE_MAPPING[columnType] || columnType
    return items
      .filter(item => item.type === englishType)
      .sort((a, b) => calculatePriorityScore(b) - calculatePriorityScore(a))
  }

  // Calculate KPI metrics
  const totalItems = items.length
  const activeItems = items.filter(item => item.status === 'IN PROGRESS' || item.status === 'READY').length
  const needsInfo = items.filter(item => item.status === 'NEEDS INFO').length
  const blocked = items.filter(item => item.status === 'BLOCKED').length
  const done = items.filter(item => item.status === 'DONE').length
  const routingMissing = items.filter(item => !item.entry_point || item.entry_point === 'null' || item.entry_point === '').length
  const routingBlocked = items.filter(item => item.entry_point === 'ROUTING_BLOCKED').length

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h2 className="text-xl font-bold text-foreground">Active Backlog</h2>
      </div>

      {/* KPI Bar */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="grid grid-cols-7 gap-2">
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-blue-400" />
              <span className="text-[10px] text-muted-foreground">Total</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{totalItems}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <Info className="w-3 h-3 text-green-400" />
              <span className="text-[10px] text-muted-foreground">Active</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{activeItems}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3 text-yellow-400" />
              <span className="text-[10px] text-muted-foreground">Needs Info</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{needsInfo}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <XCircle className="w-3 h-3 text-red-400" />
              <span className="text-[10px] text-muted-foreground">Blocked</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{blocked}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] text-muted-foreground">Done</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{done}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <XCircle className="w-3 h-3 text-orange-400" />
              <span className="text-[10px] text-muted-foreground">Routing Missing</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{routingMissing}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <XCircle className="w-3 h-3 text-purple-400" />
              <span className="text-[10px] text-muted-foreground">Routing Blocked</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{routingBlocked}</p>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-hidden p-4">
        <div className="h-full w-full grid grid-cols-7 gap-3">
          {COLUMNS.map((column) => {
            const columnItems = getColumnItems(column)
            return (
              <div key={column} className="flex flex-col bg-card border border-border rounded-lg min-w-0">
                <div className="p-3 border-b border-border bg-muted/50">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-foreground text-sm truncate">{column}</h3>
                    <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded-full flex-shrink-0">
                      {columnItems.length}
                    </span>
                  </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-2">
                  {columnItems.map((item) => (
                    <KanbanCard key={item.id} item={item} viewType="active" />
                  ))}
                  {columnItems.length === 0 && (
                    <div className="text-center text-muted-foreground text-xs py-6">
                      No items
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
