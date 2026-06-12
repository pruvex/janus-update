# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review the first Janus Codex task-to-model matrix and minimal mini-task benchmark plan before any further model comparisons.

## Active Phase
Dev-environment Codex model-routing and OpenRouter delegation governance. No production routing.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive public or sanitized benchmark prompts from a curated corpus or reviewed mini-task fixture.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, runtime state, dirty worktree content, or unredacted Janus project history.
- OpenRouter must not write repo files, patch code, run commands, approve Git actions, approve final audits, make release-readiness or publish decisions, or decide Janus product scope/backlog priority/user-facing behavior.
- Production routing remains `UNKNOWN`/disabled until local Codex mini baselines exist, OpenRouter prompt/schema fixes are reviewed, benchmark evidence is reviewed, and the user explicitly approves activation.

## Last Codex Work
Confirmed no healthcheck reminder was due.
Routed the request through `janus-skill-router` and accepted the user-provided `GPT-5.5 / medium` setup for a bounded documentation and benchmark-design block.
Read the primary sync and governance artifacts:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/openrouter-delegation/benchmark_corpus.json`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- `documentation/codex/SKILL_USAGE_LOG.md`
- `AGENTS.md`
- `documentation/codex/CODEX_PROJECT_PROFILE.md`
- `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
- `documentation/pipeline/PIPELINE_CONTRACT.md`
- Installed `janus-*` skill task/gate definitions

Created `documentation/codex/model-routing/task_model_matrix.md` as a proposed review artifact.
The matrix inventories recurring Janus Codex tasks, separates `MINI_CANDIDATE` from `GPT_5_4_CANDIDATE`, `HIGH_LOCAL_ONLY`, and `HUMAN_ONLY`, and hard-denies OpenRouter for Git, final audit, release, repo writes, command execution, private files/logs/local DBs/secrets, broad source inspection, and product/backlog/release/user-facing decisions.
The first mini-candidate set is intentionally limited to five classes:

- sanitized skill/governance excerpt classification
- public/sanitized schema-bound extraction
- non-binding benchmark result interpretation
- non-binding model cost/latency comparison
- documentation wording suggestion

Defined one minimal deterministic test case per mini-candidate and a local Codex baseline sequence:
`5.4 mini` low -> medium -> high, escalating to `5.4` only if mini cannot solve the task cleanly.
Defined an OpenRouter comparison plan but did not run live calls.
Recorded current local OpenRouter evidence in the matrix as local-only evidence:

- `inclusionai/ring-2.6-1t`: promising but HOLD; missed risk flags, one timeout, and misclassified an `ASSIST` case as `ALLOW`.
- `stepfun/step-3.7-flash`: best schema-valid candidate so far but HOLD; correct `DENY`/`ASSIST`, one `ALLOW` schema-extraction case as `UNKNOWN`, risk flags often missing.
- `minimax/minimax-m3`: schema/provider incompatible with HTTP 200 top-level invalid-params error payloads.
- `qwen/qwen3.7-plus`: strongest mode classifier so far but schema fail due missing required fields.
- Free Gemma 26B: rate-limited/inconclusive.
- Free Gemma 31B: unreliable/HOLD.
- Nemotron Nano free: excluded/incompatible.

No OpenRouter live calls were run.
No broad Codex benchmark sweep was run.
No production routing was approved.
No Git staging, commit, push, tag, merge, release, or backlog update was performed.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/codex/model-routing/task_model_matrix.md

## Remote Sync Evidence
- Latest synchronized commit noted in prior state: `378a1c72c` (`docs(ai): reconcile openrouter run feedback sync state`) on `backup/develop`.
- Branch context: `develop` / `backup/develop` workflow.
- Generated benchmark JSON files remain untracked local evidence and were not staged or pushed.
- This matrix and CURRENT_STATE update are local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE.

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- Focused source reads of required OpenRouter, Codex workflow, pipeline, and installed Janus skill definitions -> PASS
- `git diff --check -- documentation/codex/model-routing/task_model_matrix.md` -> PASS
- Full changed-doc diff check pending after CURRENT_STATE and usage-log update.

## Open Risks
- The matrix is proposed, not approved routing policy.
- Local post-patch benchmark JSON evidence was reviewed by ChatGPT/user context but remains uncommitted local evidence; do not treat it as remote truth.
- OpenRouter candidates are all HOLD/UNKNOWN/EXCLUDED until schema/risk-flag prompt improvements and local Codex mini baselines exist.
- Mini-task definitions may need user/ChatGPT review before any baseline runs.
- The existing worktree contains many unrelated pre-existing Janus product/test/documentation changes; do not stage broadly.
- GitHub or other remotes will not see this local CURRENT_STATE until a later explicit `janus-git-governance` commit/push.

## Next Recommended Step for ChatGPT
Review `documentation/codex/model-routing/task_model_matrix.md`, especially whether the five mini-candidate task classes are small enough and whether `documentation wording suggestion` should remain `ASSIST_ONLY`.

## Next Recommended Step for Codex
After review, select exactly one mini-candidate task and prepare the smallest local Codex baseline case across `5.4 mini` low, medium, and high reasoning. Do not run OpenRouter live calls until the baseline exists and the harness prompt/schema/risk-flag fixes are planned.

## Last Updated
2026-06-12 01:58 local time
