# OR Healthcheck Dummy Ingestion Validation - 2026-06-13

Status: DRY-RUN VALIDATION / DOCUMENTATION-ONLY / NO OR CALLS / NO MODEL CALLS / NO LIVE EVALS / NO PRODUCTION ROUTING

## Purpose

Validate the dummy OR telemetry artifacts against the documented schema before any separate `5.4` candidate work resumes.

## Ingestion Mode Used

Documentation-only dry-run validation.

Reason:

- the current healthcheck runner `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py` does not yet ingest OR telemetry JSONL
- no non-invasive runtime ingestion path exists yet for the dummy telemetry sample
- this report therefore validates the expected ingestion path and the artifact alignment without changing runtime behavior

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

- Result: `DRY-RUN ONLY`
- Check: current `health_snapshot.py` is read-only hygiene tooling and does not yet read OR telemetry JSONL rows

## Expected Ingestion Path

When runtime ingestion is implemented later, the expected path is:

1. append OR telemetry rows to a dedicated JSONL log file
2. parse each line as one JSON object
3. validate required field presence against the documented schema
4. derive healthcheck summaries from schema fields only
5. render bounded healthcheck output without changing routing authority

## Validation Summary

- Dummy JSONL parses: `PASS`
- Schema/sample/report field alignment: `PASS`
- Summary example consistency: `PASS`
- Existing runner direct ingestion: `NOT AVAILABLE`
- Documentation-only ingestion path defined: `PASS`

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
