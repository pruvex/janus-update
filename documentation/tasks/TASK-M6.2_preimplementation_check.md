PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.2
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound scope is atomic: Phase-A T-A2 moves existing canonical-to-provider tool-name and schema handling into one shared ToolCallAdapter without extracting a tool loop or adding a transport class.
- The current sources prove the required seam: ToolManager globally rewrites canonical names for Gemini, OpenAI rewrites dots for API calls, and Gemini owns sanitization plus inbound restoration. The adapter is absent, so this is a new bounded extraction rather than a rewrite of an existing shared layer.
- Existing executor alias fallback remains explicitly out of scope and is retained as a compatibility regression.
- OpenRouter precheck review was selected but the installed lane returned `OPENROUTER_WORKER_DRY_RUN_READY`; no delegated live review was performed and Codex remains the final precheck authority.
- Risk is HIGH because forced tools, Gemini function-call history, and canonical execution routing can regress if names are adapted at the wrong boundary. The approved Spec and task breakdown fully define the architecture and acceptance boundary.
Affected Files:
- backend/llm_providers/shared/tool_call_adapter.py
- backend/services/tool_manager.py
- backend/llm_providers/openai/service.py
- backend/llm_providers/gemini/service.py
- backend/llm_providers/shared/utils.py
- backend/tests/test_tool_call_adapter.py
- backend/tests/test_tool_name_aliasing.py
- backend/tests/test_backlog_007_tool_routing_performance.py
- backend/tests/llm_providers/test_openai_service.py
- backend/tests/llm_providers/test_gemini_service.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_tool_call_adapter.py -q
- python -m pytest --noconftest backend/tests/test_tool_name_aliasing.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- python -m pytest --noconftest backend/tests/llm_providers/test_openai_service.py -q
- python -m pytest --noconftest backend/tests/llm_providers/test_gemini_service.py -q
- focused prevalidation regression selected from backend/llm_providers/shared/utils.py during execution
- python -m py_compile backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/gemini/service.py backend/llm_providers/shared/utils.py
- git diff --check -- backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/gemini/service.py backend/llm_providers/shared/utils.py backend/tests/test_tool_call_adapter.py backend/tests/test_tool_name_aliasing.py backend/tests/test_backlog_007_tool_routing_performance.py backend/tests/llm_providers/test_openai_service.py backend/tests/llm_providers/test_gemini_service.py
Scope-Regel:
- Implement only TASK-M6.2. No ToolLoopRunner, transport classes, runtime resolver, streaming migration, OAuth, OpenRouter product path, websearch policy change, feature flag, MoA hierarchy change, or executor alias-fallback removal.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_tool_call_adapter.py -q
- python -m pytest --noconftest backend/tests/test_tool_name_aliasing.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- python -m pytest --noconftest backend/tests/llm_providers/test_openai_service.py -q
- python -m pytest --noconftest backend/tests/llm_providers/test_gemini_service.py -q
- python -m py_compile backend/llm_providers/shared/tool_call_adapter.py backend/services/tool_manager.py backend/llm_providers/openai/service.py backend/llm_providers/gemini/service.py backend/llm_providers/shared/utils.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.2_task_breakdown.md
- backend/services/tool_manager.py
- backend/llm_providers/openai/service.py
- backend/llm_providers/gemini/service.py
- backend/llm_providers/shared/utils.py
- backend/tests/test_tool_name_aliasing.py
- backend/tests/test_backlog_007_tool_routing_performance.py
- backend/tests/llm_providers/test_openai_service.py
- backend/tests/llm_providers/test_gemini_service.py
Drop Context:
- Completed TASK-M6.1 implementation and audit history
- Phase-A tasks T-A3 through T-A5
- Transport classes, runtime resolver, OAuth, OpenRouter, streaming, and websearch policy work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Reason: TASK-M6.2 has one explicit adapter boundary, named consumers, preserved compatibility guards, concrete focused evidence, and no remaining product or architecture decision.
User Action: Say `ok` to start implementation of TASK-M6.2 in the clean M6 worktree.
