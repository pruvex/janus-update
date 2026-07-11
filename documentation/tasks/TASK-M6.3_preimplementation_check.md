PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.3
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound scope is atomic: extract only the provider-neutral part of OpenAI's existing `_run_full_tool_loop` behind `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=false`; do not migrate Gemini or streaming.
- The actual source confirms one bounded seam: `OpenAIGateway.reason_and_respond` dispatches the full loop only when `tool_results is None`, and `_run_full_tool_loop` currently owns MoA selection, filtered tools, prevalidation, round iteration, tool execution, and second-call history preparation.
- Responsibility boundary is explicit: `ToolLoopRunner` may own model resolution, tool filtering/definition preparation, prevalidation, round iteration, executor invocation, history preparation, and max-round handling. The gateway retains forced-tool fallback construction, prompt/synthesis decisions, routing guards, link repair, cost accumulation/persistence, and final response shaping.
- The default-off flag is implementable in the direct OpenAI gateway seam and must be in-process testable; no global configuration migration is authorized.
- OpenRouter precheck review was selected but returned `OPENROUTER_WORKER_DRY_RUN_READY`; no delegated live review occurred and Codex remains final precheck authority.
- Risk is HIGH because a misplaced extraction can alter forced-tool fallback, MoA synthesis, cost accounting, or history semantics. The Spec and task breakdown define the boundary sufficiently for one execution slice.
Affected Files:
- backend/llm_providers/shared/tool_loop_runner.py
- backend/llm_providers/openai/gateway.py
- backend/tests/test_openai_tool_loop_runner.py
- backend/tests/test_backlog_007_tool_routing_performance.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_openai_tool_loop_runner.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- focused existing OpenAI gateway regression selected during execution
- python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py
- git diff --check -- backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py backend/tests/test_openai_tool_loop_runner.py backend/tests/test_backlog_007_tool_routing_performance.py
Scope-Regel:
- Implement only TASK-M6.3. No Gemini migration, streaming migration, transport classes, runtime resolver, OAuth, OpenRouter product behavior, ToolCallAdapter change, websearch-policy change, provider-policy change, MoA hierarchy change, default-on flag, or global configuration migration.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_openai_tool_loop_runner.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- python -m py_compile backend/llm_providers/shared/tool_loop_runner.py backend/llm_providers/openai/gateway.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6_transport_phase_a.md
- documentation/tasks/TASK-M6.3_task_breakdown.md
- backend/llm_providers/openai/gateway.py
- backend/llm_providers/shared/utils.py
- backend/llm_providers/shared/moa.py
- backend/tests/test_backlog_007_tool_routing_performance.py
Drop Context:
- Completed TASK-M6.1 and TASK-M6.2 execution history
- Gemini migration, streaming migration, transport classes, runtime resolver, OAuth, OpenRouter, and websearch-policy work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Reason: TASK-M6.3 has one explicit OpenAI loop seam, an approved default-off boundary, named files, a provider-neutral responsibility matrix, and focused flag-off/flag-on evidence requirements. The only external review selection was a documented OpenRouter dry-run; Codex retains execution acceptance authority.
User Action: Say `ok` to start implementation of TASK-M6.3 in the clean M6 worktree.
