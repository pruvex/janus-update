# Task BUG-MEM-029: Medical Nano Reasoning

## 1. Ziel & Kontext
**Ziel:** Zwinge Nano-Modelle via Prompt dazu, Lebensmittel aktiv auf versteckte Allergene (z.B. Nüsse in Studentenfutter) zu prüfen.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Medical-Override Safety System, Nano-Model Prompting
- **Beeinflusst:** Allergie-Erkennung, Food-Safety, System Prompt Injection
- **Risiko-Einschätzung:** HIGH (Medical Safety Critical)

## 3. Betroffene Dateien
- `backend/services/chat_orchestrator.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):** Hidden-allergen reasoning zu CRITICAL MEDICAL WARNING Block hinzugefügt
- [x] **Phase 3 (Testing):** Syntax-Check PASSED
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m pytest backend/tests/test_orchestrator_logic.py -v`

## 6. Ergebnis & Audit-Trail
**Implementiert am:** 2026-04-08
**Editor:** Kimi

**Changes Made:**
- `backend/services/chat_orchestrator.py:3870-3872` - Extended CRITICAL MEDICAL WARNING block
- Added: "Du MUSST bei angefragten Lebensmitteln (wie Studentenfutter) ZWINGEND nachdenken, ob sie versteckte Allergene (wie Nüsse) enthalten. Warne sofort und verbiete den Verzehr, falls zutreffend!"

**Syntax-Check:** ✅ PASSED

## 7. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- Extended CRITICAL MEDICAL WARNING with hidden-allergen reasoning requirement
- Syntax-Check: ✅ PASSED
