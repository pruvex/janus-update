PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-120
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-120_kontakt_hobbyfakten_fallen_in_wissensmodus.md
Spec: N/A WITH REASON - small bounded backlog bugfix on the existing contact-memory fact path; no separate feature spec is required
Backlog Item: BACKLOG-120
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: close the gap where a clear new hobby/preference fact like `Nathan spielt gerne League of Legends` is treated as an external knowledge request instead of local contact memory.
- Artifact identity is consistent across `BACKLOG-120`, the selected handoff in `documentation/backlog/BACKLOG.md`, and the task artifact `documentation/tasks/backlog_BACKLOG-120_kontakt_hobbyfakten_fallen_in_wissensmodus.md`.
- Scope stays on the existing backend contact-memory seam: fact-telling detection, explicit contact-subject extraction, and contact preference persistence for already known contacts. Do not broaden into generic gaming search, broad intent redesign, or address-book UI work.
- Existing code already contains directly relevant seams for named contact fact statements and preference sync in `backend/services/orchestrator/intent_engine.py`, `backend/services/memory_extractor.py`, `backend/services/contact_manager.py`, and the focused regression surfaces in `backend/tests/test_calendar_routing_fix.py` and `backend/tests/test_contact_manager.py`.
- Implementation risk is MEDIUM because the bug sits between orchestration classification and downstream contact-memory write behavior, but the slice remains small with concrete acceptance criteria and nearby green regression patterns.
- A later Git checkpoint via `janus-git-governance` is recommended before commit or push because this slice changes user-visible contact memory behavior.
Affected Files:
- backend/services/orchestrator/intent_engine.py
- backend/services/memory_extractor.py
- backend/services/contact_manager.py
- backend/tests/test_calendar_routing_fix.py
- backend/tests/test_contact_manager.py
Evidence Focus:
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/memory_extractor.py backend/services/contact_manager.py backend/tests/test_calendar_routing_fix.py backend/tests/test_contact_manager.py
- Add or update focused coverage for `spielt gerne`-style contact fact detection, correct contact-subject anchoring for an existing contact, and bounded no-op behavior for generic gaming knowledge queries.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_calendar_routing_fix.py -q
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/memory_extractor.py backend/services/contact_manager.py backend/tests/test_calendar_routing_fix.py backend/tests/test_contact_manager.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-120
- documentation/tasks/backlog_BACKLOG-120_kontakt_hobbyfakten_fallen_in_wissensmodus.md
- backend/services/orchestrator/intent_engine.py fact-telling seam for named contact statements
- backend/services/memory_extractor.py explicit contact-subject extraction seam
- backend/services/contact_manager.py preference/contact sync seam
- backend/tests/test_calendar_routing_fix.py and backend/tests/test_contact_manager.py as the focused regression surface
Drop Context:
- unrelated DONE backlog history
- OR infrastructure items
- detailed BACKLOG-119 audit bundle beyond keeping its behavior stable
- broad gaming/news/wiki routing history outside the bound contact-fact case
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The slice is implementation-ready on the current contact-memory fact seam and needs a bounded fix across contact fact detection and persistence without reopening larger routing architecture questions.
User Action: Say `ok` to start implementation of `BACKLOG-120` with the bound scope and evidence gate above.
