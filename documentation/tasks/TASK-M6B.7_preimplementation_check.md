# PREIMPLEMENTATION CHECK - TASK-M6B.7

PRE-CHECK RESULT
PRE-CHECK PASSED

## Bound Identity

- Target Task: `TASK-M6B.7`
- Target Subtask: `N/A`
- Task: `documentation/tasks/TASK-M6_transport_phase_b.md`
- Spec: `documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md` (Phase-B T-B6)
- Decision Summary: `documentation/tasks/TASK-M6B.7_decision_summary.md`
- Backlog Item: `N/A WITH REASON` (approved Phase-B task continuation, not a Backlog item)
- Assigned Model: `5.6 Terra`
- Mode: `SINGLE_TASK_PRECHECK`

## Gate Decision

- Atomic scope: PASS. The task adds one direct `ollama` transport injection behind the existing default-off `TRANSPORT_LAYER_ENABLED` flag.
- Scope boundary: PASS. All direct `OllamaGateway.reason_and_respond` service requests receive the injected seam; Atomic/AgentRuntime/engine logic and tool execution ownership remain unchanged.
- Product decisions: PASS. The user explicitly selected all direct Ollama gateway calls after the Atomic discriminator was found absent.
- Risk: MEDIUM. The change touches a live local-provider dispatch seam, but default-off behavior and explicit Atomic exclusion have hermetic regression coverage.
- Test surface: PASS. Focused flag routing/injection tests plus existing gateway and Atomic weather regressions are available without a live local model.

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.7
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A WITH REASON
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Inject OllamaLocalTransport only when TRANSPORT_LAYER_ENABLED is true and the existing direct ollama silo is selected.
- Use the transport only at OllamaGateway's existing provider request seam for all direct calls.
- Keep Atomic/AgentRuntime/engine logic, tool execution ownership, tool filtering, forced-tool forwarding, budget guard, response behavior, OpenAI, Gemini, Google, OpenRouter, Codex, streaming, and fallback unchanged.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/ollama/gateway.py
- backend/tests/test_transport_layer_ollama_gateway.py
Evidence Focus:
- python -m pytest backend/tests/test_transport_layer_ollama_gateway.py backend/tests/llm_providers/test_ollama_gateway.py backend/tests/test_agent_factory_runtime.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/ollama/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_transport_layer_ollama_gateway.py backend/tests/llm_providers/test_ollama_gateway.py backend/tests/test_agent_factory_runtime.py backend/tests/test_runtime_llm.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound Phase-B T-B6 task and locked Ollama gateway-only decision
- direct ollama silo, OllamaGateway request/synthesis seam, and Atomic exclusion
- focused regression commands
Drop Context:
- old provider-rollout history
- unrelated backlog and audit artifacts
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
