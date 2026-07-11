SKILL 5 DEBUG RESULT: FIXED

Iteration: 1
Progress-Validierung: Failure Code `PET_DETAIL_RECOVERY_BYPASSES_STALE_CONTACT_CARD`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The live AppData contact for `Oliver Schwab` still stored `thunfisch ueberhaupt nicht` under generic owner `preferences` instead of the pet-specific `personal_details` cluster.
- The authoritative Garfield dislike memory already existed in `memories`, but the contact-backed pet overview path still read the stale raw contact card and therefore omitted Garfield's dislike from `was weisst du alles ueber olis haustiere?`.
- `backend/tools/memory_tools.py` built contact pet-detail memories directly from `models.Contact` rows and bypassed DB-aware normalization/recovery.
- Existing contact normalization could clean pet details already present in `personal_details`, but it had no read-time recovery for legacy pet facts that had been misfiled under owner preferences.

Fix Summary:
- Extended `backend/data/crud.py` with DB-aware pet-detail recovery that can reconstruct missing named-pet detail lines from trusted memory rows for live-style stale contacts.
- Added recovery parsing for pet facts such as `mag X ueberhaupt nicht`, `mag X nicht`, `frisst gerne X`, and `ist ein X`, then rewrote them into owner-facing typed details like `Katze Garfield mag Thunfisch ueberhaupt nicht`.
- When a recovered pet dislike covers a stale generic owner preference fragment, the normalization now removes that fragment from `preferences` so the contact card stops presenting Garfield's dislike as Oli's own preference.
- Updated `backend/tools/memory_tools.py` so contact-backed pet-overview reads normalize each contact through the same DB-aware recovery path before emitting authoritative `contact-*` pet facts.
- Added focused regressions for both contact-card normalization and the `memory.read` pet-overview path using the same stale live-style state that reproduced the bug.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m py_compile backend\\data\\crud.py backend\\tools\\memory_tools.py backend\\tests\\test_contact_card_normalization.py backend\\tests\\test_memory_tools.py`: PASS
  - `python -m pytest backend\\tests\\test_contact_card_normalization.py -q`: PASS (`9 passed`)
  - `python -m pytest backend\\tests\\test_memory_tools.py -q -k "live_style_contact_state or pet_overview"`: PASS (`2 passed, 26 deselected`)
  - `python -m pytest backend\\tests\\integration\\test_pet_recall_chat_path.py -q`: PASS (`1 passed`)
  - `python -m pytest backend\\tests\\test_provider_auth_fallback.py -q -k "pet_overview or memory_read_fallback_v2"`: PASS (`2 passed, 7 deselected`)
  - `python -m pytest backend\\tests\\test_contact_manager.py -q -k "pet_dislike_memory_for_named_pet or pet_preference_memory_for_named_pet"`: PASS (`2 passed, 45 deselected`)
  - direct live AppData sqlite inspection before fix authoring: PASS, contact `Oliver Schwab` showed stale `preferences=[\"big bang theory\", \"strategiespiele wie panzer general\", \"thunfisch ueberhaupt nicht\"]` while trusted Garfield pet memories already existed

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/data/crud.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-116_debug_live_pet_detail_recovery_2026-07-01.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/backlog/BACKLOG.md`
- `documentation/tasks/backlog_BACKLOG-116_execution_result.md`
- `documentation/test-runs/BACKLOG-116_live_retest_preflight_2026-07-01.md`
- `documentation/test-results/BACKLOG-116-live-retest-2026-07-01/BACKLOG-116_live_retest_api_evidence.json`
- `documentation/test-runs/BACKLOG-116_debug_live_pet_detail_recovery_2026-07-01.md`
Evidence Paths:
- `backend/data/crud.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_memory_tools.py`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `PET_DETAIL_RECOVERY_BYPASSES_STALE_CONTACT_CARD`
Changed Files:
- `backend/data/crud.py`
- `backend/tools/memory_tools.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-116_debug_live_pet_detail_recovery_2026-07-01.md`
Decision:
- rerun the bounded `BACKLOG-116` live validation gate in `janus-test-pipeline`; do not route to `janus-final-audit` until the live Janus answer includes Garfield's tuna dislike as a Garfield fact
Reason:
- the local debug slice is fixed and regression-covered, but the failure was confirmed in the real Janus app data path and must be cleared by a fresh live retest
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Approve one fresh live retest with the exact gate phrase `OK START LIVE TEST` when the local backend/app is ready again.
