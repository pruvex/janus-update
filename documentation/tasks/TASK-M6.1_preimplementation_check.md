PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.1
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound scope is atomic: Phase A T-A1 only consolidates the existing model hierarchy into `MOA_MODEL_HIERARCHY` and adds a drift regression.
- The approved Spec mapping preserves active behavior: OpenAI `balanced=gpt-5.4-mini`, Gemini `vision=gemini-3-flash-preview` and `logic=gemini-3-pro-preview`, plus the current Ollama tiers including `fast`.
- Repository scan found exactly two hierarchy definitions. Existing MoA readers in debug and execution-dispatch paths do not introduce additional definitions.
- Risk is HIGH because model-tier selection and provider fallback are central behavior, but the scope is bounded by the approved verbatim mapping, default behavior preservation, and a dedicated drift regression.
Affected Files:
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_model_hierarchy_single_source.py
- backend/tests/test_moa_routing.py
Evidence Focus:
- python -m pytest backend/tests/test_model_hierarchy_single_source.py -q
- python -m pytest backend/tests/test_moa_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py
- git diff --check -- backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py backend/tests/test_model_hierarchy_single_source.py documentation/tasks/TASK-M6_transport_phase_a.md documentation/tasks/TASK-M6.1_task_breakdown.md documentation/tasks/TASK-M6.1_preimplementation_check.md
Scope-Regel:
- Implement only TASK-M6.1. Preserve the approved mapping exactly; no ToolCallAdapter, ToolLoopRunner, streaming, transport class, OAuth, OpenRouter, websearch, feature-flag, or provider-policy expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_model_hierarchy_single_source.py -q
- python -m pytest backend/tests/test_moa_routing.py -q
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m py_compile backend/llm_providers/shared/moa.py backend/services/chat_orchestrator.py backend/llm_providers/gemini/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, task-breakdown handoff, and approved Spec review metadata verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.1_task_breakdown.md
- backend/llm_providers/shared/moa.py
- backend/services/chat_orchestrator.py
- backend/llm_providers/gemini/gateway.py
- backend/tests/test_moa_routing.py
Drop Context:
- Phase-A tasks T-A2 through T-A5
- Phase-B/C transport work
- OAuth, OpenRouter, websearch, and unrelated mixed-worktree history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Reason: The approved mapping removes the only architecture ambiguity. TASK-M6.1 is now a bounded high-risk consolidation with concrete consumers, explicit exclusions, and focused regression gates.
User Action: Say `ok` to start implementation of TASK-M6.1 in the clean M6 worktree.
