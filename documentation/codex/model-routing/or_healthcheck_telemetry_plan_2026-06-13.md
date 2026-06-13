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
- `estimated_prompt_tokens`
- `estimated_completion_tokens`
- `estimated_or_cost`
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

## Field Guidance

- `workflow_id`: stable identifier for one documentation workflow run.
- `skill_id`: exact `DOC-SKILL-XXX` row or equivalent documentation-skill identifier.
- `routing_mode`: `Codex-only`, `Auto-sparsam`, or `Manual-review`.
- `selected_path`: concise executed route such as `codex_local`, `or_first_then_codex_validate`, or `or_rejected_fallback_codex`.
- `codex_default_model`: declared Codex default such as `5.4 mini low`.
- `or_model`: selected OR model name when one is part of the route; blank or `N_A` when not used.
- `estimated_prompt_tokens`: predicted prompt-token count before the OR call.
- `estimated_completion_tokens`: predicted completion-token count before the OR call.
- `estimated_or_cost`: planned OR spend estimate from the current price snapshot.
- `price_snapshot_source`: source for the model price snapshot used in the estimate.
- `price_snapshot_timestamp`: timestamp of the price snapshot used for the estimate.
- `actual_prompt_tokens`: prompt-token count reported after the OR call when available.
- `actual_completion_tokens`: completion-token count reported after the OR call when available.
- `actual_reasoning_tokens`: reasoning-token count when OpenRouter usage or later generation stats expose it.
- `actual_cached_tokens`: cached-token count when exposed by response usage or later generation stats.
- `actual_or_cost`: actual OR cost when available from response usage or generation lookup.
- `generation_id`: OpenRouter generation identifier when available for later reconciliation.
- `usage_source`: `response_usage`, `generation_endpoint`, or `fallback_estimate`.
- `estimated_codex_effort`: optional local effort estimate such as `low`, `medium`, `high`, or token/time proxy.
- `estimation_error_percent`: percent deviation between estimated and actual OR cost when both are known.
- `cost_delta_vs_codex_estimate`: OR actual or fallback-estimated cost minus local Codex effort proxy converted to a comparable planning number when available.
- `latency_ms`: total OR path latency when available.
- `validation_result`: local validation result such as `PASS`, `FAIL`, `HOLD`, or `NEEDS_REVIEW`.
- `fallback_used`: `YES` or `NO`.
- `rework_required`: `YES` or `NO`.
- `final_outcome`: terminal workflow result such as `OR_PASSED_LOCAL_VALIDATION`, `CODEX_ONLY_FINAL`, `MANUAL_REVIEW_REQUIRED`, or `BLOCKED`.
- `reason_for_escalation`: concise cause when the flow leaves Auto-sparsam or Manual-review.
- `quality_notes`: short bounded notes for observed quality, boundary preservation, or mismatch patterns.

## Cost Prediction And Actual Accounting

### Pre-call Cost Estimate Formula

Before an OR call, estimate:

```text
estimated_or_cost =
  (estimated_prompt_tokens / 1_000_000 * prompt_price_per_million)
  + (estimated_completion_tokens / 1_000_000 * completion_price_per_million)
```

If the price model exposes one blended output rate rather than separate completion categories, use the best bounded approximation from the active price snapshot and note it in `quality_notes`.

### Post-call Actual Cost Capture

After an OR call, capture actual accounting from OpenRouter usage when available:

- read prompt and completion token counts from response usage metadata
- record reasoning and cached token counts when the response provides them
- record response cost if the response already contains it
- keep `generation_id` so later reconciliation can re-query generation stats if needed
- mark `usage_source=response_usage` when response-level usage was sufficient

### Fallback Calculation If Usage Is Missing

If response-level usage is incomplete:

1. use `generation_id` to reconcile later via generation stats
2. if later reconciliation succeeds, set `usage_source=generation_endpoint`
3. if no usage source becomes available, compute a bounded fallback estimate from:
   - stored pre-call token estimates
   - latest retained price snapshot
   - any known output-length proxy from the saved response
4. mark `usage_source=fallback_estimate`
5. flag the record in `quality_notes` as lower-confidence accounting

### Price Snapshot Retention Rule

Retain the exact price basis that was used for prediction:

- keep `price_snapshot_source`
- keep `price_snapshot_timestamp`
- do not recompute historical estimates against newer prices during later healthcheck summaries
- if price data changes later, compare old vs new only in a separate planning note, not by mutating the original telemetry record

### Estimation Error

When both estimate and actual are available:

```text
estimation_error_percent =
  ((actual_or_cost - estimated_or_cost) / estimated_or_cost) * 100
```

If `estimated_or_cost` is zero or unavailable, leave `estimation_error_percent` blank or `N_A`.

## Healthcheck Outputs

The Codex healthcheck extension should summarize OR telemetry into these outputs:

- `per-skill OR reliability summary`
- `per-model OR reliability summary`
- `fallback frequency`
- `validation failure frequency`
- `cost delta summary`
- `time delta summary`
- `recommendation signal: OR_PREFERRED / CODEX_PREFERRED / MANUAL_REVIEW`
- `price snapshot coverage summary`
- `usage accounting completeness summary`
- `estimation error summary`

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

### Price snapshot coverage summary

Track whether cost prediction used a retained price basis:

- rows with `price_snapshot_source`
- rows with `price_snapshot_timestamp`
- rows missing one or both values

### Usage accounting completeness summary

Track cost-accounting quality by source:

- `response_usage` count
- `generation_endpoint` count
- `fallback_estimate` count
- rows missing `generation_id` where later reconciliation would have helped

### Estimation error summary

When both predicted and actual costs exist, summarize:

- median estimation error
- worst overestimate
- worst underestimate
- skills or models with repeated error drift

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

Healthcheck optimization reports should prefer these summary fields when available:

- top `skill_id` by fallback pressure
- top `or_model` by validation stability
- cost prediction accuracy band
- usage accounting completeness rate
- median latency by model
- OR-vs-Codex cost delta trend
- recommendation signal distribution

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
