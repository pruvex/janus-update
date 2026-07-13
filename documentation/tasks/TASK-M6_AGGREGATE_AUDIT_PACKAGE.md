# AUDIT_PACKAGE

Generated: 2026-07-13 19:18:42 UTC

## Goal

Aggregate M6 transport-refactor closure audit with documented C3 architecture debt

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: M6 Phase A/B/C1/C2/C4 validated; C3 retained as documented architecture debt
- Task File: documentation\tasks\TASK-M6_transport_phase_c.md
- Backlog Item: N/A WITH REASON: task/spec initiative
- Pre-Implementation Check: N/A WITH REASON - No precheck file provided.
- Manual Janus Evidence: PRESENT: enabled Gemini/OpenAI/Ollama weather smokes from completed M6 slices; C4 N/A test-only.
- Pipeline Completion Status: All implemented M6 slices complete; C3 has no safe deletion candidate and is explicitly retained.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
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

### TASK-M6C.2 Extract shared response post-processors

- Completion: `DONE` after `documentation/tasks/TASK-M6C.2_FINAL_AUDIT.md` (`PASS`). The central `backend/services/llm_gateway.py:reason_and_respond` return seam now owns the registered OpenAI-compatible release-list link repair and Gemini-native preserved-metadata rendering.
- Validation: focused registry and transport-gateway suite `24 passed`, syntax, scoped diff, and enabled Gemini Berlin-weather smoke with `Quelle: Open-Meteo` PASS.
- Scope: T-C2 only; Websearch policy, fallback, model policy, transport enablement, tool execution, streaming, persistence, UI, T-C3, and T-C4 remain unchanged.

### TASK-M6C.4 Add provider tool-ID parity coverage

- Completion: `DONE` after `documentation/tasks/TASK-M6C.4_FINAL_AUDIT.md` (`PASS`). Validation: focused parity plus adapter regression suite `14 passed`, syntax, and scoped diff PASS.
- Scope: test-only OpenAI/Gemini canonical tool-ID roundtrip for `system.weather` and `system.websearch`; C3 remains open.

## Deferred Phase-C Work

- `T-C3` provider-branch removal remains documented architecture debt: the extended inventory found active contracts only, so no safe deletion was released. `T-C4` provider tool-ID parity coverage is complete and validated.
```

## Pre-Implementation Check

```text
N/A WITH REASON - No file provided.
```

## Changed Files

```text
M PROJECT_STATE.md
 M documentation/01_CENTRAL_TASK_REGISTRY.md
 M documentation/ai/CURRENT_STATE.md
 M documentation/codex/SKILL_USAGE_LOG.md
 M documentation/pipeline/TEST_PIPELINE_RUN_LOG.md
 M documentation/tasks/TASK-M6_transport_phase_c.md
?? backend/tests/test_provider_parity.py
?? codex_weekly_healthcheck.md
?? codex_weekly_skill_cost_audit.json
?? codex_weekly_skill_cost_audit.md
?? documentation/SPEC/M6C3_provider_branch_reachability_inventory.md
?? documentation/SPEC/M6C4_provider_tool_id_parity.md
?? documentation/logs/
?? documentation/tasks/TASK-M6C.3_decision_summary.md
?? documentation/tasks/TASK-M6C.3_provider_branch_inventory.md
?? documentation/tasks/TASK-M6C.3_provider_branch_inventory_result.md
?? documentation/tasks/TASK-M6C.3_task_breakdown.md
?? documentation/tasks/TASK-M6C.3_task_compilation.md
?? documentation/tasks/TASK-M6C.4_AUDIT_PACKAGE.md
?? documentation/tasks/TASK-M6C.4_DOCUMENTATION_UPDATE.md
?? documentation/tasks/TASK-M6C.4_FINAL_AUDIT.md
?? documentation/tasks/TASK-M6C.4_decision_summary.md
?? documentation/tasks/TASK-M6C.4_execution_result.md
?? documentation/tasks/TASK-M6C.4_preimplementation_check.md
?? documentation/tasks/TASK-M6C.4_provider_tool_id_parity.md
?? documentation/tasks/TASK-M6C.4_task_breakdown.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.3_provider_branch_inventory_result.md (2671 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.4_FINAL_AUDIT.md (1557 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.2_FINAL_AUDIT.md (2578 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6B_PHASE_B_FINAL_AUDIT.md (2168 bytes)
```

## Diff Summary

```text
PROJECT_STATE.md                                 |  1 +
 documentation/01_CENTRAL_TASK_REGISTRY.md        |  9 +++++++++
 documentation/ai/CURRENT_STATE.md                | 20 ++++++++++----------
 documentation/codex/SKILL_USAGE_LOG.md           | 13 +++++++++++++
 documentation/pipeline/TEST_PIPELINE_RUN_LOG.md  |  7 +++++++
 documentation/tasks/TASK-M6_transport_phase_c.md |  5 +++++
 6 files changed, 45 insertions(+), 10 deletions(-)
```

## Validation

```text
Phase-B direct-provider matrix: 63 passed; enabled OpenAI/Gemini/Ollama Berlin-weather smokes PASS.
T-C1 Websearch selection: 111 passed, 6 deselected; enabled Gemini smoke PASS.
T-C2 response postprocessors: 24 passed; enabled Gemini smoke PASS.
T-C4 canonical tool-ID parity: 14 passed; test-only, manual evidence N/A.
All bound final-audit validators and scoped diff checks: PASS.
```

## Notes

No additional notes provided.

## Risks

C3 provider-branch count reduction remains unimplemented architecture debt; Cursor external re-review returned PASS. Normal Git governance and a separately approved master merge remain.

## Open Issues

C3 cleanup remains open; do not claim Exit-C branch-count target met.

## Re-Audit Delta

- Direct validation transcription was added: Phase-B `63 passed`, C1 `111 passed, 6 deselected`, C2 `24 passed`, and C4 `14 passed`, with scoped checks PASS.
- C3 wording is consistent as inventory PASS / deletion remains open / architecture debt; no dead-code-removal claim exists.
- Cursor external re-review result: `PASS` on 2026-07-13. It confirmed provider boundaries, canonical tool identity, C3 wording, and scoped evidence. No fix remains for this gate.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6_AGGREGATE_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
