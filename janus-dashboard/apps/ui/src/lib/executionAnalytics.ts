import type { BacklogItem, TaskExecutionRecord } from '@shared/types'

export interface EstimatedTimeInsight {
  label: string
  confidence: number
  sampleSize: number
  basis: string
}

function median(values: number[]): number {
  if (values.length === 0) {
    return 0
  }

  const sorted = [...values].sort((a, b) => a - b)
  const middle = Math.floor(sorted.length / 2)

  if (sorted.length % 2 === 0) {
    return Math.round((sorted[middle - 1] + sorted[middle]) / 2)
  }

  return Math.round(sorted[middle])
}

function formatMinutes(minutes: number): string {
  if (minutes < 60) {
    return `~${minutes}m`
  }

  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60

  if (remainingMinutes === 0) {
    return `~${hours}h`
  }

  return `~${hours}h ${remainingMinutes}m`
}

function normalize(value: string | null | undefined): string {
  return value?.trim().toUpperCase().replace(/\s+/g, '_') || ''
}

function eligibleRecords(records: TaskExecutionRecord[]): TaskExecutionRecord[] {
  return records.filter((record) => (
    record.successful &&
    !record.reopened &&
    Number.isFinite(record.duration_minutes) &&
    record.duration_minutes > 0 &&
    record.source !== undefined
  ))
}

function calculateConfidence(sampleSize: number, basisRank: number): number {
  const sampleConfidence = Math.min(70, sampleSize * 14)
  return Math.max(35, Math.min(95, sampleConfidence + basisRank))
}

export function estimateTaskTime(item: BacklogItem, records: TaskExecutionRecord[]): EstimatedTimeInsight | null {
  const completedRecords = eligibleRecords(records)
  if (completedRecords.length === 0) {
    return null
  }

  const itemType = normalize(item.type)
  const itemRisk = normalize(item.implementation_risk)
  const itemEffort = normalize(item.effort)

  const matchers: Array<{ basis: string; rank: number; matches: (record: TaskExecutionRecord) => boolean }> = [
    {
      basis: 'Typ + Risiko + Aufwand',
      rank: 25,
      matches: (record) => normalize(record.task_type) === itemType && normalize(record.risk) === itemRisk && normalize(record.effort) === itemEffort,
    },
    {
      basis: 'Typ + Aufwand',
      rank: 15,
      matches: (record) => normalize(record.task_type) === itemType && normalize(record.effort) === itemEffort,
    },
    {
      basis: 'Aufwand',
      rank: 5,
      matches: (record) => normalize(record.effort) === itemEffort,
    },
    {
      basis: 'Typ',
      rank: 0,
      matches: (record) => normalize(record.task_type) === itemType,
    },
    {
      basis: 'alle abgeschlossenen Tasks',
      rank: -10,
      matches: () => true,
    },
  ]

  for (const matcher of matchers) {
    const matches = completedRecords.filter(matcher.matches)
    if (matches.length > 0) {
      const minutes = median(matches.map((record) => record.duration_minutes))
      return {
        label: formatMinutes(minutes),
        confidence: calculateConfidence(matches.length, matcher.rank),
        sampleSize: matches.length,
        basis: matcher.basis,
      }
    }
  }

  return null
}
