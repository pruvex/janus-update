SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `CONTACT_FACT_STATEMENT_FALSE_AMBIGUITY`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Der Satz `OLI LIEBT Big bang theory` wurde in `backend/services/orchestrator/intent_engine.py` korrekt als `is_fact_telling=True` erkannt, aber parallel noch als ambig markiert.
- Ausloeser war die allgemeine Kurzquery-Ambiguity-Heuristik in `detect_ambiguity_in_query(...)`, die fuer kurze Aussagen ohne speziellen Bypass `is_ambiguous=True` setzte.
- Der bestehende Ambiguity-Bypass galt nur fuer `personal_recall`, nicht fuer explizite Kontaktfakt-Aussagen wie `Name liebt X`.
- Dadurch lief der Chat in den Clarification-Pfad und fragte unnötig `Worauf bezieht sich die Information über Oli?`.

Fix Summary:
- Der Ambiguity-Bypass in `detect_all_intents(...)` greift jetzt auch fuer `is_fact_telling=True`.
- Explizite Kontaktfakt-Saetze werden damit nicht mehr durch die Kurzquery-Heuristik blockiert.
- Neue Regression sichert, dass `OLI LIEBT Big bang theory` als Fakt-Aussage erkannt wird und keinen Ambiguity-Clarification-Pfad mehr oeffnet.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_calendar_routing_fix.py -q`
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/tests/test_calendar_routing_fix.py`
  - direkter Intent-Check: `is_fact_telling=True`, `is_ambiguous=False`, `ambiguity_confidence=0.0`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `backend/services/orchestrator/intent_engine.py`
- `backend/tests/test_calendar_routing_fix.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_fact_statement_ambiguity_bypass.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_fact_statement_ambiguity_bypass.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_live_db_reconstruction_apply.md`
Evidence Paths:
- `backend/services/orchestrator/intent_engine.py`
- `backend/tests/test_calendar_routing_fix.py`
Failure Code:
- `CONTACT_FACT_STATEMENT_FALSE_AMBIGUITY`
Changed Files:
- `backend/services/orchestrator/intent_engine.py`
- `backend/tests/test_calendar_routing_fix.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_fact_statement_ambiguity_bypass.md`
Decision:
- `NEEDS RETEST`
Reason:
- Die Intent-Heuristik ist jetzt testgruen, aber der Nutzer muss den Live-Pfad nach Janus-Neustart gegen `OLI LIEBT Big bang theory` verifizieren.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Janus neu starten, `OLI LIEBT Big bang theory` senden und danach `Was mag Oli?` oder die `Oli`-Karte pruefen. Erwartung: keine Rueckfrage mehr und `Big bang theory` wird dem Kontakt `Oli` zugeordnet.
