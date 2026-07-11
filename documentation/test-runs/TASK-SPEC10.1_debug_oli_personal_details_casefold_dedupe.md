SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code `CONTACT_PERSONAL_DETAILS_CASEFOLD_DEDUPE`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Der bestehende Kontakt-Normalisierungspfad in `backend/data/crud.py` verschob zwar Ernaehrungsfakten sauber von `preferences` nach `personal_details`, deduplizierte aber bestehende `personal_details` nicht case-insensitiv.
- Dadurch konnten in der Live-DB fuer `Oliver Schwab` zwei gleichbedeutende Details nebeneinander stehen:
  - `wohnt in Köln Stammheim`
  - `wohnt in köln stammheim`

Fix Summary:
- Neue Hilfsfunktion `_dedupe_contact_string_list(...)` dedupliziert strukturierte Kontaktlisten case-insensitiv bei Erhalt des ersten Eintrags.
- `_normalize_contact_structured_fields(...)` nutzt diese Deduplizierung jetzt fuer `preferences` und `personal_details`.
- Regression stellt sicher, dass `personal_details` fuer `Oliver Schwab` auf genau einen Wohnort-Eintrag zusammenfallen.
- Die Live-DB wurde mit derselben Normalisierung sofort bereinigt; `Oliver Schwab` hat jetzt nur noch `wohnt in Köln Stammheim`.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m py_compile backend/data/crud.py backend/tests/test_contact_manager.py`
  - Live-DB normalisiert: `BEFORE ['wohnt in Köln Stammheim', 'wohnt in köln stammheim']` -> `AFTER ['wohnt in Köln Stammheim']`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_personal_details_casefold_dedupe.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_personal_details_casefold_dedupe.md`
Evidence Paths:
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `CONTACT_PERSONAL_DETAILS_CASEFOLD_DEDUPE`
Changed Files:
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_personal_details_casefold_dedupe.md`
Decision:
- `NEEDS RETEST`
Reason:
- Code, Tests und Live-DB-Bereinigung sind gruen; der Nutzer sollte jetzt die `Oli`-Karte bzw. `Was weißt du über Oli?` noch einmal live pruefen.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Janus neu starten und die `Oli`-Karte oder `Was weißt du über Oli?` erneut pruefen, um zu bestaetigen, dass der Wohnort nur noch einmal erscheint.
