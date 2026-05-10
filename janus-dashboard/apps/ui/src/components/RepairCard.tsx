import { useState } from 'react'
import { Copy } from 'lucide-react'
import type { RepairIssue } from '../lib/repairIssues'
import { getParentTaskReference } from '../lib/repairIssues'
import { buildRepairHandover } from '../lib/repairHandover'

interface RepairCardProps {
  issue: RepairIssue
  showButton?: boolean
}

const TYPE_COLORS: Record<string, { bg: string; text: string }> = {
  BUG: { bg: 'bg-orange-500/20', text: 'text-orange-400' },
  CHANGE: { bg: 'bg-blue-500/20', text: 'text-blue-400' },
  ENHANCEMENT: { bg: 'bg-green-500/20', text: 'text-green-400' },
  IMPROVEMENT: { bg: 'bg-teal-500/20', text: 'text-teal-400' },
  TECH_DEBT: { bg: 'bg-gray-500/20', text: 'text-gray-400' },
  UNCLEAR: { bg: 'bg-purple-500/20', text: 'text-purple-400' },
  'SPEC FEATURE': { bg: 'bg-cyan-500/20', text: 'text-cyan-400' },
}

const ISSUE_COLORS: Record<string, string> = {
  ROUTING_MISSING: 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10',
  ROUTING_BLOCKED: 'text-purple-400 border-purple-500/30 bg-purple-500/10',
  NEEDS_INFO: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
  BLOCKED: 'text-red-400 border-red-500/30 bg-red-500/10',
}

const valueOrFallback = (value: string | null | undefined, fallback = 'nicht angegeben') => {
  return value && value.trim() && value.trim().toLowerCase() !== 'null' ? value : fallback
}

export function RepairCard({ issue, showButton = true }: RepairCardProps) {
  const [copied, setCopied] = useState(false)
  const item = issue.item
  const typeColor = TYPE_COLORS[item.type] || TYPE_COLORS.UNCLEAR
  const issueColor = ISSUE_COLORS[issue.type] || ISSUE_COLORS.BLOCKED

  const handleCopyHandover = async () => {
    try {
      await navigator.clipboard.writeText(buildRepairHandover(issue))
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy repair handover:', err)
    }
  }

  return (
    <div className="bg-card border border-border rounded-lg p-3 hover:border-accent transition-colors w-full min-w-0">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="text-[10px] font-mono text-muted-foreground break-all">#{item.id}</span>
        <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${typeColor.bg} ${typeColor.text} flex-shrink-0`}>
          {item.type}
        </span>
      </div>

      <h3 className="font-semibold text-foreground text-xs mb-2 line-clamp-3 leading-tight break-words overflow-wrap-anywhere">
        {item.title}
      </h3>

      <div className={`mb-2 rounded border px-2 py-1 text-[10px] font-medium ${issueColor}`}>
        {issue.type}
      </div>

      <div className="space-y-1.5 mb-2">
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Parent Task</p>
          <p className="text-[10px] text-foreground break-words">{getParentTaskReference(item)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Recommended Skill</p>
          <p className="text-[10px] text-foreground break-words">{issue.recommendedSkill}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-1.5 mb-2">
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Importance</p>
          <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.importance)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Effort</p>
          <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.effort)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Risk</p>
          <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.implementation_risk)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Status</p>
          <p className="text-[10px] font-medium text-foreground">{valueOrFallback(item.status)}</p>
        </div>
      </div>

      <div className="space-y-1.5 mb-2">
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Entry Point</p>
          <p className="text-[10px] text-muted-foreground break-all">{valueOrFallback(item.entry_point)}</p>
        </div>
        <div>
          <p className="text-[9px] text-muted-foreground uppercase tracking-wider">Routing Confidence</p>
          <p className="text-[10px] text-muted-foreground break-all">{valueOrFallback(item.routing_confidence)}</p>
        </div>
      </div>

      {showButton && (
        <button
          onClick={handleCopyHandover}
          className="w-full flex items-center justify-center gap-1.5 px-2 py-1.5 rounded bg-accent hover:bg-accent/80 text-accent-foreground text-[10px] font-medium transition-colors"
        >
          <Copy className="w-3 h-3" />
          {copied ? 'Copied!' : 'Copy Handover (Windsurf)'}
        </button>
      )}
    </div>
  )
}
