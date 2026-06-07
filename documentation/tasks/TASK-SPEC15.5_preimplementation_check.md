PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC15.5
Target Subtask: N/A
Task: C:\KI\Janus-Projekt\documentation\tasks\TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Spec: C:\KI\Janus-Projekt\documentation\SPEC\15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED

Pre-Check Context:
- Bound only to the regression-hardening slice in TASK-SPEC15.5.
- Existing implementation evidence from TASK-SPEC15.2 through TASK-SPEC15.4 already covers the product behavior that this task must now lock in with focused tests and existing surface checks.
- No open product or architecture decision remains; the task is limited to making silent private-contact writes, repeated nuisance proposals, unsafe enrichment, and unguarded Memory coupling fail loudly in automation.

Affected Files:
- backend/tests/test_contact_manager.py
- backend/tests/test_calendar_tools.py
- backend/tests/test_memory_tools.py
- backend/tests/test_memory_write_update_conflict_handling.py
- frontend/js/settings.js

Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_calendar_tools.py -q
- python -m pytest backend/tests/test_memory_tools.py -q
- python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q
- node --check frontend/js/settings.js

Scope-Regel:
- Implement only TASK-SPEC15.5. Add the smallest useful regression coverage for confirmation-first private-contact proposals, duplicate or merge routing, suppression memory for rejected suggestions, public-organization enrichment ambiguity handling, and confirmed-only Memory coupling. No architecture drift, no provider fallback, no new product behavior, and no scope expansion beyond the named regression surfaces.

Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_calendar_tools.py -q
- python -m pytest backend/tests/test_memory_tools.py -q
- python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q
- node --check frontend/js/settings.js
- npx playwright test <runner> --headed --workers=1 --reporter=list

Artifact Identity Check:
- Task file path, Target Task, Spec path, and predecessor execution evidence were verified.
- No Backlog artifact is bound to this Spec task, so Backlog Item remains N/A by design.

Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan or TestResult artifacts.
- This task may extend only the named regression files and existing surface checks; any separate TestSpec or TestRun work must route through janus-test-pipeline.

Keep Context:
- Spec 15 privacy and confirmation rules
- TASK-SPEC15.2 to TASK-SPEC15.4 behavioral evidence
- named regression files and exact evidence commands

Drop Context:
- old feature-design history
- unrelated backlog, release, or audit work
- implementation ideas outside regression hardening

Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths proving the guarded contact-intelligence behavior remains enforced by automation.

Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
User Action: Implementiere nur TASK-SPEC15.5 und halte die Ausfuehrung auf die benannten Regressionstests plus den bestehenden Settings-Surface-Check gebunden.
