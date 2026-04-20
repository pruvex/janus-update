# Task 041: Upload Prompt Hardening

## 1. Ziel & Kontext
Beim Datei-Upload soll das LLM gezwungen werden, das NEUE Dokument zu lesen statt alte Zusammenfassungen aus dem Gedächtnis zu verwenden. Der Prompt muss von einer sanften Empfehlung zu einer absoluten Verbots-Direktive gehärtet werden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Bestehendes Upload-System in frontend/js/chat.js
- **Beeinflusst:** Datei-Upload Auto-Prompt, Tool-Aufrufe bei Upload
- **Risiko-Einschätzung:** LOW

## 3. Betroffene Dateien
- `frontend/js/chat.js`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Upload-Prompt in frontend/js/chat.js von sanfter Empfehlung zu absoluter Verbots-Direktive ändern, Tool-Namen aktualisieren (knowledge_read_full_text oder knowledge.query).
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit Datei-Upload validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `node --check frontend/js/chat.js`
- [ ] Targeted: Datei-Upload im Chat testen, Tool-Aufruf verifizieren

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix (Prompt Hardening) - frontend/js/chat.js:**
- Zeile 453-456: Upload-Prompt von sanfter Empfehlung zu absoluter Verbots-Direktive gehärtet
- Alt: "Rufe zuerst den INHALT der PDF ab. Nutze dazu das Tool 'query_knowledge_base'..."
- Neu: "!!! STOPP !!! Lies KEINE alten Zusammenfassungen aus dem Gedächtnis! Du MUSST zwingend das Tool 'knowledge_read_full_text' (oder 'knowledge.query') mit dem Dateinamen '${file.name}' aufrufen, um das NEUE Dokument zu lesen. Wenn du antwortest, ohne ein Tool aufgerufen zu haben, ist das ein kritischer Systemfehler!"
- Tool-Namen aktualisiert: 'query_knowledge_base' → 'knowledge_read_full_text' (oder 'knowledge.query')
- **Ergebnis:** LLM wird gezwungen, das Lese-Tool auszuführen, selbst wenn Chat-Verlauf oder Memory voll mit alten Zusammenfassungen ist.

**Validierung:**
- node --check für chat.js erfolgreich (keine Syntax-Fehler)
- Erwartete Side-Effects: Bei Datei-Upload wird das LLM gezwungen, das neue Dokument zu lesen statt alte Zusammenfassungen aus dem Gedächtnis zu nutzen.

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
