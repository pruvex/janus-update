Mode: `DIAMOND_RETEST_AUDIT`

Bound artifacts:
- `documentation/ai/CURRENT_STATE.md`
- `documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md`
- `documentation/tasks/backlog_BACKLOG-115_preimplementation_check.md`
- `backend/data/crud.py`
- `backend/services/contact_manager.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_contact_card_normalization.py`

Decision: `BLOCKED`

Evidence:
- Focused automated evidence is green:
  - `python -m pytest backend/tests/test_contact_manager.py -q`: PASS (`45 passed`)
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS (`8 passed`)
  - `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`: PASS
- Live targeted runtime evidence is still red:
  - Raw AppData contact DB at `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db` still contains three `Oliver Schwab` rows, with two empty historical duplicates (`id=3`, `id=4`) and one rich primary contact (`id=1`).
  - The visible reader path is only partially fixed: `crud.search_contacts_by_name(db, "Oliver Schwab")` collapses the empty duplicates to one visible contact, but that contact still exposes both `Hund Tasso frisst gerne thunfisch` and `Hund Tasso frisst gerne hunfisch`.
  - Because the runtime card still shows a duplicated/incorrect Tasso fact variant, the acceptance target "sauber dedupliziert und fachlich korrekt" is not yet met.
- Supporting runtime observation:
  - `GET http://127.0.0.1:8001/health` was unavailable during this validation, so the check used the real AppData DB plus the live reader path directly instead of a running HTTP backend.

Next skill: `janus-debug`

Model recommendation:
- Model: `5.4`
- Intelligence: `medium`
- Chat: `same`

Keep Context:
- `documentation/test-runs/BACKLOG-115_live_validation_2026-06-30.md`
- `documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md`
- `documentation/tasks/backlog_BACKLOG-115_preimplementation_check.md`
- `backend/data/crud.py` contact normalization seam
- `backend/services/contact_manager.py` visible contact selection seam

Drop Context:
- OR rollout infrastructure
- older unrelated contact-memory fixes
- unrelated dirty worktree files

```text
NEXT: janus-debug
BACKLOG: BACKLOG-115
EVIDENCE: FAIL
ACTION: debug why the live visible contact still shows both "Hund Tasso frisst gerne thunfisch" and "Hund Tasso frisst gerne hunfisch" even though duplicate Oliver rows are already collapsed on read
```
