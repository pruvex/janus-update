# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Record the Auto Router batch lessons learned for the seven live-evidenced mini documentation skills while keeping fixed-model Auto-sparsam canonical.

## Active Phase
Documentation-skill mini Auto Router lessons-learned closeout. The fixed-model mini evidence layer remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. The bounded Auto Router 7-skill batch stopped early after `DOC-SKILL-002` returned `finish_reason=length`, and the lessons-learned note records that Auto Router is not broadly confirmed across the mini documentation scope.

## Last Decision
Fixed-model Auto-sparsam remains canonical. Auto Router remains experiment-only. No production routing, canonical routing-table update, global OR approval, `DOC-SKILL-011` run, `DOC-SKILL-012` start, or separate `5.4` candidate continuation is approved.

## Last Codex Work
Created the Auto Router mini lessons-learned decision note. The note records that Auto Router is not broadly confirmed for the seven mini documentation skills, that `DOC-SKILL-001` should remain `KEEP_FIXED`, that `DOC-SKILL-002` should remain `MANUAL_REVIEW`, that `DOC-SKILL-010` remains `FURTHER_TEST_CANDIDATE`, that `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, and `DOC-SKILL-009` received no new broad-batch evidence, and that future Auto Router testing should be targeted rather than broad.

## Changed Files
- `documentation/codex/model-routing/or_auto_router_mini_lessons_learned_2026-06-13.md`
- `documentation/codex/model-routing/or_auto_router_7skill_batch_plan_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_auto_router_7skill_batch_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_auto_router_7skill_batch_result_2026-06-13.md`
- `documentation/codex/model-routing/or_auto_router_7skill_batch_classification_2026-06-13.md`
- `documentation/codex/model-routing/smoke-test-capture/auto-router-7skill-batch-2026-06-13-live-001/*`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- Intended commit for this block: `docs(codex): record auto router mini lessons`
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
- lessons-learned note exists: PASS.
- `DOC-SKILL-001` `KEEP_FIXED` rationale included: PASS.
- `DOC-SKILL-002` `MANUAL_REVIEW` rationale included: PASS.
- `DOC-SKILL-010` `FURTHER_TEST_CANDIDATE` rationale included: PASS.
- no production activation language: PASS.

## Open Risks
- The repository worktree still contains many unrelated modified and untracked files; staging must remain path-specific.
- The 7-skill Auto Router batch did not reach `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, or `DOC-SKILL-010`, so broad Auto Router usefulness is still unproven.
- `DOC-SKILL-001` shows Auto Router can be materially more expensive than the fixed baseline even when capture and validation pass.
- `DOC-SKILL-002` still shows a completion-budget risk under Auto Router with `openai/gpt-oss-120b`.
- All Auto Router evidence remains local bounded experiment evidence only and must not be misread as production routing approval.

## Next Recommended Step for ChatGPT
Treat the 7-skill Auto Router batch as partial negative breadth evidence, keep fixed-model Auto-sparsam canonical, retain `DOC-SKILL-010` as `FURTHER_TEST_CANDIDATE`, and require explicit approval before any further targeted Auto Router follow-up.

## Next Recommended Step for Codex
Stop after this lessons-learned closeout, keep Auto Router experiment-only, and do not continue into more Auto Router calls, production routing changes, or separate `5.4` candidate work without a new explicit request.

## Last Updated
2026-06-13 22:33 local time
