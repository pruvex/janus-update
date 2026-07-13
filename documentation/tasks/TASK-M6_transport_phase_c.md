TASK-M6C
- Source Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase C Decoupling + Cleanup
- Generated At: 2026-07-13

## Generated Tasks

### TASK-M6C.1 Decouple Websearch provider coercion from ToolExecutor
- Ziel:
  - Implement the approved Phase-C `T-C1`: remove Websearch provider/model coercion from `ToolExecutor` by relocating the existing Websearch-specific decision to the live `system.websearch` wrapper boundary.
- Scope:
  - Bound the work to the existing `system.websearch` argument path in `backend/services/tool_executor.py` and the live Websearch wrapper boundary `backend/tool_registry.py:websearch_wrapper`.
  - Introduce or consume only the approved default-off `TRANSPORT_WEBSEARCH_DECOUPLED` rollout flag. Preserve legacy behavior while the flag is absent or false.
  - Keep the existing provider/model compatibility and cross-provider safety behavior covered at the wrapper boundary; do not expand into provider gateways, transports, tool schemas, the Websearch service implementation, ToolLoopRunner, streaming, or Phase-C tasks `T-C2` through `T-C4`.
- Files:
  - `backend/services/tool_executor.py`
  - `backend/tool_registry.py`
  - `backend/tests/test_backlog_007_tool_routing_performance.py`
  - `backend/tests/tools/test_websearch.py`
- Steps:
  1. Isolate the existing `system.websearch` provider/model coercion from the executor path behind the approved default-off rollout seam.
  2. Place the equivalent Websearch-specific policy at `websearch_wrapper` without changing the legacy flag-off contract.
  3. Add focused hermetic regressions for flag-off preservation, enabled-path boundary ownership, and provider/model safety behavior.
- Acceptance Criteria:
  - With `TRANSPORT_WEBSEARCH_DECOUPLED` absent or `false`, the current Websearch execution behavior remains preserved.
  - With the flag enabled, `ToolExecutor` no longer owns Websearch provider/model coercion and the Websearch boundary receives the required provider/model context.
  - Existing cross-provider safety behavior remains covered by focused tests; no gateway, transport, or unrelated tool path is changed.
  - Focused tests run without network access or provider credentials.
- Tests:
  - Focused Websearch executor regressions in `backend/tests/test_backlog_007_tool_routing_performance.py`.
  - Focused Websearch provider/model regressions in `backend/tests/tools/test_websearch.py`.
  - Syntax and scoped-diff checks selected by preimplementation check.
- Completion: `DONE` after `documentation/tasks/TASK-M6C.1_FINAL_AUDIT.md` (`PASS`). Validation: focused Websearch selection `111 passed, 6 deselected`, syntax, scoped diff, and enabled Gemini Berlin-weather smoke PASS. This completion closes T-C1 only.
- Model: 5.6 Terra
- Reason:
  - `T-C1` is the first approved Phase-C table entry and directly establishes the Exit-C condition that Websearch must run without provider coercion inside the executor. The current seam is provider-sensitive and requires a bounded high-reasoning precheck before code changes.

## Deferred Phase-C Work

- `T-C2` response post-processor extraction, `T-C3` provider-branch removal, and `T-C4` provider parity tests remain separate later tasks. They are not released by this artifact.
