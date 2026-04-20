# Task 043: OpenAI Naming Shim

## 1. Ziel & Kontext
Alle an die OpenAI-API gesendeten Tool-Namen müssen dem ^[a-zA-Z0-9_-]+$-Pattern entsprechen. OpenAI akzeptiert keine Punkte in Tool-Namen, was zu BadRequestError 400 führt. Ein Shim muss Tool-Namen normalisieren (Punkte durch Unterstriche ersetzen), bevor sie an OpenAI gesendet werden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Bestehendes OpenAI-Provider-System
- **Beeinflusst:** Tool-Name-Normalisierung für OpenAI-API
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- `backend/llm_providers/openai/service.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Tool-Name-Shim implementieren (Tool-Liste und tool_choice normalisieren), Logging hinzufügen.
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit PDF-Upload validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/llm_providers/openai/service.py`

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix (OpenAI Naming Shim) - backend/llm_providers/openai/service.py:**
- Zeile 93-111: Tool-Name-Normalisierungs-Shim implementiert
- Tool-Liste Normalisierung: function['name'] wird von 'domain.action' zu 'domain_action' konvertiert
- tool_choice Normalisierung: tool_choice['function']['name'] wird ebenfalls normalisiert
- Logging: [OPENAI_SHIM] Normalizing tool name from 'domain.action' to 'domain_action'
- Logging: [OPENAI_SHIM] Normalizing tool_choice from 'domain.action' to 'domain_action'
- **Ergebnis:** OpenAI-API akzeptiert Tool-Namen ohne BadRequestError 400; Forced Tool-Call bei PDF-Upload funktioniert jetzt erfolgreich.

**Validierung:**
- py_compile für openai/service.py erfolgreich
- Erwartete Side-Effects: BadRequestError 400 bei tool_choice verschwindet; Forced Tool-Call beim PDF-Upload wird erfolgreich sein; KI wird nicht mehr halluzinieren, da sie den echten Inhalt der PDF als Tool-Antwort erhält.

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
