import { useEffect, useState } from 'react'
import { fetchBacklogItems, fetchBacklogRecommendations, fetchTaskExecutionHistory } from '../lib/api'
import type { BacklogItem, BacklogPriorityAssessment, TaskExecutionRecord } from '@shared/types'
import { KanbanCard } from '../components/KanbanCard'
import { estimateTaskTime } from '../lib/executionAnalytics'
import { Loader2, AlertTriangle, Info, CheckCircle, XCircle, Target, ListChecks } from 'lucide-react'

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

const SPEC_GROUP_STYLES = [
  'border-cyan-400/70 bg-cyan-500/5',
  'border-emerald-400/70 bg-emerald-500/5',
  'border-amber-400/70 bg-amber-500/5',
  'border-violet-400/70 bg-violet-500/5',
]

const specNumber = (item: BacklogItem, field: string, fallback: number) => {
  const value = Number.parseInt(String(item.raw_fields?.[field] || ''), 10)
  return Number.isFinite(value) ? value : fallback
}

const sortSpecItems = (items: BacklogItem[]) => {
  return [...items].sort((a, b) => {
    const groupCompare = String(a.raw_fields?.['Spec Feature Group Label'] || '').localeCompare(String(b.raw_fields?.['Spec Feature Group Label'] || ''))
    if (groupCompare !== 0) return groupCompare
    const sequenceCompare = specNumber(a, 'Spec Sequence Order', 9999) - specNumber(b, 'Spec Sequence Order', 9999)
    if (sequenceCompare !== 0) return sequenceCompare
    return a.id.localeCompare(b.id)
  })
}

const groupSpecItems = (items: BacklogItem[]) => {
  const sorted = sortSpecItems(items)
  const groups: Array<{ id: string; label: string; items: BacklogItem[] }> = []
  const byId = new Map<string, { id: string; label: string; items: BacklogItem[] }>()

  for (const item of sorted) {
    const id = String(item.raw_fields?.['Spec Feature Group Id'] || 'ungrouped')
    const label = String(item.raw_fields?.['Spec Feature Group Label'] || 'Ungrouped Specs')
    let group = byId.get(id)
    if (!group) {
      group = { id, label, items: [] }
      byId.set(id, group)
      groups.push(group)
    }
    group.items.push(item)
  }

  return groups
}

export function ActiveView() {
  const [items, setItems] = useState<BacklogItem[]>([])
  const [executionRecords, setExecutionRecords] = useState<TaskExecutionRecord[]>([])
  const [priorityAssessments, setPriorityAssessments] = useState<BacklogPriorityAssessment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      setLoading(true)
      const [response, recommendations, history] = await Promise.all([
        fetchBacklogItems(),
        fetchBacklogRecommendations(),
        fetchTaskExecutionHistory().catch(() => null),
      ])
      const activeItems = response.items.filter(item => item.status !== 'DONE')
      setItems(activeItems)
      setPriorityAssessments(recommendations.assessments || [])
      setExecutionRecords(history?.records || [])
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
    const columnItems = items
      .filter(item => item.type === englishType)
      .sort((a, b) => (priorityById.get(a.id)?.rank || 999) - (priorityById.get(b.id)?.rank || 999))
    return englishType === 'SPEC FEATURE' ? sortSpecItems(columnItems) : columnItems
  }

  const priorityById = new Map(priorityAssessments.map((assessment) => [assessment.taskId, assessment]))
  const recommendedNext = priorityAssessments[0]
  const recommendedItem = recommendedNext ? items.find((item) => item.id === recommendedNext.taskId) : null

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

      {/* Recommendation */}
      <div className="p-4 border-b border-border bg-muted/20">
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_minmax(260px,380px)] gap-3">
          <div className="bg-card border border-border rounded-lg p-3 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Target className="w-4 h-4 text-emerald-500" />
              <h3 className="text-sm font-semibold text-foreground">Naechste Empfehlung</h3>
            </div>
            {recommendedNext && recommendedItem ? (
              <div className="space-y-1.5">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-xs font-mono text-muted-foreground flex-shrink-0">#{recommendedItem.id}</span>
                  <p className="text-sm font-semibold text-foreground truncate">{recommendedItem.title}</p>
                  <span className="ml-auto text-xs font-bold text-emerald-600 flex-shrink-0">{recommendedNext.score}/100</span>
                </div>
                <p className="text-xs text-muted-foreground">{recommendedNext.reason}</p>
                <p className="text-xs font-medium text-foreground">{recommendedNext.recommendedAction}</p>
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">Keine Active-Items offen. Dashboard ist leer fuer neue Umsetzung.</p>
            )}
          </div>
          <div className="bg-card border border-border rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <ListChecks className="w-4 h-4 text-blue-500" />
              <h3 className="text-sm font-semibold text-foreground">Bewertungslogik</h3>
            </div>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Score kombiniert Wichtigkeit, Empfehlung, Status, Entry Point, Routing Confidence, Risiko, Aufwand,
              Alter und Abschlussnachweise. Active-Items mit PASS-/DONE-Evidence werden als VERIFY DONE markiert.
            </p>
          </div>
        </div>
      </div>

      {/* KPI Bar */}
      <div className="p-4 border-b border-border bg-muted/30">
        <div className="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-7 gap-2">
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
              <CheckCircle className="w-3 h-3 text-emerald-400" />
              <span className="text-[10px] text-muted-foreground">Done</span>
            </div>
            <p className="text-lg font-bold text-foreground mt-0.5">{done}</p>
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
      <div className="flex-1 overflow-auto p-4">
        <div className="h-full grid grid-flow-col auto-cols-[minmax(220px,240px)] gap-3 min-w-max">
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
                  {column === 'SPEC FEATURE' ? (
                    groupSpecItems(columnItems).map((group, groupIndex) => (
                      <div
                        key={group.id}
                        className={`rounded-lg border-2 p-2 ${SPEC_GROUP_STYLES[groupIndex % SPEC_GROUP_STYLES.length]}`}
                      >
                        <div className="mb-2 flex items-center justify-between gap-2">
                          <p className="truncate text-[11px] font-bold uppercase tracking-wide text-foreground">{group.label}</p>
                          <span className="rounded-full border border-border bg-background/70 px-2 py-0.5 text-[10px] font-semibold text-muted-foreground">
                            {group.items.length}
                          </span>
                        </div>
                        <div className="space-y-2">
                          {group.items.map((item) => (
                            <KanbanCard
                              key={item.id}
                              item={item}
                              viewType="active"
                              estimatedTime={estimateTaskTime(item, executionRecords)}
                              priorityAssessment={priorityById.get(item.id) || null}
                            />
                          ))}
                        </div>
                      </div>
                    ))
                  ) : (
                    columnItems.map((item) => (
                      <KanbanCard
                        key={item.id}
                        item={item}
                        viewType="active"
                        estimatedTime={estimateTaskTime(item, executionRecords)}
                        priorityAssessment={priorityById.get(item.id) || null}
                      />
                    ))
                  )}
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
