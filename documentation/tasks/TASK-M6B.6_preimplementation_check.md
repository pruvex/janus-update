# PREIMPLEMENTATION CHECK - TASK-M6B.6

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6B.6`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6_transport_phase_b.md`
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6)
- Decision Summary: `documentation/tasks/TASK-M6B.6_decision_summary.md`
- Backlog Item: `N/A WITH REASON` (approved Phase-B task continuation, not a Backlog item)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. The task adds one direct `gemini` transport injection behind the existing default-off `TRANSPORT_LAYER_ENABLED` flag.
- Scope boundary: PASS. Only `GeminiGateway._run_simple_tool_loop` receives the injected seam. Engine-owned Gemini and drill-down stay on their current service seams; no direct `google` gateway route exists or is created.
- Product decisions: PASS. The operator selected normal Gemini tool-loop only; no unresolved provider, fallback, credential, or architecture decision remains.
- Risk: MEDIUM. The change touches a live provider dispatch seam, but the default is false and tests can prove both routing states and exclusions hermetically.
- Test surface: PASS. Focused flag routing/injection tests plus existing Gemini runner coverage are available without credentials or network access.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.6
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Inject GeminiNativeTransport only when TRANSPORT_LAYER_ENABLED is true and the existing direct gemini silo is selected.
- Pass the transport only into the normal _run_simple_tool_loop request and second-call-history seams.
- Keep engine-owned Gemini, drill-down, Google, OpenRouter, Ollama, Codex, streaming, model policy, grounding, cost attribution, synthesis, and response shaping unchanged.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_transport_layer_gemini_gateway.py
Evidence Focus:
- python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/gemini/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_transport_layer_gemini_gateway.py backend/tests/test_gemini_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound Phase-B T-B6 task and locked normal-loop-only decision
- direct gemini silo and GeminiGateway service/history seams
- focused regression commands
Drop Context:
- old failed drafts
- unrelated provider rollouts, backlog work, and audit history
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
User Action: Codex continues with the bounded Cursor-first execution slice; manual validation is requested only after automated evidence passes.
