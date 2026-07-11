SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 5

Progress-Validierung: Failure Code CONTACT_FOLLOWUP_MEMORY_WRITE_MISSING_CONTACT_SUBJECT + CONTACT_SAVE_CONFIRMATION_EMPTY_RESPONSE; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
Der manuelle Janus-Test vom 2026-06-08 um ca. 16:32 zeigte nach erfolgreichem Recall eine neue Anschlussfehlerkette:

- Nutzer: `richtig und er liebt star wars und kimchi`
- Janus schrieb zwar globales Memory `Chris Gier liebt Star Wars und Kimchi.`
- Zwei Gemini-Toolcalls nutzten das alte Batch-Argumentformat `entries` und scheiterten vor der Legacy-Harmonisierung an `INVALID_ARGUMENTS`.
- Der dritte Toolcall war formal gueltig, enthielt aber kein `subject_name`; dadurch meldete das Kontakt-Update `contact_proposal.reason=missing_subject` und schrieb nicht ins Adressbuch.
- Nach erfolgreichem `memory.write` blieb die Antwortsynthese leer, wodurch Janus statt einer Speicherbestaetigung den generischen Robustheitsfallback ausgab.

Zusaetzlich bleibt die vorherige Iteration Teil des korrigierten Umfangs:

- `Chris ist Vegetarier` gehoert in `personal_details`/Besonderheiten, nicht in `preferences`.
- Bestehende falsch persistierte Diaet-Werte werden beim Kontakt-CRUD aus `preferences` nach `personal_details` migriert.
- Kontakt-Recall darf aus lokalen Memory-/Adressbuchdaten antworten, ohne Web/RSS/Wikipedia oder Identitaetsklarstellung.

Fix Summary:
`ToolExecutor.execute_tool_call` normalisiert `memory.write`-Legacy-Batchargumente jetzt vor der Pydantic-Schema-Pruefung. Aus `{"entries": [{"text": "...", "tags": ["Chris Gier", "Vorlieben"], "priority": 0.8}]}` wird ein aktueller Einzelfakt mit `fact`, `priority_override`, `tags`, `subject_name="Chris Gier"` und `category="Vorlieben"`. Der Guard deckt nun beide internen Toolnamen ab: `memory_write` und `memory.write`.

`contact_manager.stage_contact_update_from_memory` kann fehlende Kontakt-Subjekte nun aus dem Fakttext ableiten, wenn ein bestehender Kontaktname oder Nickname vor dem Kontaktpraedikat steht, z. B. `Chris Gier liebt ...`. Sichere, exakte Kontaktfakten aus `source_type="tool"` duerfen wie textbasierte Fakten direkt angewendet werden, solange sie nur erlaubte Felder betreffen und nicht sensitiv sind.

Kontakt-Vorlieben aus einfachen Konjunktionen werden gesplittet: `Star Wars und Kimchi` landet als `["star wars", "kimchi"]`, waehrend laengere Phrasen wie `Zeit im Garten` nicht zerlegt werden.

Der Tool-Loop hat einen deterministischen `memory.write`-Fallback erhalten. Wenn nach erfolgreichem Speicher-Tool keine stabile Modellantwort entsteht, bestaetigt Janus lokal. Bei angewendetem Kontaktupdate lautet der Fallback sinngemaess, dass der Fakt im lokalen Gedaechtnis und im Adressbuch vermerkt wurde.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_contact_manager.py backend/tests/test_provider_auth_fallback.py backend/tests/test_calendar_routing_fix.py -q` PASS, 49 passed
  - `python -m py_compile backend/services/tool_executor.py backend/services/contact_manager.py backend/services/orchestrator/execution_engine.py backend/tests/test_contact_manager.py backend/tests/test_provider_auth_fallback.py backend/tests/test_calendar_routing_fix.py` PASS

Artifact Identity Check: PASS

Final Feature Suite: PASS

Changed Files:
- `backend/services/tool_executor.py`
- `backend/services/contact_manager.py`
- `backend/services/orchestrator/execution_engine.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_provider_auth_fallback.py`
- `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: NEEDS_INFO
Required Artifacts: `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`; current manual Janus test result
Evidence Paths: `backend/tests/test_contact_manager.py`; `backend/tests/test_provider_auth_fallback.py`; `backend/tests/test_calendar_routing_fix.py`; `backend/services/tool_executor.py`; `backend/services/contact_manager.py`; `backend/services/orchestrator/execution_engine.py`
Failure Code: CONTACT_FOLLOWUP_MEMORY_WRITE_MISSING_CONTACT_SUBJECT + CONTACT_SAVE_CONFIRMATION_EMPTY_RESPONSE
Changed Files: `backend/services/tool_executor.py`, `backend/services/contact_manager.py`, `backend/services/orchestrator/execution_engine.py`, `backend/tests/test_contact_manager.py`, `backend/tests/test_provider_auth_fallback.py`, `documentation/test-runs/BACKLOG-108_contact_fact_routing_debug.md`
Decision: Wait for manual Janus validation before any final audit.
Reason: Auto-verification is green, but the user-reported live Janus path must pass before routing to final audit.
Recommended Model: 5.4
Recommended Intelligence: hoch
Next User Action: Restart Janus if the backend is already running with old code, then run the manual Janus test below. If it fails, continue `janus-debug`; if it passes, proceed to `janus-final-audit`.
