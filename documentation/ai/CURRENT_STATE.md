# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Create a no-live planning artifact for future OpenRouter candidate evaluation of documentation-skill tasks.

## Active Phase
Documentation-skill governance update. No OpenRouter activation, no OpenRouter live calls, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table v1 remains the canonical reference for documentation-skill work:

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`

`janus-documentation-update` must treat the active model and reasoning level as user-declared, not self-detected. If `DECLARED CODEX MODEL` is missing, Codex must stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

The gate output uses `Declared model/reasoning` instead of `Current model/reasoning`. The gate does not switch models automatically, does not activate OpenRouter, and does not enable production routing.

## Last Codex Work
Created a no-live planning artifact for a future OpenRouter candidate evaluation of documentation-skill tasks.

Planning artifact saved at:

- `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md`

The plan includes:

- purpose
- hard constraint: no OpenRouter live calls in this planning step
- all 18 `DOC-SKILL-*` rows from routing table v1
- current `5.4 mini` low/medium allowances
- per-task fixture structure
- candidate filtering based on execution-time pricing cheaper than GPT-5.4 mini
- pass/fail rubric
- future terminal-driven workflow
- external-option decision rule
- final-authority boundary with Janus/Codex governance

## Changed Files
- `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): plan documentation skill or candidate evaluation` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter comparison, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: CLEAR.
- Bound artifact reread for no-live OR evaluation planning: PASS.
- Future OR candidate evaluation plan created without live calls: PASS.
- Markdown sanity on touched documentation files: PASS.
- `git diff --check` on touched tracked files: PASS.
- OpenRouter live calls: NOT RUN / forbidden by scope.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The plan depends on current OpenRouter pricing at future execution time; pricing was not fetched in this planning step.
- The plan is not approval to run OpenRouter calls, generate result JSON, offer a model externally, or activate production routing.

## Next Recommended Step for ChatGPT
Review the no-live evaluation plan and decide whether a future approved live-run gate is warranted.

## Next Recommended Step for Codex
Run final validation, commit the planning artifact checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-12 23:53 local time
