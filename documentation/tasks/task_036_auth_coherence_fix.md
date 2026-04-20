# Task 036: Auth-Coherence Fix

## 1. Ziel & Kontext
Nach der PROVIDER-COHERENCE Korrektur in _execute_generation muss der API-Key für den neuen Provider aktualisiert werden, um Auth-Mismatch zu verhindern.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 034 (Provider-Coherence Enforcement), bestehende Key-Refresh-Logik in _classify_request
- **Beeinflusst:** Auth-Coherence, API-Key-Management bei Provider-Wechsel
- **Risiko-Einschätzung:** LOW

## 3. Betroffene Dateien
- `backend/services/chat_orchestrator.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** Nach PROVIDER-COHERENCE Korrektur API-Key für neuen Provider laden (ähnlich wie _classify_request), [AUTH-COHERENCE] Log hinzufügen.
- [ ] **Phase 3 (Testing):** Syntax-Check + gezielte Szenarien mit Provider-Drift validieren.
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m py_compile backend/services/chat_orchestrator.py`

## 6. Ergebnis & Audit-Trail

**Implementierungsdatum:** 2026-04-18

**Durchgeführte Änderungen:**

**Fix (Auth-Coherence) - chat_orchestrator.py:**
- Zeile 1541-1559: Hinzugefügt API Key Refresh nach PROVIDER-COHERENCE Korrektur in _execute_generation
- Logik: Wenn Provider korrigiert wurde, wird der API Key für den neuen Provider via keyring geladen (ähnlich wie _classify_request)
- Ollama-Sonderbehandlung: Placeholder key 'ollama' wird gesetzt
- Logging: [AUTH-COHERENCE] Key refreshed for healed provider: {provider}
- **Ergebnis:** Auth-Coherence folgt jetzt Provider-Coherence. Bei Provider-Wechsel wird der korrekte API Key automatisch geladen.

**Validierung:**
- py_compile für chat_orchestrator.py erfolgreich (keine Syntax-Fehler)
- Erwartete Side-Effects: Verhindert Auth-Mismatch bei Provider-Drift, API Key wird automatisch nach Provider-Korrektur aktualisiert

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
