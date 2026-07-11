PRE-CHECK RESULT
PRE-CHECK PASSED

NEXT: janus-executioner
Target Task: TASK-MEM-M4.1
Target Subtask: N/A
Task: documentation/tasks/TASK-MEM-M4_session_search_fts5.md
Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
Backlog Item: N/A
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic: implement Memory Phase C Session-Search as one bounded FTS5 slice with a separate `session_fts.db`, one central message-write hook, one on-demand tool, and focused episodic intent routing.
- Artifact identity is consistent across Memory Spec section 6, Roadmap section 4 M4 MC, the compiled task artifact `documentation/tasks/TASK-MEM-M4_session_search_fts5.md`, and the released handoff `documentation/tasks/TASK-MEM-M4.1_task_breakdown.md`.
- The affected file cluster is concrete and intentionally bounded to the session-search store/service/tool path, central message persistence, one skill-registration seam, one intent-routing seam, one backfill script, and focused tests.
- Risk is MEDIUM because this slice adds a new searchable memory surface and changes the message persistence path, but it remains bounded by a default-off feature flag, sanitizer reuse from `memory_tools.py`, snippet truncation, and a strict no-Frozen-Core/no-transport boundary.
Affected Files:
- backend/services/memory/session_fts_store.py
- backend/services/memory/session_search_service.py
- backend/tools/session_search_tools.py
- backend/skills/system/session_search.json
- backend/tool_registry.py
- backend/data/crud.py
- backend/services/orchestrator/intent_engine.py
- backend/scripts/backfill_session_fts.py
- backend/tests/test_session_fts_store.py
- backend/tests/test_session_search_tools.py
- backend/tests/test_memory_regression.py
Evidence Focus:
- python -m pytest backend/tests/test_session_fts_store.py -v
- python -m pytest backend/tests/test_session_search_tools.py -v
- python -m pytest backend/tests/test_memory_regression.py -q
- python -m py_compile backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py backend/data/crud.py backend/services/orchestrator/intent_engine.py backend/tool_registry.py backend/scripts/backfill_session_fts.py
- git diff --check -- backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py backend/skills/system/session_search.json backend/tool_registry.py backend/data/crud.py backend/services/orchestrator/intent_engine.py backend/scripts/backfill_session_fts.py backend/tests/test_session_fts_store.py backend/tests/test_session_search_tools.py backend/tests/test_memory_regression.py documentation/tasks/TASK-MEM-M4_session_search_fts5.md documentation/tasks/TASK-MEM-M4.1_task_breakdown.md documentation/tasks/TASK-MEM-M4.1_preimplementation_check.md documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_session_fts_store.py -v
- python -m pytest backend/tests/test_session_search_tools.py -v
- python -m pytest backend/tests/test_memory_regression.py -q
- python -m py_compile backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py backend/data/crud.py backend/services/orchestrator/intent_engine.py backend/tool_registry.py backend/scripts/backfill_session_fts.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/tasks/TASK-MEM-M4_session_search_fts5.md
- documentation/tasks/TASK-MEM-M4.1_task_breakdown.md
- backend/data/crud.py
- backend/tool_registry.py
- backend/services/orchestrator/intent_engine.py
- backend/tools/memory_tools.py
- backend/services/rag/fts_store.py
Drop Context:
- sealed M1 Memory A+B implementation details except the explicit pattern for bounded memory slices
- Frozen Core, USER.md export, Transport, OAuth, OpenRouter product work, and delegation hardening
- optional routine UI or silent routine-learning follow-up work
- unrelated dirty worktree changes
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Reason: The M4 MC slice is now precheck-ready as one bounded Session-Search FTS5 block with explicit storage, routing, sanitizer, and flag-off evidence gates.
User Action: Say `ok` to start implementation of `TASK-MEM-M4.1` with the bound scope and evidence gate above.
