SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `EXTRACTOR_CONTACT_SYNC_ROLE_GAP`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Der fehlgeschlagene Live-Test `richtig und er liebt star wars und kimchi` lief nicht ueber `memory.write`, sondern ueber `memory_extractor.extract_and_save_fact_from_interaction()`.
- Die extrahierten Fakten fuer `Chris Gier liebt Star Wars` und `Chris Gier liebt Kimchi` hatten `subject_name="chris gier"`, aber `subject_role=null`.
- Im Extractor wurde der Kontakt-Sync nur bei `subject_role == "contact"` angestossen. Dadurch wurde `Kimchi` im Live-Pfad als Memory gespeichert, aber nicht in den bestehenden Adressbuchkontakt gespiegelt.

Fix Summary:
- `backend/services/memory_extractor.py` setzt bei eindeutigem vorhandenen Kontakt-Kontext (`subject_hint` / aufgeloestes Subjekt) fehlende `subject_role` vor Save/Sync auf den bekannten Kontakt-Kontext.
- Neuer Regressionstest deckt den Live-Fall `subject_name vorhanden, subject_role fehlt` ab und verifiziert, dass der bestehende Kontakt trotzdem aktualisiert wird.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q`
  - `python -m py_compile backend/services/memory_extractor.py backend/services/contact_manager.py backend/tools/memory_tools.py backend/services/tool_executor.py`

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/SPEC/10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10.1_preimplementation_check.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_subject_role_fallback.md`
Evidence Paths:
- `documentation/logs/janus_backend.log`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
Failure Code:
- `EXTRACTOR_CONTACT_SYNC_ROLE_GAP`
Changed Files:
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
Decision:
- `NEEDS RETEST`
Reason:
- Die technische Root Cause ist gefixt und automatisiert abgesichert, aber der Nutzer muss den Live-Chat-Pfad nach Backend-Neustart erneut pruefen.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Backend neu starten und denselben Live-Test mit `richtig und er liebt star wars und kimchi` gefolgt von `Was mag Chris Gier?` erneut ausfuehren.
