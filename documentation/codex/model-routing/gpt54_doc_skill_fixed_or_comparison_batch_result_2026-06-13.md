# GPT-5.4 Documentation Skill Fixed OR Comparison Batch Result - 2026-06-13

Status: BOUNDED LIVE EVIDENCE / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Scope

Approved bounded comparison batch:

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`

Candidate pool:

- `openai/gpt-oss-20b`
- `openai/gpt-oss-120b`
- `inclusionai/ling-2.6-flash`
- `mistralai/mistral-nemo`
- `ibm-granite/granite-4.1-8b`

## Batch Outcome

| metric | value |
| --- | --- |
| workflow_id | `GPT54-FIXED-OR-COMPARISON-BATCH-001` |
| accepted telemetry rows | `12` |
| technical failure rows | `3` |
| total actual cost | `0.00117698` |
| total estimated cost | `0.00183970` |
| accepted models seen | `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, `mistralai/mistral-nemo`, `ibm-granite/granite-4.1-8b` |
| fallback_count | `0` |
| validation_result_counts | `PASS=1`, `HOLD=6`, `FAIL=5` |
| recommendation_signal_counts | `OR_PREFERRED=1`, `MANUAL_REVIEW=6`, `CODEX_PREFERRED=5` |

## Technical Failure Summary

`inclusionai/ling-2.6-flash` failed on all three scoped skills with upstream `HTTP 429` rate limiting. These rows were captured as technical failures only and were not accepted into the main telemetry file because `generation_id` and usage were unavailable.

Failure artifact:

- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_fixed_or_comparison_batch_failures_2026-06-13.jsonl`

## Per-Row Summary

| skill_id | model | validation_result | recommendation_signal | actual_cost | notes |
| --- | --- | --- | --- | ---: | --- |
| `DOC-SKILL-002` | `openai/gpt-oss-20b` | `HOLD` | `MANUAL_REVIEW` | `0.00023372` | missed explicit no-production caveat |
| `DOC-SKILL-002` | `mistralai/mistral-nemo` | `HOLD` | `MANUAL_REVIEW` | `0.00002590` | missed `not approved` and no-production caveat |
| `DOC-SKILL-002` | `ibm-granite/granite-4.1-8b` | `PASS` | `OR_PREFERRED` | `0.00007530` | clean preservation against current local baseline checks |
| `DOC-SKILL-002` | `openai/gpt-oss-120b` | `HOLD` | `MANUAL_REVIEW` | `0.00012904` | missed explicit no-production caveat |
| `DOC-SKILL-006` | `openai/gpt-oss-20b` | `FAIL` | `CODEX_PREFERRED` | `0.00021836` | live-call permission drift and missing operator reminder |
| `DOC-SKILL-006` | `mistralai/mistral-nemo` | `FAIL` | `CODEX_PREFERRED` | `0.00001670` | live-call permission drift |
| `DOC-SKILL-006` | `ibm-granite/granite-4.1-8b` | `FAIL` | `CODEX_PREFERRED` | `0.00004080` | live-call permission drift and missing operator reminder |
| `DOC-SKILL-006` | `openai/gpt-oss-120b` | `FAIL` | `CODEX_PREFERRED` | `0.00022295` | live-call permission drift and missing operator reminder |
| `DOC-SKILL-008` | `openai/gpt-oss-20b` | `HOLD` | `MANUAL_REVIEW` | `0.00008606` | missed routing-table, experiment-only, and mini-path caveats |
| `DOC-SKILL-008` | `openai/gpt-oss-120b` | `HOLD` | `MANUAL_REVIEW` | `0.00007038` | missed routing-table, experiment-only, and mini-path caveats |
| `DOC-SKILL-008` | `mistralai/mistral-nemo` | `FAIL` | `CODEX_PREFERRED` | `0.00001612` | authority violation and missing non-production caveats |
| `DOC-SKILL-008` | `ibm-granite/granite-4.1-8b` | `HOLD` | `MANUAL_REVIEW` | `0.00004165` | missed routing-table, experiment-only, and no-live-5.4 caveats |

## Healthcheck Ingestion

Accepted telemetry file:

- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_fixed_or_comparison_batch_2026-06-13.jsonl`

Healthcheck summary:

- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-FIXED-OR-COMPARISON-BATCH-001/healthcheck_summary.json`

`health_snapshot.py --or-telemetry-jsonl` ingestion passed on the accepted telemetry file.

## Batch Decision

This batch does not support broad OR replacement for the first three `5.4` documentation-skill fixtures.

What it does support:

- one narrow positive signal for `DOC-SKILL-002` on `ibm-granite/granite-4.1-8b`
- strong evidence that `DOC-SKILL-006` should stay local/Codex for now
- mixed-to-negative evidence for `DOC-SKILL-008`, with no tested candidate clearing all caveat gates

## Boundaries

- no production routing was enabled
- no canonical routing-table update was made
- no global OR approval was created
- Auto Router was not used
- mini fixed-model Auto-sparsam remains unchanged
