SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code `CONTACT_RECALL_IDENTITY_POISON`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Kontaktgebundene Recall-Turns wie `Was weißt du alles über Chris Gier?` konnten in `backend/services/memory_extractor.py` weiterhin ein falsches `user:physis:heisst:name` erzeugen, obwohl der Turn auf einen bestehenden Kontakt gebunden war.
- Weil fuer diese Recall-Fakten teils `subject_role` fehlte, griff die spaetere Identity-Normalisierung nicht sauber kontaktseitig, und es entstanden falsche `user`-Memories wie `Chris Gier`, `vegetarier`, `star wars` und `kimchi`.
- Die drei sichtbaren Kontaktkarten in der Live-App waren kein neuer Produktpfad, sondern lokale Debug-Dubletten in der App-DB: `Christoph Gier` zweimal und `Chris Gier` einmal.

Fix Summary:
- `backend/services/memory_extractor.py` verwirft jetzt auf kontaktgebundenen Turns ohne Selbstvorstellung jeden extrahierten Identity-Slot fuer `user`.
- Der Extractor backfillt bei eindeutigem Kontakt-Subjekt fehlende `subject_role` frueher, noch vor der Identity-Normalisierung.
- Neuer Regressionstest simuliert genau den vergifteten Recall-Fall und verifiziert, dass kein `user:physis:heisst:name` gespeichert wird und der Kontaktfakt trotzdem auf `Chris Gier` landet.
- Live-App-DB bereinigt: falsche `user`-Memories `17/18/19/20` entfernt bzw. repariert, korrekter Identity-Slot `Rolf Adam` wiederhergestellt, Debug-Dubletten `Kontakt 2/3` in den urspruenglichen Kontakt gemerged.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q`
  - `python -m py_compile backend/services/memory_extractor.py backend/services/contact_manager.py backend/tools/memory_tools.py backend/services/tool_executor.py`
  - Live-DB-Verifikation per SQLAlchemy-Skript: Identity-Slot laedt als `Rolf Adam`, `USER_POISON_COUNT=0`, nur noch ein `Christoph Gier`-Kontakt vorhanden

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_identity_poison_cleanup.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/SPEC/10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10.1_preimplementation_check.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_subject_role_fallback.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_identity_poison_cleanup.md`
Evidence Paths:
- `documentation/logs/janus_backend.log`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
Failure Code:
- `CONTACT_RECALL_IDENTITY_POISON`
Changed Files:
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_identity_poison_cleanup.md`
Decision:
- `NEEDS RETEST`
Reason:
- Codefix und Live-Datenreparatur sind erfolgt, aber der Nutzer muss den echten Janus-Recall-Pfad nach Neustart noch einmal bestaetigen.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Janus komplett neu starten und zuerst `Was weißt du alles über Chris Gier?` testen. Danach `Was mag Chris Gier?`. Erwartung: kein `Hallo Chris Gier`, keine Dubletten, und `Star Wars`, `Kimchi`, `Vegetarier` kommen nur als Kontaktwissen zu Chris.
