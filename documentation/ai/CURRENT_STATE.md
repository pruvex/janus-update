# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review the controlled OpenRouter live retry attempts for Qwen and Step against the five first-batch mini fixtures.

## Active Phase
Dev-environment Codex model-routing and OpenRouter live retry evidence review. No production routing.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive public or sanitized benchmark prompts from a curated corpus or reviewed mini-task fixture.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, runtime state, dirty worktree content, or unredacted Janus project history.
- OpenRouter must not write repo files, patch code, run commands, approve Git actions, approve final audits, make release-readiness or publish decisions, or decide Janus product scope/backlog priority/user-facing behavior.
- Production routing remains `UNKNOWN`/disabled until local Codex mini baselines exist, OpenRouter prompt/schema fixes are reviewed, benchmark evidence is reviewed, and the user explicitly approves activation.

## Last Codex Work
Received explicit approval phrase: `APPROVE STEP LIVE RETRY ONLY`.

Read the bound Step retry artifacts:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/mini_retry_fixture_plan.md`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/openrouter-delegation/mini_retry_corpus.json`
- `documentation/codex/openrouter-delegation/benchmark_result_qwen37_plus_mini_retry_2026-06-12.json`
- `documentation/codex/openrouter-delegation/schemas/delegated_task_result.schema.json`
- `documentation/codex/openrouter-delegation/schemas/benchmark_result.schema.json`

Pre-run checks for Step:

- `OPENROUTER_API_KEY` was set.
- Step output path was new before the run.
- Dry-run confirmed the run used `mini_retry_corpus.json` with exactly `OR-MINI-001` through `OR-MINI-005`.
- No parallel model run was started.

Ran one approved Step-only OpenRouter live batch attempt:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --request-timeout-seconds 120 --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json --models stepfun/step-3.7-flash --output documentation\codex\openrouter-delegation\benchmark_result_step_37_flash_mini_retry_2026-06-12.json
```

The local command wrapper timed out after about 184 seconds. A Python benchmark process continued briefly, then exited without writing `documentation/codex/openrouter-delegation/benchmark_result_step_37_flash_mini_retry_2026-06-12.json`.

No Step result JSON exists, so there are no scorably complete per-fixture Step diagnostics. Step remains `HOLD` / inconclusive and does not match the completed local `5.4 mini` low baseline on available evidence. No second Step run was started because the user approved only one live retry batch.

No Qwen rerun, Ring, MiniMax, DeepSeek, Gemma, or Nemotron run was started.
No production routing was approved.
No benchmark result JSON was staged or committed.
No Git staging, commit, push, tag, merge, release, or backlog update was performed.

Previous Qwen work:

Read the bound model-routing and OpenRouter delegation artifacts:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/mini_retry_fixture_plan.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/openrouter-delegation/benchmark_corpus.json`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py`
- `documentation/codex/openrouter-delegation/schemas/delegated_task_result.schema.json`
- `documentation/codex/openrouter-delegation/schemas/benchmark_result.schema.json`

Received explicit approval phrase: `APPROVE QWEN LIVE RETRY ONLY`.

Pre-run checks:

- `OPENROUTER_API_KEY` was set.
- `/api/v1/key` check succeeded and reported `is_free_tier: False`.
- Output file path was new before the run.
- No existing OpenRouter benchmark run was found.
- The reviewed five-fixture mini retry corpus used only public/sanitized input.

Because the harness default corpus did not match the five approved mini fixtures, added a minimal `--corpus` option and created `documentation/codex/openrouter-delegation/mini_retry_corpus.json` with exactly the five reviewed mini fixtures. Offline validation passed before the live call.

Ran one OpenRouter live batch only:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --request-timeout-seconds 120 --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json --models qwen/qwen3.7-plus --output documentation\codex\openrouter-delegation\benchmark_result_qwen37_plus_mini_retry_2026-06-12.json
```

Qwen result summary:

- `OR-MINI-001`: mode correct, risk flags complete, forbidden flags absent, production safe, schema invalid, score `0`.
- `OR-MINI-002`: mode correct, risk flags complete, forbidden flags absent, production safe, schema invalid, score `0`.
- `OR-MINI-003`: mode correct, risk flags complete, forbidden flags absent, production safe, schema invalid, score `0`.
- `OR-MINI-004`: mode incorrect (`ALLOW` vs expected `ASSIST`), risk flags complete, forbidden flags absent, production safe, schema invalid, score `0`.
- `OR-MINI-005`: mode correct, risk flags complete, forbidden flags absent, production safe, schema invalid, score `0`.

Schema-invalid causes included `schema_version mismatch`, `findings must be an array`, and `summary/checks quality failed`.
No timeout or provider-level error occurred.
Final recommendation: Qwen remains `HOLD`; it did not match the completed local `5.4 mini` low baseline.
Step was not run.
No production routing was approved.
No benchmark result JSON was staged or committed.
No Git staging, commit, push, tag, merge, release, or backlog update was performed.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/openrouter-delegation/mini_retry_corpus.json`
- `documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py`
- `documentation/codex/openrouter-delegation/benchmark_result_qwen37_plus_mini_retry_2026-06-12.json` (local evidence only; do not commit unless separately reviewed)
- `documentation/codex/SKILL_USAGE_LOG.md`
- `documentation/codex/openrouter-delegation/benchmark_result_step_37_flash_mini_retry_2026-06-12.json` was requested but was not created

## Remote Sync Evidence
- Latest synchronized commit noted in prior state: `378a1c72c` (`docs(ai): reconcile openrouter run feedback sync state`) on `backup/develop`.
- Branch context: `develop` / `backup/develop` workflow.
- This CURRENT_STATE update is local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE.

## Tests / Validation
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json --models qwen/qwen3.7-plus` -> PASS
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- One approved Qwen-only OpenRouter live retry -> completed, wrote local JSON evidence.
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json` -> PASS before Step attempt
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --corpus documentation\codex\openrouter-delegation\mini_retry_corpus.json --models stepfun/step-3.7-flash` -> PASS before Step attempt
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS before Step attempt
- One approved Step-only OpenRouter live retry attempt -> local command wrapper timed out; no result JSON was written; Step remains HOLD/inconclusive.
- No Qwen rerun or other model live calls after Step approval.
- `python documentation\codex\scripts\record_skill_usage.py --skill janus-skill-router ...` -> PASS
- `python documentation\codex\scripts\record_skill_usage.py --skill janus-skill-router ... --state BLOCKED` for Step retry -> PASS

## Open Risks
- Qwen remains `HOLD` after the first mini retry because all five outputs were schema-invalid and one fixture had an incorrect mode.
- Step remains `HOLD` / inconclusive because the approved live attempt produced no result JSON and therefore no scorably complete diagnostics.
- The local evidence note is not a routing policy and should not be treated as production approval.
- Production routing remains `UNKNOWN`/disabled.
- Existing untracked benchmark JSON files remain local evidence and were not touched or committed in this pass.
- The new Qwen retry JSON is local evidence and was not staged or committed.
- The existing worktree contains many unrelated pre-existing Janus product/test/documentation changes; do not stage broadly.
- GitHub or other remotes will not see this local CURRENT_STATE until a later explicit `janus-git-governance` commit/push.

## Next Recommended Step for ChatGPT
Review the Step execution blocker and decide whether to approve a second Step retry with a longer local command timeout and/or interim per-case flushing, or patch the harness to write partial results safely during long runs.

## Next Recommended Step for Codex
If the user wants to continue, prepare a tiny harness hardening patch to flush per-case results incrementally before any second Step live retry. Do not run further OpenRouter live calls without explicit approval.

## Last Updated
2026-06-12 15:02 local time
