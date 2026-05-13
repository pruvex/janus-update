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
  is_test_blocker: boolean
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

export interface TaskExecutionRecord {
  execution_id: string
  task_id: string
  task_title?: string
  task_type: string
  skill_used: string
  skill_chain?: string[]
  importance: string
  effort: string
  risk: string
  started_at: string
  finished_at: string
  duration_minutes: number
  successful: boolean
  reopened: boolean
  retry_count?: number
  routing_confidence_before?: number | null
  routing_confidence_after?: number | null
  completed_in_version?: string | null
  completed_by_task?: string | null
  validation_evidence?: string | null
  source: 'skill_lifecycle' | 'backlog_sync' | 'manual_skill_update_with_evidence'
}

export interface TaskExecutionHistoryResponse {
  schema: string
  updated_at: string | null
  source: string
  records: TaskExecutionRecord[]
}
