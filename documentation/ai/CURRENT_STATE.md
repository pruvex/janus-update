# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the bounded 7-skill Auto Router comparison batch outcome for the live-evidenced mini documentation skills while keeping fixed-model Auto-sparsam canonical.

## Active Phase
Documentation-skill mini Auto Router batch comparison closeout. The fixed-model mini evidence layer remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. The bounded Auto Router 7-skill batch was approved but stopped early after `DOC-SKILL-002` returned `finish_reason=length`.

## Last Decision
Fixed-model Auto-sparsam remains canonical. Auto Router remains experiment-only. No production routing, canonical routing-table update, global OR approval, `DOC-SKILL-011` run, `DOC-SKILL-012` start, or separate `5.4` candidate continuation is approved.

## Last Codex Work
Created the 7-skill Auto Router batch plan, ran the bounded live batch through the file-first wrapper, accepted one telemetry row for `DOC-SKILL-001`, aborted the batch after `DOC-SKILL-002` hit `finish_reason=length`, and recorded result plus classification artifacts.

## Changed Files
- `documentation/codex/model-routing/or_auto_router_7skill_batch_plan_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_auto_router_7skill_batch_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_auto_router_7skill_batch_result_2026-06-13.md`
- `documentation/codex/model-routing/or_auto_router_7skill_batch_classification_2026-06-13.md`
- `documentation/codex/model-routing/smoke-test-capture/auto-router-7skill-batch-2026-06-13-live-001/*`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- Intended commit for this block: `test(codex): run auto router mini batch comparison`
- Push target for this block: `backup/develop` only.
- No push to `origin`, tag, merge, release, reset, routing-table update, or production routing activation is part of this block.

## Tests / Validation Performed
- OpenRouter Auto Router documentation checked for `openrouter/auto`, `plugins.allowed_models`, and `cost_quality_tradeoff`: PASS.
- 7-skill batch plan artifact exists: PASS.
- File-first wrapper used for every attempted live call: PASS.
- call count `<= 7`: PASS (`2` attempted).
- per-call cap `<= 0.0020`: PASS.
- total accepted actual cost `<= 0.0140`: PASS (`0.000525`).
- `DOC-SKILL-001` accepted row has response body, `generation_id`, selected routed model, `finish_reason`, usage, actual cost, and `validation_result=PASS`: PASS.
- `health_snapshot.py --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_auto_router_7skill_batch_2026-06-13.jsonl`: PASS.
- `DOC-SKILL-001` Auto Router vs fixed baseline comparison recorded: PASS.
- `DOC-SKILL-002` response body, `generation_id`, usage, and actual cost captured: PASS.
- `DOC-SKILL-002` completion adequacy gate with `finish_reason=length`: FAIL.
- batch aborted on the first completion-budget failure: PASS.
- classification note exists: PASS.
- no production activation language: PASS.

## Open Risks
- The repository worktree still contains many unrelated modified and untracked files; staging must remain path-specific.
- The 7-skill Auto Router batch did not reach `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, or `DOC-SKILL-010`, so broad Auto Router usefulness is still unproven.
- `DOC-SKILL-001` shows Auto Router can be materially more expensive than the fixed baseline even when capture and validation pass.
- `DOC-SKILL-002` still shows a completion-budget risk under Auto Router with `openai/gpt-oss-120b`.
- All Auto Router evidence remains local bounded experiment evidence only and must not be misread as production routing approval.

## Next Recommended Step for ChatGPT
Treat the 7-skill Auto Router batch as partial negative evidence for breadth. Keep fixed-model Auto-sparsam canonical, retain `DOC-SKILL-010` as `FURTHER_TEST_CANDIDATE`, and require explicit approval before any further live Auto Router follow-up.

## Next Recommended Step for Codex
Stop after this batch closeout, commit the bounded experiment artifacts, and do not continue into more Auto Router calls, production routing changes, or separate `5.4` candidate work without a new explicit request.

## Last Updated
2026-06-13 22:26 local time
