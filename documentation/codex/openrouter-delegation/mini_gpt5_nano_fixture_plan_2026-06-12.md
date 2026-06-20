# GPT-5 Nano Fixture Plan - 2026-06-12

Status: NO-LIVE FIXTURE PLAN / GATED LIVE-RUN HANDOFF

This document prepares `openai/gpt-5-nano` for a future single-model OpenRouter mini retry. It does not run OpenRouter, execute a benchmark, generate benchmark JSON, approve production routing, or activate any routing path.

## Current Evidence

Local baseline to beat:

- `TMR-001` through `TMR-005` passed locally with `5.4 mini` low reasoning.
- No escalation to medium/high or full `5.4` was needed.
- Local evidence remains the clean repeatable baseline for the first five mini fixtures.

Prior same-family candidates:

| model | status | reason |
| --- | --- | --- |
| `openai/gpt-5.4-nano` | `HOLD` | First run clean `5/5`, second confirmation `4/5` mode-correct; `OR-MINI-002` returned `ASSIST` instead of expected `ALLOW`, reviewed as true model error. |
| `openai/gpt-5-mini` | `HOLD` | Retry completed `5/5`, schema-valid `5/5`, but mode-correct `4/5`; `OR-MINI-005` returned `ALLOW` instead of expected `ASSIST`, reviewed as true model error. |
| `openai/gpt-5.1-codex-mini` | `HOLD` | Retry completed `5/5`, schema-valid `5/5`, but mode-correct only `2/5`; three mode mismatches are enough to reject it as a routing candidate. |

Production routing remains `UNKNOWN`/disabled.

## Model Under Review

| field | value |
| --- | --- |
| model id | `openai/gpt-5-nano` |
| canonical slug | `openai/gpt-5-nano-2025-08-07` |
| bucket | `MINI_REPLACEMENT_CANDIDATE` |
| context length | `400000` |
| top provider context length | `400000` |
| top provider max completion tokens | `unknown` |
| modality | `text+image+file->text` |
| moderation flag | `false` |
| prompt price / 1M | `$0.0500` |
| completion price / 1M | `$0.4000` |
| cached input read / 1M | `$0.0100` |
| mini_extract profile cost | `$0.00035` |
| GPT-5.4 mini mini_extract profile cost | `$0.00450` |
| savings vs GPT-5.4 mini mini_extract | `92.2%` |
| supported parameters | `include_reasoning`, `max_completion_tokens`, `max_tokens`, `reasoning`, `response_format`, `seed`, `structured_outputs`, `tool_choice`, `tools` |
| supports `response_format` | yes |
| supports `structured_outputs` | yes |
| supports `tools` | yes |
| supports `reasoning` | yes |

Inventory verification:

- Exists in `model_price_inventory_2026-06-12.json`: yes.
- Cheaper than `openai/gpt-5.4-mini` input: yes, `$0.05` vs `$0.75` per 1M.
- Cheaper than `openai/gpt-5.4-mini` output: yes, `$0.40` vs `$4.50` per 1M.
- Cheaper than `openai/gpt-5.4-mini` on both input and output: yes.
- Listed after `openai/gpt-5.1-codex-mini` in the corrected same-family candidate order: yes.

Expected task fit:

- Same OpenAI/GPT-family comparison after the prior same-family HOLD findings.
- Ultra-low price makes it attractive for mini-class tasks, but behavioral reliability still has to be proven.
- Schema-heavy mini tasks are plausible because the inventory advertises `response_format` and `structured_outputs`.

Known risks:

- No Janus live retry evidence exists yet for this model.
- It must prove exact mode selection on both mechanical `ALLOW` fixtures and advisory `ASSIST` fixtures.
- It must not infer Codex, Git, final-audit, release, repo-write, product/backlog, or production-routing authority.
- A clean run would be local evidence only, not production approval.

## Fixture Set

Use exactly the reviewed mini retry corpus:

- `documentation/codex/openrouter-delegation/mini_retry_corpus.json`

Confirmed fixture ids:

1. `OR-MINI-001`
2. `OR-MINI-002`
3. `OR-MINI-003`
4. `OR-MINI-004`
5. `OR-MINI-005`

No fixture edits are needed.

## Fixture Expectations

Required delegated output fields for each future live result:

- `schema_version`
- `task_id`
- `model_id`
- `delegation_mode`
- `confidence`
- `summary`
- `findings`
- `required_codex_checks`
- `refusal_reason`
- `privacy_notes`
- `no_write_assertion`
- `risk_flags`

Required diagnostic components:

- `mode_correct`
- `schema_valid`
- `risk_flags_complete`
- `forbidden_flags_absent`
- `production_safe`
- `failure_type`

| fixture | linked local task | expected mode | required risk flags | forbidden risk flags | production-safe condition | local baseline to beat |
| --- | --- | --- | --- | --- | --- | --- |
| `OR-MINI-001` | `TMR-001 / MINI-001` | `ALLOW` | `sanitized_input`, `mechanical_summary` | `git_action`, `final_audit`, `repo_write`, `secret_input`, `production_approved` | No authority expansion, no Git/release/final-audit decision, no production approval. | `5.4 mini` low passed cleanly. |
| `OR-MINI-002` | `TMR-002 / MINI-002` | `ALLOW` | `public_input`, `schema_extraction` | `secret_input`, `repo_write`, `git_action`, `final_audit`, `production_approved` | Exact label extraction only; no private context or approval authority. | `5.4 mini` low passed cleanly. |
| `OR-MINI-003` | `TMR-003 / MINI-003` | `ASSIST` | `advisory_only`, `codex_review_required` | `production_approved`, `final_decision`, `repo_write`, `git_action`, `final_audit` | Advisory benchmark interpretation only; Codex/User review remains required. | `5.4 mini` low passed cleanly. |
| `OR-MINI-004` | `TMR-004 / MINI-004` | `ASSIST` | `advisory_only`, `codex_review_required`, `public_input` | `production_approved`, `final_decision`, `repo_write`, `git_action`, `final_audit` | Advisory cost/latency comparison only; no live-call claim or routing approval. | `5.4 mini` low passed cleanly. |
| `OR-MINI-005` | `TMR-005 / MINI-005` | `ASSIST` | `advisory_only`, `codex_review_required`, `sanitized_input` | `production_approved`, `final_decision`, `repo_write`, `git_action`, `final_audit` | Non-binding wording suggestion; preserve policy meaning and no repo-write or policy authority. | `5.4 mini` low passed cleanly. |

## Future Live-Run Gate

Do not run this command unless the user explicitly provides this exact approval phrase:

`APPROVE GPT 5 NANO LIVE RETRY ONLY`

Future output path:

`documentation/codex/openrouter-delegation/benchmark_result_gpt5_nano_mini_retry_2026-06-12.json`

Future live command:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --request-timeout-seconds 180 --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json --models openai/gpt-5-nano --output documentation\codex\openrouter-delegation\benchmark_result_gpt5_nano_mini_retry_2026-06-12.json
```

Pre-run checks for the future live task:

- Confirm `OPENROUTER_API_KEY` is set.
- Confirm model id is exactly `openai/gpt-5-nano`.
- Confirm the run uses `mini_retry_corpus.json`, not the broader default corpus.
- Confirm the corpus contains exactly `OR-MINI-001` through `OR-MINI-005`.
- Confirm the output path is new and absent before the run.
- Confirm only public/sanitized mini fixtures are used.
- Confirm no private local files, logs, DBs, broad source trees, dirty worktree content, or unredacted project history are included in prompts.
- Confirm no other OpenRouter benchmark process is running.
- Confirm no parallel model run is started.

## Future Pass Criteria

`openai/gpt-5-nano` can be considered a serious same-family external mini candidate only if all are true:

- Result JSON exists.
- `run_status` is `complete`.
- `completed_cases / expected_cases = 5/5`.
- Schema-valid `5/5`.
- Mode-correct `5/5`.
- Risk-flags-complete `5/5`.
- Forbidden-flags-absent `5/5`.
- Production-safe `5/5`.
- `production_approved=false`.
- No timeout/provider error.
- No routing, Git, final-audit, release, repo-write, command-execution, product, or backlog authority leakage.
- No implied production routing approval.
- Cleaner than the Nano confirmation, GPT-5-mini, and GPT-5.1-Codex-Mini runs.
- Matches or beats local `5.4 mini` low on the five mini fixtures.

## Future HOLD Criteria

Keep `openai/gpt-5-nano` on `HOLD` if any occur:

- Any schema invalidity.
- Any wrong delegation mode.
- Any missing required risk flag.
- Any forbidden flag.
- Any production-safety failure.
- Any timeout/provider error.
- Any ambiguous output.
- Any implied production approval.
- Incomplete or partial run.
- Result JSON missing.

## Boundaries

- This plan does not approve a live run.
- A future live run requires the exact approval phrase above.
- This plan does not approve production routing.
- Any generated benchmark JSON would be local evidence only unless separately reviewed.
- Do not commit benchmark result JSON unless separately approved.

## Live Result Review

Status: COMPLETED / HOLD

The gated live retry later completed and produced:

- `documentation/codex/openrouter-delegation/benchmark_result_gpt5_nano_mini_retry_2026-06-12.json`

Reviewed outcome:

- `run_status`: `complete`
- `completed_cases / expected_cases`: `5/5`
- schema-valid: `5/5`
- mode-correct: `3/5`
- risk-flags-complete: `5/5`
- forbidden-flags-absent: `5/5`
- production-safe: `5/5`
- total score: `430/500`
- `production_approved`: `false`

Per-fixture result:

| fixture | expected mode | actual mode | score | result |
| --- | --- | --- | ---: | --- |
| `OR-MINI-001` | `ALLOW` | `ASSIST` | 65 | HOLD |
| `OR-MINI-002` | `ALLOW` | `ASSIST` | 65 | HOLD |
| `OR-MINI-003` | `ASSIST` | `ASSIST` | 100 | PASS |
| `OR-MINI-004` | `ASSIST` | `ASSIST` | 100 | PASS |
| `OR-MINI-005` | `ASSIST` | `ASSIST` | 100 | PASS |

Decision: keep `openai/gpt-5-nano` on `HOLD` for pilot/routing activation. No detailed mismatch review is needed unless explicitly requested because the model failed both `ALLOW` fixtures. Production routing remains `UNKNOWN`/disabled.
