from __future__ import annotations

from pydantic import BaseModel, Field


class BacklogItem(BaseModel):
    id: str
    title: str
    section: str | None = None
    type: str | None = None
    status: str | None = None
    source: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    summary: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    reproduction_context: str | None = None
    affected_area: str | None = None
    evidence: str | None = None
    notes: str | None = None
    importance: str | None = None
    implementation_risk: str | None = None
    effort: str | None = None
    readiness: str | None = None
    recommendation: str | None = None
    entry_point: str | None = None
    routing_reason: str | None = None
    routing_confidence: str | None = None
    routing_decided_by: str | None = None
    routing_decided_at: str | None = None
    routing_blocker: str | None = None
    handoff: str | None = None
    recommended_next_skill: str | None = None
    handoff_created: str | None = None
    precheck_artifact: str | None = None
    target_task: str | None = None
    completed_in_version: str | None = None
    completed_by_task: str | None = None
    completed_at: str | None = None
    final_audit: str | None = None
    validation_evidence: str | None = None
    changelog: str | None = None
    is_test_blocker: bool = False
    raw_fields: dict[str, str] = Field(default_factory=dict)


class BacklogCounts(BaseModel):
    total: int = 0
    active: int = 0
    history: int = 0
    needs_info: int = 0
    ready: int = 0
    in_progress: int = 0
    done: int = 0
    blocked: int = 0
    routing_missing: int = 0
    routing_blocked: int = 0


class BacklogItemsResponse(BaseModel):
    source: str
    items: list[BacklogItem]
    counts: BacklogCounts
