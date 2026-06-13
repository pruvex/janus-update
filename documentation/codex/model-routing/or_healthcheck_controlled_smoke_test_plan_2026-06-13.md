# OR Healthcheck Controlled Smoke Test Plan - 2026-06-13

Status: SMOKE-TEST PLAN ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Define one controlled one-shot OR telemetry smoke test for the completed mini workflow planning layer before any separate `5.4` candidate work resumes.

## Scope Lock

- mini matrix counts remain:
  - `OR_CONFIRMED=7`
  - `NEEDS_STRONGER_TEST=0`
  - `OR_REJECTED=0`
- `DOC-SKILL-011` remains `NOT RUN`
- the separate `5.4` candidate phase remains paused
- this artifact does not authorize any OR call by itself

## Selected One-Shot Target

- selected skill: `DOC-SKILL-008`
- selected OR model: `qwen/qwen3.5-flash-02-23`

Reason:

- the mini matrix already records `DOC-SKILL-008` as `OR_CONFIRMED`
- the existing dummy telemetry sample and dummy summary already use the same task/model pair
- the task is bounded to sanitized changelog-style drafting and remains outside production authority

## Max Allowed Cost

- max allowed cost: `0.0020`

Interpretation:

- the smoke test must stop before execution if the pre-call estimate exceeds the cap
- any post-call actual cost above the cap is an automatic fail for the smoke-test result

## Required Expected Telemetry Fields

The smoke test must produce or confirm these fields:

- `workflow_id`
- `skill_id`
- `routing_mode`
- `selected_path`
- `codex_default_model`
- `or_model`
- `estimated_prompt_tokens`
- `estimated_completion_tokens`
- `estimated_or_cost`
- `cost_estimate_confidence_percent`
- `cost_estimate_sample_count`
- `cost_estimate_mean_abs_error_percent`
- `cost_estimate_p50_error_percent`
- `cost_estimate_p90_error_percent`
- `cost_estimate_basis`
- `prompt_template_hash`
- `task_variant`
- `price_snapshot_source`
- `price_snapshot_timestamp`
- `actual_prompt_tokens`
- `actual_completion_tokens`
- `actual_reasoning_tokens`
- `actual_cached_tokens`
- `actual_or_cost`
- `generation_id`
- `usage_source`
- `estimated_codex_effort`
- `estimation_error_percent`
- `cost_delta_vs_codex_estimate`
- `latency_ms`
- `validation_result`
- `fallback_used`
- `rework_required`
- `final_outcome`
- `reason_for_escalation`
- `quality_notes`
- `recommendation_signal`

## Required Pre-Call Cost Estimate

Before any OR call is allowed in a later approved run, all of these must exist:

- `estimated_prompt_tokens`
- `estimated_completion_tokens`
- `estimated_or_cost`
- `price_snapshot_source`
- `price_snapshot_timestamp`
- `cost_estimate_confidence_percent`
- `cost_estimate_sample_count`

Gate:

- if `estimated_or_cost > 0.0020`, abort
- if `cost_estimate_confidence_percent` is unavailable, record that explicitly before deciding whether a one-shot approval is still acceptable

## Required Post-Call Usage And Cost Capture

If a later approved smoke test actually runs, it must capture:

- `actual_prompt_tokens`
- `actual_completion_tokens`
- `actual_reasoning_tokens` when available
- `actual_cached_tokens` when available
- `actual_or_cost`
- `generation_id`
- `usage_source`
- `latency_ms`

Preferred source order:

1. `response_usage`
2. `generation_endpoint`
3. `fallback_estimate`

## Required Healthcheck Invocation

After a later approved smoke-test row exists, use:

```powershell
python C:\KI\Janus-Projekt\documentation\codex\skills\janus-health-check\scripts\health_snapshot.py --repo C:\KI\Janus-Projekt --mode DAILY --or-telemetry-jsonl <path-to-smoke-test-jsonl>
```

The smoke test passes only if the healthcheck runner can read the row and emit bounded OR summary fields.

## Pass Criteria

All of these must be true:

1. the selected task remains `DOC-SKILL-008`
2. the selected model remains `qwen/qwen3.5-flash-02-23`
3. pre-call estimate is present and under the cost cap
4. post-call usage and cost capture are present from an accepted source
5. `health_snapshot.py` reads the resulting JSONL row successfully
6. the healthcheck OR summary reflects the new smoke-test row
7. local validation result is recorded explicitly
8. no production routing, release, git-governance, or routing-table language appears

## Fail Criteria

Any of these means fail:

- pre-call estimate missing
- actual usage/cost capture missing and no accepted fallback estimate exists
- healthcheck runner cannot read the resulting JSONL
- summary fields do not match the resulting row
- actual cost exceeds `0.0020`
- validation result is `FAIL` or unresolved

## Abort Criteria

Abort before or during a later approved run when any of these happens:

- `estimated_or_cost > 0.0020`
- state contradiction between matrix, workflow plan, telemetry plan, and selected task
- selected skill is no longer `OR_CONFIRMED`
- usage capture path is known unavailable before execution
- the request drifts toward production routing, routing-table update, release flow, or broader candidate continuation

## Rollback / No-Persist Rule

If telemetry is incomplete:

- do not persist the smoke-test row as accepted operational telemetry
- do not treat partial data as healthcheck-ready evidence
- keep incomplete artifacts only as explicit failure/debug evidence if needed
- do not update production routing, routing tables, or candidate-phase status from incomplete telemetry

## Non-Goals

- no OR calls
- no production routing activation
- no canonical routing-table update
- no `5.4` candidate continuation
- no DOC-SKILL-011 run
- no live evals
