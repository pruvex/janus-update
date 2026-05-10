import { useEffect, useState } from 'react'
import { fetchBacklogItems } from '../lib/api'
import type { BacklogItem } from '@shared/types'
import { KanbanCard } from '../components/KanbanCard'
import { Loader2, CheckCircle } from 'lucide-react'

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

export function HistoryView() {
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
      const historyItems = response.items.filter(item => item.status === 'DONE')
      // Sort by most recently completed (completed_at field) - most recent first
      const sortedItems = historyItems.sort((a, b) => {
        const dateA = a.completed_at ? new Date(a.completed_at).getTime() : 0
        const dateB = b.completed_at ? new Date(b.completed_at).getTime() : 0
        return dateB - dateA
      })
      setItems(sortedItems)
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
    return items.filter(item => item.type === englishType)
  }

  // Calculate KPI metrics for history
  const totalItems = items.length
  const completedThisWeek = items.filter(item => {
    if (!item.completed_at) return false
    const completedDate = new Date(item.completed_at)
    const oneWeekAgo = new Date()
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7)
    return completedDate >= oneWeekAgo
  }).length

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h2 className="text-xl font-bold text-foreground">History</h2>
      </div>

      {/* KPI Bar */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] text-muted-foreground">Total Completed</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{totalItems}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <div className="flex items-center gap-1.5">
              <CheckCircle className="w-3 h-3 text-blue-400" />
              <span className="text-[10px] text-muted-foreground">This Week</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{completedThisWeek}</p>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-y-auto p-4">
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
                    <KanbanCard key={item.id} item={item} viewType="history" />
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
