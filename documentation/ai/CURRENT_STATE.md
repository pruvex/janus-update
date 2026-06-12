# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Create the per-task live-evaluation preparation queue for documentation-skill tasks currently allowed for GPT-5.4 mini.

## Active Phase
Documentation-skill live-evaluation planning checkpoint. No OpenRouter inference/model tests, no production routing, no benchmark execution, no benchmark JSON generation, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

Rows currently allowed for GPT-5.4 mini were identified from `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md` and prepared as a per-task evaluation queue. The eligible rows are DOC-SKILL-001, DOC-SKILL-002, DOC-SKILL-003, DOC-SKILL-006, DOC-SKILL-008, DOC-SKILL-009, and DOC-SKILL-010.

Each task remains `NOT RUN` and must be evaluated separately before moving to the next task. The queue is planning only and does not approve OpenRouter calls, external model use, production routing, or repo-write authority.

## Last Codex Work
Created:

- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`

Queue contents:

- eligible task count: 7
- one `NOT RUN` section per eligible DOC-SKILL row
- task id and routing-table summary
- required model/reasoning
- proposed single-task fixture name
- pass/fail rubric reference
- A1 candidate set reference
- per-task note that evaluation must be separate before moving to the next task

## Changed Files
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): prepare gpt54 mini doc skill eval queue` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter inference/model test, benchmark result JSON generation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user deferred it for later.
- Bound artifact reread for queue checkpoint: PASS.
- Routing table reread: PASS.
- A1 shortlist CSV readable: PASS, 12 candidates.
- Markdown sanity on touched documentation files: PASS.
- `git diff --check` on touched tracked files: PASS.
- OpenRouter inference/model tests: NOT RUN / forbidden by scope.
- Benchmark JSON generation: NOT RUN / forbidden by scope.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The A1 candidate list is time-sensitive metadata; current OpenRouter pricing must be rechecked before any future execution.
- The queue is not approval to run OpenRouter calls, offer a model externally, batch multiple tasks, or activate production routing.

## Next Recommended Step for ChatGPT
Review whether the seven-task GPT-5.4 mini queue is the right first live-evaluation order before any explicit live-run approval.

## Next Recommended Step for Codex
Run final validation, commit the queue checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-13 00:20 local time
