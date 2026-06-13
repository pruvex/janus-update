# OR Healthcheck Dummy Ingestion Validation - 2026-06-13

Status: DRY-RUN VALIDATION / DOCUMENTATION-ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING

## Purpose

Validate the dummy OR telemetry artifacts against the documented schema before any separate `5.4` candidate work resumes.

## Ingestion Mode Used

Healthcheck runner dry-run with optional dummy JSONL input.

Reason:

- the existing read-only runner now supports an optional `--or-telemetry-jsonl` path
- only the dummy JSONL sample was used
- no production behavior was changed because the runner reads OR telemetry only when the optional flag is passed

## Bound Artifacts

- `documentation/codex/model-routing/or_healthcheck_telemetry_jsonl_schema_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_dummy_sample_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_summary_dummy_example_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_plan_2026-06-13.md`

## Dry-Run Checks

### 1. Dummy JSONL Parse

- Result: `PASS`
- Method: one-line JSON object parsed successfully into a structured object

### 2. Schema And Sample Field Alignment

- Result: `PASS`
- Check: the documented JSONL schema lists the operational telemetry, cost, confidence, fallback, validation, and recommendation fields expected by the dummy sample

Required coverage confirmed for:

- `estimated_or_cost`
- `actual_or_cost`
- `cost_estimate_confidence_percent`
- `cost_estimate_sample_count`
- `cost_estimate_mean_abs_error_percent`
- `cost_estimate_p50_error_percent`
- `cost_estimate_p90_error_percent`
- `prompt_template_hash`
- `task_variant`
- `latency_ms`
- `validation_result`
- `fallback_used`
- `rework_required`
- `recommendation_signal`

### 3. Summary Example Consistency

- Result: `PASS`
- Check: the dummy summary example references only fields defined in the JSONL schema

### 4. Healthcheck Runner Readiness

- Result: `PASS`
- Check: current `health_snapshot.py` can now read the dummy OR telemetry JSONL via an optional flag and emit a bounded summary without changing default healthcheck behavior

Observed dummy summary output:

- `record_count`: `1`
- `models_seen`: `qwen/qwen3.5-flash-02-23`
- `skills_seen`: `DOC-SKILL-008`
- `estimated_cost_total`: `0.00042`
- `actual_cost_total`: `0.0004`
- `confidence_average`: `72.0`
- `fallback_count`: `0`
- `validation_result_counts`: `PASS=1`
- `recommendation_signal_counts`: `OR_PREFERRED=1`

## Expected Ingestion Path

The current dry-run ingestion path is:

1. call `health_snapshot.py` with `--or-telemetry-jsonl <dummyfile>`
2. parse each line as one JSON object
3. derive bounded OR summary fields from schema-backed sample data
4. include the OR summary only when the optional flag is used
5. keep normal healthcheck output unchanged when the flag is omitted

## Validation Summary

- Dummy JSONL parses: `PASS`
- Schema/sample/report field alignment: `PASS`
- Summary example consistency: `PASS`
- Existing runner optional ingestion: `PASS`
- Dry-run ingestion path defined: `PASS`

## Non-Goals Reconfirmed

- no OR calls
- no model calls
- no live evals
- no production routing activation
- no canonical routing-table update
- no `5.4` candidate continuation

## Notes

- `DOC-SKILL-011` remains `NOT RUN`.
- Mini matrix counts remain `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, `OR_REJECTED=0`.
- The separate `5.4` candidate phase remains paused.
