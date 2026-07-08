PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-MEM-M1.1
Target Subtask: N/A
Task: documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: implement Memory Phase A Hot-Layer-Caps and Phase B On-Demand Memory Injection as one guarded retrieval slice with explicit flag-off parity, protected health slots, and no Session-Search/Frozen-Core expansion.
- Artifact identity is consistent across the Memory spec sections 4 and 5, the roadmap M1 Memory A+B entry, the compiled task artifact `documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md`, and the released handoff `documentation/tasks/TASK-MEM-M1.1_task_breakdown.md`.
- The affected file cluster is concrete and intentionally bounded to memory retrieval/injection services, config/observability support, and focused memory regression tests.
- Risk is MEDIUM because this slice changes live memory-injection behavior and core-slot budgeting, but it remains bounded by feature flags and explicit medical/health safety constraints.
Affected Files:
- backend/services/memory/retrieval_service.py
- backend/services/memory_budget.py
- backend/services/memory_observability.py
- backend/services/chat_orchestrator.py
- backend/services/orchestrator/intent_engine.py
- backend/tests/test_memory_hot_layer_cap.py
- backend/tests/test_memory_on_demand_injection.py
- backend/tests/test_memory_diamond.py
- backend/tests/test_memory_regression.py
- backend/tests/test_memory_tools.py
- backend/tests/test_memory_retrieval_relevance_priority.py
Evidence Focus:
- python -m pytest backend/tests/test_memory_hot_layer_cap.py -v
- python -m pytest backend/tests/test_memory_on_demand_injection.py -v
- python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q
- python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py
- git diff --check -- backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py backend/services/orchestrator/intent_engine.py backend/tests/test_memory_hot_layer_cap.py backend/tests/test_memory_on_demand_injection.py documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md documentation/tasks/TASK-MEM-M1.1_task_breakdown.md documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_memory_hot_layer_cap.py -v
- python -m pytest backend/tests/test_memory_on_demand_injection.py -v
- python -m pytest backend/tests/test_memory_diamond.py backend/tests/test_memory_regression.py backend/tests/test_memory_tools.py backend/tests/test_memory_retrieval_relevance_priority.py -q
- python -m py_compile backend/services/memory/retrieval_service.py backend/services/memory_budget.py backend/services/memory_observability.py backend/services/chat_orchestrator.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- documentation/tasks/TASK-MEM-M1.1_task_breakdown.md
- backend/services/memory/retrieval_service.py
- backend/services/chat_orchestrator.py
Drop Context:
- sealed Intent M1 implementation details except the explicit Recall caveat
- Session-Search, Frozen Core, and USER.md export phases
- Transport, OAuth, OpenRouter, and delegation hardening work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The MA/MB slice is now precheck-ready as one bounded memory retrieval/injection hardening block with explicit flag, health-safety, and regression evidence gates.
User Action: Say `ok` to start implementation of `TASK-MEM-M1.1` with the bound scope and evidence gate above.
