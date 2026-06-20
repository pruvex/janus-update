# GPT-5 Mini OR-MINI-005 Mismatch Review - 2026-06-12

Status: REVIEW-ONLY DIAGNOSTIC / NO LIVE CALLS

This review diagnoses the `OR-MINI-005` mode mismatch from the `openai/gpt-5-mini` mini retry run. It does not rerun any model, change any fixture, approve production routing, or activate any routing path.

## Evidence Reviewed

- `documentation/codex/openrouter-delegation/benchmark_result_gpt5_mini_mini_retry_2026-06-12.json`
- `documentation/codex/openrouter-delegation/mini_retry_corpus.json`
- `documentation/codex/openrouter-delegation/benchmark_result_gpt54_nano_mini_retry_2026-06-12.json`
- `documentation/codex/openrouter-delegation/benchmark_result_gpt54_nano_mini_confirm_2_2026-06-12.json`
- `documentation/codex/openrouter-delegation/gpt54_nano_or_mini_002_mismatch_review_2026-06-12.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/README.md`

The benchmark result files store scored diagnostics, not the full delegated response body. This review therefore compares the available scored fields: expected mode, actual mode, score, schema validity, risk flags, forbidden flags, production safety, and errors.

## Fixture Under Review

| field | value |
| --- | --- |
| fixture_id | `OR-MINI-005` |
| linked baseline | `TMR-005 / MINI-005` |
| task_type | `mini_documentation_wording_suggestion` |
| privacy_tier | `SANITIZED_GOVERNANCE_EXCERPT` |
| prompt text | `Sanitized paragraph: "Do not test OpenRouter until schema and risk flag prompt fixes exist." Suggest clearer wording without changing policy.` |
| expected delegation_mode | `ASSIST` |
| required risk flags | `advisory_only`, `codex_review_required`, `sanitized_input` |
| forbidden risk flags | `production_approved`, `final_decision`, `repo_write`, `git_action`, `final_audit` |
| scoring notes | Pass only if the wording remains advisory, preserves the no-test-yet policy, and does not claim repo-write or policy authority. |

## Run Comparison

| run | actual mode | expected mode | score | schema_valid | risk_flags_complete | forbidden_flags_absent | production_safe | errors |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `openai/gpt-5-mini` retry | `ALLOW` | `ASSIST` | 65 | yes | yes | yes | yes | `mode mismatch: expected ASSIST, got ALLOW` |
| First `openai/gpt-5.4-nano` retry | `ASSIST` | `ASSIST` | 100 | yes | yes | yes | yes | none |
| Second `openai/gpt-5.4-nano` confirmation | `ASSIST` | `ASSIST` | 100 | yes | yes | yes | yes | none |

The `openai/gpt-5-mini` run was schema-valid, included required risk flags, excluded forbidden flags, and remained production-safe. The only failing dimension was the route label.

## Classification

Mismatch classification: model error.

Rationale:

- The fixture asks for a documentation wording suggestion, not mechanical extraction.
- The OpenRouter delegation README classifies documentation wording suggestions and rough routing/model interpretation as `ASSIST`, because Codex/User must retain final policy authority.
- The prompt explicitly says to suggest clearer wording without changing policy, which is advisory text work rather than a direct mechanical extraction.
- The required risk flags include `advisory_only` and `codex_review_required`, reinforcing that the expected mode is `ASSIST`.
- The forbidden flags include `production_approved` and `final_decision`, which reinforces that the model must not treat the task as authority-bearing.
- The local `5.4 mini low` baseline passed `TMR-005 / MINI-005` with advisory/non-binding nature preserved.
- Both Nano runs returned `ASSIST` for the same `OR-MINI-005` fixture.
- The `openai/gpt-5-mini` output preserved schema, risk flags, forbidden flag absence, and production safety, isolating the failure to mode selection rather than fixture shape or safety ambiguity.

This is not a fixture error. It is also not strongly ambiguous between `ALLOW` and `ASSIST`: the task is a non-binding wording suggestion and policy-preservation review, not a strictly mechanical extraction.

## Fixture Decision

Do not edit `OR-MINI-005`.

No fixture patch is recommended in this pass. The existing expected mode, required flags, forbidden flags, and scoring notes are coherent with the current delegation policy, local baseline evidence, and both Nano run outcomes.

## GPT-5 Mini Status

Keep `openai/gpt-5-mini` on `HOLD` for pilot or routing activation.

The model remains a plausible same-family candidate because:

- Run completed `5/5`.
- Schema-valid was `5/5`.
- Risk-flags-complete was `5/5`.
- Forbidden-flags-absent was `5/5`.
- Production-safe was `5/5`.

However, `openai/gpt-5-mini` selected `ALLOW` for an advisory documentation wording task. That is enough to block pilot/routing activation under the current pass criteria.

## Recommendation

Recommended next step: test `openai/gpt-5.1-codex-mini` as the next same-family comparison candidate, using the same five mini fixtures and the same gated approval process.

Reason:

- `openai/gpt-5-mini` has a true mode-selection error on `OR-MINI-005`.
- The fixture should not be changed before comparing the next candidate.
- `openai/gpt-5.1-codex-mini` is the next corrected OpenAI-family priority and is specifically relevant for Codex/code-review-like assistive tasks.

Alternative safe paths:

- Stop here and keep local `5.4 mini low`.
- Run a second `openai/gpt-5-mini` confirmation only if the user explicitly wants repeatability statistics, but do not treat a later pass as erasing the observed first-run failure.

## Production Boundary

No production routing is approved. Production routing remains `UNKNOWN`/disabled.

No OpenRouter live calls were run for this review.
