PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-108
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
Spec: documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: BACKLOG-108
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: close the gap where confirmed contact knowledge about an already matched existing contact can remain memory-only instead of reaching the existing contact persistence or proposal path.
- Artifact identity is consistent across `BACKLOG-108`, the selected handoff in `documentation/backlog/BACKLOG.md`, the task artifact `documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md`, and the existing Spec-15 contact-memory contract.
- Existing behavior already covers confirmation-first contact proposals and confirmed Memory-to-contact suggestion staging, so this fix must stay on the missing existing-contact chat-to-contact seam without reopening the broader address-book model or proposal architecture.
- Implementation risk is MEDIUM because the task touches cross-system write semantics between chat orchestration, Memory coupling, and contact persistence, but it remains bounded to an existing backend path with explicit regression targets.
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
- Add or update focused coverage for confirmed existing-contact facts, proposal-versus-persist behavior, no false "firmly remembered" wording when contact persistence did not happen, and ambiguity-safe no-op behavior.
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
- documentation/backlog/BACKLOG.md section for BACKLOG-108
- documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
- documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
- backend/services/chat_orchestrator.py and backend/services/contact_manager.py around contact proposal confirmation and contact extraction/persistence
Drop Context:
- unrelated DONE backlog history
- broader Spec-15 execution history outside the existing-contact persistence seam
- unrelated UI/address-book redesign work from Spec 16
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The task is implementation-ready on a warm `5.4` backend context and needs careful but bounded reasoning across chat, Memory, and contact persistence without opening new product decisions.
User Action: Say `ok` to start implementation of `BACKLOG-108` with the bound scope and evidence gate above.
