# OR Healthcheck Telemetry Plan - 2026-06-13

Status: PLANNING ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Define a telemetry extension for Codex healthcheck reporting so every OR-routed documentation activity can later be summarized for reliability, fallback pressure, validation health, and cost/time tradeoffs before any separate `5.4` candidate work continues.

## Scope Lock

This plan is bounded by the completed `5.4 mini` workflow-ready planning layer and its mini matrix scope:

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

The separate `5.4` candidate phase remains paused.

`DOC-SKILL-011` remains `NOT RUN`.

No global OR approval is created by this telemetry plan.

## Telemetry Event Definition

Every OR-routed activity should be recordable with these fields:

- `workflow_id`
- `skill_id`
- `routing_mode`
- `selected_path`
- `codex_default_model`
- `or_model`
- `estimated_or_cost`
- `actual_or_cost`
- `estimated_codex_effort`
- `latency_ms`
- `validation_result`
- `fallback_used`
- `rework_required`
- `final_outcome`
- `reason_for_escalation`
- `quality_notes`

## Field Guidance

- `workflow_id`: stable identifier for one documentation workflow run.
- `skill_id`: exact `DOC-SKILL-XXX` row or equivalent documentation-skill identifier.
- `routing_mode`: `Codex-only`, `Auto-sparsam`, or `Manual-review`.
- `selected_path`: concise executed route such as `codex_local`, `or_first_then_codex_validate`, or `or_rejected_fallback_codex`.
- `codex_default_model`: declared Codex default such as `5.4 mini low`.
- `or_model`: selected OR model name when one is part of the route; blank or `N_A` when not used.
- `estimated_or_cost`: planned OR spend estimate when available.
- `actual_or_cost`: actual OR cost when available from later instrumentation.
- `estimated_codex_effort`: optional local effort estimate such as `low`, `medium`, `high`, or token/time proxy.
- `latency_ms`: total OR path latency when available.
- `validation_result`: local validation result such as `PASS`, `FAIL`, `HOLD`, or `NEEDS_REVIEW`.
- `fallback_used`: `YES` or `NO`.
- `rework_required`: `YES` or `NO`.
- `final_outcome`: terminal workflow result such as `OR_PASSED_LOCAL_VALIDATION`, `CODEX_ONLY_FINAL`, `MANUAL_REVIEW_REQUIRED`, or `BLOCKED`.
- `reason_for_escalation`: concise cause when the flow leaves Auto-sparsam or Manual-review.
- `quality_notes`: short bounded notes for observed quality, boundary preservation, or mismatch patterns.

## Healthcheck Outputs

The Codex healthcheck extension should summarize OR telemetry into these outputs:

- `per-skill OR reliability summary`
- `per-model OR reliability summary`
- `fallback frequency`
- `validation failure frequency`
- `cost delta summary`
- `time delta summary`
- `recommendation signal: OR_PREFERRED / CODEX_PREFERRED / MANUAL_REVIEW`

## Output Interpretation

### Per-skill OR reliability summary

For each `skill_id`, summarize:

- runs counted
- local validation pass rate
- fallback rate
- rework rate
- final recommendation signal

### Per-model OR reliability summary

For each `or_model`, summarize:

- runs counted
- validation pass rate
- fallback rate
- escalation rate
- cost visibility completeness

### Fallback frequency

Track how often OR-routed work falls back to Codex-only or Manual-review.

### Validation failure frequency

Track how often local validation rejects or blocks OR-assisted output.

### Cost delta summary

When estimates or actuals exist, compare:

- OR estimated vs actual cost
- OR cost vs estimated Codex effort proxy
- low-cost win, neutral, or loss signals

### Time delta summary

When latency or local effort proxies exist, compare:

- OR path latency vs expected Codex-only effort
- quick win, neutral, or slowdown signals

### Recommendation Signal

For each summarized scope, emit one of:

- `OR_PREFERRED`
- `CODEX_PREFERRED`
- `MANUAL_REVIEW`

Suggested meaning:

- `OR_PREFERRED`: repeated local validation success with low fallback and acceptable cost/time
- `CODEX_PREFERRED`: repeated fallback, validation failure, or weak cost/time value
- `MANUAL_REVIEW`: mixed quality, limited data, or escalation-sensitive boundary behavior

## Healthcheck Integration Notes

The telemetry extension is intended for Codex healthcheck reporting only after instrumentation exists. It should fit naturally beside existing healthcheck signals for hygiene, drift, and repeated workflow friction.

The first planned use is a bounded summary artifact in healthcheck output, not a live routing controller.

## Explicit Non-Goals

- no OR calls
- no production routing activation
- no routing-table update
- no `5.4` candidate continuation
- no live evals

## Operational Notes

- This plan is telemetry planning only.
- It does not authorize OR execution.
- It does not change mini workflow boundaries.
- It does not change the paused state of the separate `5.4` candidate phase.
