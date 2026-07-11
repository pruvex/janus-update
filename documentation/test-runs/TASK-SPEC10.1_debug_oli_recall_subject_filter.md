SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `MEMORY_READ_FALLBACK_SUBJECT_CONTAMINATION`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Die Live-Antwort auf `Was weißt du über Oli?` kam aus `_build_memory_read_fallback_response(...)` in `backend/services/orchestrator/execution_engine.py`.
- Dieser Fallback sammelte bisher alle `memory.read`-Fakten aus dem Tool-Ergebnis und renderte sie ungefiltert, auch wenn die Nutzerfrage klar auf einen einzelnen Kontakt wie `Oli` zielte.
- Dadurch konnten bei einem breiten `memory.read`-Trefferbild fremde Kontaktfakten wie `Chris gier liebt star wars` und `Chris gier liebt kimchi` in die `Oli`-Antwort hineinlaufen.

Fix Summary:
- `_build_memory_read_fallback_response(...)` filtert jetzt bei personenzentrierten Recall-Fragen die Memory-Fakten anhand der Subjekt-Terme aus der Nutzerfrage.
- Fuer `Oli`- und `Oliver Schwab`-Anfragen wird zusaetzlich eine spezifische Intro-Zeile erzeugt statt der generischen lokalen-Gedächtnis-Einleitung.
- Neue Regression stellt sicher, dass ein gemischtes `memory.read`-Payload fuer `Oli` nur `Oli`-Fakten rendert und keine `Chris`-Fakten.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_provider_auth_fallback.py -q`
  - `python -m py_compile backend/services/orchestrator/execution_engine.py backend/tests/test_provider_auth_fallback.py`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_recall_subject_filter.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_recall_subject_filter.md`
- `documentation/test-runs/TASK-SPEC10.1_debug_live_db_reconstruction_apply.md`
Evidence Paths:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
Failure Code:
- `MEMORY_READ_FALLBACK_SUBJECT_CONTAMINATION`
Changed Files:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
- `documentation/test-runs/TASK-SPEC10.1_debug_oli_recall_subject_filter.md`
Decision:
- `NEEDS RETEST`
Reason:
- Der Fallback-Recall ist jetzt gefiltert und testgrün, aber der Nutzer muss den Live-Pfad mit Janus neu starten und erneut gegen `Oli` verifizieren.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Janus neu starten und `Was weißt du über Oli?` erneut testen. Danach optional `Was macht Chris gerne?`, um sicherzustellen, dass Chris-Fakten weiterhin korrekt beantwortet werden.
