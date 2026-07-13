# AUDIT_PACKAGE

Generated: 2026-07-13 19:07:49 UTC

## Goal

Audit TASK-M6C.4 OpenAI/Gemini canonical tool-ID parity coverage

## Scope Rules

- Audit the provided package and changed artifacts only.
- Do not rely on development chat history.
- Verify cost, caching, skill quality, safety scope, and validation evidence.
- On re-audit, review the blocker delta first before widening scope.
- If scoped paths were provided, treat them as the audit diff boundary.

## Bound Audit Inputs

- Spec: APPROVED C4 Spec; parent M6 Phase-C remains active
- Task File: documentation\tasks\TASK-M6C.4_provider_tool_id_parity.md
- Backlog Item: N/A WITH REASON: approved Phase-C test-only continuation
- Pre-Implementation Check: documentation\tasks\TASK-M6C.4_preimplementation_check.md
- Manual Janus Evidence: N/A WITH REASON: test-only coverage; no product runtime behavior changed.
- Pipeline Completion Status: Implementation complete; focused automated evidence PASS.

## Backlog Item

```text
N/A WITH REASON - No backlog source or marker provided.
```

## Task Acceptance Scope

```text
TASK-M6C.4
- Source Spec: `documentation/SPEC/M6C4_provider_tool_id_parity.md`
- Backlog Item: `N/A`
- Feature: Epic 4 Provider Transport Refactor, Phase C Tool-ID Parity
- Generated At: 2026-07-13

## Generated Tasks

### TASK-M6C.4 Add hermetic OpenAI/Gemini canonical tool-ID parity coverage
- Ziel:
  - Add one hermetic regression module proving canonical tool-ID roundtrip parity for `system.weather` and `system.websearch`.
- Scope:
  - Assert OpenAI and Gemini outbound names are provider-safe and equal for the two selected canonical IDs.
  - Assert each provider adapter restores the provider-safe names to the original canonical IDs.
  - Preserve all product source behavior; this slice adds tests only.
- Files:
  - `backend/tests/test_provider_parity.py` (new)
  - `backend/tests/test_tool_call_adapter.py` (existing regression selection only)
- Steps:
  1. Express the approved two-skill matrix as parameterized hermetic assertions.
  2. Check outbound provider-safe naming and inbound canonical restoration for both providers.
  3. Run the new suite with the existing adapter regression module and scoped diff validation.
- Acceptance Criteria:
  - `system.weather` has OpenAI/Gemini canonical roundtrip parity.
  - `system.websearch` has OpenAI/Gemini canonical roundtrip parity.
  - The new suite requires no network access or provider credentials.
  - No non-test product source file changes.
- Tests:
  - `python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py -q`
  - Syntax and scoped diff checks selected by preimplementation check.
- Model: 5.6 Terra
- Reason:
  - The approved C4 Spec defines one small, binary test-only parity slice with no runtime provider authority.
```

## Pre-Implementation Check

```text
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
```

## Changed Files

```text
?? backend/tests/test_provider_parity.py
?? documentation/tasks/TASK-M6C.4_execution_result.md
```

## Artifact Inventory

```text
FILE C:\KI\Janus-M6-Transport-Prep\backend\tests\test_provider_parity.py (651 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.4_execution_result.md (1323 bytes)
FILE C:\KI\Janus-M6-Transport-Prep\documentation\SPEC\M6C4_provider_tool_id_parity.md (4137 bytes)
```

## Diff Summary

```text
No diff stat available.
```

## Validation

```text
# TASK EXECUTION RESULT - TASK-M6C.4

Canonical State: HANDOFF
Target Task: TASK-M6C.4

Changed Files:
- `backend/tests/test_provider_parity.py`

Executed Checks:
- `python -m pytest backend/tests/test_provider_parity.py backend/tests/test_tool_call_adapter.py -q` — PASS (`14 passed`).
- `python -m py_compile backend/tests/test_provider_parity.py` — PASS.
- `git diff --check` — PASS.

Auto-Verification:
- Status: PASS
- Evidence: each selected canonical ID has OpenAI/Gemini provider-safe outbound parity and canonical inbound roundtrip coverage.

Manual Janus Validation Gate:
- Status: N/A WITH REASON
- Test Example: N/A.
- Expected Result: N/A; the slice changes hermetic regression coverage only and does not alter Janus product runtime behavior.
- If Failed: route to janus-debug.
- If Passed: route to janus-final-audit.

NEXT_STEP
Target Skill: janus-final-audit
Canonical State: HANDOFF
Required Artifacts: C4 Spec, task, precheck, execution result, focused test evidence.
Evidence Paths: `documentation/tasks/TASK-M6C.4_preimplementation_check.md`; focused pytest command.
Failure Code: N/A
Decision: test-only execution complete.
Reason: all bounded automated evidence passed.
Recommended Model: 5.6 Terra
Recommended Intelligence: high
New Chat: no
Next User Action: none until audit or Git approval.
```

## Notes

No additional notes provided.

## Risks

Covers only system.weather and system.websearch, not whole-catalog provider parity.

## Open Issues

Parent T-C3 branch cleanup remains open; Phase C remains active.

## Re-Audit Delta

No re-audit delta provided.

## Final Audit Handoff

```text
NEW_CHAT_HANDOFF
NEXT: final-skill-audit
MODEL: 5.6 Sol/high if runtime-supported; otherwise 5.6 Terra/high
PASS: C:\KI\Janus-M6-Transport-Prep\documentation\tasks\TASK-M6C.4_AUDIT_PACKAGE.md
ASK: Lade nur dieses Paket im neuen Chat und starte dann den Final Audit.
DROP: dev chat history
```

Use `5.6 Sol/high` when the current Codex run can start it; if Codex reports `gpt-5.6-sol` is unsupported for the active ChatGPT account, use `5.6 Terra/high` and record `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT`.

For bounded same-thread re-audits after a local blocker fix, `5.6 Terra/high` is acceptable when the package stays compact and the risk did not escalate.
