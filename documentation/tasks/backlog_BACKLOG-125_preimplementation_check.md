PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: BACKLOG-125
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-125_ollama_service_gateway_kwargs_nameerror.md
Spec: N/A WITH REASON - confirmed legacy Ollama-service bug with a bounded local correction; no product decision or new feature specification is required.
Backlog Item: BACKLOG-125
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the existing Ollama-service fix for `_estimated_prompt_tokens`: consume the internal value before `request_payload.update(kwargs)`, retain it for `_await_with_deadline`, and remove both undefined `gateway_kwargs` references.
- Add a focused hermetic Ollama-service regression that exercises normal and synthesis response calls with `_estimated_prompt_tokens`; it must prove no NameError and that the internal key is not forwarded into the OpenAI-compatible request payload.
- Execution is Cursor-first, bounded to the two files below; Codex owns candidate review, all test execution, and the manual default-off local-Ollama smoke.
Affected Files:
- backend/llm_providers/ollama/service.py
- backend/tests/llm_providers/test_ollama_service.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/llm_providers/test_ollama_service.py backend/tests/llm_providers/test_ollama_adapter.py -q
- python -m py_compile backend/llm_providers/ollama/service.py
- git diff --check and scoped review against the exclusions below
Scope-Regel:
- Implement only BACKLOG-125. No change to Ollama gateway, adapter, legacy import, transport layer, ToolLoopRunner, runtime resolver, llm_gateway, endpoint/model-node policy, capability cache, native-tool fallback, retry policy, streaming behavior beyond the already-existing synthesis request, provider fallback, credential handling, feature-flag consumer/flip, or M6B.3 integration.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/llm_providers/test_ollama_service.py backend/tests/llm_providers/test_ollama_adapter.py -q
- python -m py_compile backend/llm_providers/ollama/service.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, selected handoff, debug result, and N/A-with-reason Spec binding verified. BACKLOG-125 is the unique selected service-fix target; M6B.3 remains a separate blocked audit dependency.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle; the named Ollama service and adapter tests are source-owned focused regressions.
Keep Context:
- documentation/backlog/BACKLOG.md entry BACKLOG-125
- documentation/tasks/backlog_BACKLOG-125_ollama_service_gateway_kwargs_nameerror.md
- documentation/tasks/TASK-M6B.3_debug_result.md
- backend/llm_providers/ollama/service.py and archived Ollama service tests as read-only seams
Drop Context:
- M6B.3 transport implementation/audit history
- later M6 Phase-B work
- unrelated provider, dashboard, release, and broad backlog history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The root cause, two-file allowlist, request-payload boundary, regression seam, exclusions, and manual retest prerequisite are explicit.
User Action: Authorize only the bounded Cursor-first BACKLOG-125 execution slice and return the candidate diff plus focused evidence for Codex review.
