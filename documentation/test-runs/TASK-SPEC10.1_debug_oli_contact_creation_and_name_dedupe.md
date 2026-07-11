SKILL 5 DEBUG RESULT: BLOCKED

Iteration: 3
Progress-Validierung: Failure Code `NEW_CONTACT_MEMORY_CREATE_AND_NAME_DEDUPE`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- `stage_contact_update_from_memory()` konnte bestaetigte Kontakt-Memories nur auf bestehende Kontakte anwenden. Neue Kontakte wie `Oli (Oliver Schwab)` wurden deshalb trotz klarer Direktnennung nicht ins Adressbuch uebernommen.
- Der Extractor liess redundante Namensvarianten wie `heißt` und `heisst_voller_name` als getrennte Fakten durch, wodurch derselbe Namensfakt mehrfach im Recall auftauchte.
- Wohnortfakten wie `wohnt in Köln-Stammheim` drifteten zwischen Detail- und Adresspfad.

Fix Summary:
- `backend/services/contact_manager.py` kann jetzt aus direkten, bestaetigten Namensfakten neue private Kontakte anlegen.
- Namensfakten werden als `name`/`nickname` fuer Kontakte erkannt; Wohnortfakten werden als Detail stabilisiert.
- Nicht-sensitive `personal_details` sowie kontaktbezogene Namensupdates koennen bei exaktem Match direkt angewendet werden.
- `backend/services/memory_extractor.py` normalisiert Kontakt-Namens- und Wohnortfakten vor der Canonical-Key-Erzeugung, damit `heißt`/`voller Name` und Wohnortvarianten dedupliziert werden.
- Regressionen decken neuen Kontakt aus Namensfakt plus Namens-Dedupe im Extractor ab.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py -q`
  - `python -m py_compile backend/services/memory_extractor.py backend/services/contact_manager.py backend/tools/memory_tools.py backend/services/tool_executor.py`

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_contact_creation_and_name_dedupe.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: BLOCKED
Required Artifacts:
- `documentation/SPEC/10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10_contact_memory_reconciliation.md`
- `documentation/tasks/TASK-SPEC10.1_preimplementation_check.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_contact_creation_and_name_dedupe.md`
Evidence Paths:
- `documentation/logs/janus_backend.log`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
Failure Code:
- `NEW_CONTACT_MEMORY_CREATE_AND_NAME_DEDUPE`
Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_contact_creation_and_name_dedupe.md`
Decision:
- `BLOCKED`
Reason:
- Der Codefix ist grün, aber bei der Live-Reproduktion wurde die lokale App-DB versehentlich mit einem Test-Cleanup getroffen. Es konnte nur ein minimaler Teilzustand aus dem Chatverlauf wiederhergestellt werden; vor weiterem Vorgehen braucht es Nutzerentscheidung fuer weitere Rekonstruktion oder Restore aus externer Sicherung.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Entscheiden, ob eine weitergehende Rekonstruktion aus `messages` versucht werden soll oder ob eine externe DB-Sicherung eingespielt wird. Danach erst Live-Retest des `Oli`-Pfads.
