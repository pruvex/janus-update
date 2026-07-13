# PREIMPLEMENTATION CHECK - TASK-M6C.4

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6C.4`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6C.4_provider_tool_id_parity.md`
- Spec: `documentation/SPEC/M6C4_provider_tool_id_parity.md`
- Backlog Item: `N/A WITH REASON` (approved Phase-C test-only continuation)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. Add one new hermetic test module only.
- Scope boundary: PASS. No product source, provider call, credential, network, transport, streaming, or tool-execution change.
- Risk: LOW. Assertions use the existing ToolCallAdapter contract for two selected canonical IDs only.
- Test surface: PASS. Existing adapter regression module supplies direct contract protection.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6C.4
Target Subtask: N/A
Task: documentation/tasks/TASK-M6C.4_provider_tool_id_parity.md
Spec: documentation/SPEC/M6C4_provider_tool_id_parity.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Add only backend/tests/test_provider_parity.py with hermetic OpenAI/Gemini canonical ID roundtrip parity for system.weather and system.websearch.
- Do not change product source or claim whole-catalog parity.
Affected Files:
- backend/tests/test_provider_parity.py
- backend/tests/test_tool_call_adapter.py
Evidence Focus:
- python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py -q
- python -m py_compile backend/tests/test_provider_parity.py
- git diff --check
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No product source or scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py -q
- python -m py_compile backend/tests/test_provider_parity.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- C4 two-skill parity Spec and existing ToolCallAdapter contract
Drop Context:
- C3 inventory and previous M6 delivery history
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
User Action: Codex may run the bounded test-only execution slice.
