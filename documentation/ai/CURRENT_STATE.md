# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Prepare a skill-scoped task inventory and model-assignment plan for the Janus documentation skill, focused on local `5.4 mini` documentation-task baselines and safe OpenRouter assist-only fixture candidates.

## Active Phase
Documentation/design-only model-routing planning for the documentation skill. No OpenRouter live calls, benchmark reruns, model execution, production routing activation, backlog update, Git staging, commit, push, tag, merge, reset, or release in this pass.

## Last Decision
This remains a Codex development-environment and skill-orchestration evaluation, not a Janus application backlog item.

Local `5.4 mini` low remains the clean baseline for small sanitized documentation assist tasks. The tested cheaper same-family OpenAI candidates remain `HOLD` for routing activation:

- `openai/gpt-5.4-nano`
- `openai/gpt-5-mini`
- `openai/gpt-5.1-codex-mini`
- `openai/gpt-5-nano`

OpenRouter remains disallowed for routing decisions and production routing remains `UNKNOWN`/disabled. OpenRouter may only be considered later for public/sanitized, non-binding documentation assist fixtures after explicit approval and Codex review.

## Last Codex Work
Created documentation-skill scoped planning artifacts:

- `documentation/codex/model-routing/documentation_skill_task_inventory_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_model_assignment_registry_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_or_fixture_plan_2026-06-12.md`

Inventory result:

- 18 documentation-skill tasks inventoried.
- 6 tasks marked `CODEX_ONLY`.
- 6 tasks marked `OR_ASSIST_CANDIDATE`.
- 0 tasks marked `OR_EXECUTION_CANDIDATE`.
- 2 tasks marked `SCRIPT_ONLY`.
- 3 tasks marked `BLOCKED_FOR_OR`.
- 1 task marked `LOCAL_BASELINE_ONLY`.

Safe first OR-assist fixture candidates prepared as no-live plans only:

1. Benchmark JSON summary fixture.
2. Model scoring report summary fixture.
3. Non-binding handoff draft fixture.
4. Markdown cleanup fixture.
5. Changelog summary fixture.

Recommended first fixture to benchmark after review: `DOC-FIX-001` benchmark JSON summary, because it is the most mechanical safe documentation assist task and can be scored on exact field preservation, `HOLD`/no-production wording, and absence of authority expansion.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/documentation_skill_task_inventory_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_model_assignment_registry_2026-06-12.md`
- `documentation/codex/model-routing/documentation_skill_or_fixture_plan_2026-06-12.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- No Git staging, commit, push, tag, merge, reset, release, or backlog update was performed.
- These documentation planning artifacts and this CURRENT_STATE update are local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE or documentation-skill model-assignment artifacts.

## Tests / Validation
- Markdown sanity on touched documentation files -> PASS.
- `git diff --check` on touched files -> PASS.
- Confirmed no OpenRouter live calls, benchmark reruns, or model execution in this documentation pass -> PASS.
- Confirmed no benchmark JSON generated in this documentation pass -> PASS.
- Verified no staged files -> PASS.
- Skill usage recorded with `documentation/codex/scripts/record_skill_usage.py` -> PASS.

## Open Risks
- Assignment registry is policy/design only and needs user/Codex review before any fixture benchmark.
- No OR execution candidates are approved for documentation-skill tasks.
- Real `CURRENT_STATE`, final audit, release, backlog/product-scope, capability registry, and private repo-state contradiction tasks remain local/Codex-only or blocked for OR.
- `DOC-SKILL-009` real `SKILL_USAGE_LOG` append remains script/Codex-owned; only synthetic or sanitized summary could be an OR assist fixture later.
- The worktree may contain unrelated pre-existing changes; do not stage broadly.

## Next Recommended Step for ChatGPT
Review the documentation-skill task inventory and model-assignment registry. Confirm whether the first safe OR-assist benchmark should be `DOC-FIX-001` benchmark JSON summary.

## Next Recommended Step for Codex
If the user approves a benchmark follow-up, prepare a gated no-live-to-live handoff for exactly one fixture: local `5.4 mini` low baseline versus one explicitly named OpenRouter candidate on `DOC-FIX-001`. Do not run OpenRouter without explicit approval.

## Last Updated
2026-06-12 20:58 local time
