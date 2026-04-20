# Task 042: Forced Tool-Call (Anti-Hallucination Guard)

## 1. Ziel & Kontext
Den Audit-Workflow beim PDF-Upload stabilisieren und "falsche" Erinnerungen verhindern. Das LLM muss zwingend das Lese-Tool aufrufen, und die Fakten-Extraktion muss während des Audit-Intents deaktiviert werden, um Halluzinationen zu vermeiden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Bestehendes Upload-System in backend/api/routers/rag.py, Orchestrator
- **Beeinflusst:** Upload-Endpoint, Tool-Enforcement, Fact-Extraction
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- `backend/api/routers/rag.py`
- `backend/services/orchestrator/execution_dispatcher.py` oder `backend/llm_providers/gemini/gateway.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Fix 1 (Force Tool-Call): tool_choice enforcement in upload endpoint; Fix 2 (Fact-Poisoning Guard): fact extraction deactivation during audit intent.
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit PDF-Upload validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/api/routers/rag.py backend/services/orchestrator/execution_dispatcher.py`

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix 1 (Force Tool-Call) - backend/data/schemas.py:**
- Zeile 504: audit_file Marker zu ChatRequest hinzugefügt (Optional[str] = None)
- Zweck: Identifiziert Audit-Intent bei Datei-Upload

**Fix 1 (Force Tool-Call) - frontend/js/chat.js:**
- Zeile 490: audit_file Marker beim Upload an Backend gesendet (audit_file: file.name)
- Zweck: Frontend kommuniziert Audit-Intent an Orchestrator

**Fix 1 (Force Tool-Call) - backend/services/orchestrator/execution_dispatcher.py:**
- Zeile 325-332: Tool-Choice-Enforcement implementiert
- Wenn audit_file gesetzt: force_tool_name = "knowledge.query"
- Logging: [ANTI-HALLUCINATION] Forcing knowledge.query tool_choice for audit_file={filename}
- Zweck: LLM wird gezwungen, das Lese-Tool aufzurufen

**Fix 2 (Fact-Poisoning Guard) - backend/services/chat_orchestrator.py:**
- Zeile 1039-1042: Fact-Extraction-Deaktivierung bei Audit-Intent
- Wenn audit_file gesetzt: skip_fact_extraction = True
- Logging: [ANTI-HALLUCINATION] Skipping fact extraction for audit_file={filename}
- Zweck: System lernt nicht aus eigenen Halluzinationen während Audit

**Validierung:**
- py_compile für schemas.py, execution_dispatcher.py, chat_orchestrator.py erfolgreich
- node --check für chat.js erfolgreich
- Erwartete Side-Effects: Bei Datei-Upload wird IMMER und ZUVERLÄSSIG ein Lese-Tool aufgerufen; keine falschen "Datei existiert bereits"-Erinnerungen mehr.

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
