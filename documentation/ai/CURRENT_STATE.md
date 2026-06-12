# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Adopt the documentation-skill routing table v1 as the canonical model-routing reference for `janus-documentation-update`.

## Active Phase
Documentation-skill governance update. No OpenRouter activation, no OpenRouter live calls, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table v1 is now the canonical reference for documentation-skill work:

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`

`janus-documentation-update` must classify documentation work against the table's `DOC-SKILL-*` rows before acting. If the current model or reasoning level is insufficient for the matching row, Codex must stop, tell the user exactly which model and reasoning to select, and continue only after user confirmation or an explicit instruction to stay in the current setup.

The gate does not switch models automatically. It does not activate OpenRouter. It does not enable production routing. Blocked or upstream-owned documentation scopes must route through the required upstream Janus skill path before returning to `janus-documentation-update`.

## Last Codex Work
Added a new `## Documentation Skill Model-Switch Gate` section to the active installed `janus-documentation-update` skill and the tracked repo skill source.

The section:

- names `documentation_skill_routing_table_v1_2026-06-12.md` as the canonical documentation-skill routing reference
- requires classification against the routing table before documentation-skill work
- requires a stop-and-tell-user gate when the current model or reasoning is insufficient
- preserves explicit user confirmation before continuing
- keeps automatic model switching, OpenRouter activation, and production routing forbidden
- routes blocked or upstream-owned scopes back to the required upstream Janus skill path

## Changed Files
- `C:\Users\pruve\.codex\skills\janus-documentation-update\SKILL.md`
- `documentation/codex/skills/janus-documentation-update/SKILL.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): add documentation skill model switch gate` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter comparison, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: CLEAR.
- Routing table v1 read and used as canonical reference: PASS.
- Active `janus-documentation-update` skill read before editing: PASS.
- Markdown sanity on routing table and both skill copies: PASS.
- `git diff --check` on tracked skill change: PASS.
- Fresh benchmark JSON scan after skill edit: PASS, none generated.
- OpenRouter live calls: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The installed active skill copy is outside the repo and cannot itself be represented as a Git-tracked file; the repo skill source carries the committed counterpart.
- Future documentation-skill users must still select the correct row from the routing table instead of treating the gate as blanket permission.

## Next Recommended Step for ChatGPT
Review the committed gate language and confirm that the routing table v1 is now acceptable as the canonical documentation-skill routing reference.

## Next Recommended Step for Codex
Use `janus-git-governance` for the requested checkpoint commit and push to `backup/develop` only, staging only the tracked files from this task.

## Last Updated
2026-06-12 23:06 local time
