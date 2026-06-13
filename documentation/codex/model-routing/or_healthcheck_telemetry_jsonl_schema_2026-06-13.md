# OR Healthcheck Telemetry JSONL Schema - 2026-06-13

Status: SCHEMA DOCUMENTATION / DUMMY-ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING

## Purpose

Define the operational JSONL row shape for future OR healthcheck telemetry records that follow the completed `5.4 mini` workflow-ready planning layer.

## Record Format

- File format: `JSONL`
- One JSON object per line
- UTF-8 text
- Append-only operational logging
- Dummy artifacts in this phase are examples only and not live telemetry

## Scope Guard

This schema is prepared for the completed mini workflow planning layer only:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Preserved matrix counts remain:

- `OR_CONFIRMED=7`
- `NEEDS_STRONGER_TEST=0`
- `OR_REJECTED=0`

`DOC-SKILL-011` remains `NOT RUN`.

## JSONL Row Schema

Each row should contain these fields:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `workflow_id` | string | yes | Stable workflow run id |
| `skill_id` | string | yes | `DOC-SKILL-XXX` |
| `routing_mode` | string | yes | `Codex-only`, `Auto-sparsam`, `Manual-review` |
| `selected_path` | string | yes | Executed route label |
| `codex_default_model` | string | yes | Declared Codex default |
| `or_model` | string | no | `N_A` when unused |
| `estimated_prompt_tokens` | integer | no | Pre-call estimate |
| `estimated_completion_tokens` | integer | no | Pre-call estimate |
| `estimated_or_cost` | number | no | Planned OR cost |
| `cost_estimate_confidence_percent` | number | no | Estimate confidence |
| `cost_estimate_sample_count` | integer | no | Historical cohort size |
| `cost_estimate_mean_abs_error_percent` | number | no | Historical MAE% |
| `cost_estimate_p50_error_percent` | number | no | Historical median error% |
| `cost_estimate_p90_error_percent` | number | no | Historical p90 error% |
| `cost_estimate_basis` | string | no | Cohort basis label |
| `prompt_template_hash` | string | no | Prompt-family hash |
| `task_variant` | string | no | Task-shape label |
| `price_snapshot_source` | string | no | Price basis source |
| `price_snapshot_timestamp` | string | no | ISO timestamp |
| `actual_prompt_tokens` | integer | no | Actual usage |
| `actual_completion_tokens` | integer | no | Actual usage |
| `actual_reasoning_tokens` | integer | no | Actual usage |
| `actual_cached_tokens` | integer | no | Actual usage |
| `actual_or_cost` | number | no | Actual OR cost |
| `generation_id` | string | no | Later reconciliation id |
| `usage_source` | string | no | `response_usage`, `generation_endpoint`, `fallback_estimate` |
| `estimated_codex_effort` | string | no | Local effort proxy |
| `estimation_error_percent` | number | no | Estimated vs actual error |
| `cost_delta_vs_codex_estimate` | number | no | OR minus Codex estimate |
| `latency_ms` | integer | no | OR path latency |
| `validation_result` | string | yes | `PASS`, `FAIL`, `HOLD`, `NEEDS_REVIEW` |
| `fallback_used` | string | yes | `YES`, `NO` |
| `rework_required` | string | yes | `YES`, `NO` |
| `final_outcome` | string | yes | Terminal workflow outcome |
| `reason_for_escalation` | string | no | Empty when not escalated |
| `quality_notes` | string | no | Bounded note |
| `recommendation_signal` | string | yes | `OR_PREFERRED`, `CODEX_PREFERRED`, `MANUAL_REVIEW` |

## Operational Rules

- Use only schema fields defined here in the JSONL row.
- Keep timestamps in ISO 8601 format.
- Use decimal numbers for cost fields.
- Keep dummy examples clearly marked as dummy or sample data.
- Do not use this schema to imply production routing activation.

## Non-Goals

- no OR calls
- no model calls
- no production routing activation
- no canonical routing-table update
- no `5.4` candidate continuation
- no live evals
