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
