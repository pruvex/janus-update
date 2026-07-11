PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-119
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-119_kontakt_beziehungsfakten_provider_und_chatuebergreifend_persistieren.md
Spec: N/A WITH REASON - small bounded backlog bugfix on the existing contact-memory persistence seam; no separate feature spec is required
Backlog Item: BACKLOG-119
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: close the gap where a clear relationship fact like `Nathans Freundin heisst Elena` can be acknowledged by one provider but fail to reach a durable contact-/relationship persistence path that another chat and model can later recall.
- Artifact identity is consistent across `BACKLOG-119`, the selected handoff in `documentation/backlog/BACKLOG.md`, and the task artifact `documentation/tasks/backlog_BACKLOG-119_kontakt_beziehungsfakten_provider_und_chatuebergreifend_persistieren.md`.
- Scope stays on the existing backend contact-memory seam: relationship extraction, contact fact staging/persistence, and relationship-aware recall from local knowledge. Do not broaden into a new social-graph model or a generic relationship feature set.
- Existing code already contains directly relevant seams for relationship handling and contact sync in `backend/services/memory_extractor.py`, `backend/services/contact_manager.py`, `backend/tools/memory_tools.py`, `backend/services/chat_orchestrator.py`, and `backend/data/crud.py`.
- Implementation risk is MEDIUM because the task touches cross-system behavior between extraction, persistence, and recall across provider paths, but it remains bounded to an existing contact-/memory pipeline with concrete regression surfaces.
- A later Git checkpoint via `janus-git-governance` is recommended before commit or push because this slice changes user-visible memory/contact behavior.
Affected Files:
- backend/services/chat_orchestrator.py
- backend/services/contact_manager.py
- backend/services/memory_extractor.py
- backend/tools/memory_tools.py
- backend/data/crud.py
- backend/tests/test_contact_manager.py
- backend/tests/test_memory_tools.py
- backend/tests/test_memory_write_update_conflict_handling.py
Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_memory_tools.py -q
- python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q
- python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py backend/services/memory_extractor.py backend/tools/memory_tools.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py
- Add or update focused coverage for cross-chat/provider relationship persistence, correct recall of a persisted relationship fact, and ambiguity-safe no-op behavior for unclear relationship statements.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_memory_tools.py -q
- python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q
- python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py backend/services/memory_extractor.py backend/tools/memory_tools.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-119
- documentation/tasks/backlog_BACKLOG-119_kontakt_beziehungsfakten_provider_und_chatuebergreifend_persistieren.md
- documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
- backend/services/memory_extractor.py relationship-fact normalization seam
- backend/services/contact_manager.py and backend/tools/memory_tools.py around contact fact staging/persistence
- backend/services/chat_orchestrator.py and backend/data/crud.py where contact-backed recall and normalization can still lose relationship facts
Drop Context:
- unrelated DONE backlog history
- OR infrastructure and live-test lane work
- broad address-book redesign or new relationship-feature brainstorming
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The slice is implementation-ready on the current backend contact-/memory seam and needs bounded reasoning across extraction, persistence, and recall without opening new product decisions.
User Action: Say `ok` to start implementation of `BACKLOG-119` with the bound scope and evidence gate above.
