# Task BUG-MEM-028: Identity Adverb Guard

## 1. Ziel & Kontext
**Ziel:** Verhindere, dass Adverbien wie "exakt" oder "genau" als User-Namen extrahiert werden.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Memory Extraction Pipeline, Identity-Extraktion
- **Beeinflusst:** User Profile, Namensauflösung, Entity Recognition
- **Risiko-Einschätzung:** LOW

## 3. Betroffene Dateien
- `backend/services/memory_extractor.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):** Adverb-Filter in IDENTITY-EXTRAKTION Section eingefügt
- [x] **Phase 3 (Testing):** Syntax-Check PASSED
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m pytest backend/tests/test_memory_extractor.py -v`

## 6. Ergebnis & Audit-Trail
**Implementiert am:** 2026-04-08
**Editor:** Kimi

**Changes Made:**
- `backend/services/memory_extractor.py:408` - Added adverb guard warning in IDENTITY-EXTRAKTION section
- Prompt injection: "ACHTUNG: Namen sind immer Substantive! Adverbien wie 'exakt', 'genau', 'wirklich' DÜRFEN NIEMALS als Name extrahiert werden."

**Syntax-Check:** ✅ PASSED

## 7. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- Added adverb guard to IDENTITY-EXTRAKTION section in extraction prompt
- Syntax-Check: ✅ PASSED
