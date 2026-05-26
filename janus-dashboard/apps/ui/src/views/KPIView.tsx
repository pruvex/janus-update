import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { RepairCard } from '../components/RepairCard'
import { TypeKanbanBoard } from '../components/TypeKanbanBoard'
import { fetchBacklogItems } from '../lib/api'
import type { RepairIssueType, RepairIssue } from '../lib/repairIssues'
import { getRepairIssues } from '../lib/repairIssues'

const ALL_REPAIR_ISSUES: RepairIssueType[] = ['ROUTING_MISSING', 'ROUTING_BLOCKED', 'NEEDS_INFO', 'BLOCKED']

export function KPIView() {
  const [issues, setIssues] = useState<RepairIssue[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadIssues()
  }, [])

  const loadIssues = async () => {
    try {
      setLoading(true)
      const response = await fetchBacklogItems()
      const allIssues: RepairIssue[] = []
      ALL_REPAIR_ISSUES.forEach((issueType) => {
        allIssues.push(...getRepairIssues(response.items, issueType))
      })
      setIssues(allIssues)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load repair issues')
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

  const affectedItems = new Set(issues.map((issue) => issue.item.id)).size

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-xl font-bold text-foreground">Error Overview</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Operational repair board derived from backlog.snapshot.json. No manual completion state is stored in the dashboard.
        </p>
      </div>

      <div className="p-4 border-b border-border bg-muted/30">
        <div className="grid grid-cols-3 gap-2 max-w-3xl">
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Repair Cards</span>
            <p className="text-lg font-bold text-foreground mt-0.5">{issues.length}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Affected Items</span>
            <p className="text-lg font-bold text-foreground mt-0.5">{affectedItems}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-2">
            <span className="text-[10px] text-muted-foreground">Repair Mode</span>
            <p className="text-lg font-bold text-foreground mt-0.5">Read-only</p>
          </div>
        </div>
      </div>

      <TypeKanbanBoard<RepairIssue>
        items={issues}
        getItemType={(issue) => issue.item.type}
        getItemKey={(issue) => issue.id}
        renderItem={(issue) => <RepairCard issue={issue} />}
        emptyText="No repair issues"
      />
    </div>
  )
}
