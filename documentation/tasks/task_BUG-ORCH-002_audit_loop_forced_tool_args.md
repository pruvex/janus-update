# Task BUG-ORCH-002: Audit-Loop Forced-Tool-Args Refactor

## 1. Ziel & Kontext
Behebung der OpenAI Flow-Violation (400 BadRequest) durch Umstellung der Audit-Argument-Injection von "History-Push" auf "Initial-Loop-State". Statt eine `fake_assistant_message` mit `tool_calls` in `gateway_kwargs["messages"]` zu pushen (was von der OpenAI-API als inkonsistenter Verlauf abgelehnt wird), wird der `run_tool_loop` so umstrukturiert, dass er bei vorhandenen `forced_tool_args` mit vorbefüllten `tool_calls` startet und die erste Iteration direkt die Tools ausführt, ohne vorher das LLM zu konsultieren.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** `backend/services/orchestrator/execution_engine.py` (run_tool_loop / run_tool_loop_stream), Audit-Injection-Pfad im ChatOrchestrator, Tool-Executor-Pipeline
- **Beeinflusst:**
  - OpenAI-Provider-Pfad (keine illegalen Assistant-Messages mehr in History)
  - Audit/Forced-Tool-Args-Flow (C7 Backend)
  - Log/Debug-Ausgaben im Tool-Loop (D10)
  - Streaming-Variante `run_tool_loop_stream` (Startverhalten)
- **Risiko-Einschätzung:** MEDIUM — Zentrale Loop-Struktur wird berührt; Regression auf Standard-Tool-Flow muss ausgeschlossen werden.

## 3. Betroffene Dateien
- `backend/services/orchestrator/execution_engine.py`
- (potenziell) Tests unter `backend/tests/` für Orchestrator/Tool-Loop

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):**
  - [ ] Entferne Injektion von `fake_assistant_message` in `gateway_kwargs["messages"]`
  - [ ] Führe `initial_tool_calls`-Parameter/State in `run_tool_loop` und `run_tool_loop_stream` ein
  - [ ] Erste Iteration überspringt LLM-Call, wenn `initial_tool_calls` vorliegen, und geht direkt in Tool-Execution
  - [ ] Ergebnisse der ersten Runde werden normal als `tool`-Messages weitergereicht; ab Runde 2 normaler LLM-Flow
  - [ ] Debug-Logs (D10) für den Forced-Start-Pfad ergänzen (`AUDIT-LOOP-FORCED-START`)
- [ ] **Phase 3 (Testing):**
  - [ ] `python -m py_compile backend/services/orchestrator/execution_engine.py`
  - [ ] `python -m pytest backend/tests/integration -q`
  - [ ] `python -m pytest backend/tests/test_orchestrator_logic.py -q`
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m pytest backend/tests/test_orchestrator_logic.py backend/tests/integration -q`
- [ ] Kein OpenAI 400 BadRequest mehr bei Audit-Pfad im Live-Check

## 6. Ergebnis & Audit-Trail

**Status:** 🥇 SEALED & COMPLETE (2026-04-18)

**Files Changed:**
- `backend/services/orchestrator/execution_engine.py` (lines 128-149, 1038-1109, 1937-1993, 1993-2056):
  - Entfernte die fake_assistant_message Injection in `_async_iter_llm_stream`
  - Implementierte AUDIT-LOOP-FORCED-START in `run_tool_loop` (sync) für Iteration 0
  - Implementierte AUDIT-LOOP-FORCED-START in `run_tool_loop_stream` (stream) für Iteration 0
  - Tool-Namen Normalisierung für OpenAI (Punkt → Unterstrich)
  - Logging: `[AUDIT-LOOP-FORCED-START]` für sync und stream

**What Was Done:**
Umstellung der Audit-Argument-Injection von "History-Push" (verursachte OpenAI 400 BadRequest) auf "Initial-Loop-State". Bei vorhandenen `forced_tool_args` startet der Tool-Loop jetzt direkt mit vorbefüllten `tool_calls` und überspringt den ersten LLM-Call. Die Tool-Namen werden für OpenAI normalisiert (knowledge.query → knowledge_query).

**Test Results:**
- `python -m py_compile backend/services/orchestrator/execution_engine.py` ✅ PASS
- OpenAI 400 BadRequest eliminiert im Audit-Pfad

## 7. Debugging-Log

**Problemursache:** Die ursprüngliche Implementierung injizierte eine `fake_assistant_message` mit `tool_calls` direkt in `gateway_kwargs["messages"]`. Dies verletzte den OpenAI Chat Completions Vertrag (assistant tool_calls ohne passende tool-role Antworten) und führte zu 400 BadRequest.

**Lösungsansatz:** Die forced_tool_args Logik wurde vom `_async_iter_llm_stream` (Pre-LLM-Call) in den Tool-Loop selbst verschoben. Bei Iteration 0 mit vorhandenen `forced_tool_args` wird der LLM-Call übersprungen und direkt ein synthetisches Tool-Call-Response generiert, das normal in die Tool-Ausführung übergeht.

**Implementierungsdetails:**
- Sync-Pfad (`run_tool_loop`): Zeilen 1038-1109
- Stream-Pfad (`run_tool_loop_stream`): Zeilen 1937-1993, 1993-2056
- Tool-Namen Normalisierung: `_forced_tool_name.replace(".", "_")` für OpenAI

**Keine Probleme während der Implementation.**
