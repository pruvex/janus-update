# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Prepare DOC-SKILL-002 as the next task-level documentation-skill evaluation using the DOC-SKILL-001 winner as the default external candidate.

## Active Phase
Documentation-skill DOC-SKILL-002 fixture preparation checkpoint. No OpenRouter calls, no production routing, no canonical routing-table update, no DOC-SKILL-003 start, no release action, and no product-code change.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

DOC-SKILL-001 remains `TASK_DECISION_RECORDED` in the GPT-5.4 mini evaluation queue.

DOC-SKILL-002 is prepared as the next task-level documentation-skill evaluation and remains `NOT RUN`. It uses the DOC-SKILL-001 selected external candidate as its default external candidate, with the DOC-SKILL-001 backups retained as backups only if needed.

This is fixture preparation only. No OpenRouter calls were run, no production routing decision was made, no model was marked production-approved, no canonical routing-table update was made, and no DOC-SKILL-003 or later task was started.

## Last Codex Work
Created:

- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/request_payloads/manifest.md`
- four request payload JSON files under `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/request_payloads/`

Candidate strategy:

- default external candidate: `openai/gpt-oss-20b`
- backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

Updated the GPT-5.4 mini evaluation queue with the DOC-SKILL-002 fixture path and candidate strategy while keeping DOC-SKILL-002 and DOC-SKILL-003+ at `NOT RUN`.

## Changed Files
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/README.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/request_payloads/manifest.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/request_payloads/*.json`
- `documentation/codex/model-routing/documentation_skill_gpt54_mini_task_eval_queue_v1_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): prepare doc skill 002 fixture` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, OpenRouter call, routing-table update, DOC-SKILL-003 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user deferred it for later.
- Bound artifact reread for DOC-SKILL-002 fixture preparation: PASS.
- DOC-SKILL-002 fixture files exist: PASS.
- `input.sanitized.json` parses: PASS.
- request payload JSON parses: PASS, 4.
- manifest exists: PASS.
- DOC-SKILL-001 remains `TASK_DECISION_RECORDED`: PASS.
- DOC-SKILL-002 remains `NOT RUN`: PASS.
- DOC-SKILL-003+ remain `NOT RUN`: PASS.
- No OpenRouter calls: NOT RUN / forbidden by scope.
- No routing table update: PASS.
- No production routing activation: PASS.
- `git diff --check` on touched files: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The A1 candidate list is time-sensitive metadata; current OpenRouter pricing must be rechecked before any future execution.
- The DOC-SKILL-002 fixture is not approval to run OpenRouter calls, update production routing, update the canonical routing table, or continue to DOC-SKILL-003.

## Next Recommended Step for ChatGPT
Review the DOC-SKILL-002 fixture and decide whether a separate explicit approval should run the reduced-candidate live evaluation.

## Next Recommended Step for Codex
Run final validation, commit the DOC-SKILL-002 fixture checkpoint, and push `backup/develop` only.

## Last Updated
2026-06-13 12:26 local time
