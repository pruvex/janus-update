# TASK BREAKDOWN - TASK-M6.5

## Binding Sources
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Section 3.3.3 and Phase-A `T-A5`).
- Parent Task: `documentation/tasks/TASK-M6_transport_phase_a.md`.
- Backlog Item: `N/A` - roadmap/spec-driven infrastructure slice.

## Released Target
- Target Task: `TASK-M6.5`.
- Title: Route streaming through the gateway and ToolLoopRunner path.
- Execution Model: `5.6 Terra`, `high`.
- Readiness: `PRECHECK_READY`.

## Atomic Scope
- Keep StreamEvent protocol, stream auth isolation, forced-tool start, provider delta normalization, and stream-final cost handling in `backend/services/orchestrator/execution_engine.py`.
- When the Phase-A flag is enabled, route only non-streaming tool-round handoff through the existing gateway/`ToolLoopRunner` boundary.
- Preserve the flag-off streaming path exactly; do not turn StreamEvents into the synchronous runner contract.

## Files
- `backend/services/orchestrator/execution_engine.py`.
- bound gateway/runner seams only as required by the handoff.
- `backend/tests/test_streaming_tool_loop_runner.py` (new).

## Explicit Exclusions
- No StreamEvent protocol rewrite, provider delta parser migration, auth-isolation change, forced-tool policy change, Gemini grounding-policy change, transport classes, resolver, OAuth, or Phase-B work.

## Acceptance Criteria
- Flag-off streaming behavior remains unchanged.
- Flag-on does not bypass the declared gateway/runner boundary for non-streaming tool rounds.
- StreamEvent parsing, auth isolation, forced-tool start, and stream-final cost ownership remain in `execution_engine.py`.
- Focused stream flag-off/flag-on consistency regressions pass.

## Tests
- focused streaming runner regression selected by precheck.
- provider stream regression for OpenAI and Gemini selected by precheck.
- `python -m py_compile backend/services/orchestrator/execution_engine.py`.

## Next Skill
`janus-preimplementation-check`
