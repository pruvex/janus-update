PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: BACKLOG-129
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-129_gemini_stream_duplicate_tool_delta.md
Spec: N/A WITH REASON - confirmed single provider-streaming defect with a log-backed bounded correction.
Backlog Item: BACKLOG-129
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only same-response Gemini Function-Call delta deduplication before repeated identical deltas enter the first streaming tool round.
- The live trace proves one equal `system_weather` chunk is emitted twice before tool execution. The existing raw-parts history buffer already deduplicates persistence; the execution event emission is the bound correction seam.
- Preserve distinct same-name calls with different canonical arguments and preserve the existing hard-loop breaker for genuine duplicate calls after a tool round.
Affected Files:
- backend/llm_providers/gemini/service.py
- backend/tests/llm_providers/test_gemini_service.py
- backend/tests/test_execution_dispatcher_wikipedia_guard.py
- documentation/tasks/backlog_BACKLOG-129_execution_result.md
Evidence Focus:
- python -m pytest backend/tests/llm_providers/test_gemini_service.py backend/tests/test_execution_dispatcher_wikipedia_guard.py -q
- python -m py_compile backend/llm_providers/gemini/service.py
- git diff --check
Scope-Regel:
- Implement only BACKLOG-129. No change to transport-layer enablement, forced-tool selection, OpenAI or Ollama providers, tool schemas, capability policy, feature flags, planner behavior, general hard-loop-breaker semantics, provider fallback, or unrelated M6 merge conflict resolution.
Automated Evidence Gate:
- python -m pytest backend/tests/llm_providers/test_gemini_service.py backend/tests/test_execution_dispatcher_wikipedia_guard.py -q
- python -m py_compile backend/llm_providers/gemini/service.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, selected handoff, debug result, Gemini stream-emission seam, and duplicate-guard regression seam verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle; the named provider and duplicate-guard tests are source-owned focused regressions.
Keep Context:
- BACKLOG-129 handoff and debug result
- backend/llm_providers/gemini/service.py
- backend/tests/llm_providers/test_gemini_service.py
- backend/tests/test_execution_dispatcher_wikipedia_guard.py
Drop Context:
- closed M6 transport slices
- unrelated ready backlog items
- broad merge and release history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The reproduction, provider emission seam, regression boundary, and cross-round hard-loop protection are all explicit and one bounded implementation slice remains.
User Action: Authorize only the bounded BACKLOG-129 execution slice.
