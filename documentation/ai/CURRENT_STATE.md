# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Save the validated documentation-skill model-switch gate as a reusable template for future Janus skills.

## Active Phase
Documentation-skill governance update. No OpenRouter activation, no OpenRouter live calls, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table v1 remains the canonical reference for documentation-skill work:

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`

`janus-documentation-update` must treat the active model and reasoning level as user-declared, not self-detected. If `DECLARED CODEX MODEL` is missing, Codex must stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

The gate output uses `Declared model/reasoning` instead of `Current model/reasoning`. The gate does not switch models automatically, does not activate OpenRouter, and does not enable production routing.

## Last Codex Work
Created a reusable model-switch gate template from the validated `janus-documentation-update` gate and dry-run cases.

Template saved at:

- `documentation/codex/model-routing/skill_model_switch_gate_template_v1_2026-06-12.md`

The template includes:

- purpose
- required `DECLARED CODEX MODEL`
- stop-before-sufficiency rule
- user-confirmation rule
- blocked-scope upstream rule
- no auto-switch / no OR / no production routing
- five required dry-run cases for future skills

## Changed Files
- `documentation/codex/model-routing/skill_model_switch_gate_template_v1_2026-06-12.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): add reusable model switch gate template` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter comparison, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: CLEAR.
- Bound artifact reread for template extraction: PASS.
- Reusable template created from validated dry-run gate: PASS.
- Markdown sanity on touched documentation files: PASS.
- `git diff --check` on touched tracked files: PASS.
- OpenRouter live calls: NOT RUN / forbidden by scope.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The template is intentionally generic and must be bound to each future skill's own routing table or model requirements before use.
- The dry-run evidence remains conversational validation, not an automated test harness.

## Next Recommended Step for ChatGPT
Review the template wording before reusing it in another Janus skill.

## Next Recommended Step for Codex
Run final validation, commit the template checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-12 23:46 local time
