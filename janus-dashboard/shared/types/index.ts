export interface BacklogItem {
  id: string
  title: string
  type: string
  status: string
  importance: string
  implementation_risk: string
  effort: string
  readiness: string
  recommendation: string
  entry_point: string
  routing_reason: string
  routing_confidence: string
  routing_decided_by: string | null
  routing_decided_at: string | null
  routing_blocker: string | null
  handoff: string
  recommended_next_skill: string
  handoff_created: string | null
  precheck_artifact: string | null
  target_task: string | null
  completed_in_version: string | null
  completed_by_task: string | null
  completed_at: string | null
  final_audit: string | null
  validation_evidence: string | null
  changelog: string | null
  raw_fields: Record<string, any>
}

export interface BacklogCounts {
  total: number
  active: number
  history: number
  needs_info: number
  ready: number
  in_progress: number
  done: number
  blocked: number
  routing_missing: number
  routing_blocked: number
}

export interface BacklogResponse {
  source: string
  generated_from?: string
  generated_at?: string
  snapshot_schema?: string
  snapshot_path?: string
  is_stale?: boolean
  items: BacklogItem[]
  counts: BacklogCounts
}
