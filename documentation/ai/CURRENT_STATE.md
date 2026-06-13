# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Prepare DOC-SKILL-010 fixture checkpoint and sync the task-level status, queue state, and usage log.

## Active Phase
Documentation-skill DOC-SKILL-010 fixture-preparation checkpoint. DOC-SKILL-001, DOC-SKILL-002, DOC-SKILL-003, DOC-SKILL-006, DOC-SKILL-008, and DOC-SKILL-009 remain `TASK_DECISION_RECORDED`; DOC-SKILL-010 is prepared and remains `NOT RUN`. No production routing, no canonical routing-table update, no DOC-SKILL-011 start, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

DOC-SKILL-001 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-002 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-003 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-006 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-010 is prepared as the next task-level documentation-skill evaluation and remains `NOT RUN`. It uses the established reduced candidate strategy:

- default external candidate: `openai/gpt-oss-20b`
- backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

This is fixture preparation only. No OpenRouter calls were run, no production routing decision was made, no model was marked production-approved, no canonical routing-table update was made, and no DOC-SKILL-011 or later task was started.

## Last Codex Work
Prepared the DOC-SKILL-010 fixture package and recorded the queue state for the next task-level evaluation.

Saved evidence under:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/request_payloads/manifest.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/request_payloads/*.json`

The DOC-SKILL-010 gate includes scorer calibration from the DOC-SKILL-006 run: do not over-require the exact phrase `non-binding` when governance boundaries are clearly preserved.

Updated the GPT-5.4 mini evaluation queue with DOC-SKILL-010 as `NOT RUN` and DOC-SKILL-011+ still `NOT RUN`.

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/request_payloads/manifest.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/request_payloads/*.json`
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): sync doc skill 010 fixture state` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, routing-table update, DOC-SKILL-011 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user previously deferred it for later.
- Bound artifact reread for DOC-SKILL-009 live-evaluation closeout: PASS.
- DOC-SKILL-001 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-002 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-003 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-006 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-008 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-009 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-010 remains `NOT RUN`: PASS.
- DOC-SKILL-011+ remain `NOT RUN`: PASS.
- No routing table update: PASS.
- No production routing activation: PASS.
- `git diff --check` on touched files: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The DOC-SKILL-010 fixture is not approval to update production routing, update the canonical routing table, mark any model production-approved, or continue to DOC-SKILL-011.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-010 fixture and decide whether a separate explicit approval should run the reduced-candidate live evaluation.

## Next Recommended Step for Codex
Commit the DOC-SKILL-010 fixture-state sync checkpoint, push `backup/develop` only, and stop before DOC-SKILL-011.

## Last Updated
2026-06-13 16:05 local time
