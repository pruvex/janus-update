# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the completed reduced DOC-SKILL-002 live evaluation and task-level model decision.

## Active Phase
Documentation-skill DOC-SKILL-002 task-level evaluation checkpoint. DOC-SKILL-002 is evaluated and has `TASK_DECISION_RECORDED`. No production routing, no canonical routing-table update, no DOC-SKILL-003 start, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

DOC-SKILL-001 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-002 is now `TASK_DECISION_RECORDED`. The task-level internal default remains GPT-5.4 mini low. The selected external OpenRouter candidate for this task-level documentation-skill evidence is `openai/gpt-oss-20b`.

This is evidence only. No production routing decision was made, no model was marked production-approved, no canonical routing-table update was made, and no DOC-SKILL-003 or later task was started.

## Last Codex Work
Ran the approved reduced DOC-SKILL-002 live evaluation for `DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001`.

Attempted models:

- `openai/gpt-oss-20b`: PASS, selected external candidate after calibrated evidence review
- `openai/gpt-oss-120b`: PASS, retained as backup evidence but not selected
- `qwen/qwen3.5-flash-02-23`: NOT RUN / not needed
- `deepseek/deepseek-v4-flash`: NOT RUN / not needed

Calibration note: the initial automated scorer over-flagged the default candidate's `Disabled: Yes` / `not scored as PASS` wording. Calibrated evidence review treats that wording as disabled-state preservation and records the default candidate as PASS. The already-attempted backup_1 call is retained as extra evidence.

Created DOC-SKILL-002 evidence under:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/raw/`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/normalized/`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`

Updated the DOC-SKILL-002 README and GPT-5.4 mini evaluation queue to record `TASK_DECISION_RECORDED` while leaving DOC-SKILL-003+ at `NOT RUN`.

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/evaluation_results.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/evaluation_summary.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/task_model_decision.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/raw/*.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/results/normalized/*.md`
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): run doc skill 002 reduced evaluation` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, routing-table update, DOC-SKILL-003 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user deferred it for later.
- Bound artifact reread for DOC-SKILL-002 reduced live evaluation: PASS.
- OpenRouter inference/model calls: 2 attempted for DOC-SKILL-002 only.
- Raw responses saved for attempted models: PASS, 2.
- Normalized responses saved for attempted models: PASS, 2.
- `evaluation_results.json` parses: PASS.
- `evaluation_summary.md` exists: PASS.
- `task_model_decision.md` exists: PASS.
- Selected external candidate `openai/gpt-oss-20b` is present and PASS: PASS.
- DOC-SKILL-001 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-002 queue status updated to `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-003+ remain `NOT RUN`: PASS.
- No routing table update: PASS.
- No production routing activation: PASS.
- `git diff --check` on touched files: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- DOC-SKILL-002 evidence includes one extra backup call because the initial scorer over-flagged the default candidate before calibrated review.
- The DOC-SKILL-002 task-level decision is not approval to run DOC-SKILL-003, update production routing, update the canonical routing table, or mark any model production-approved.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-002 task-level decision evidence and decide whether DOC-SKILL-003 should be prepared in a separate, explicit task.

## Next Recommended Step for Codex
Run final validation, commit the DOC-SKILL-002 reduced evaluation checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-13 13:10 local time
