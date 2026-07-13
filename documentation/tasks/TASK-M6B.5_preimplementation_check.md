PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.5
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement one reversible Phase-B flag-on path for the existing direct `openai` provider only. `TRANSPORT_LAYER_ENABLED` is false by default; absent/false continues the exact existing silo dispatch.
- At the gateway router, resolve the provider and inject `OpenAICompatTransport` only when the flag is true, the provider is `openai`, and the selected OpenAI gateway exposes its existing service. The OpenAI gateway consumes the optional transport only for current service-level request and second-call-history seams.
- The existing gateway keeps provider access policy, skill selection, MoA/tool-loop policy, synthesis, response shaping, cost persistence, and streaming ownership. OpenRouter has resolver metadata but no direct runtime gateway silo and stays excluded.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/openai/gateway.py
- backend/tests/test_transport_layer_openai_gateway.py
- backend/tests/test_runtime_llm.py (only if required to assert the new flag boundary)
Evidence Focus:
- python -m pytest backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_runtime_llm.py
- git diff --check
Scope-Regel:
- Implement only the direct OpenAI flag-gated transport injection. No OpenRouter routing, Gemini/Google/Ollama/Codex enablement, transport-contract expansion, provider fallback, credential retrieval, streaming, Websearch, policy migration, legacy removal, or dashboard/documentation closure.
Automated Evidence Gate:
- python -m pytest backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_runtime_llm.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/openai/gateway.py backend/tests/test_transport_layer_openai_gateway.py backend/tests/test_runtime_llm.py
- git diff --check
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Phase-B T-B6, TASK-M6B.5, user-locked first-provider decision, task-breakdown handoff, and current direct OpenAI gateway seam verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle.
Keep Context:
- documentation/tasks/TASK-M6B.5_decision_summary.md
- documentation/tasks/TASK-M6B.5_task_breakdown.md
- backend/services/llm_gateway.py and backend/llm_providers/openai/gateway.py
- focused flag-off/flag-on regression commands
Drop Context:
- completed M6B.1-M6B.4 audit history
- Ollama BACKLOG-125 through BACKLOG-128 recovery details
- later multi-provider rollout and Phase-C work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first bounded implementation candidate, Codex-owned review/validation, then a manual default-off and enabled OpenAI smoke gate.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: This is the first live, flag-gated provider integration; the scope is restricted to one direct provider path and requires strict legacy-path preservation.
User Action: Authorize only the bounded Cursor-first TASK-M6B.5 execution slice.
