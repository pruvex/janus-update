SKILL 5 DEBUG RESULT: FIXED

Iteration: 1
Progress-Validierung: Failure Code `CONTACT_CARD_PET_DETAIL_TYPO_VARIANT_NOT_DEDUPED`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- The visible duplicate-contact fix was already working, but the live runtime still carried one stale malformed pet-detail variant on the surviving primary `Oliver Schwab` row: `Hund Tasso frisst gerne hunfisch`.
- `backend/data/crud.py` normalized `frisst gern` to `frisst gerne`, but it did not normalize the specific live typo variant `hunfisch` to the canonical `thunfisch`.
- Because dedupe ran after that narrower normalization, the reader path still treated `Hund Tasso frisst gerne thunfisch` and `Hund Tasso frisst gerne hunfisch` as distinct details and exposed both on the visible contact card.

Fix Summary:
- Added one bounded pet-detail tail normalizer in `backend/data/crud.py`.
- Kept the fix intentionally narrow to the proven live typo variant: `hunfisch` -> `thunfisch`.
- Reused that normalizer for both owner-facing pet trait details and raw pet trait detail normalization before dedupe.
- Added one regression in `backend/tests/test_contact_card_normalization.py` that now covers:
  - `frisst gerne thunfisch`
  - `frisst gern thunfisch`
  - `frisst gerne hunfisch`
- Added one focused runtime-shaped reader-path regression in `backend/tests/test_contact_manager.py` proving that an already stored live contact with both `thunfisch` and `hunfisch` now loads as a single clean detail.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS (`8 passed`)
  - `python -m pytest backend/tests/test_contact_manager.py -q -k "visible_contact"`: PASS (`2 passed`)
  - `python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py backend/tests/test_contact_manager.py`: PASS
  - direct reader-path recheck via `crud.search_contacts_by_name(db, "Oliver Schwab")`: PASS, returns one visible `Oliver Schwab` contact with only one `Hund Tasso frisst gerne thunfisch`
  - direct AppData DB read after normalization checkpoint: PASS, `contacts.id=1.personal_details` no longer contains `hunfisch`

Artifact Identity Check: N/A
Final Feature Suite: PASS
Changed Files:
- `backend/data/crud.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_contact_manager.py`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md`
- `documentation/tasks/backlog_BACKLOG-115_preimplementation_check.md`
- `documentation/test-runs/BACKLOG-115_live_validation_2026-06-30.md`
- `documentation/test-runs/BACKLOG-115_debug_result_2026-06-30.md`
Evidence Paths:
- `backend/data/crud.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_contact_manager.py`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `CONTACT_CARD_PET_DETAIL_TYPO_VARIANT_NOT_DEDUPED`
Changed Files:
- `backend/data/crud.py`
- `backend/tests/test_contact_card_normalization.py`
- `backend/tests/test_contact_manager.py`
Decision:
- rerun the bounded `BACKLOG-115` validation gate now that the live visible Tasso typo variant has a direct regression and the AppData contact readback is clean
Reason:
- this debug slice is fixed locally and on the bound live reader path, but final release-readiness still belongs to `janus-test-pipeline` retest before any `janus-final-audit` handoff
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Say `ok` to rerun the bounded `BACKLOG-115` validation gate in `janus-test-pipeline`.

```text
NEXT: janus-test-pipeline
FAILURE_SLICE: BACKLOG-115 / CONTACT_CARD_PET_DETAIL_TYPO_VARIANT_NOT_DEDUPED
STATE: FIXED LOCALLY AND ON LIVE READER PATH
ACTION: rerun the bounded BACKLOG-115 validation gate and only route to janus-final-audit if the visible Oliver/Tasso/Garfield contact-card result stays clean
```
