# PREIMPLEMENTATION CHECK - TASK-M6C.2

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6C.2`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6C.2_response_postprocessors.md`
- Spec: `documentation/SPEC/Spec Done/M6C2_response_postprocessor_extraction.md`
- Backlog Item: `N/A WITH REASON` (approved Phase-C continuation is bound by the parent transport-refactor Spec and a reviewed C2 delta Spec)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. C2 extracts only the existing OpenAI release-list link repair and Gemini grounding/link rendering into a shared response-postprocessor boundary.
- Ownership: PASS. The user selected Option A: `backend/services/llm_gateway.py:reason_and_respond` invokes the registry after the selected provider silo returns.
- Scope boundary: PASS. Gateway-owned quality, cost, and synthesis behavior stay in the provider gateways; Websearch policy, fallback, model policy, transports, tool execution, streaming, persistence, UI, T-C3, and T-C4 remain excluded.
- Risk: HIGH. The router is a live cross-provider seam and must preserve the provider response contract, including optional Gemini metadata.
- Test surface: PASS. A new hermetic registry test module covers both migrated behaviors, missing metadata, and unregistered providers. Existing focused transport gateway tests protect the selected OpenAI/Gemini gateway seams.
- Cursor-first execution: PASS. The bounded package is ready for Cursor-assisted implementation; a local bounded fallback is permitted only if Cursor cannot execute the package.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6C.2
Target Subtask: N/A
Task: documentation/tasks/TASK-M6C.2_response_postprocessors.md
Spec: documentation/SPEC/Spec Done/M6C2_response_postprocessor_extraction.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only C2: shared OpenAI release-list link repair and Gemini grounding/link rendering after the selected provider silo returns.
- Central invocation owner is backend/services/llm_gateway.py:reason_and_respond. Do not move gateway-owned quality, cost, or synthesis logic.
- Preserve the existing response contract; missing optional metadata and unregistered provider families must leave the response unchanged.
- Keep Websearch policy, provider fallback, model policy, transports, tool execution, streaming, persistence, UI, T-C3, and T-C4 unchanged.
Affected Files:
- backend/llm_providers/shared/response_postprocessors.py
- backend/services/llm_gateway.py
- backend/llm_providers/openai/gateway.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_response_postprocessors.py
- backend/tests/test_transport_layer_openai_gateway.py
- backend/tests/test_transport_layer_gemini_gateway.py
Evidence Focus:
- python -m pytest backend/tests/test_response_postprocessors.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_transport_layer_gemini_gateway.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/response_postprocessors.py
- git diff --check
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_response_postprocessors.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_transport_layer_gemini_gateway.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/response_postprocessors.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- approved C2 delta Spec and user-selected central router ownership
- direct OpenAI release-list link repair and Gemini metadata/link behavior
- provider response contract and hermetic regression boundary
Drop Context:
- completed Phase-A and Phase-B delivery history
- Phase-C T-C1 details and later T-C3/T-C4 work
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
User Action: Codex may run the bounded Cursor-first execution slice; request manual provider validation only after automated evidence passes.
