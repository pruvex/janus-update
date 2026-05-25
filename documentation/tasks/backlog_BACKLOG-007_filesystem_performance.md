# BACKLOG TASK - BACKLOG-007 - Performance-Optimierung fuer Filesystem-Tool-Calls

## 1. Ziel
Unnoetige Tool-Aufrufe werden reduziert, Tool-Call-Effizienz ist verbessert, und provider-spezifischer Overhead wird im lokalen Tool-Payload-Hot-Path kleiner. Die bestehende Janus-Provider-Agnostik bleibt unveraendert: kein Hidden-Fallback auf einen anderen Provider.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-007
- **Beeinflusst:** Backend / Performance / Tool-Call-Effizienz / Model-Selection / Prompt-Cache
- **Risiko-Einschaetzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Unnoetige Tool-Aufrufe reduzieren (z.B. alias-/duplikatbedingte Mehrfachangebote fuer dieselbe Filesystem-Capability).
- Tool-Call-Effizienz verbessern (weniger redundante Tool-Payload-Builds).
- BACKLOG-022-Scope integrieren: duplicate Tool-List-Konstruktion und Gemini duplicate Tool-Sanitization.
- Model-Selection fuer einfache Tasks pruefen, ohne die konfigurierte Janus Model-Policy oder Provider-Silos zu umgehen.
- Prompt-Cache-Effizienz verbessern durch stabile kanonische Tool-/Skill-Keys.
- Performance-Unterschied zwischen Providern im lokalen Tool-Payload-Hot-Path reduzieren.

### OUT OF SCOPE
- Aenderung an Filesystem-Tool-Implementierungen selbst.
- Aenderung an Provider-Integration, Model-Katalog oder Cross-Provider-Fallback.
- Live-Benchmark mit echten externen Provider-Calls als harte Abschlussbedingung.

## 4. Umsetzung
1. Tool-Registry/Tool-Manager analysiert: ein Tool wird unter Skill-ID und Alias-Varianten registriert.
2. Gemeinsame Skill-ID-Normalisierung fuer allowed_skill_ids eingefuehrt.
3. `_filter_tools_by_skill_ids` liefert kanonische, duplikatfreie Tools in Skill-Prioritaetsreihenfolge.
4. `tool_manager.get_tool_definitions` nutzt kanonische Cache-Keys, sodass Alias-Varianten denselben Cache-Pfad treffen.
5. `llm_gateway.reason_and_respond` normalisiert explizite und automatisch selektierte Skill-Listen vor Silo-Uebergabe.
6. OpenAI- und Gemini-Tool-Loops bauen `tools_for_call` einmal pro Turn statt in jeder Tool-Runde neu.
7. Regressionsschutz fuer OpenAI und Gemini beweist, dass auch mehrstufige Tool-Loops die Payload nur einmal bauen.

## 5. Acceptance Criteria
- [x] Unnoetige Tool-Aufrufe werden reduziert: alias-/duplikatbedingte Mehrfachangebote fuer dieselbe Filesystem-Capability werden vor dem Provider-Payload entfernt.
- [x] Tool-Call-Effizienz ist verbessert: OpenAI- und Gemini-Tool-Loops bauen die gefilterte Tool-Payload einmal pro Turn statt einmal pro Tool-Runde.
- [x] Tool list contains no duplicate entries; duplicate sanitization overhead is minimal (BACKLOG-022 merged scope).
- [x] Model-Selection fuer einfache Tasks ist reviewt und geschuetzt: Skill-Prioritaet bleibt stabil, MoA/Model-Policy und provider-agnostische Routing-Regeln wurden nicht durch Hidden-Fallbacks veraendert.
- [x] Prompt-Cache-Effizienz ist verbessert: stabile kanonische allowed_skill_ids vermeiden aliasbedingte Cache-Key-Spreizung in Tool-Definition-Caches.
- [x] Performance-Unterschied zwischen Modellen ist reduziert im lokalen Hot-Path: wiederholte Tool-Definition-Builds und Gemini-Duplicate-Sanitization fuer identische Aliase sind regressionsgeschuetzt entfernt.

## 6. Tests / Validierung
- `python -m pytest backend\tests\test_backlog_007_tool_routing_performance.py -q` -> PASS 5/5.
- `python -m pytest tests\test_backlog_parser.py backend\tests\test_mcp_debug_auth_preflight.py backend\tests\test_backlog_007_tool_routing_performance.py -q` -> PASS 14/14.
- `python -m py_compile backend\llm_providers\shared\utils.py backend\llm_providers\openai\gateway.py backend\llm_providers\gemini\gateway.py backend\services\llm_gateway.py backend\services\tool_manager.py backend\tests\test_backlog_007_tool_routing_performance.py` -> PASS.
- `npm run sync:backlog` -> PASS after BACKLOG-007 documentation update.
- `npm run build --workspace=@janus-dashboard/api` -> PASS.
- `npm run build --workspace=@janus-dashboard/ui` -> PASS.
- Final audit: `documentation/test-runs/BACKLOG-007_final_audit.md`.

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Lokale Performance-Verbesserung mit deterministischem Scope (Tool-Call-Effizienz, Skill-ID-Normalisierung, Cache-Key-Stabilitaet).

## 8. Abschluss
- **Status:** DONE
- **Completed at:** 2026-05-21
- **Completed by:** SKILL 7 - DOKUMENTATIONSUPDATE
- **Validation evidence:** siehe Abschnitt 6 und `documentation/test-runs/BACKLOG-007_final_audit.md`.
