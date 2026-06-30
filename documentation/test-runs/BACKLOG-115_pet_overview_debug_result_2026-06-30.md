SKILL 5 DEBUG RESULT: FIXED

Iteration: 1
Progress-Validierung: Failure Code `PET_OVERVIEW_RECALL_CONTACT_ALIAS_FILTER_MISSES_OLIS`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The manual live prompt `was weißt du über olis haustiere?` exercised the pet-overview recall path, not only the contact-card reader path.
- The recall query could arrive in a degraded umlaut shape such as `was wei?t du ?ber olis haustiere?`, and the subject extraction did not reliably reduce possessive `olis` to the contact alias `Oli`.
- When the subject alias was missing or weak, `memory.read` could surface stale memory-only pet facts and omit or de-prioritize the authoritative contact-card details.
- This allowed a non-address-book fact (`Garfield mag keinen Thunfisch`) to appear while clean contact facts such as Garfield's cat identity and Tasso's food/breed details were incomplete.

Fix Summary:
- Hardened `backend/tools/memory_tools.py` so contact pet-overview queries can normalize possessive aliases like `olis` to the contact nickname `Oli`.
- Added contact pet-overview context terms so scope extraction stops at words such as `haustiere`, `hund`, and `katze` instead of treating them as part of the subject.
- Made matched contact pet details authoritative for pet-overview reads: when contact-backed pet details exist, the reader returns the clean `contact-*` facts instead of stale memory-only pet facts.
- Extended `backend/tests/test_memory_tools.py` with a runtime-shaped regression for `was wei?t du ?ber olis haustiere?`, including a stale Garfield/Thunfisch memory fact that must not appear.
- Updated `backend/tests/integration/test_pet_recall_chat_path.py` so the chat-path fixture uses the four contact-backed facts and asserts no Garfield preference/dislike statement is emitted.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_memory_tools.py -q -k "pet_overview"`: PASS (`1 passed, 26 deselected`)
  - `python -m pytest backend/tests/test_provider_auth_fallback.py -q -k "pet_overview"`: PASS (`2 passed, 7 deselected`)
  - `python -m pytest backend/tests/integration/test_pet_recall_chat_path.py -q`: PASS (`1 passed`)
  - `python -m py_compile backend/tools/memory_tools.py backend/tests/test_memory_tools.py backend/tests/integration/test_pet_recall_chat_path.py`: PASS
  - direct live AppData `memory.read` probe for `was weißt du über olis haustiere?`: PASS, returns exactly four `contact-*` facts:
    - `Oliver Schwab hat einen Hund namens tasso`
    - `Oliver Schwab hat eine Katze namens garfield`
    - `Hund Tasso ist ein podenco`
    - `Hund Tasso frisst gerne thunfisch`
  - direct live AppData `memory.read` probe: PASS, `HAS_GARFIELD_THUNFISCH=False`

Artifact Identity Check: N/A
Final Feature Suite: PASS
Changed Files:
- `backend/tools/memory_tools.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
- `documentation/test-runs/BACKLOG-115_pet_overview_debug_result_2026-06-30.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md`
- `documentation/tasks/backlog_BACKLOG-115_preimplementation_check.md`
- `documentation/test-runs/BACKLOG-115_live_validation_2026-06-30.md`
- `documentation/test-runs/BACKLOG-115_debug_result_2026-06-30.md`
- `documentation/test-runs/BACKLOG-115_retest_validation_2026-06-30.md`
- `documentation/test-runs/BACKLOG-115_pet_overview_debug_result_2026-06-30.md`
Evidence Paths:
- `backend/tools/memory_tools.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `PET_OVERVIEW_RECALL_CONTACT_ALIAS_FILTER_MISSES_OLIS`
Changed Files:
- `backend/tools/memory_tools.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
- `documentation/test-runs/BACKLOG-115_pet_overview_debug_result_2026-06-30.md`
Decision:
- rerun the bounded `BACKLOG-115` live validation gate in `janus-test-pipeline`; do not route to `janus-final-audit` until the user-facing prompt is manually green in the app
Reason:
- the debug slice is fixed and locally validated, but the user found it through manual live chat behavior; the next gate must confirm the actual app answer.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Restart/reload the local Janus backend/app if needed, then retest the exact prompt `was weißt du über olis haustiere?`.
