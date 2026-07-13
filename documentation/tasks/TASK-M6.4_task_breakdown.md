# TASK BREAKDOWN - TASK-M6.4

## Binding Sources

- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 3.3 and Phase-A `T-A4`).
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_a.md`.
- Backlog Item: `N/A` - roadmap/spec-driven infrastructure slice.
- Prior Slice: `TASK-M6.3` is checkpointed; its default-off OpenAI runner boundary is unchanged.

## Released Target

- Target Task: `TASK-M6.4`.
- Title: Migrate the Gemini gateway to the shared ToolLoopRunner.
- Execution Model: `5.6 Terra`, `high`.
- Readiness: `PRECHECK_READY`.

## OpenRouter Review Evidence

- Operator choice: OpenRouter (`2`), model `qwen/qwen3-coder-30b-a3b-instruct`.
- Workflow: `WF-M6.4-TASK-BREAKDOWN-2026-07-11-001`.
- Result: `OPENROUTER_WORKER_DRY_RUN_READY`; no live delegated review was performed and Codex retains refinement authority.

## Verified Gemini Responsibilities

- Gemini's `_run_simple_tool_loop` applies visible model overrides and the native `system.websearch` default-to-Flash policy before generic MoA resolution.
- Gemini raises the list-query round cap to `12`, accumulates grounding-query cost, preserves grounding metadata, and persists Gemini-specific request attribution after both normal and synthesis responses.
- Gemini keeps engine-owned and drill-down paths outside the simple loop; its history bridge uses the native provider service.

## Resolved Boundary Decision

- Spec Section 3.3.2 now binds the runner to provider-neutral callbacks/context for model selection, effective max rounds, and generic per-response facts.
- Gemini retains visible override/Flash-default policy, list-query round policy, grounding metadata/query-cost accumulation, request attribution, native proto/schema/history bridging, routing guards, synthesis, preserved metadata, engine-owned handling, and drill-down paths.
- `TASK-M6.4` migrates only `_run_simple_tool_loop`; it must not infer a provider-policy API beyond the explicit callback/context boundary.

## Candidate Files After Decision

- `backend/llm_providers/gemini/gateway.py`.
- `backend/llm_providers/shared/tool_loop_runner.py`.
- `backend/tests/test_gemini_tool_loop_runner.py` (new).
- `backend/tests/test_backlog_007_tool_routing_performance.py`.
- focused Gemini gateway/cost-attribution regressions selected after the decision.

## Acceptance Criteria

- The explicit spec decision assigns Gemini model-policy, list-round, grounding-observability, and native synthesis ownership without changing the M6.3 OpenAI behavior.
- The Gemini default-off path remains unchanged until the decided runner integration is enabled.
- Gemini proto, schema, history, grounding metadata, query-cost accounting, and request attribution remain behaviorally intact on the migrated path.
- Engine-owned and drill-down paths remain outside this migration unless a later bound task explicitly includes them.

## Tests

- focused Gemini runner and gateway regressions defined by the approved ownership decision.
- `python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q` where the local ChromaDB environment permits collection.
- focused Gemini cost-attribution and grounding-metadata regressions selected by precheck.
- `python -m py_compile backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/tool_loop_runner.py`.

## Next Skill

`janus-preimplementation-check`
