PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: TASK-SPEC15.4
Target Subtask: N/A
Task: documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Spec: documentation/SPEC/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
Backlog Item: N/A
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: connect only confirmed contact knowledge with Memory and confirmed Memory knowledge with contact-update suggestions, without reopening direct-context extraction, public web enrichment, or broad regression-only work.
- Scope is limited to four concrete behaviors on the current write paths: confirmed contact facts may become reusable Memory, confirmed relevant Memory may become contact-update suggestions, sensitive personal facts must remain confirmation-gated, and traceability must persist across apply/reject/conflict outcomes.
- Existing primitives already cover the two key safety rails this task must reuse instead of replacing them: contact proposal persistence and suppression from TASK-SPEC15.2/15.3, plus sensitive/non-durable blocking on the current memory write path in `backend/tools/memory_tools.py`.
- Execution must keep the reverse direction proposal-safe: Memory-backed contact enrichment may suggest updates, but must not silently mutate contact cards or bypass the existing proposal contract for preferences, dislikes, personal details, health-adjacent facts, or relationship details.
- The current Memory stack still writes through `backend.services.memory` and `memory_extractor` subject tracking; implementation must stay inside the listed task files and avoid architecture drift into unrelated retrieval or provider-selection layers.
- This task explicitly excludes direct-context proposal logic from TASK-SPEC15.2, public-organization web enrichment from TASK-SPEC15.3, and broad regression expansion from TASK-SPEC15.5.
- Implementation risk is HIGH because this slice links two persistent systems with privacy-sensitive write semantics; a `janus-git-governance` checkpoint is recommended before execution because the worktree remains dirty outside the bound artifacts.
Affected Files:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/tools/memory_tools.py
- backend/services/memory_extractor.py
- backend/tests/test_memory_tools.py
- backend/tests/test_memory_write_update_conflict_handling.py
- backend/tests/test_contact_manager.py
Evidence Focus:
- `python -m pytest backend/tests/test_memory_tools.py -q`
- `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q`
- `python -m pytest backend/tests/test_contact_manager.py -q`
- Add or update focused coverage for confirmed-only Memory handoff, contact-update suggestion routing, sensitive-field confirmation gates, and explicit conflict/rejection traceability.
- `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tools/memory_tools.py backend/services/memory_extractor.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py backend/tests/test_contact_manager.py`
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_memory_tools.py -q
- python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tools/memory_tools.py backend/services/memory_extractor.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py backend/tests/test_contact_manager.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- bound task/spec identity
- existing contact proposal persistence and suppression contract
- current memory_write sensitivity and no-durable guards
- evidence commands above
Drop Context:
- TASK-SPEC15.2 direct-context extraction details outside the proposal contract
- TASK-SPEC15.3 public web-enrichment internals beyond the shipped proposal state
- unrelated dirty-worktree files, old audit chatter, and unbound implementation history
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: high
Reason: The task is implementation-ready and benefits from warm 5.4 context while using higher reasoning for confirmed-only cross-system writes, privacy-sensitive suggestion routing, and explicit conflict traceability.
User Action: Say `ok` to start implementation of `TASK-SPEC15.4` with the bound scope and evidence gate above.
