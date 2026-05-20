export interface BacklogItem {
    id: string;
    title: string;
    section?: string | null;
    type: string;
    status: string;
    importance: string;
    implementation_risk: string;
    effort: string;
    readiness: string;
    recommendation: string;
    entry_point: string;
    routing_reason: string;
    routing_confidence: string;
    handoff: string;
    recommended_next_skill: string;
    completed_in_version: string | null;
    completed_by_task: string | null;
    completed_at: string | null;
    final_audit: string | null;
    validation_evidence: string | null;
    changelog: string | null;
    raw_fields: Record<string, any>;
}
export interface BacklogCounts {
    total: number;
    active: number;
    history: number;
    needs_info: number;
    ready: number;
    in_progress: number;
    done: number;
    blocked: number;
    routing_missing: number;
    routing_blocked: number;
}
export interface BacklogResponse {
    source: string;
    items: BacklogItem[];
    counts: BacklogCounts;
}
export interface TestResultSummary {
    total: number;
    passed: number;
    failed: number;
    blocked: number;
    manualGateRequired: number;
}
export interface TestResultCase {
    testCaseId: string;
    result: string;
    classification: string;
    evidencePath: string;
    durationMs?: number;
    notes?: string;
    timestamp?: string;
}
export interface TestResultRecord {
    schemaVersion: string;
    testRunId: string;
    title?: string;
    status: 'PASS' | 'FAIL' | 'PARTIAL' | 'BLOCKED' | 'RUNNING' | string;
    summary: TestResultSummary;
    artifacts: {
        resultDirectory: string;
        resultJson: string;
        evidenceFiles: string[];
    };
    results: TestResultCase[];
    updatedAt: string;
}
export interface TestResultsResponse {
    schema: string;
    source: string;
    records: TestResultRecord[];
}
export interface TestCaseOverview {
    testCaseId: string;
    totalRuns: number;
    passedRuns: number;
    failedRuns: number;
    passRate: number;
    lastResult: 'PASS' | 'FAIL' | 'BLOCKED' | 'RUNNING';
    lastRunId: string;
    lastTimestamp: string;
}
export interface TestSpecOverview {
    specId: string;
    fileName: string;
    path: string;
    categoryId: string;
    categoryLabel: string;
    categoryOrder: number;
    title: string;
    capability: string;
    description: string;
    reliableBehavior: string;
    impactLevel: 'critical' | 'high' | 'medium' | 'low';
    impactScore: number;
    impactReason: string;
    recommendedNext: boolean;
    status: 'PASS' | 'FAIL' | 'PARTIAL' | 'BLOCKED' | 'RUNNING' | 'NOT_RUN' | string;
    latestRunId: string | null;
    latestRunTitle: string | null;
    latestUpdatedAt: string | null;
    passRate: number;
    total: number;
    passed: number;
    failed: number;
    blocked: number;
    manualGateRequired: number;
    providerPassRate: Record<string, number>;
    typePassRate: Record<string, number>;
    failedTestCases: string[];
    resultJson: string | null;
}
export interface TestOverviewResponse {
    schema: string;
    source: string;
    summary: {
        totalTestSpecs: number;
        validatedSpecs: number;
        perfectSpecs: number;
        attentionSpecs: number;
        notRunSpecs: number;
        overallPassRate: number;
        latestUpdatedAt: string | null;
    };
    testSpecs: TestSpecOverview[];
}
export interface TestSuiteCategory {
    id: string;
    label: string;
    order: number;
    description: string;
    totalTestSpecs: number;
    validatedSpecs: number;
    perfectSpecs: number;
    attentionSpecs: number;
    notRunSpecs: number;
    overallPassRate: number;
    testSpecs: TestSpecOverview[];
}
export interface TestSuiteResponse {
    schema: string;
    source: string;
    summary: TestOverviewResponse['summary'];
    recommendedNext: TestSpecOverview | null;
    categories: TestSuiteCategory[];
}
