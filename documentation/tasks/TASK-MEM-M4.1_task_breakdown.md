TASK BREAKDOWN RESULT
- Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- Task File: documentation/tasks/TASK-MEM-M4_session_search_fts5.md
- Target Task: TASK-MEM-M4.1
- Decision: TASK DESIGN COMPLETE
- Source Of Truth: Memory Spec section 6 plus Roadmap section 4 M4 MC. This slice is limited to Session-Search FTS5 with one separate index store, one central message-write hook, one bounded tool path, and focused episodic intent routing. It must not widen into Frozen Core (M5), USER.md export, Transport, OAuth, OpenRouter product work, or unrelated memory-policy changes.
- Files: backend/services/memory/session_fts_store.py, backend/services/memory/session_search_service.py, backend/tools/session_search_tools.py, backend/skills/system/session_search.json, backend/tool_registry.py, backend/data/crud.py, backend/services/orchestrator/intent_engine.py, backend/scripts/backfill_session_fts.py, backend/tests/test_session_fts_store.py, backend/tests/test_session_search_tools.py, backend/tests/test_memory_regression.py only if directly affected
- Tests: run `python -m pytest backend/tests/test_session_fts_store.py -v`; run `python -m pytest backend/tests/test_session_search_tools.py -v`; run `python -m pytest backend/tests/test_memory_regression.py -q`; run `python -m py_compile backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py backend/data/crud.py backend/services/orchestrator/intent_engine.py backend/tool_registry.py backend/scripts/backfill_session_fts.py`; run scoped `git diff --check` on the touched memory/task artifacts
- Execution Model: 5.6 Terra
- Readiness: Scope is atomic and precheck-ready. The slice is product-relevant because it changes message persistence, adds a new retrieval surface, and touches intent routing, but it remains bounded by a default-off flag, sanitizer reuse, and an explicit no-Frozen-Core/no-transport boundary.
- Next Skill: janus-preimplementation-check
- Model Recommendation: 5.6 Terra, medium

```text
@janus-preimplementation-check
Spec: documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
Task: documentation/tasks/TASK-MEM-M4_session_search_fts5.md
Backlog Item: N/A
Target Task: TASK-MEM-M4.1
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Terra
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
