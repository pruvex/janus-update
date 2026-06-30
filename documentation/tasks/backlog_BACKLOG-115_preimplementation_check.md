PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-115
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md
Spec: N/A WITH REASON - small bounded backlog bugfix on an existing address-book normalization seam; no separate feature spec is required
Backlog Item: BACKLOG-115
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: keep exactly one relevant `Oliver Schwab` contact in the visible selection path and normalize duplicated or tautological Tasso/Garfield pet details on the same contact card seam.
- Artifact identity is consistent across `documentation/backlog/BACKLOG.md`, the selected handoff in `documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md`, and the current `BACKLOG-108` follow-up history in `documentation/ai/CURRENT_STATE.md`.
- Existing code already contains two directly relevant mechanisms: `backend/services/contact_manager.py` prefers the richest exact duplicate contact for pet-detail updates, and `backend/data/crud.py` already normalizes and dedupes `personal_details`, including named-pet details.
- Implementation risk is LOW to bounded MEDIUM because the seam is visible and small, but it touches the live contact selection and normalization path, so execution must stay conservative and avoid broader contact-model or memory-architecture changes.
- A later Git checkpoint via `janus-git-governance` is recommended before commit or push because this slice updates user-visible contact behavior and its regression tests.
Affected Files:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/tests/test_contact_manager.py
- backend/tests/test_contact_card_normalization.py
- existing address-book UI file(s) only if the backend-only cleanup does not fully remove duplicate visible Oliver entries
Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py
- Add or update focused coverage for richest-contact selection in the presence of empty duplicate Oliver rows, normalization of near-duplicate pet wording such as `gern` versus `gerne`, and suppression of tautological Garfield detail lines when a better owner- or pet-specific detail already exists.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-115
- documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md
- backend/services/contact_manager.py duplicate-contact selection seam
- backend/data/crud.py personal-detail normalization seam
Drop Context:
- unrelated READY backlog items
- broad OR rollout history
- older contact-memory debugging outside the visible Oliver/Tasso/Garfield contact-card cleanup seam
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The slice is implementation-ready on the warm contact-normalization context and needs careful but bounded backend reasoning with focused regression coverage.
User Action: Say `ok` to start implementation of `BACKLOG-115` with the bound scope and evidence gate above.
