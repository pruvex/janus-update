# Task BUG-MEM-021: Context Commander & Search-Guard V3

## 1. Ziel & Kontext
Drei orthogonale Härtungen im Chat-Orchestrator:
(1) Recall-Guard blockiert Websuchen bei Eigen-Referenz-Fragen,
(2) Medical-Override injiziert ein kritisches Warnsignal wenn Gesundheits-Slots geladen sind,
(3) Instruction-Hardening erweitert die GPT-Direktive um Familienmitglieder-Kontext.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 018 (GPT No-Robot-Rule), Task 015/016 (Identity Hard-Lock), Memory-V2 Kategorie-System
- **Beeinflusst:** `_should_force_websearch_skill`, Identity-Directive-Block, Memory-Slot-Selektion
- **Risiko-Einschätzung:** MEDIUM — drei isolierte Änderungen in `chat_orchestrator.py`; keine DB-Änderung

## 3. Betroffene Dateien
- `backend/services/chat_orchestrator.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):**
  - [ ] 2a — RECALL-GUARD: `_should_force_websearch_skill` um Eigen-Referenz-Regex erweitern
        Regex: `(wer|was|wie|welche|wei[sß]t).*(ich|mein|meine|mir|mich)`
        → gibt `False` zurück (blockiert Websuche) wenn match
  - [ ] 2b — MEDICAL-OVERRIDE: Nach Memory-Slot-Selektion geladene Slots auf Kategorie
        `Gesundheit` / `health` prüfen → wenn vorhanden, `!!! CRITICAL MEDICAL WARNING !!!`
        Block ganz oben in `final_system_prompt` injizieren
  - [ ] 2c — INSTRUCTION-HARDENING: GPT-Direktive um Familienmitglieder-Kontext erweitern;
        wenn bekannte Verwandte im Memory-Kontext, verbiete "Ich habe keine Infos dazu"
- [ ] **Phase 3 (Testing):** `python -m pytest backend/tests -q`
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted syntax: `python -c "import py_compile; py_compile.compile('backend/services/chat_orchestrator.py', doraise=True); print('OK')"`
- [ ] Recall-Guard Unit: Regex matcht `"Was bin ich allergisch gegen?"` → blockiert Suche
- [ ] Recall-Guard Unit: Regex matcht nicht `"Wer ist der Präsident?"` → Suche erlaubt
- [ ] Medical-Override: Slot mit `category='Gesundheit'` → WARNING im Prompt vorhanden
- [ ] Instruction-Hardening: GPT-Direktive enthält Familien-Verbot wenn Stefan/Lisa im Kontext

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
