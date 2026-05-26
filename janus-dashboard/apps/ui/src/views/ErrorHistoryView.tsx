import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { RepairCard } from '../components/RepairCard'
import { TypeKanbanBoard } from '../components/TypeKanbanBoard'
import { fetchBacklogItems } from '../lib/api'
import type { RepairIssueType, RepairIssue } from '../lib/repairIssues'
import { getIssueTitle, hasValue } from '../lib/repairIssues'

interface ResolvedRepairIssue {
  id: string
  type: RepairIssueType
  title: string
  recommendedSkill: string
  item: any
  completedAt: string
}

function wasErrorItem(item: any): boolean {
  return (
    item.status === 'DONE' &&
    (hasValue(item.routing_blocker) ||
     hasValue(item.recommendation) ||
     item.readiness === 'NEEDS INFO' ||
     item.implementation_risk === 'HIGH' ||
     item.implementation_risk === 'CRITICAL')
  )
}

function inferErrorType(item: any): RepairIssueType {
  if (item.routing_blocker) return 'ROUTING_BLOCKED'
  if (!hasValue(item.entry_point)) return 'ROUTING_MISSING'
  if (item.readiness === 'NEEDS INFO') return 'NEEDS_INFO'
  return 'BLOCKED'
}

export function ErrorHistoryView() {
  const [resolvedIssues, setResolvedIssues] = useState<ResolvedRepairIssue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadResolvedIssues()
  }, [])

  const loadResolvedIssues = async () => {
    try {
      setLoading(true)
      const response = await fetchBacklogItems()
      const resolvedItems = response.items.filter(wasErrorItem)
      const issues: ResolvedRepairIssue[] = resolvedItems.map((item) => {
        const errorType = inferErrorType(item)
        return {
          id: `${errorType}:resolved:${item.id}`,
          type: errorType,
          title: getIssueTitle(errorType),
          recommendedSkill: 'RESOLVED',
          item,
          completedAt: item.completed_at || '',
        }
      })
      const sortedIssues = issues.sort((a, b) => {
        const dateA = a.completedAt ? new Date(a.completedAt).getTime() : 0
        const dateB = b.completedAt ? new Date(b.completedAt).getTime() : 0
        return dateB - dateA
      })
      setResolvedIssues(sortedIssues)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load error history')
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

  const affectedItems = new Set(resolvedIssues.map((issue) => issue.item.id)).size

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-xl font-bold text-foreground">Error History</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Resolved errors derived from completed backlog items. Sorted by completion date.
        </p>
      </div>

      <div className="p-4 border-b border-border bg-muted/30">
        <div className="grid grid-cols-3 gap-2 max-w-3xl">
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Resolved Cards</span>
            <p className="text-lg font-bold text-foreground mt-0.5">{resolvedIssues.length}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Affected Items</span>
            <p className="text-lg font-bold text-foreground mt-0.5">{affectedItems}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Status</span>
            <p className="text-lg font-bold text-foreground mt-0.5">Resolved</p>
          </div>
        </div>
      </div>

      <TypeKanbanBoard<ResolvedRepairIssue>
        items={resolvedIssues}
        getItemType={(issue) => issue.item.type}
        getItemKey={(issue) => issue.id}
        renderItem={(issue) => <RepairCard issue={issue as RepairIssue} showButton={false} />}
        emptyText="No resolved errors"
      />
    </div>
  )
}
