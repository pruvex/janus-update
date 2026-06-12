# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review and document the completed `openai/gpt-5.1-codex-mini` mini retry result.

## Active Phase
Dev-environment Codex model-routing evidence review. No OpenRouter live calls, benchmark reruns, model execution, production routing activation, backlog update, or Git action in this pass.

## Last Decision
This remains a Codex development-environment and skill-orchestration evaluation, not a Janus application backlog item.

OpenRouter delegation remains non-production:

- OpenRouter may only receive public or sanitized benchmark prompts from curated fixtures when explicitly approved.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, runtime state, dirty worktree content, or unredacted Janus project history.
- OpenRouter must not write repo files, patch code, run commands, approve Git actions, approve final audits, make release-readiness or publish decisions, or decide Janus product scope/backlog priority/user-facing behavior.
- Production routing remains `UNKNOWN`/disabled until local and external evidence is reviewed and the user explicitly approves activation.

## Last Codex Work
Reviewed and documented the completed `openai/gpt-5.1-codex-mini` mini retry result.

Evidence reviewed:

- `documentation/codex/openrouter-delegation/benchmark_result_gpt51_codex_mini_mini_retry_2026-06-12.json`
- `documentation/codex/openrouter-delegation/mini_gpt51_codex_mini_fixture_plan_2026-06-12.md`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/model_candidate_shortlist_2026-06-12.md`
- `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`
- `documentation/codex/openrouter-delegation/mini_retry_corpus.json`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

Updated:

- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/mini_gpt51_codex_mini_fixture_plan_2026-06-12.md`

`openai/gpt-5.1-codex-mini` result:

- `run_status`: `complete`
- `completed_cases / expected_cases`: `5/5`
- `missing_cases`: none
- `failure_type`: `none`
- `failure_message`: `null`
- schema-valid: `5/5`
- mode-correct: `2/5`
- risk-flags-complete: `5/5`
- forbidden-flags-absent: `5/5`
- production-safe: `5/5`
- production_approved: `false`
- total score: `395/500`
- timeout/provider errors: `0`

Per-fixture summary:

- `OR-MINI-001`: HOLD, expected `ALLOW`, got `ASSIST`, score `65`.
- `OR-MINI-002`: HOLD, expected `ALLOW`, got `UNKNOWN`, score `65`.
- `OR-MINI-003`: PASS, expected `ASSIST`, got `ASSIST`, score `100`.
- `OR-MINI-004`: PASS, expected `ASSIST`, got `ASSIST`, score `100`.
- `OR-MINI-005`: HOLD, expected `ASSIST`, got `ALLOW`, score `65`.

Decision:

- Keep `openai/gpt-5.1-codex-mini` on `HOLD` for pilot/routing activation.
- Do not perform detailed mismatch review unless explicitly requested, because `3/5` mode failures are enough to reject it as a mini routing candidate.
- Do not edit mini fixtures.
- Production routing remains `UNKNOWN`/disabled.

Current same-family status:

- Local `5.4 mini low`: clean repeatable baseline for `TMR-001` through `TMR-005`.
- `openai/gpt-5.4-nano`: `HOLD`; first run clean `5/5`, second confirmation `4/5` mode-correct because `OR-MINI-002` returned `ASSIST` instead of expected `ALLOW`; mismatch reviewed as true model error.
- `openai/gpt-5-mini`: `HOLD`; first run `4/5` mode-correct because `OR-MINI-005` returned `ALLOW` instead of expected `ASSIST`; mismatch reviewed as true model error.
- `openai/gpt-5.1-codex-mini`: `HOLD`; retry complete but mode-correct only `2/5`.

Prior non-OpenAI status:

- `qwen/qwen3.7-plus`: `HOLD`; schema-valid `0/5`, mode-correct `4/5`, risk-flags-complete `5/5`, forbidden-flags-absent `5/5`, production-safe `5/5`.
- `stepfun/step-3.7-flash`: `HOLD`; second retry completed, schema-valid `5/5`, mode-correct `4/5`, risk-flags-complete `5/5`, forbidden-flags-absent `5/5`, production-safe `4/5`.
- `minimax/minimax-m3`: `HOLD`; schema projection history requires review.
- `inclusionai/ring-2.6-1t`: `HOLD`; prior timeout, missing risk flags, and ASSIST/ALLOW issue.
- Free models: `HOLD` / inconclusive for production-style routing.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/mini_gpt51_codex_mini_fixture_plan_2026-06-12.md`
- `documentation/codex/SKILL_USAGE_LOG.md`
- `documentation/codex/openrouter-delegation/benchmark_result_gpt51_codex_mini_mini_retry_2026-06-12.json` (reviewed local evidence only; not generated in this documentation pass)

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- No Git staging, commit, push, tag, merge, release, or backlog update was performed.
- This CURRENT_STATE update and the GPT-5.1-Codex-Mini evidence review are local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE or scoring-report updates.

## Tests / Validation
- JSON parse for `benchmark_result_gpt51_codex_mini_mini_retry_2026-06-12.json` -> PASS.
- Confirmed required benchmark result fields -> PASS.
- Confirmed `completed_cases / expected_cases = 5/5` -> PASS.
- Confirmed mode-correct `2/5` -> PASS.
- Confirmed schema-valid, risk-flags-complete, forbidden-flags-absent, and production-safe all `5/5` -> PASS.
- Confirmed `summary.production_approved=false` -> PASS.
- Markdown sanity on touched docs -> PASS.
- No OpenRouter live calls, benchmark reruns, or model execution in this documentation pass -> PASS.
- No benchmark result JSON generated in this documentation pass -> PASS.
- `git diff --check` on touched files -> PASS.
- Verified no staged files -> PASS.
- Skill usage recorded with `documentation/codex/scripts/record_skill_usage.py` -> PASS.

## Open Risks
- `openai/gpt-5.1-codex-mini` is schema-stable and production-safe on this run, but fails route-label reliability with three mode mismatches.
- Cheaper same-family candidates tested so far are all `HOLD`; local `5.4 mini low` remains the cleaner mini baseline.
- Broader tasks beyond `TMR-001` through `TMR-005` remain untested for same-family candidates.
- Production routing remains `UNKNOWN`/disabled.
- The worktree contains unrelated pre-existing changes; do not stage broadly.

## Next Recommended Step for ChatGPT
Review the GPT-5.1-Codex-Mini HOLD conclusion. Recommended next task: prepare a no-live fixture plan and gated live-run handoff for `openai/gpt-5-nano` as the next same-family comparison candidate.

## Next Recommended Step for Codex
If the user continues, prepare the no-live fixture plan and gated live-run handoff for `openai/gpt-5-nano`. Do not run OpenRouter or approve production routing.

## Last Updated
2026-06-12 19:57 local time
