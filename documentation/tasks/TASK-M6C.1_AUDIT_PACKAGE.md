# AUDIT_PACKAGE

Generated: 2026-07-13 16:33:50 UTC

## Goal

Final audit of TASK-M6C.1: default-off Websearch provider/model coercion decoupling from ToolExecutor to the consumed ToolRegistry wrapper boundary.

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md (Phase-C T-C1)
- Task File: documentation/tasks/TASK-M6_transport_phase_c.md
- Backlog Item: N/A WITH REASON - No backlog marker provided.
- Pre-Implementation Check: documentation/tasks/TASK-M6C.1_preimplementation_check.md
- Manual Janus Evidence: PRESENT - 2026-07-13 18:22 +02:00: Gemini gemini-3.1-pro-preview with TRANSPORT_WEBSEARCH_DECOUPLED=true returned a source-backed Berlin weather response from Open-Meteo; no empty bubble, raw tool JSON, or provider/model error.
- Pipeline Completion Status: remaining T-C1 tasks none; implementation complete yes; manual enabled-path smoke PASS; T-C2 through T-C4 deferred by task artifact

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
- Model: 5.6 Terra
- Reason:
  - `T-C1` is the first approved Phase-C table entry and directly establishes the Exit-C condition that Websearch must run without provider coercion inside the executor. The current seam is provider-sensitive and requires a bounded high-reasoning precheck before code changes.

## Deferred Phase-C Work

- `T-C2` response post-processor extraction, `T-C3` provider-branch removal, and `T-C4` provider parity tests remain separate later tasks. They are not released by this artifact.
```

## Pre-Implementation Check

```text
# PREIMPLEMENTATION CHECK - TASK-M6C.1

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6C.1`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6_transport_phase_c.md`
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-C T-C1)
- Backlog Item: `N/A WITH REASON` (approved transport-refactor continuation, not a Backlog item)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. The task moves only the existing `system.websearch` provider/model coercion out of `ToolExecutor` to the live `backend.tool_registry:websearch_wrapper` boundary.
- Scope boundary: PASS. `TRANSPORT_WEBSEARCH_DECOUPLED` is the approved default-off Phase-C rollout guard. Provider gateways, transports, schemas, the Websearch service implementation, streaming, ToolLoopRunner, and T-C2 through T-C4 remain excluded.
- Product decisions: PASS. The approved Spec names T-C1, its two source modules, the default-off Phase-C flag, and the Exit-C requirement that Websearch has no provider coercion in the executor.
- Risk: HIGH. The affected executor branch currently enforces provider/model compatibility and cross-provider safety for a live tool path; hermetic flag-off and flag-on regressions are mandatory.
- Test surface: PASS. Existing focused executor Websearch regressions and Websearch provider/model tests provide a no-network evidence surface.
- Git checkpoint: RECOMMENDED before execution because the bounded slice changes live tool-dispatch policy ownership.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6C.1
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_c.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only Phase-C T-C1: relocate the existing system.websearch provider/model coercion from ToolExecutor to backend.tool_registry:websearch_wrapper.
- Keep TRANSPORT_WEBSEARCH_DECOUPLED absent/false behavior equivalent to the legacy executor path.
- With the flag true, remove Websearch-specific coercion ownership from ToolExecutor while preserving provider/model compatibility and cross-provider safety at websearch_wrapper.
- Keep provider gateways, transports, schemas, the Websearch service implementation, streaming, ToolLoopRunner, unrelated tools, and T-C2 through T-C4 unchanged.
Affected Files:
- backend/services/tool_executor.py
- backend/tool_registry.py
- backend/tests/test_backlog_007_tool_routing_performance.py
- backend/tests/tools/test_websearch.py
Evidence Focus:
- python -m pytest backend/tests/test_backlog_007_tool_routing_performance.py backend/tests/tools/test_websearch.py -q -k "websearch or tool_executor"
- python -m py_compile backend/services/tool_executor.py backend/tool_registry.py
- git diff --check
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_backlog_007_tool_routing_performance.py backend/tests/tools/test_websearch.py -q -k "websearch or tool_executor"
- python -m py_compile backend/services/tool_executor.py backend/tool_registry.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound Phase-C T-C1 task and approved default-off rollout flag
- ToolExecutor system.websearch argument branch and backend.tool_registry:websearch_wrapper
- focused provider/model safety regressions
Drop Context:
- completed Phase-A and Phase-B delivery history
- Epic 5, Epic 6, and later Phase-C task details
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Codex may run the bounded Cursor-first execution slice; request manual validation only after automated evidence passes.
```

## Changed Files

```text
M backend/services/tool_executor.py
 M backend/tests/test_backlog_007_tool_routing_performance.py
 M backend/tests/tools/test_websearch.py
 M backend/tool_registry.py
?? documentation/tasks/TASK-M6C.1_AUDIT_PACKAGE.md
?? documentation/tasks/TASK-M6C.1_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\backend\services\tool_executor.py (75891 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\backend\tool_registry.py (68908 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\backend\tests\test_backlog_007_tool_routing_performance.py (19297 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\backend\tests\tools\test_websearch.py (142878 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6_transport_phase_c.md (3070 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.1_task_breakdown.md (2711 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.1_preimplementation_check.md (4462 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.1_execution_result.md (4227 bytes)
```

## Diff Summary

```text
backend/services/tool_executor.py                  | 32 +++++++---
 .../test_backlog_007_tool_routing_performance.py   | 40 ++++++++++++
 backend/tests/tools/test_websearch.py              | 37 +++++++++++
 backend/tool_registry.py                           | 74 +++++++++++++++++++++-
 4 files changed, 174 insertions(+), 9 deletions(-)
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-M6C.1

Canonical State: NEEDS_INFO
Target Task: `TASK-M6C.1`

## Execution Result

The corrected live Websearch seam is implemented. With `TRANSPORT_WEBSEARCH_DECOUPLED=true`, `ToolExecutor` no longer coerces `system.websearch` provider/model arguments. It forwards a private runtime-context object to `backend.tool_registry:websearch_wrapper`, where the equivalent legacy policy is applied immediately before the consumed Websearch service call. With the flag unset or false, the existing executor policy remains active.

The earlier blocked candidate is superseded only with respect to its non-consuming file cluster. The flat `backend/services/websearch.py` module remains unchanged.

## Changed Product Files

- `backend/services/tool_executor.py`
- `backend/tool_registry.py`
- `backend/tests/test_backlog_007_tool_routing_performance.py`
- `backend/tests/tools/test_websearch.py`

## Automated Evidence

Auto-Verification:
- Status: PASS
- `python -m py_compile backend/services/tool_executor.py backend/tool_registry.py`: PASS.
- Focused pytest policy and transport boundary set: PASS (`6 passed in 0.79s`). It proves the default-off Gemini legacy paths, flag-on context forwarding without raw provider/model injection, wrapper-boundary Gemini coercion, and unchanged treatment of a rejected cross-provider forced selection.
- Broader focused Websearch selection: PASS (`111 passed, 6 deselected`); the preserved legacy behavior leaves a rejected cross-provider forced selection unchanged rather than selecting a substitute provider.
- `git diff --check`: PASS.

## Manual Janus Validation Gate:

- Status: PASS
- Test Example: From `C:\KI\Janus-M6-Transport-Prep`, set `$env:TRANSPORT_WEBSEARCH_DECOUPLED = "true"`, run `npm run start-dev`, then ask a current-information request that invokes Websearch, for example: `Wie ist das Wetter in Berlin?`
- Expected Result: a normal source-backed Websearch answer is rendered; no empty bubble, raw tool JSON, or provider/model compatibility error appears.
- Evidence: `2026-07-13 18:22 +02:00`, Gemini `gemini-3.1-pro-preview` returned a normal Open-Meteo-backed Berlin weather answer. No empty bubble, raw tool JSON, or provider/model error was reported.
- If Failed: route to janus-debug
- If Passed: route to janus-final-audit

## Cursor-First Evidence

- Shared delegation wrapper remained non-viable because it forwards unsupported `--cursor-pool`.
- Direct Cursor worker package validation passed, but the worker timed out after 180 seconds and left an unverified candidate.
- Codex inspected and reverted that candidate, corrected the actual live seam through task breakdown and precheck, then completed this bounded execution locally with focused evidence.

NEXT_SKILL_HANDOFF
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: `documentation/tasks/TASK-M6_transport_phase_c.md`; `documentation/tasks/TASK-M6C.1_task_breakdown.md`; `documentation/tasks/TASK-M6C.1_preimplementation_check.md`; this execution result
Evidence Paths: `backend/services/tool_executor.py`; `backend/tool_registry.py`; `backend/tests/test_backlog_007_tool_routing_performance.py`; `backend/tests/tools/test_websearch.py`; `documentation/codex/model-routing/cursor-worker-runs/WF-M6C1-CURSOR-20260713-R1/`; `documentation/codex/model-routing/cursor-worker-runs/WF-M6C1-CURSOR-20260713-R3/`
Failure Code: N/A
Changed Files: `backend/services/tool_executor.py`; `backend/tool_registry.py`; `backend/tests/test_backlog_007_tool_routing_performance.py`; `backend/tests/tools/test_websearch.py`; `documentation/tasks/TASK-M6C.1_execution_result.md`; `documentation/ai/CURRENT_STATE.md`; `documentation/codex/SKILL_USAGE_LOG.md`
Decision: HANDOFF
Reason: automated and enabled-path manual evidence are PASS; final audit is required before documentation synchronization
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no
Next User Action: review the final-audit outcome; no additional manual T-C1 test is pending
Copy Prompt: TASK-M6C.1 automated and manual enabled-path Websearch evidence is PASS. Use the bound audit package for janus-final-audit; route to janus-documentation-update only on PASS or PASS WITH FIXES.
```

## Notes

No additional notes provided.

## Risks

Provider/model policy is live-tool dispatch logic. Flag-off and enabled-path evidence are required; no provider gateway, transport, schema, or Websearch-service implementation change is in scope.

## Open Issues

None for T-C1. T-C2 through T-C4 remain intentionally deferred Phase-C tasks.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.1_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
