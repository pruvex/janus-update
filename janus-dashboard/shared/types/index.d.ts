export interface BacklogItem {
    id: string;
    title: string;
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
