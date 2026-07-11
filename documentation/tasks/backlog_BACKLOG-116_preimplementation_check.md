PRE-CHECK RESULT
PRE-CHECK PASSED

Target Task: BACKLOG-116
Target Subtask: N/A
Task: documentation/tasks/backlog_BACKLOG-116_garfield_thunfisch_fakt_haustieruebersicht.md
Spec: N/A WITH REASON - small bounded backlog bugfix on an existing address-book pet-detail and memory-recall seam; no separate feature spec is required
Backlog Item: BACKLOG-116
Assigned Model: 5.4
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The bound task is atomic enough for execution: keep the Garfield/Tuna fact pet-specific, ensure it is not surfaced as a generic Oli contact fact, and include it in the aggregated Oli pet overview without breaking direct Garfield recall.
- Artifact identity is consistent across `documentation/backlog/BACKLOG.md` and the selected handoff in `documentation/tasks/backlog_BACKLOG-116_garfield_thunfisch_fakt_haustieruebersicht.md`.
- Existing code already contains directly relevant seams in `backend/services/contact_manager.py`, `backend/data/crud.py`, and `backend/services/orchestrator/execution_engine.py`.
- Existing BACKLOG-115 coverage intentionally filtered `Garfield mag ... thunfisch` from pet-overview fallback output. Implementation must preserve protection against stale generic memory drift while allowing an explicitly pet-specific Garfield fact to appear when it is contact-backed or otherwise safely attributable to Garfield.
- Implementation risk is LOW to bounded MEDIUM because the change is narrow but touches user-visible memory/contact recall behavior and an existing fallback regression.
- A later Git checkpoint via `janus-git-governance` is recommended before commit or push because this slice updates user-visible address-book and recall behavior.
Affected Files:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/services/orchestrator/execution_engine.py
- backend/tests/test_contact_manager.py
- backend/tests/test_contact_card_normalization.py
- backend/tests/test_provider_auth_fallback.py
- backend/tests/test_memory_tools.py
- backend/tests/integration/test_pet_recall_chat_path.py
Evidence Focus:
- python -m pytest backend/tests/test_contact_manager.py -q -k "pet"
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m pytest backend/tests/test_provider_auth_fallback.py -q -k "pet_overview or memory_read_fallback_v2"
- python -m pytest backend/tests/test_memory_tools.py -q -k "pet_overview"
- python -m pytest backend/tests/integration/test_pet_recall_chat_path.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/services/orchestrator/execution_engine.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py backend/tests/test_provider_auth_fallback.py backend/tests/test_memory_tools.py backend/tests/integration/test_pet_recall_chat_path.py
- Add or update focused coverage for `Garfield mag Thunfisch ueberhaupt nicht` so the aggregated Oli pet overview includes the Garfield dislike while stale or generic non-contact pet preference drift remains controlled.
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback redesign, no broad contact schema migration, no live database repair unless separately routed.
Automated Evidence Gate:
- python -m pytest backend/tests/test_contact_manager.py -q -k "pet"
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m pytest backend/tests/test_provider_auth_fallback.py -q -k "pet_overview or memory_read_fallback_v2"
- python -m pytest backend/tests/test_memory_tools.py -q -k "pet_overview"
- python -m pytest backend/tests/integration/test_pet_recall_chat_path.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/services/orchestrator/execution_engine.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py backend/tests/test_provider_auth_fallback.py backend/tests/test_memory_tools.py backend/tests/integration/test_pet_recall_chat_path.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
Keep Context:
- documentation/backlog/BACKLOG.md section for BACKLOG-116
- documentation/tasks/backlog_BACKLOG-116_garfield_thunfisch_fakt_haustieruebersicht.md
- backend/services/contact_manager.py pet-detail writeback and contact selection seams
- backend/data/crud.py contact personal-detail normalization seam
- backend/services/orchestrator/execution_engine.py pet-overview memory-read fallback seam
- existing pet-overview tests that currently distinguish contact-backed facts from stale Garfield/Thunfisch memory drift
Drop Context:
- unrelated READY backlog items
- broad OR rollout history
- older DONE history outside the Oliver/Tasso/Garfield pet-detail path
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
Expected Output:
- Implementation result, executed checks, changed files, and next-skill handoff.

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.4
Recommended Intelligence: medium
Reason: The slice is implementation-ready on a bounded address-book and pet-overview recall seam, and needs focused backend reasoning with regression coverage.
User Action: Say `ok` to start implementation of `BACKLOG-116` with the bound scope and evidence gate above.
