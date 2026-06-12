# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Summarize the completed first local mini-baseline batch and prepare a focused OpenRouter harness-fix plan before any external comparison.

## Active Phase
Dev-environment Codex model-routing and OpenRouter harness preparation. No production routing.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive public or sanitized benchmark prompts from a curated corpus or reviewed mini-task fixture.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, runtime state, dirty worktree content, or unredacted Janus project history.
- OpenRouter must not write repo files, patch code, run commands, approve Git actions, approve final audits, make release-readiness or publish decisions, or decide Janus product scope/backlog priority/user-facing behavior.
- Production routing remains `UNKNOWN`/disabled until local Codex mini baselines exist, OpenRouter prompt/schema fixes are reviewed, benchmark evidence is reviewed, and the user explicitly approves activation.

## Last Codex Work
Read the bound model-routing and OpenRouter delegation artifacts:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/task_model_matrix.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/openrouter-delegation/benchmark_corpus.json`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py`

Added a compact first-batch summary to `documentation/codex/model-routing/local_mini_baseline_results.md`.
The summary records that `TMR-001` through `TMR-005` all passed with `5.4 mini` low, no escalation was required, this is the local baseline to beat, OpenRouter candidates must match or beat `5.4 mini` low, and the evidence is not production routing approval.

Added a focused harness-fix plan to `documentation/codex/openrouter-delegation/model_scoring_report.md`.
The plan separates follow-up work into prompt repair, risk-flag taxonomy, scoring split, schema projection, and OpenRouter retry tasks.
It keeps the current Qwen, Step, Ring, and MiniMax findings visible and preserves production routing as `UNKNOWN`/disabled.

No Python harness code was changed.
No OpenRouter live calls were run.
No broad benchmark sweep was run.
No Git staging, commit, push, tag, merge, release, or backlog update was performed.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Latest synchronized commit noted in prior state: `378a1c72c` (`docs(ai): reconcile openrouter run feedback sync state`) on `backup/develop`.
- Branch context: `develop` / `backup/develop` workflow.
- This CURRENT_STATE update is local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE.

## Tests / Validation
- Focused source reads of required routing and OpenRouter harness artifacts -> PASS
- Markdown sanity for touched docs -> PASS
- `git diff --check` on touched docs -> PASS
- No Python harness validation, because no code was touched.
- Skill usage recorded with `documentation/codex/scripts/record_skill_usage.py` -> PASS
- `documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py` was already dirty in the broader worktree; it was read only and not edited in this pass.
- No OpenRouter live calls.

## Open Risks
- The first local mini-baseline batch is complete, but only for `TMR-001` through `TMR-005`; higher-level tasks remain untested.
- The local evidence note is not a routing policy and should not be treated as production approval.
- The harness-fix plan is not implemented yet.
- The existing worktree contains many unrelated pre-existing Janus product/test/documentation changes; do not stage broadly.
- GitHub or other remotes will not see this local CURRENT_STATE until a later explicit `janus-git-governance` commit/push.

## Next Recommended Step for ChatGPT
Review the first-batch summary and focused harness-fix plan. Choose whether to implement prompt/schema/scoring harness fixes or prepare OpenRouter retry fixtures after those fixes.

## Next Recommended Step for Codex
If the user wants to continue, route a separate implementation task for the prompt/schema/scoring harness fixes. Do not run OpenRouter live calls until the fixes are reviewed.

## Last Updated
2026-06-12 02:35 local time
