PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC15.3
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Spec: documentation/SPEC/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: harden only the existing public-contact enrichment path so web enrichment stays available for organizations and other public entries while private contacts remain excluded.
- Scope is limited to three concrete behaviors on the current enrichment path: enforce public-or-organization-only gating, convert ambiguous web hits into explicit selection-required or proposal outcomes, and convert conflicting public fields into proposal-safe updates instead of silent overwrite.
- This task should reuse the proposal-state and confirmation primitives already established in TASK-SPEC15.2 rather than inventing a second approval mechanism or expanding the settings surface.
- Execution must preserve compatibility with both the newer `contact_type` field and the legacy `category` heuristics still used in the current enrichment path, because existing local rows may rely on either shape during migration overlap.
- This task explicitly excludes direct-context private-contact proposal changes from TASK-SPEC15.2, Memory coupling from TASK-SPEC15.4, and broad regression-only hardening from TASK-SPEC15.5.
- Implementation risk is HIGH because the current enrichment path already performs live websearch, uses provider-bound background extraction, and still applies clear public fields directly when missing, so ambiguity and conflict handling must be tightened without breaking legitimate organization enrichment.
- The repository worktree remains dirty outside this task's bound artifacts, so execution must stage explicit pathspecs only and should recommend a `janus-git-governance` checkpoint before touching persistence plus externally informed update logic.
Affected Files:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/api/routers/contacts.py
- backend/tests/test_contact_manager.py
Evidence Focus:
- `python -m pytest backend/tests/test_contact_manager.py -q`
- Add or update enrichment regression coverage for private-contact blocking, ambiguity gating, and conflict-as-proposal behavior.
- `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/api/routers/contacts.py backend/tests/test_contact_manager.py`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/api/routers/contacts.py backend/tests/test_contact_manager.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec identity
- existing `enrich_incomplete_contacts` flow in contact_manager
- proposal-state persistence introduced in TASK-SPEC15.2
- privacy rule that private contacts never receive web enrichment
- evidence commands above
Drop Context:
- TASK-SPEC15.2 direct-context extraction and chat confirmation details beyond the already-shipped proposal contract
- TASK-SPEC15.4 Memory write coupling and TASK-SPEC15.5 broader regression expansion
- unrelated dirty-worktree files, old audit chatter, and unbound implementation history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The task is implementation-ready and benefits from warm 5.4 context while using higher reasoning for privacy-safe enrichment gating, ambiguity handling, and conflict-to-proposal conversion on externally informed data.
User Action: Say `ok` to start implementation of `TASK-SPEC15.3` with the bound scope and evidence gate above.
