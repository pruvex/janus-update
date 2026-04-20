# Task 044: Forced Tool Re-Injection

## 1. Ziel & Kontext
Wenn ein Tool via tool_choice erzwungen wird, aber nicht in der Tool-Liste enthalten ist, gibt OpenAI einen 400 Bad Request Fehler. Ein Re-Injection Guard muss prüfen, ob das erzwungene Tool in der Tool-Liste vorhanden ist, und falls nicht, die Tool-Definition aus dem tool_registry nachladen und injizieren.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 043 (OpenAI Naming Shim)
- **Beeinflusst:** OpenAI-Provider Tool-Choice-Handling
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- `backend/llm_providers/openai/service.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Re-Injection Guard implementieren (tool_choice prüfen, fehlendes Tool aus tool_registry nachladen), Logging hinzufügen.
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit PDF-Upload validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/llm_providers/openai/service.py`

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix (Re-Injection Guard) - backend/llm_providers/openai/service.py:**
- Zeile 113-138: Forced Tool Re-Injection Guard implementiert
- Prüft ob tool_choice mit function existiert
- Extrahiert forced_tool_name (nach Shim-Konvertierung zu _)
- Prüft ob forced_tool_name in params['tools'] vorhanden ist
- Wenn nicht: Importiert skill_router, holt Tool-Definition via get_tool_definition(), formatiert für OpenAI API und injiziert in params['tools']
- Logging: [OPENAI_SHIM] Re-injecting missing forced tool definition: %s (warning level)
- Error-Logging bei Fehlschlag der Re-Injektion
- **Ergebnis:** 400 Bad Request Fehler verschwindet endgültig; PDF-Audit-Workflow funktioniert wie geplant.

**Validierung:**
- py_compile für openai/service.py erfolgreich
- Erwartete Side-Effects: 400 Bad Request Fehler verschwindet; PDF-Audit-Workflow funktioniert: Upload -> Forced Tool Call -> Korrekte Inhaltsanalyse -> Zusammenfassung.

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
