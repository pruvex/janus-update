# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the completed DOC-SKILL-009 reduced live evaluation and sync the task-level decision, queue status, and usage log.

## Active Phase
Documentation-skill DOC-SKILL-009 live-evaluation closeout. DOC-SKILL-001, DOC-SKILL-002, DOC-SKILL-003, DOC-SKILL-006, and DOC-SKILL-008 remain `TASK_DECISION_RECORDED`; DOC-SKILL-009 is now `TASK_DECISION_RECORDED` after the reduced live evaluation. No production routing, no canonical routing-table update, no DOC-SKILL-010 start, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

DOC-SKILL-001 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-002 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-003 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-006 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-009 completed the reduced live evaluation and is `TASK_DECISION_RECORDED`. It used the established reduced candidate strategy:

- default external candidate: `openai/gpt-oss-20b`
- backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

The live run attempted `openai/gpt-oss-20b`, `openai/gpt-oss-120b`, and `qwen/qwen3.5-flash-02-23`; `qwen/qwen3.5-flash-02-23` was PASS and `deepseek/deepseek-v4-flash` was not needed. No production routing decision was made, no model was marked production-approved, no canonical routing-table update was made, and no DOC-SKILL-010 or later task was started.

## Last Codex Work
Ran the reduced DOC-SKILL-009 live evaluation and recorded the task-level decision.

Saved evidence under:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/raw/*.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/normalized/*.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`

The DOC-SKILL-009 gate includes scorer calibration from the DOC-SKILL-006 run: do not over-require the exact phrase `non-binding` when governance boundaries are clearly preserved.

Updated the GPT-5.4 mini evaluation queue with DOC-SKILL-009 as `TASK_DECISION_RECORDED` and DOC-SKILL-010+ still `NOT RUN`.

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/raw/*.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/normalized/*.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): run doc skill 009 reduced evaluation` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, routing-table update, DOC-SKILL-010 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user previously deferred it for later.
- Bound artifact reread for DOC-SKILL-009 live-evaluation closeout: PASS.
- DOC-SKILL-001 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-002 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-003 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-006 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-008 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-009 becomes `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-010+ remain `NOT RUN`: PASS.
- No routing table update: PASS.
- No production routing activation: PASS.
- `git diff --check` on touched files: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The DOC-SKILL-009 live evaluation is evidence only; it is not approval to update production routing, update the canonical routing table, mark any model production-approved, or continue to DOC-SKILL-010.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-009 task-level decision if a canonical routing update is ever requested, but keep production routing separate.

## Next Recommended Step for Codex
Commit the DOC-SKILL-009 live-evaluation checkpoint, push `backup/develop` only, and stop before DOC-SKILL-010.

## Last Updated
2026-06-13 15:50 local time
