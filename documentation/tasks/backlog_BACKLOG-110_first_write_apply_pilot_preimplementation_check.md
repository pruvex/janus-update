PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-BACKLOG-110-W1
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-110_first_write_apply_pilot_slice.md
Spec: documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: BACKLOG-110
Assigned Model: 5.4
Mode: SINGLE_TASK_PRECHECK
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound pilot slice is atomic enough for the first real `execution_write_apply_candidate` candidate: only the new explicit residence-fact mapping seam is in scope, not the broader `BACKLOG-110` cleanup or UI follow-up.
- Artifact identity is consistent across the original `BACKLOG-110` handoff, the narrowed write-pilot slice, the existing Spec-15 contact-intelligence source of truth, and the execution-write readiness gate.
- The exact first-pilot safety posture is now clear: backend-only default path, no cleanup migration, no frontend work, no broader contact-schema redesign, and no provider or release boundary.
- Implementation risk is MEDIUM because the slice is narrow and real, but it still touches a write-capable contact-persistence seam where over-mapping free-text details into address data would be the main failure mode.
Affected Files:
- backend/services/contact_manager.py
- backend/tests/test_contact_manager.py
- backend/data/crud.py only if strictly required to complete the bounded mapping seam
- backend/tests/test_contact_card_normalization.py only if strictly required to prove backend-visible normalization without UI edits
Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q only if backend/tests/test_contact_card_normalization.py is touched
- python -m py_compile backend/services/contact_manager.py backend/tests/test_contact_manager.py
- python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py only if those optional files are touched
- delegated write candidate must preserve exact allowlist discipline, max touched files <= 2, and no delete/rename/move activity
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q only if backend/tests/test_contact_card_normalization.py is touched
- python -m py_compile backend/services/contact_manager.py backend/tests/test_contact_manager.py
- python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py only if those optional files are touched
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/tasks/backlog_BACKLOG-110_first_write_apply_pilot_slice.md
- documentation/tasks/backlog_BACKLOG-110_preimplementation_check.md
- documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md
- documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
- backend/services/contact_manager.py
- backend/tests/test_contact_manager.py
Drop Context:
- broader BACKLOG-110 cleanup of already affected contacts
- frontend/address-card follow-up unless a later separate slice proves necessary
- unrelated contact-memory recall debugging, OR family comparison history, and earlier broad address-book redesign chatter
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
User Action: Say `ok` to start implementation of `TASK-BACKLOG-110-W1` with the frozen two-file-first pilot scope and bounded optional-file fallback only if strictly required.
