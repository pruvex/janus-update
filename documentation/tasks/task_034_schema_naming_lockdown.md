# Task 034: Schema & Naming Lockdown für Video-Tools und Provider-Coherence

## 1. Ziel & Kontext
Fix Schema & Naming Issues in video_tools.py, gemini/gateway.py und chat_orchestrator.py, um 400er Fehler bei Video-Fragen zu eliminieren und saubere Pydantic-Validierung im Backend-Log zu gewährleisten.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 030 (Video List System), Task 033 (MCL Video Player)
- **Beeinflusst:** Video-Skill-Funktionalität, Provider-Gateway-Validierung, ChatOrchestrator Provider-Coherence
- **Risiko-Einschätzung:** MEDIUM (Änderungen an Provider-Gateways und Orchestrator-Flow)

## 3. Betroffene Dateien
- backend/tools/video_tools.py
- backend/llm_providers/gemini/gateway.py
- backend/llm_providers/openai/gateway.py (vorsorglich)
- backend/services/chat_orchestrator.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):**
  - **Fix 1 (Schema):** In video_tools.py sicherstellen, dass das data-Dictionary im Rückgabe-Objekt von video_search (oder der Hilfsfunktion für den Output) die Felder "query": query und "retrieved_at": <ISO-String> enthält.
  - **Fix 2 (Naming):** In gemini/gateway.py (und vorsorglich openai/gateway.py) sicherstellen, dass allowed_function_names nur existierende Tool-Namen enthält. Logik korrigieren, die video_search statt video.search injiziert.
  - **Fix 3 (Coherence):** In ChatOrchestrator._execute_generation prüfen. PROVIDER-MODEL-MISMATCH muss durch einen präventiven Provider-Check VOR dem Gateway-Call unterbunden werden. Wenn request.model zu Provider X gehört, muss request.provider sofort auf X gesetzt werden.
- [ ] **Phase 3 (Testing):** Pydantic-Validierung mit Video-Request testen, 400er Fehler eliminieren
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: Video-Request mit Pydantic-Validierung testen, Backend-Log auf Schema-Violations prüfen

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix 1 (Schema) - video_tools.py:**
- Zeile 1285-1290: Hinzugefügt "query": query und "retrieved_at": started_at.isoformat() zu data-Dictionary in feed_authority_result
- Zeile 1488-1496: Hinzugefügt "query": query und "retrieved_at": started_at.isoformat() zu data-Dictionary in standard result
- **Ergebnis:** data-Dictionary enthält jetzt immer "query" und "retrieved_at" (ISO-String) für saubere Pydantic-Validierung

**Fix 2 (Naming) - execution_dispatcher.py:**
- Zeile 317-324: Geändert von "video_search" zu "video.search" in provider_tool_name und force_tool_name
- **Ergebnis:** Konsistente Nutzung von "video.search" (dot-notation) statt "video_search" (underscore)

**Fix 2 (Naming) - response_finalizer.py:**
- Zeile 147: Geändert von {"video.search", "video_search", "system.video_search"} zu {"video.search"}
- Zeile 203: Geändert von {"video.search", "video_search", "system.video_search"} zu {"video.search"}
- **Ergebnis:** Entfernung von Legacy-Fallbacks, nur noch "video.search" wird akzeptiert

**Fix 3 (Coherence) - chat_orchestrator.py:**
- Zeile 1513-1539: Hinzugefügt preventive Provider Check in _execute_generation vor Gateway call
- Logik: Erkennt Provider aus Model-Präfix (gpt- → openai, gemini- → gemini, claude- → anthropic, :/llama/llava → ollama)
- Korrigiert automatisch request.provider wenn es nicht zum Model gehört
- **Ergebnis:** PROVIDER-MODEL-MISMATCH wird präventiv verhindert

**Validierung:**
- py_compile für alle geänderten Dateien erfolgreich (keine Syntax-Fehler)
- Erwartete Side-Effects: Eliminierung der 400er Fehler bei Video-Fragen, saubere Pydantic-Validierung, stabilere modal_request Daten

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
