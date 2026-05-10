import type { BacklogItem } from '@shared/types'

export type RepairIssueType = 'ROUTING_MISSING' | 'ROUTING_BLOCKED' | 'NEEDS_INFO' | 'BLOCKED'

export interface RepairIssue {
  id: string
  type: RepairIssueType
  title: string
  recommendedSkill: string
  item: BacklogItem
}

const emptyValues = new Set(['', 'null', 'none', 'undefined'])

export function hasValue(value: string | null | undefined): value is string {
  return Boolean(value && !emptyValues.has(value.trim().toLowerCase()))
}

export function isRoutingMissing(item: BacklogItem): boolean {
  return item.status !== 'DONE' && (!hasValue(item.entry_point) || item.entry_point === 'ROUTING_MISSING')
}

export function isRoutingBlocked(item: BacklogItem): boolean {
  return item.status !== 'DONE' && item.entry_point === 'ROUTING_BLOCKED'
}

export function isNeedsInfo(item: BacklogItem): boolean {
  return item.status === 'NEEDS INFO'
}

export function isBlocked(item: BacklogItem): boolean {
  return item.status === 'BLOCKED'
}

export function getRepairIssues(items: BacklogItem[], issueType: RepairIssueType): RepairIssue[] {
  return items
    .filter((item) => {
      switch (issueType) {
        case 'ROUTING_MISSING':
          return isRoutingMissing(item)
        case 'ROUTING_BLOCKED':
          return isRoutingBlocked(item)
        case 'NEEDS_INFO':
          return isNeedsInfo(item)
        case 'BLOCKED':
          return isBlocked(item)
        default:
          return false
      }
    })
    .map((item) => ({
      id: `${issueType}:${item.id}`,
      type: issueType,
      title: getIssueTitle(issueType),
      recommendedSkill: getRecommendedRepairSkill(issueType, item),
      item,
    }))
}

export function getIssueTitle(issueType: RepairIssueType): string {
  switch (issueType) {
    case 'ROUTING_MISSING':
      return 'Routing Missing'
    case 'ROUTING_BLOCKED':
      return 'Routing Blocked'
    case 'NEEDS_INFO':
      return 'Needs Info'
    case 'BLOCKED':
      return 'Blocked'
    default:
      return 'Repair Issue'
  }
}

export function getRecommendedRepairSkill(issueType: RepairIssueType, item: BacklogItem): string {
  if (issueType === 'NEEDS_INFO') {
    return 'BACKLOG SKILL 1 – INTAKE TRIAGE'
  }

  if (issueType === 'ROUTING_MISSING' || issueType === 'ROUTING_BLOCKED') {
    return 'BACKLOG SKILL 3 – EXECUTION HANDOFF'
  }

  if (issueType === 'BLOCKED') {
    if (item.entry_point === 'ROUTING_BLOCKED' || !hasValue(item.entry_point)) {
      return 'BACKLOG SKILL 3 – EXECUTION HANDOFF'
    }

    if (!hasValue(item.readiness) || item.readiness === 'NEEDS INFO') {
      return 'BACKLOG SKILL 1 – INTAKE TRIAGE'
    }

    return 'SKILL 5 – FEATURE DEBUG'
  }

  return 'BACKLOG SKILL 1 – INTAKE TRIAGE'
}

export function getParentTaskReference(item: BacklogItem): string {
  const rawFields = item.raw_fields || {}
  const value = rawFields.Parent || rawFields['Parent Task'] || rawFields['Parent task'] || rawFields['Parent Backlog'] || item.completed_by_task
  return typeof value === 'string' && hasValue(value) ? value : 'nicht angegeben'
}
