# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Tighten the `janus-documentation-update` model-switch gate so documentation-skill sufficiency is based on the user-declared Codex model and reasoning level.

## Active Phase
Documentation-skill governance update. No OpenRouter activation, no OpenRouter live calls, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table v1 remains the canonical reference for documentation-skill work:

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`

`janus-documentation-update` must treat the active model and reasoning level as user-declared, not self-detected. If `DECLARED CODEX MODEL` is missing, Codex must stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

The gate output now uses `Declared model/reasoning` instead of `Current model/reasoning`. The gate still does not switch models automatically, does not activate OpenRouter, and does not enable production routing.

## Last Codex Work
Updated the `## Documentation Skill Model-Switch Gate` section in both the active installed skill copy and the tracked repo skill source.

Added behavior:

- current model/reasoning is treated as user-declared, not self-detected
- missing `DECLARED CODEX MODEL` blocks sufficiency decisions until the user provides or confirms model/reasoning
- gate output includes `Declared model/reasoning`
- insufficient declared model/reasoning still stops before edits or validation

## Changed Files
- `C:\Users\pruve\.codex\skills\janus-documentation-update\SKILL.md`
- `documentation/codex/skills/janus-documentation-update/SKILL.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): require declared model for documentation skill gate` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter comparison, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: CLEAR.
- Requested files read before editing: PASS.
- Active and tracked `janus-documentation-update` skill gate updated: PASS.
- Markdown sanity on touched documentation and skill files: PASS.
- `git diff --check` on touched tracked files: PASS.
- OpenRouter live calls: NOT RUN / forbidden by scope.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The installed active skill copy is outside the repo and cannot itself be represented as a Git-tracked file; the repo skill source carries the committed counterpart.
- Git pre-commit governance may require splitting `CURRENT_STATE.md` and `SKILL_USAGE_LOG.md` into follow-up commits if it rejects a mixed skill-rule/governance commit.

## Next Recommended Step for ChatGPT
Review the declared-model gate wording and confirm it matches the intended dry-run behavior.

## Next Recommended Step for Codex
Run validation, record skill usage, then use `janus-git-governance` for the requested backup-only checkpoint.

## Last Updated
2026-06-12 23:20 local time
