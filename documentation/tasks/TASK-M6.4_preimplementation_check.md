PRE-CHECK RESULT
PRE-CHECK PASSED

legacy handoff start
NEXT: janus-executioner
Target Task: TASK-M6.4
Target Subtask: N/A
Task: documentation/tasks/TASK-M6_transport_phase_a.md
Spec: documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound scope is atomic: migrate only Gemini `_run_simple_tool_loop` through the default-off shared runner boundary defined in Spec Section 3.3.2.
- Gemini retains visible override/Flash-default policy, list-query round policy, grounding metadata/query-cost accounting, request attribution, native history bridge, routing guards, synthesis, preserved metadata, engine-owned handling, and drill-down paths.
- The runner receives only gateway-owned resolved model/MoA state, effective max rounds, and generic per-response facts; no Gemini policy is added to the runner.
- OpenRouter precheck review was selected but returned `OPENROUTER_WORKER_DRY_RUN_READY`; no delegated live review occurred and Codex remains final precheck authority.
- Risk is HIGH because Flash-default websearch, grounding/cost attribution, or native history behavior can regress if ownership crosses the boundary.
Affected Files:
- backend/llm_providers/gemini/gateway.py
- backend/llm_providers/shared/tool_loop_runner.py
- backend/tests/test_gemini_tool_loop_runner.py
- backend/tests/test_backlog_007_tool_routing_performance.py
Evidence Focus:
- python -m pytest --noconftest backend/tests/test_gemini_tool_loop_runner.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- focused Gemini grounding/cost-attribution regression selected during execution
- python -m py_compile backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/tool_loop_runner.py
Scope-Regel:
- Implement only TASK-M6.4. No OpenAI behavior change, streaming migration, engine-owned/drill-down migration, transport classes, runtime resolver, OAuth, OpenRouter product behavior, ToolCallAdapter change, provider-policy change, or MoA hierarchy change.
Automated Evidence Gate:
- python -m pytest --noconftest backend/tests/test_gemini_tool_loop_runner.py -q
- python -m pytest --noconftest backend/tests/test_backlog_007_tool_routing_performance.py -q
- python -m py_compile backend/llm_providers/gemini/gateway.py backend/llm_providers/shared/tool_loop_runner.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and task-breakdown handoff verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/PROVIDER_TRANSPORT_REFACTOR_SPEC.md
- documentation/tasks/TASK-M6.4_task_breakdown.md
- backend/llm_providers/gemini/gateway.py
- backend/llm_providers/shared/tool_loop_runner.py
Drop Context:
- completed M6.1 through M6.3 history; streaming, engine-owned, drill-down, and transport resolver work
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.
legacy handoff end

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
Reason: TASK-M6.4 has an explicit Gemini gateway-owned policy/observability boundary, named files, high-risk focused evidence, and no remaining architecture decision.
User Action: Say `ok` to start implementation of TASK-M6.4 in the clean M6 worktree.
