# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Review documentation-skill planning artifacts and prepare the gated no-live benchmark-planning step for `DOC-FIX-001` only.

## Active Phase
Documentation/design-only model-routing planning for the documentation skill. No OpenRouter live calls, benchmark execution, model execution, benchmark result JSON generation, production routing activation, backlog update, Git staging, commit, push, tag, merge, reset, or release in this pass.

## Last Decision
This remains a Codex development-environment and skill-orchestration evaluation, not a Janus application backlog item.

Local `5.4 mini` low remains the clean baseline for small sanitized documentation assist tasks. The tested cheaper same-family OpenAI candidates remain `HOLD` for routing activation:

- `openai/gpt-5.4-nano`
- `openai/gpt-5-mini`
- `openai/gpt-5.1-codex-mini`
- `openai/gpt-5-nano`

OpenRouter remains disallowed for routing decisions and production routing remains `UNKNOWN`/disabled. OpenRouter may only be considered later for public/sanitized, non-binding documentation assist fixtures after explicit approval and Codex review.

## Last Codex Work
Reviewed documentation-skill scoped planning artifacts:

- `documentation/codex/model-routing/documentation_skill_task_inventory_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_model_assignment_registry_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_or_fixture_plan_2026-06-12.md`

Confirmed:

- The three documentation-skill planning artifacts are present.
- `DOC-FIX-001` is advisory-only and `ASSIST`-only.
- `DOC-FIX-001` input is sanitized benchmark JSON.
- `DOC-FIX-001` preserves `run_status=complete`, `completed_cases=5`, `expected_cases=5`, `mode_correct=3/5`, `production_approved=false`, `known_decision=HOLD`, and Codex/User review.
- No fixture grants OpenRouter routing approval, production approval, repo writes, Git authority, release authority, final-audit authority, backlog/product-scope authority, or private local file access.

Created:

- `documentation/codex/model-routing/doc_fix_001_benchmark_plan_2026-06-12.md`

Planning result:

- `DOC-FIX-001` is valid for first benchmark planning.
- Proposed future OR candidate: `openai/gpt-5.4-nano`, for sanitized documentation assist comparison only.
- Future approval phrase for local-only baseline: `APPROVE DOC-FIX-001 LOCAL BASELINE ONLY`.
- Future approval phrase for one OR comparison: `APPROVE DOC-FIX-001 OR COMPARISON: openai/gpt-5.4-nano`.
- Future OR output path: `documentation/codex/openrouter-delegation/benchmark_result_doc_fix_001_gpt54_nano_2026-06-12.json`.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/doc_fix_001_benchmark_plan_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_task_inventory_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_model_assignment_registry_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_or_fixture_plan_2026-06-12.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- Prior documentation planning artifacts were committed and pushed to `backup/develop` at commit `245c2e861`, followed by CURRENT_STATE sync commit `a93908603`.
- The new `DOC-FIX-001` benchmark plan and this CURRENT_STATE update are local only until a later explicit `janus-git-governance` commit/push.
- No push to `origin`, tag, merge, reset, release, benchmark execution, benchmark result JSON generation, OpenRouter live call, or backlog update was performed in this pass.
- GitHub or other remote readers may not contain the latest `DOC-FIX-001` benchmark plan until a later push.

## Tests / Validation
- Planning artifact presence check -> PASS.
- `DOC-FIX-001` advisory-only / ASSIST-only review -> PASS.
- `DOC-FIX-001` sanitized input review -> PASS.
- `DOC-FIX-001` pass/fail/forbidden authority review -> PASS.
- Markdown sanity on touched documentation files -> PASS.
- `git diff --check` on touched files -> PASS.
- Confirmed no OpenRouter live calls, benchmark execution, or model execution in this documentation pass -> PASS.
- Confirmed no benchmark result JSON generated in this documentation pass -> PASS.
- Verified no staged files -> PASS.
- Skill usage recorded with `documentation/codex/scripts/record_skill_usage.py` -> PASS.

## Open Risks
- `DOC-FIX-001` benchmark plan is no-live and needs ChatGPT/User review before any baseline or OR comparison.
- No OR execution candidates are approved for documentation-skill tasks.
- Real `CURRENT_STATE`, final audit, release, backlog/product-scope, capability registry, and private repo-state contradiction tasks remain local/Codex-only or blocked for OR.
- The worktree may contain unrelated pre-existing changes; do not stage broadly.

## Next Recommended Step for ChatGPT
Review `documentation/codex/model-routing/doc_fix_001_benchmark_plan_2026-06-12.md`. Decide whether the next step should be a local baseline-only `DOC-FIX-001` check or a later gated OR comparison after local baseline evidence exists.

## Next Recommended Step for Codex
If the user approves a benchmark follow-up, require one exact phrase: `APPROVE DOC-FIX-001 LOCAL BASELINE ONLY` for local-only baseline, or `APPROVE DOC-FIX-001 OR COMPARISON: openai/gpt-5.4-nano` for one gated OR comparison after baseline evidence. Do not run OpenRouter without explicit approval.

## Last Updated
2026-06-12 21:09 local time
