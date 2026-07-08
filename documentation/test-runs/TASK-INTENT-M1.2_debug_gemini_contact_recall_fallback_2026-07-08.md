SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 2
Progress-Validierung: Failure Code `GEMINI_CONTACT_RECALL_HISTORY_DRIFT`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN
Root Cause:
- Nach dem Live-DB-Cleanup war der Re-Test erstmals aussagekraeftig: GPT antwortete auf `Was weisst du ueber Chris?` sauber aus den lokalen Kontaktvorlieben, Gemini dagegen mischte weiterhin ungestuetzte Appearance-/Zeitstempel-Fakten in die Antwort.
- Der Unterschied lag nicht mehr in der lokalen Kontaktkarte, sondern im providerabhaengigen Antwortpfad nach `memory.read`: Bei kontaktbezogenem Recall durfte Gemini trotz vorhandener lokaler Facts noch freie Verlaufs-/Syntheseantworten ueber den Tool-Output stellen.
- Dadurch war der Recall-Pfad fuer Kontaktfragen nicht deterministisch genug und konnte alte oder ungestuetzte History-Fragmente ueber lokale `memory.read`-Resultate legen.

Fix Summary:
- `backend/services/orchestrator/execution_engine.py` erkennt kontaktbezogene Recall-Fragen jetzt explizit (`Was weißt du über ...`, `Was mag ...`, `Welche Vorlieben/Hobbys hat ...`, Beziehungs-Recall usw.).
- Wenn fuer solche Recall-Fragen lokale `memory.read`-Fakten vorliegen, wird der stabile lokale Memory-Fallback jetzt deterministisch forciert statt nur bei leerem/generischem Modelltext.
- Neue Unit-Regression deckt den Force-Fallback fuer Kontakt-Recall direkt ab.
- Neue Integrations-Regression simuliert genau den Gemini-Fall: `memory.read` liefert saubere Chris-Fakten, der zweite Modellschritt liefert absichtlich kontaminierten Appearance-Freitext, und Janus antwortet trotzdem mit dem lokalen Recall-Fallback.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_provider_auth_fallback.py backend/tests/integration/test_pet_recall_chat_path.py -q`
  - `python -m py_compile backend/services/orchestrator/execution_engine.py`
  - `git diff --check -- backend/services/orchestrator/execution_engine.py backend/tests/test_provider_auth_fallback.py backend/tests/integration/test_pet_recall_chat_path.py`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON
Changed Files:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
- `documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md`
- `documentation/ai/CURRENT_STATE.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/TASK-INTENT-M1.2_execution_result.md`
- `documentation/test-runs/TASK-INTENT-M1.2_debug_live_db_contamination_cleanup_2026-07-08.md`
- `documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md`
Evidence Paths:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
Failure Code:
- `GEMINI_CONTACT_RECALL_HISTORY_DRIFT`
Changed Files:
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_provider_auth_fallback.py`
- `backend/tests/integration/test_pet_recall_chat_path.py`
- `documentation/test-runs/TASK-INTENT-M1.2_debug_gemini_contact_recall_fallback_2026-07-08.md`
- `documentation/ai/CURRENT_STATE.md`
Decision:
- `NEEDS RETEST`
Reason:
- Der provider-spezifische Recall-Drift fuer Gemini ist jetzt lokal gefixt und testabgesichert, aber der echte Janus-Livepfad muss mit demselben Chris-Recall noch einmal bestaetigt werden.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Janus normal starten und denselben Test erneut fahren: `Was weisst du ueber Chris?` zuerst mit GPT und dann mit Gemini. Erwartung: beide bleiben auf den lokalen Chris-Vorlieben und nennen keine Appearance-/Brillen-/Piercing-/Groessenfakten mehr.
