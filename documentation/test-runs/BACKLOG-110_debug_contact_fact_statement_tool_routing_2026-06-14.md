SKILL 5 DEBUG RESULT: NEEDS RETEST

Iteration: 1
Progress-Validierung: Failure Code `CONTACT_FACT_STATEMENT_TOOL_ROUTING_GAP`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Iteration: 2
Progress-Validierung: Failure Code `CONTACT_FACT_STATEMENT_LIVE_SKILL_SELECTOR_AND_PRONOUN_CONTEXT_GAP`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- Der fuer freie Kontakt-Faktsaetze gedachte Extraktionspfad `extract_and_save_contact_from_text(...)` war im normalen Chat-Toolkatalog nicht registriert.
- `ToolSelector` bot bei Aussagen wie `Oliver Schwab wohnt in Köln-Stammheim` oder `und er hat einen Hund` deshalb keinen dedizierten Kontakt-Extraktionskandidaten an.
- Im Live-Chat konnte das Modell dadurch direkt in eine vorsichtige Drittpersonen-Antwort kippen, statt den Kontakt-/Adressbuchpfad zu nutzen.
- In der naechsten Debug-Stufe zeigte sich zusaetzlich ein zweiter Runtime-Seam: Die Candidate-Selektion verwendete zunaechst noch den Legacy-Funktionsnamen, waehrend die finale Tooldefinition ueber die Skill-ID `contacts.extract_from_text` lief. Dadurch konnte `select_tools(...)` den neuen Kandidaten trotz Registrierung wieder verlieren.
- Der Live-Retest um 23:15 zeigte einen weiteren Runtime-Seam: Der Hintergrund-Extractor speicherte `Oliver Schwab wohnt in Köln-Stammheim`, aber der user-facing Hauptpfad antwortete weiterhin wie bei einer Wissens-/Verifikationsfrage.
- Der echte `SkillSelector`/Capability-Registry-Pfad lud bei Kontakt-Faktsaetzen noch keinen `contacts.extract_from_text` Pflichtskill; die erste Reparatur im Chat-`ToolSelector` deckte diesen zweiten Pfad nicht ab.
- Der Folgesatz `und er hat einen Hund` wurde nicht als Fact-Telling erkannt, lief deshalb in den Ambiguity-Block, deaktivierte Tools und erzeugte eine Klaerungsfrage.
- Die Kontextanker-Funktion `get_last_subject_from_chat(...)` pruefte nur den allerneuesten Memory-Eintrag. Wenn dieser `unbekannt` oder ohne verwertbare Subjektrolle war, konnte der Pronomen-Kontext nicht auf den letzten brauchbaren Kontaktanker zurueckfallen.

Fix Summary:
- `backend/tool_registry.py` registriert jetzt `extract_and_save_contact_from_text` mit `ContactExtractionArgs` im echten Runtime-Toolkatalog.
- `backend/services/chat/tool_selector.py` bietet die Kontakt-Extraktion jetzt auch fuer einfache Kontakt-Faktsaetze an, selbst wenn der Nutzer nicht explizit `Kontakt` oder `Adressbuch` sagt.
- `backend/services/chat/tool_selector.py` verwendet dafuer jetzt durchgaengig die Skill-ID `contacts.extract_from_text`, damit Candidate-Selektion und finale Toolliste denselben Identifier benutzen.
- Ein neues Skill-Mapping unter `backend/skills/contacts/extract_from_text.json` macht den Pfad im Skill-System sauber bekannt.
- `backend/services/orchestrator/intent_engine.py` erkennt jetzt auch Kontakt-Wohnort-/Besitzsaetze und Pronomen-Folgesaetze wie `und er hat einen Hund` als Fact-Telling, sodass der Ambiguity-Block nicht mehr greift.
- `backend/services/capability_registry.py` macht bei Fact-Telling `memory.write` und `contacts.extract_from_text` im Registry-basierten SkillSelector-Pfad mandatory und sperrt externe Wissenssuche.
- `backend/services/memory/retrieval_service.py` sucht den letzten brauchbaren Kontaktanker in den letzten 20 Chat-Memories und ueberspringt `unbekannt`, statt nur den allerneuesten Eintrag zu pruefen.
- Neue Regressionen decken Wohnort- und Haustier-Folgesaetze, Registry-Pflichtskill und robusteren Kontaktanker ab.

Auto-Verification:
- Status: PASS
- Evidence:
- `python -m py_compile backend/tool_registry.py backend/services/chat/tool_selector.py backend/tests/test_tool_selector_contact_routing.py`
- `python -m pytest backend/tests/test_tool_selector_contact_routing.py -q`
- `python -m pytest backend/tests/test_contact_manager.py -q`
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`
- `python -m pytest backend/tests/test_contact_manager.py -q -k extract_and_save_contact_stages_private_contact_proposal`
- `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/capability_registry.py backend/services/memory/retrieval_service.py backend/tests/test_calendar_routing_fix.py backend/tests/unit/test_skill_selector_filesystem_calendar.py backend/tests/test_memory_tools.py`
- `python -m pytest backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_pronoun_contact_fact_followup_bypasses_ambiguity_clarification backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_contact_fact_statement_bypasses_ambiguity_clarification -q`
- `python -m pytest backend/tests/unit/test_skill_selector_filesystem_calendar.py::TestSkillSelectorFilesystemCalendar::test_registry_fact_telling_loads_memory_and_contact_extraction -q`
- `python -m pytest backend/tests/test_memory_tools.py::test_get_last_subject_from_chat_skips_unknown_or_unscoped_recent_memory -q`
- `python -m pytest backend/tests/test_tool_selector_contact_routing.py backend/tests/test_contact_manager.py -q`
- `python -m pytest backend/tests/unit/test_skill_selector_filesystem_calendar.py backend/tests/test_calendar_routing_fix.py -q`

Artifact Identity Check: PASS
Final Feature Suite: N/A WITH REASON

Changed Files:
- `backend/tool_registry.py`
- `backend/services/chat/tool_selector.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/capability_registry.py`
- `backend/services/memory/retrieval_service.py`
- `backend/skills/contacts/extract_from_text.json`
- `backend/tests/test_tool_selector_contact_routing.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/unit/test_skill_selector_filesystem_calendar.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-110_debug_contact_fact_statement_tool_routing_2026-06-14.md`

NEXT_STEP
Target Skill: janus-debug
Canonical State: HANDOFF
Required Artifacts:
- `documentation/test-runs/BACKLOG-110_debug_contact_fact_statement_tool_routing_2026-06-14.md`
- `documentation/test-runs/BACKLOG-110_execution_validation.md`
- `documentation/ai/CURRENT_STATE.md`
Evidence Paths:
- `backend/tool_registry.py`
- `backend/services/chat/tool_selector.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/capability_registry.py`
- `backend/services/memory/retrieval_service.py`
- `backend/tests/test_tool_selector_contact_routing.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/unit/test_skill_selector_filesystem_calendar.py`
- `backend/tests/test_memory_tools.py`
Failure Code:
- `CONTACT_FACT_STATEMENT_LIVE_SKILL_SELECTOR_AND_PRONOUN_CONTEXT_GAP`
Changed Files:
- `backend/tool_registry.py`
- `backend/services/chat/tool_selector.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/capability_registry.py`
- `backend/services/memory/retrieval_service.py`
- `backend/skills/contacts/extract_from_text.json`
- `backend/tests/test_tool_selector_contact_routing.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/unit/test_skill_selector_filesystem_calendar.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-110_debug_contact_fact_statement_tool_routing_2026-06-14.md`
Decision:
- `NEEDS RETEST`
Reason:
- Die lokale Debug-Reparatur ist testgruen, aber der echte Janus-Livepfad muss nach App/Backend-Neustart erneut mit einer normalen Doku-/Adressbuch-Aussage verifiziert werden.
Recommended Model:
- `5.4`
Recommended Intelligence:
- `medium`
Next User Action:
- Janus/Backend neu starten und erneut `Oliver Schwab wohnt in Köln-Stammheim` sowie direkt danach `und er hat einen Hund` testen. Erwartung: kein `keine verifizierten Fakten` und keine Pronomen-Klaerungsfrage mehr; stattdessen Kontakt-/Memory-/Adressbuch-Bestaetigung oder sauberer Update-Vorschlag.
