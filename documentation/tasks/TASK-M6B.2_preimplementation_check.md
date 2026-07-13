PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6B.2
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_b.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement only the Phase-B T-B3 thin Gemini-native transport wrapper over the existing Gemini service seam.
- Execution is Cursor-first and bounded to the two transport files and one new hermetic test; Codex reviews the allowlisted diff and evidence on 5.6 Terra/high.
- The existing Gemini service remains the authority for native proto/schema/history conversion, tool adaptation, and request/response semantics. No caller is rerouted and `TRANSPORT_LAYER_ENABLED` remains default-off and unconsumed.
Affected Files:
- backend/llm_providers/transports/gemini_native.py
- backend/llm_providers/transports/__init__.py
- backend/tests/test_gemini_native_transport.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_gemini_native_transport.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/gemini_native.py
- focused existing Gemini service and ToolCallAdapter regressions selected by the executioner
- git diff --check and scoped review against the exclusions below
Scope-Regel:
- Implement only TASK-M6B.2. No change to Gemini service/gateway, ToolLoopRunner, ToolCallAdapter, runtime resolver, llm_gateway, execution engine, native proto/schema/history behavior, model/Flash policy, grounding/cost attribution, synthesis/drill-down, streaming, provider fallback, resolver/gateway integration, or TRANSPORT_LAYER_ENABLED consumer/flip.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_gemini_native_transport.py -q
- python -m py_compile backend/llm_providers/transports/__init__.py backend/llm_providers/transports/gemini_native.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified. `TASK-M6B.1` is independently closed; `TASK-M6B.2` is the unique next target in the same approved Phase-B task artifact.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. This task changes no TestSpec or oracle; the named transport test is a source-owned focused regression.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_b.md
- documentation/tasks/TASK-M6B.2_task_breakdown.md
- backend/llm_providers/shared/base_transport.py and backend/llm_providers/gemini/service.py as read-only contract/service seams
Drop Context:
- completed M6B.1 implementation/audit history
- later M6B.3 through M6B.5 tasks
- unrelated ChromaDB-dependent suites and Git/release history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Cursor-first implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: The one-wrapper scope, three-file allowlist, binary acceptance criteria, and hermetic evidence are explicit; Gemini-native behavior stays delegated to the existing service.
User Action: Start only the bounded Cursor-first TASK-M6B.2 execution slice and return the candidate diff and focused evidence for Codex review.
