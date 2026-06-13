# Fixed OR Live Validation - 2026-06-13

Status: FIXTURE AND LOCAL VALIDATION ONLY / NO LIVE OR CALLS / NO AUTO ROUTER / NO PRODUCTION ROUTING

## Validation Summary

- config parses as JSON: PASS
- config includes exactly the seven enabled mini skills: PASS
- config maps each enabled skill to the correct fixed OR model: PASS
- Auto Router disabled in config: PASS
- operator-choice path exists: PASS
- local Codex option makes no OR call: PASS
- fixed OR option builds fixed-model request body: PASS
- out-of-scope skill routes to Codex-only before wrapper invocation: PASS
- missing confidence aborts before wrapper invocation: PASS
- `health_snapshot.py --or-telemetry-jsonl` ingests accepted fixture telemetry: PASS

## Evidence Paths

### Config parse

- `documentation/codex/model-routing/config/doc_skill_mini_fixed_or_live_enabled_2026-06-13.json`

### Local Codex option

- run directory:
  - `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-LOCAL-VALIDATION-001/doc-skill-001/`
- evidence:
  - `operator_choice_prompt.json`
  - `operator_decision.json`

Expected result:

- local choice recorded
- no wrapper response artifacts created
- no OR telemetry JSONL appended

### Fixed OR fixture option

- fixture response:
  - `documentation/codex/model-routing/fixtures/fixed_or_live_success_fixture_2026-06-13.json`
- run directory:
  - `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-FIXTURE-VALIDATION-001/doc-skill-001/`
- accepted telemetry:
  - `documentation/codex/model-routing/or_healthcheck_telemetry_fixed_or_session_2026-06-13_FIXED-OR-FIXTURE-VALIDATION-001.jsonl`

Key checks:

- `request_body.json` model is `openai/gpt-oss-20b`
- `response_summary.json` contains `generation_id`, usage, actual cost, and `finish_reason=stop`
- `operator_summary.json` reports `validation_result=PASS`
- `healthcheck_summary.json` shows successful OR telemetry ingestion

### Out-of-scope fallback

- summary:
  - `documentation/codex/model-routing/fixed_or_live_validation_out_of_scope_2026-06-13.json`

Expected result:

- `DOC-SKILL-011` routes to `codex_only_pre_wrapper`
- no wrapper invocation

### Missing confidence abort

- validation config:
  - `documentation/codex/model-routing/config/doc_skill_mini_fixed_or_live_enabled_missing_confidence_fixture_2026-06-13.json`
- validation fixture JSONL:
  - `documentation/codex/model-routing/fixtures/fixed_or_live_missing_confidence_fixture_2026-06-13.jsonl`
- summary:
  - `documentation/codex/model-routing/fixed_or_live_validation_missing_confidence_2026-06-13.json`

Expected result:

- route aborts before wrapper invocation
- final outcome is `ABORTED_MISSING_CONFIDENCE`

## Boundary Reminder

- no live OR call was made during validation
- no Auto Router was used
- no production routing was activated
- no canonical routing-table update was made
