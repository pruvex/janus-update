export interface BacklogItem {
  id: string
  title: string
  section?: string | null
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

export interface BacklogPriorityAssessment {
  taskId: string
  score: number
  rank: number
  label: 'DO NEXT' | 'READY' | 'REVIEW' | 'WAIT' | 'BLOCKED' | 'VERIFY DONE'
  reason: string
  recommendedAction: string
  recommendedSkill: string
  completionEvidence: boolean
}

export interface BacklogRecommendationResponse {
  schema: string
  source: string
  generated_at: string
  active_count: number
  recommended_next: BacklogPriorityAssessment | null
  assessments: BacklogPriorityAssessment[]
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

export interface TestResultSummary {
  total: number
  passed: number
  failed: number
  blocked: number
  manualGateRequired: number
}

export interface TestResultCase {
  testCaseId: string
  result: string
  classification: string
  evidencePath: string
  durationMs?: number
  notes?: string
  timestamp?: string
}

export interface TestResultRecord {
  schemaVersion: string
  testRunId: string
  title?: string
  status: 'PASS' | 'FAIL' | 'PARTIAL' | 'BLOCKED' | 'RUNNING' | string
  summary: TestResultSummary
  artifacts: {
    resultDirectory: string
    resultJson: string
    evidenceFiles: string[]
  }
  results: TestResultCase[]
  updatedAt: string
}

export interface TestResultsResponse {
  schema: string
  source: string
  records: TestResultRecord[]
}

export interface TestCaseOverview {
  testCaseId: string
  totalRuns: number
  passedRuns: number
  failedRuns: number
  passRate: number
  lastResult: 'PASS' | 'FAIL' | 'BLOCKED' | 'RUNNING'
  lastRunId: string
  lastTimestamp: string
}

export interface TestSpecOverview {
  specId: string
  fileName: string
  path: string
  categoryId: string
  categoryLabel: string
  categoryOrder: number
  title: string
  capability: string
  description: string
  reliableBehavior: string
  impactLevel: 'critical' | 'high' | 'medium' | 'low'
  impactScore: number
  impactReason: string
  recommendedNext: boolean
  status: 'PASS' | 'FAIL' | 'PARTIAL' | 'BLOCKED' | 'RUNNING' | 'NOT_RUN' | string
  latestRunId: string | null
  latestRunTitle: string | null
  latestUpdatedAt: string | null
  passRate: number
  total: number
  plannedTotal: number
  executedTotal: number
  isPartialRun: boolean
  passed: number
  failed: number
  blocked: number
  manualGateRequired: number
  providerPassRate: Record<string, number>
  typePassRate: Record<string, number>
  failedTestCases: string[]
  resultJson: string | null
}

export interface TestOverviewResponse {
  schema: string
  source: string
  summary: {
    totalTestSpecs: number
    validatedSpecs: number
    perfectSpecs: number
    attentionSpecs: number
    notRunSpecs: number
    overallPassRate: number
    latestUpdatedAt: string | null
  }
  testSpecs: TestSpecOverview[]
}

export interface TestSuiteCategory {
  id: string
  label: string
  order: number
  description: string
  totalTestSpecs: number
  validatedSpecs: number
  perfectSpecs: number
  attentionSpecs: number
  notRunSpecs: number
  overallPassRate: number
  testSpecs: TestSpecOverview[]
}

export interface TestSuiteResponse {
  schema: string
  source: string
  summary: TestOverviewResponse['summary']
  recommendedNext: TestSpecOverview | null
  categories: TestSuiteCategory[]
}
