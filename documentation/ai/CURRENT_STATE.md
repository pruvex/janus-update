# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Close the remaining bounded mini OR live evidence batch for `DOC-SKILL-001`, `DOC-SKILL-002`, and `DOC-SKILL-003` with accepted file-first capture evidence, keep the original first `DOC-SKILL-008` smoke-test row as debug failure evidence only, and preserve the completed 5.4-mini phase boundaries while the separate `5.4` candidate phase remains paused.

## Active Phase
Documentation-skill remaining mini OR live evidence batch closure. The mini matrix phase remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. The original first approved OR smoke-test call for `DOC-SKILL-008` on `qwen/qwen3.5-flash-02-23` remains debug failure evidence only because shell-side capture lost response body, `generation_id`, and `response_usage`. The separately approved `DOC-SKILL-008` live retry remains accepted bounded telemetry evidence only. One controlled batch already executed `DOC-SKILL-009`, `DOC-SKILL-010`, and optional `DOC-SKILL-006` through the file-first wrapper. A second controlled remaining batch then executed exactly three live OR calls through the same file-first wrapper for `DOC-SKILL-001`, `DOC-SKILL-002`, and `DOC-SKILL-003`, each on `openai/gpt-oss-20b`. All three remaining calls stayed within the `0.0020` per-call cap and the `0.0060` batch cap, persisted file-first artifacts, recovered `generation_id` plus usage from `response_summary.json`, wrote accepted telemetry rows, and passed `health_snapshot.py --or-telemetry-jsonl` ingestion as a three-row batch. This remains bounded local telemetry evidence only: no production routing, no canonical routing-table update, no `DOC-SKILL-011` run, no `DOC-SKILL-012` start, no release action, and no product-code change. The separate `5.4` candidate phase remains paused and planning-only.

## Last Decision
The documentation-skill routing table remains the canonical reference for documentation-skill model and scope boundaries.

The completed `5.4 mini` planning layer now includes OR cost-accounting planning through:

- `documentation/codex/model-routing/doc_skill_gpt54_mini_or_replacement_matrix_2026-06-13.md`
- `documentation/codex/model-routing/doc_skill_gpt54_mini_workflow_routing_plan_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_plan_2026-06-13.md`

The bounded mini scope remains limited to:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Preserved counts remain:

- `OR_CONFIRMED=7`
- `NEEDS_STRONGER_TEST=0`
- `OR_REJECTED=0`

The separate `5.4` candidate phase remains paused and planning-only.

This cost-accounting planning step does not create a global model approval, does not mark any model production-approved, does not update the canonical routing table, does not run DOC-SKILL-011, does not continue the `5.4` candidate phase, and does not start DOC-SKILL-012.

## Last Codex Work
Ran the controlled remaining mini live batch through the file-first wrapper for `DOC-SKILL-001`, `DOC-SKILL-002`, and `DOC-SKILL-003` on `openai/gpt-oss-20b`. The first orchestration attempt stopped before any accepted row because `DOC-SKILL-001` lacked `sanitized_input.task_name`; the bounded rerun used a safe task-name fallback and then completed cleanly. The remaining batch produced accepted telemetry rows for all three skills, with total actual OR cost `0.00031437`. Each call persisted `request_body.json`, `response_body.json`, `response_headers.txt`, `response_summary.json`, `stdout.log`, `stderr.log`, and `exit_code.txt`, and each accepted row recorded `generation_id`, usage, actual cost, and `validation_result=PASS`. `health_snapshot.py --or-telemetry-jsonl` successfully ingested the remaining batch file with `record_count=3`, `fallback_count=0`, `validation_result_counts={"PASS": 3}`, and `recommendation_signal_counts={"OR_PREFERRED": 3}`. The original first `DOC-SKILL-008` smoke-test result still remains debug-only because that earlier run lost response body, `generation_id`, and `response_usage`.

The telemetry plan keeps the mini phase bounded to:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

Exactly one approved OR call was attempted for the smoke test in the prior block. No second OR call was made in this debugging block, no production routing decision was made, no canonical routing-table update was made, no DOC-SKILL-011 run was started, and the separate `5.4` candidate phase was not continued.

## Changed Files
- `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1`
- `documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_remaining_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_mini_live_batch_remaining_result_2026-06-13.md`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-001-openai-gpt-oss-20b/exit_code.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-002-openai-gpt-oss-20b/exit_code.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-remaining-2026-06-13-live-001/doc-skill-003-openai-gpt-oss-20b/exit_code.txt`
- `documentation/codex/model-routing/or_healthcheck_telemetry_mini_live_batch_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_mini_live_batch_result_2026-06-13.md`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-009-qwen-qwen3.5-flash-02-23/exit_code.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-010-qwen-qwen3.5-flash-02-23/exit_code.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/mini-batch-2026-06-13-live-001/doc-skill-006-openai-gpt-oss-120b/exit_code.txt`
- `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_live_retry_2026-06-13.jsonl`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/request_body.json`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/request_body_source.json`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/response_body.json`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/response_headers.txt`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/response_summary.json`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/stdout.log`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/stderr.log`
- `documentation/codex/model-routing/smoke-test-capture/live-retry-2026-06-13-doc-skill-008-001/exit_code.txt`
- `documentation/codex/model-routing/or_file_first_capture_wrapper_plan_2026-06-13.md`
- `documentation/codex/model-routing/wrapper_fixture_request_2026-06-13.json`
- `documentation/codex/model-routing/wrapper_fixture_response_2026-06-13.json`
- `documentation/codex/model-routing/or_healthcheck_smoke_test_capture_debug_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_controlled_smoke_test_result_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_smoke_test_debug_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_controlled_smoke_test_plan_2026-06-13.md`
- `documentation/codex/skills/janus-health-check/scripts/health_snapshot.py`
- `documentation/codex/model-routing/or_healthcheck_dummy_ingestion_validation_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_jsonl_schema_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_dummy_sample_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_summary_dummy_example_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_plan_2026-06-13.md`
- `documentation/codex/model-routing/doc_skill_gpt54_mini_workflow_routing_plan_2026-06-13.md`
- `documentation/codex/model-routing/doc_skill_gpt54_or_candidate_list_plan_2026-06-13.md`
- `documentation/codex/model-routing/doc_skill_gpt54_mini_or_replacement_matrix_2026-06-13.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Remote Sync Evidence
- Branch context: `develop` / `backup/develop` workflow.
- This block is intended to be committed as `docs(codex): close or smoke capture debug` and pushed to `backup/develop` only.
- No push to `origin`, tag, merge, reset, release, routing-table update, DOC-SKILL-011 run, DOC-SKILL-012 continuation, or production routing activation is part of this block.

## Tests / Validation
- Start-of-work healthcheck reminder: DUE, user previously deferred it for later.
- Mini matrix exists: PASS.
- Mini matrix includes only `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010`: PASS.
- Mini matrix counts remain `7/0/0`: PASS.
- OR telemetry plan exists: PASS.
- Telemetry plan includes prediction and actual accounting: PASS.
- Usage fallback path is documented: PASS.
- Confidence fields are documented: PASS.
- Confidence formula is documented: PASS.
- Startup display format is documented: PASS.
- Telemetry JSONL schema exists: PASS.
- Dummy sample record parses as JSON: PASS.
- Schema contains all planned telemetry, cost, and confidence fields: PASS.
- Dummy summary example references only schema fields: PASS.
- Schema/sample/report field alignment: PASS.
- Dummy JSONL parses through runner/helper: PASS.
- OR summary output matches expected dummy sample values: PASS.
- Existing healthcheck behavior remains compatible when the optional flag is omitted: PASS.
- Smoke-test plan exists: PASS.
- All gates are explicit: PASS.
- One approved OR call attempted: PASS.
- No second OR call attempted: PASS.
- Separately approved single live retry attempted exactly once: PASS.
- Controlled mini live evidence batch attempted `3` calls total: PASS.
- Remaining mini live evidence batch attempted `3` calls total: PASS.
- Pre-call cost estimate under cap: PASS.
- Direct shell-side response capture recovered `response_usage`: FAIL.
- Fallback-estimate debug row created: PASS.
- File-first live retry artifacts exist: PASS.
- `response_body.json` exists and parses for the live retry: PASS.
- `response_summary.json` contains `generation_id` and `usage` for the live retry: PASS.
- Live retry actual cost `0.000570895` <= `0.0020`: PASS.
- Accepted live retry telemetry JSONL row created: PASS.
- `health_snapshot.py --or-telemetry-jsonl` reads the accepted retry row: PASS.
- OR summary output matches the accepted retry row: PASS.
- Mini live batch telemetry JSONL file exists: PASS.
- `DOC-SKILL-009` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- `DOC-SKILL-010` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- `DOC-SKILL-006` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- Mini live batch total actual cost `0.0014551` <= `0.0060`: PASS.
- `health_snapshot.py --or-telemetry-jsonl` reads the accepted mini batch file: PASS.
- Mini live batch OR summary output matches the accepted batch file: PASS.
- Remaining mini live batch telemetry JSONL file exists: PASS.
- `DOC-SKILL-001` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- `DOC-SKILL-002` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- `DOC-SKILL-003` accepted row has response body, `generation_id`, usage, actual cost, and `validation_result=PASS`: PASS.
- Remaining mini live batch total actual cost `0.00031437` <= `0.0060`: PASS.
- `health_snapshot.py --or-telemetry-jsonl` reads the accepted remaining batch file: PASS.
- Remaining mini live batch OR summary output matches the accepted remaining batch file: PASS.
- Capture-debug note exists: PASS.
- No new OR call was made in the capture-debug block: PASS.
- Likely root cause documented: PASS.
- Capture-safe replacement pattern documented: PASS.
- File-first wrapper script exists: PASS.
- File-first wrapper plan exists: PASS.
- Wrapper validation may use local fixture data only: PASS.
- Local fixture wrapper validation created all required artifact files: PASS.
- Local fixture wrapper validation parsed `generation_id` and `usage`: PASS.
- Capture-debug phase was previously closed and remained the prerequisite for the approved retry: PASS.
- Further future live retry remains optional and explicit-approval-gated: PASS.
- Healthcheck output summaries are defined: PASS.
- No global model approval language: PASS.
- No production routing language: PASS.
- No routing-table update: PASS.
- No model calls beyond the explicitly approved OR smoke-test call plus the explicitly approved single live retry: PASS.
- The separate `5.4` candidate phase remains paused and planning-only: PASS.
- No DOC-SKILL-011 run: PASS.
- No DOC-SKILL-012 start: PASS.
- `git diff --check`: PASS.
- Staged-only git guard required before commit: PASS.

## Open Risks
- The repository worktree contains many unrelated pre-existing modified and untracked files. Commit staging must remain path-specific.
- The completed mini matrix is task-level documentation evidence only and must not be misread as a global model approval or production routing update.
- The telemetry plan is planning-only; confidence scores remain future-facing until enough comparable historical rows, price snapshots, and usage capture exist.
- The new schema and examples are dummy artifacts only; they do not prove runtime ingestion until future implementation lands.
- The new ingestion path is dummy-only by convention and still depends on explicit operator input; no production OR log path is wired yet.
- The smoke-test plan is still planning-only and must not be treated as approval to run the OR call.
- The smoke-test execution produced a capture gap, so the resulting row is debug evidence only and must not be treated as accepted operational telemetry.
- The accepted retry proves capture for this one bounded task/model pair only; it is not a global OR approval or production-routing approval.
- The bounded mini live batch adds task-level local evidence for three approved mini skills only; it still does not create any global OR approval or production-routing approval.
- The bounded remaining mini live batch adds task-level local evidence for the last three approved mini skills only; it still does not create any global OR approval or production-routing approval.
- Any later live retry beyond this accepted block would still need separate explicit approval.
- The separate `5.4` phase is paused; no candidate list should be treated as evaluation evidence until a separate explicit phase runs.

## Next Recommended Step for ChatGPT
Treat the first `DOC-SKILL-008` smoke-test row as debug-only, treat the accepted retry row plus both accepted three-row mini batches as bounded local telemetry evidence only, and keep the separate `5.4` candidate phase paused until a new planning-only request arrives.

## Next Recommended Step for Codex
Stop after documentation/governance closeout, keep the accepted retry row plus both accepted mini batches as bounded smoke-test evidence only, and do not continue into any further OR call or `5.4` candidate work without a new explicit request.

## Last Updated
2026-06-13 20:30 local time
