# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the dry-run validation results for the tightened `janus-documentation-update` model-switch gate.

## Active Phase
Documentation-skill governance update. No OpenRouter activation, no OpenRouter live calls, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table v1 remains the canonical reference for documentation-skill work:

- `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`

`janus-documentation-update` must treat the active model and reasoning level as user-declared, not self-detected. If `DECLARED CODEX MODEL` is missing, Codex must stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

The gate output uses `Declared model/reasoning` instead of `Current model/reasoning`. The gate does not switch models automatically, does not activate OpenRouter, and does not enable production routing.

## Last Codex Work
Recorded the dry-run validation outcomes for the documentation-skill model-switch gate after the tightening pass.

Dry-run results:

- sufficient declared setup: PASS
- insufficient declared setup: PASS
- user confirmation after model switch: PASS
- missing `DECLARED CODEX MODEL`: PASS
- blocked_scope routing: PASS

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): record documentation skill gate dry runs` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter comparison, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: CLEAR.
- Bound artifact reread for dry-run evidence: PASS.
- Dry-run gate scenarios reviewed against `janus-documentation-update`: PASS.
- Markdown sanity on touched documentation files: PASS.
- `git diff --check` on touched tracked files: PASS.
- OpenRouter live calls: NOT RUN / forbidden by scope.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The dry-run evidence is conversational validation, not an automated test harness.
- Git pre-commit governance may require splitting `CURRENT_STATE.md` and `SKILL_USAGE_LOG.md` if the hook rejects a mixed manual-review and codex-governance checkpoint.

## Next Recommended Step for ChatGPT
Review whether the five recorded dry-run cases are enough or whether an explicit upstream-skill-path example should be added later.

## Next Recommended Step for Codex
Run final validation, record the dry-run evidence checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-12 23:34 local time
