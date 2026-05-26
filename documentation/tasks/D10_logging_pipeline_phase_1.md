# Task: D10 - Logging Pipeline Phase 1

## 1. Ziel & Kontext
- **Ziel:** Fix für Logging-Problem, bei dem `provider` und `model` als "unknown" geloggt wurden für Diamond-Skills wie `system.weather`.
- **Kontext:** Diamond-Skills bypassen den `ToolExecutor` und werden direkt ausgeführt. Das Logging extrahiert `provider` und `model` aus `additional_context`, aber diese Werte wurden nicht an allen ToolExecutor-Instanziierungen übergeben.

## 2. Impact-Analyse & Abhängigkeiten (CRITICAL)
- **Basiert auf:**
  - `backend/services/tool_executor.py` (Logging-Extraktion aus additional_context)
  - `backend/services/logging/logger_core.py` (Supabase Async Queue)
- **Beeinflusst:**
  - `backend/services/chat_orchestrator.py` (ToolExecutor-Instanziierungen)
  - `backend/services/agent_runtime.py` (ToolExecutor-Instanziierungen)
  - `backend/services/orchestrator/execution_engine.py` (Logging-Pfad)
  - `backend/tools/weather_service.py` (Diamond-Skill Beispiel)
- **Risiko-Einschätzung:** Medium — Zentrale Logging-Infrastruktur, aber Änderungen sind additive (keine Breaking Changes)

## 3. Betroffene Dateien
- `backend/services/chat_orchestrator.py` — `provider` und `model` zu additional_context hinzugefügt (2 Stellen)
- `backend/services/agent_runtime.py` — `provider` und `model` zu additional_context hinzugefügt (3 Stellen)
- `backend/services/tool_executor.py` — Forensische Logs entfernt
- `backend/services/orchestrator/execution_engine.py` — Forensische Logs entfernt
- `backend/tools/weather_service.py` — Forensische Logs entfernt

## 4. Umsetzungsschritte (Strikte Anweisung)
1. **Root Cause Analyse:**
   - Identifiziert, dass `provider` und `model` aus `additional_context` extrahiert werden
   - Gefunden, dass nicht alle ToolExecutor-Instanziierungen diese Werte übergeben

2. **Fix Implementation:**
   - `chat_orchestrator.py` Zeile 1905-1917: `provider` und `model` zu additional_context hinzugefügt
   - `chat_orchestrator.py` Zeile 747-759: `provider` und `model` zu additional_context hinzugefügt
   - `agent_runtime.py` Zeile 60-73: `provider` und `model` zu additional_context hinzugefügt
   - `agent_runtime.py` Zeile 97-112: `provider` und `model` zu additional_context hinzugefügt
   - `agent_runtime.py` Zeile 127-140: `provider` und `model` zu additional_context hinzugefügt
   - Korrektur: `req.chosen_model` → `req.model` (ChatRequest hat `model`, nicht `chosen_model`)

3. **Cleanup:**
   - Forensische Logs aus allen Dateien entfernt (Debug-Code)

## 5. Test-Ergebnisse
- **Test:** `test_logging_fix.py` — ToolExecutor mit ungültiger Stadt aufgerufen
- **Ergebnis:** PASS — Context enthält korrekt `{'chat_id': 999999, 'provider': 'openai', 'model': 'gpt-4o-mini'}`
- **Supabase:** Events wurden zur Queue hinzugefügt, aber Batch-Upload-Worker hat nicht hochgeladen (separates Problem)

## 6. Ergebnis & Audit-Trail
- **Files changed:**
  - `backend/services/chat_orchestrator.py` — `provider` und `model` zu additional_context hinzugefügt (2 Stellen)
  - `backend/services/agent_runtime.py` — `provider` und `model` zu additional_context hinzugefügt (3 Stellen)
  - `backend/services/tool_executor.py` — Forensische Logs entfernt
  - `backend/services/orchestrator/execution_engine.py` — Forensische Logs entfernt
  - `backend/tools/weather_service.py` — Forensische Logs entfernt
- **What was done:** `provider` und `model` werden jetzt konsistent an `additional_context` übergeben bei allen ToolExecutor-Instanziierungen, sodass das Logging korrekte Werte anzeigt (nicht mehr "unknown").
- **Test result:** PASS — Context enthält korrekte provider/model Werte

## 7. Debugging-Log
- **Issue:** ChatRequest-Fehler: `'ChatRequest' object has no attribute 'chosen_model'`
- **Fix:** `req.chosen_model` → `req.model` korrigiert (ChatRequest-Schema hat `model`, nicht `chosen_model`)
- **Keine weiteren Probleme.**

## 8. Epic-Status
- **Epic:** D10 - Logging Pipeline Phase 1
- **Status:** SEALED & COMPLETE (2026-04-25)
- **Erreichte Ziele:**
  - ✅ Metadata Injection Pattern implementiert
  - ✅ Logging-Fix für Diamond-Skills
  - ✅ Forensische Logs entfernt
  - ✅ ChatRequest-Attribut-Fehler behoben
