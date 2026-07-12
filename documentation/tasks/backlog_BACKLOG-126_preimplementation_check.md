PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: BACKLOG-126
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-126_ollama_atomic_tool_handoff.md
Spec: N/A WITH REASON - confirmed existing gateway tool-handoff bug with bounded service routing correction.
Backlog Item: BACKLOG-126
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only Ollama tool-definition and force-tool forwarding from llm_gateway into OllamaGateway for the atomic weather path.
- Add focused gateway and agent-factory regressions proving system.weather reaches the provider with tools and the text-only exit is not accepted for the bound forced-tool path.
Affected Files:
- backend/services/llm_gateway.py
- backend/llm_providers/ollama/gateway.py
- backend/tests/test_agent_factory_runtime.py
- backend/tests/llm_providers/test_ollama_gateway.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_agent_factory_runtime.py backend/tests/llm_providers/test_ollama_gateway.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/ollama/gateway.py
- git diff --check
Scope-Regel:
- Implement only BACKLOG-126. No BACKLOG-125 service change, M6B.3 transport integration, resolver, provider fallback, endpoint/capability policy, feature-flag consumer/flip, or unrelated agent-loop redesign.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_agent_factory_runtime.py backend/tests/llm_providers/test_ollama_gateway.py -q
- python -m py_compile backend/services/llm_gateway.py backend/llm_providers/ollama/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- BACKLOG-126, selected handoff, debug result, llm_gateway force-tool condition, and Ollama gateway validated-tool seam verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle.
Keep Context:
- BACKLOG-126 handoff and debug result
- backend/services/llm_gateway.py
- backend/llm_providers/ollama/gateway.py
Drop Context:
- BACKLOG-125 service fix
- M6B.3 transport work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The live trace and Cursor review bind the two gateway seams and focused regressions.
User Action: Authorize only the bounded Cursor-first BACKLOG-126 execution slice.
