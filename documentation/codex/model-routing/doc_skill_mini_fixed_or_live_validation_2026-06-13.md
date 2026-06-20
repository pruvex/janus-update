# Fixed OR Live Validation - 2026-06-13

Status: FIXTURE AND LOCAL VALIDATION ONLY / NO LIVE OR CALLS / NO AUTO ROUTER / NO PRODUCTION ROUTING

## Validation Summary

- config parses as JSON: PASS
- config includes exactly the seven enabled mini skills: PASS
- config maps each enabled skill to the correct fixed OR model: PASS
- Auto Router disabled in config: PASS
- operator-choice path exists: PASS
- prompt-mode operator gate exists for skill-native use: PASS
- prompt-mode gate supports `1` for Codex and `2` for OpenRouter: PASS
- live-wrapper parameter handoff no longer requires string-to-hashtable conversion: PASS
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

### Prompt-mode operator gate

- summary:
  - `documentation/codex/model-routing/fixed_or_live_validation_prompt_mode_2026-06-13.json`
- expected command:
  - `python documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py --skill-id DOC-SKILL-001 --normal-target-model "5.4 mini low" --operator-choice prompt --workflow-id FIXED-OR-PROMPT-VALIDATION-001`

Expected result:

- summary header is `FIXED OR OPERATOR CHOICE`
- final outcome is `AWAITING_OPERATOR_CHOICE`
- prompt text asks whether `1` should use Codex or `2` should use OPR with estimated cost and confidence
- no OR call is made
- the same runner can then continue with `local` or `or`

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

### Wrapper parameter handoff fix

- wrapper run directory:
  - `documentation/codex/model-routing/fixed-or-live-runs/FIXED-OR-WRAPPER-PARAM-VALIDATION-001/doc-skill-006/`
- runner validation workflow:
  - `FIXED-OR-RUNNER-PARAM-VALIDATION-001`

Expected result:

- wrapper accepts string-based authorization, referer, and title parameters
- no PowerShell `Headers` hashtable transformation failure occurs
- fixture OR path completes with `validation_result=PASS`

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
- skill-native integration still remains bounded to the seven enabled mini documentation skills only
