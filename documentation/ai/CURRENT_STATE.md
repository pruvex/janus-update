# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the final task-level model decision for DOC-SKILL-001 from completed live-evaluation evidence.

## Active Phase
Documentation-skill task-level decision checkpoint. No new OpenRouter calls, no production routing, no canonical routing-table update, no DOC-SKILL-002 start, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

The final DOC-SKILL-001 task-level model decision is recorded from completed live-evaluation evidence.

DOC-SKILL-001 is now `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue. The internal default remains GPT-5.4 mini low. The selected external OpenRouter candidate for this task is `openai/gpt-oss-20b`, with backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, and `deepseek/deepseek-v4-flash`.

This is a task-level documentation-skill decision only. No production routing decision was made, no model was marked production-approved, no canonical routing-table update was made, and no DOC-SKILL-002 or later task was started.

## Last Codex Work
Created:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`

Decision basis:

- completed DOC-SKILL-001 live evaluation
- 9 PASS / 3 HOLD / 0 FAIL
- selected model `openai/gpt-oss-20b` is present and PASS
- HOLD models remain HOLD:
  - `openai/gpt-5-nano`
  - `qwen/qwen3-235b-a22b-thinking-2507`
  - `stepfun/step-3.7-flash`

Updated the GPT-5.4 mini evaluation queue so only DOC-SKILL-001 is marked `TASK_DECISION_RECORDED`; DOC-SKILL-002 and later entries remain `NOT RUN`.

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): record doc skill 001 model decision` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter call, routing-table update, DOC-SKILL-002 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user deferred it for later.
- Bound artifact reread for DOC-SKILL-001 task-level decision: PASS.
- `evaluation_results.json` parses: PASS.
- Selected model `openai/gpt-oss-20b` is present and PASS: PASS.
- `task_model_decision.md` exists: PASS.
- DOC-SKILL-001 queue status updated to `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-002+ remain `NOT RUN`: PASS.
- HOLD models remain HOLD: PASS.
- No OpenRouter calls: NOT RUN / forbidden by scope.
- No routing table update: PASS.
- No production routing activation: PASS.
- `git diff --check` on touched files: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The A1 candidate list is time-sensitive metadata; current OpenRouter pricing must be rechecked before any future execution.
- The DOC-SKILL-001 task-level decision is not production approval, not a canonical routing-table update, and not permission to continue to DOC-SKILL-002.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-001 task-level decision and decide whether a separate explicit approval should update any broader model-routing policy later.

## Next Recommended Step for Codex
Run final validation, commit the DOC-SKILL-001 task-level decision checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-13 01:36 local time
