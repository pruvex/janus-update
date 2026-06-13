# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Sync the OR smoke-test capture-debug outcome and prepare a reusable file-first capture wrapper for future explicitly approved smoke-test use, without making another OR call, while keeping the completed 5.4-mini phase boundaries intact and the separate `5.4` candidate phase paused.

## Active Phase
Documentation-skill OR smoke-test capture-debug sync and wrapper preparation. The mini matrix phase remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. The single approved OR smoke-test call for `DOC-SKILL-008` on `qwen/qwen3.5-flash-02-23` remains the only executed smoke-test call. No new OR call was made during this block. The capture-debug outcome is now synchronized with a reusable local file-first wrapper and a small wrapper plan. The wrapper writes request, response body, headers, parsed summary, stdout, stderr, and exit code to disk before any operator summary depends on shell output. The existing debug row remains debug failure evidence only, not accepted operational telemetry. The separate `5.4` candidate phase remains paused and planning-only. DOC-SKILL-011 remains `NOT RUN`; DOC-SKILL-012 and later remain `NOT RUN`. No production routing, no canonical routing-table update, no DOC-SKILL-011 run, no DOC-SKILL-012 start, no release action, and no product-code change.

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
Synchronized the capture-debug outcome into the rolling state and prepared a reusable file-first wrapper plus a wrapper plan. The wrapper lives under `documentation/codex/model-routing/scripts/or_file_first_capture_wrapper.ps1` and supports local fixture validation without network access. It writes `request_body.json`, `response_body.json`, `response_headers.txt`, `response_summary.json`, `stdout.log`, `stderr.log`, and `exit_code.txt` under a per-run directory before any shell summary is emitted. A fixture-only validation run produced all required artifacts locally and confirmed parsed `generation_id` and `usage` in `response_summary.json` without making an OR call.

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
- This block is intended to be committed as `docs(codex): sync or smoke capture debug` and pushed to `backup/develop` only.
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
- Pre-call cost estimate under cap: PASS.
- Direct shell-side response capture recovered `response_usage`: FAIL.
- Fallback-estimate debug row created: PASS.
- Capture-debug note exists: PASS.
- No new OR call was made in the capture-debug block: PASS.
- Likely root cause documented: PASS.
- Capture-safe replacement pattern documented: PASS.
- File-first wrapper script exists: PASS.
- File-first wrapper plan exists: PASS.
- Wrapper validation may use local fixture data only: PASS.
- Local fixture wrapper validation created all required artifact files: PASS.
- Local fixture wrapper validation parsed `generation_id` and `usage`: PASS.
- Healthcheck output summaries are defined: PASS.
- No global model approval language: PASS.
- No production routing language: PASS.
- No routing-table update: PASS.
- No model calls beyond the one explicitly approved OR smoke-test call: PASS.
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
- A later explicitly approved follow-up would still need the file-first capture wrapper before any new smoke-test attempt is worth making.
- The wrapper is locally prepared but still not authorized for a new live OR attempt without separate explicit approval.
- The separate `5.4` phase is paused; no candidate list should be treated as evaluation evidence until a separate explicit phase runs.

## Next Recommended Step for ChatGPT
Review whether the prepared wrapper and its local-fixture validation are sufficient to close the smoke-test capture-debug phase without any further live retry.

## Next Recommended Step for Codex
Keep the `5.4` candidate phase paused, do not run a second OR call, and use the wrapper only in local-fixture mode unless a future explicitly approved live retry is requested.

## Last Updated
2026-06-13 18:12 local time
