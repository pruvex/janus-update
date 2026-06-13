# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Prepare a controlled one-shot OR telemetry smoke-test plan for the completed mini workflow layer, preserve the 5.4-mini phase boundaries, and keep the separate 5.4 candidate phase paused before any continuation.

## Active Phase
Documentation-skill controlled OR smoke-test planning. The mini matrix phase remains complete for `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, and `DOC-SKILL-010` with preserved counts `OR_CONFIRMED=7`, `NEEDS_STRONGER_TEST=0`, and `OR_REJECTED=0`. The healthcheck runner can already read dummy JSONL via an optional flag, and a new one-shot smoke-test plan now defines the selected task/model pair, cost cap, telemetry gates, pass/fail criteria, abort criteria, and no-persist rule without starting any new model work. The separate `5.4` candidate phase remains paused and planning-only. DOC-SKILL-011 remains `NOT RUN`; DOC-SKILL-012 and later remain `NOT RUN`. No production routing, no canonical routing-table update, no DOC-SKILL-011 run, no DOC-SKILL-012 start, no release action, and no product-code change.

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
Prepared a documentation-only controlled one-shot smoke-test plan for OR telemetry. The plan selects one existing `OR_CONFIRMED` mini skill, locks one approved mini-matrix model, defines a hard cost cap, spells out required telemetry capture, requires the healthcheck runner invocation, and sets explicit pass/fail, abort, and no-persist rules.

The telemetry plan keeps the mini phase bounded to:

- `DOC-SKILL-001`
- `DOC-SKILL-002`
- `DOC-SKILL-003`
- `DOC-SKILL-006`
- `DOC-SKILL-008`
- `DOC-SKILL-009`
- `DOC-SKILL-010`

No model calls were run, no OR calls were run, no live eval was started, no production routing decision was made, no canonical routing-table update was made, no DOC-SKILL-011 run was started, and the separate `5.4` candidate phase was not continued.

## Changed Files
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
- This block is intended to be committed as `docs(codex): plan controlled or telemetry smoke test` and pushed to `backup/develop` only.
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
- Healthcheck output summaries are defined: PASS.
- No global model approval language: PASS.
- No production routing language: PASS.
- No routing-table update: PASS.
- No model calls: PASS.
- No OR calls: PASS.
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
- The separate `5.4` phase is paused; no candidate list should be treated as evaluation evidence until a separate explicit phase runs.

## Next Recommended Step for ChatGPT
Review the controlled smoke-test gates and confirm whether the selected skill/model pair and cost cap are acceptable before any separate `5.4` candidate work resumes.

## Next Recommended Step for Codex
Keep the `5.4` candidate phase paused, do not run the OR call, and treat the smoke-test plan as approval-gated planning only until the user explicitly authorizes execution.

## Last Updated
2026-06-13 19:05 local time
