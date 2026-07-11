SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `CONTACT_RECALL_SUBJECT_CONTAMINATION_AND_SELF_POISON`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- `memory.read` lieferte bei kontaktbezogenen Recall-Queries wie `Oli Vorlieben Hobbys Interessen` nicht nur passende `Oli`-Memories, sondern auch fremde Treffer wie `Chris Gier liebt Kimchi`.
- Diese gemischten Recall-Treffer konnten in spaeteren Antworten zu falschen Kontaktzusammenfassungen fuehren.
- Danach lief die Faktenextraktion auch ueber reine Recall-Turns wie `und was mag oli?` und konnte Assistant-Zusammenfassungen als neue Kontaktfakten zurueckspeichern. Dadurch entstand ein Selbstvergiftungs-Pfad von falscher Recall-Antwort -> falscher Kontaktkarte.
- Zusaetzlich wurde `was mögen chris und oli?` nicht als Personal-Recall erkannt, weil die Intent-Erkennung nur `was mag`, nicht aber `was mögen` abdeckte.

Fix Summary:
- `backend/tools/memory_tools.py` filtert `memory.read` jetzt bei klar erkannten Kontaktqueries auf passende Kontakt-Aliase und damit auf die richtige Person bzw. die richtigen Personen.
- `backend/services/memory_extractor.py` ueberspringt Faktenextraktion fuer reine Kontakt-Recall-Turns, damit Assistant-Zusammenfassungen nicht mehr als neue Kontaktfakten gespeichert werden.
- `backend/services/orchestrator/intent_engine.py` erkennt nun auch Mehrpersonenfragen wie `was mögen chris und oli?` als Personal-Recall und umgeht damit unnoetige Rueckfragen.
- Die Live-DB wurde fuer `Oliver Schwab` bereinigt: Entfernt wurden die nicht belegten Chris-Vorlieben; erhalten blieben die belegten `Big Bang Theory`, `Panzer General` und `wohnt in Köln Stammheim`.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_memory_tools.py backend/tests/test_contact_manager.py backend/tests/test_calendar_routing_fix.py -q`
  - `python -m py_compile backend/tools/memory_tools.py backend/services/memory_extractor.py backend/services/orchestrator/intent_engine.py backend/tests/test_memory_tools.py backend/tests/test_contact_manager.py backend/tests/test_calendar_routing_fix.py`
  - Live-DB-Check auf `Oliver Schwab` nach Bereinigung

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `backend/tools/memory_tools.py`
- `backend/services/memory_extractor.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_calendar_routing_fix.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_contact_recall_subject_scope_and_self_poison_guard.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/test-runs/TASK-SPEC10.1_debug_contact_recall_subject_scope_and_self_poison_guard.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_fact_statement_ambiguity_bypass.md`
Evidence Paths:
- `backend/tools/memory_tools.py`
- `backend/services/memory_extractor.py`
- `backend/services/orchestrator/intent_engine.py`
Failure Code:
- `CONTACT_RECALL_SUBJECT_CONTAMINATION_AND_SELF_POISON`
Changed Files:
- `backend/tools/memory_tools.py`
- `backend/services/memory_extractor.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/tests/test_memory_tools.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_calendar_routing_fix.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_contact_recall_subject_scope_and_self_poison_guard.md`
Decision:
- `NEEDS RETEST`
Reason:
- Code, Tests und Live-Datenbereinigung sind gruen, aber der Nutzer muss die betroffenen Live-Recall-Saetze nach Janus-Neustart erneut pruefen.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Janus neu starten und nacheinander `was mag oli?`, `was mögen chris und oli?` und `was mag chris?` testen. Erwartung: `Oli` bekommt nur seine eigenen Fakten; `Chris und Oli` werden ohne Rueckfrage getrennt beantwortet; es entstehen keine neuen falschen `Oli`-Vorlieben mehr.
