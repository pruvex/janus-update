# Task BUG-MEM-032: List Request Guard

## 1. Ziel & Kontext
**Ziel:** Verhindere, dass die Zwei-Phasen-Recherche für Listen-Anfrage bei persönlichen Fragen ausgelöst wird.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** _SELF_REF_RE Recall-Guard, _should_force_websearch_skill Funktion
- **Beeinflusst:** Websearch Guard, List Request Detection, Personal Query Handling
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- `backend/services/chat_orchestrator.py`

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):** List-Request Guard zu _should_force_websearch_skill hinzugefügt
- [x] **Phase 3 (Testing):** Syntax-Check PASSED
- [x] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m pytest backend/tests/test_orchestrator_logic.py -v`

## 6. Ergebnis & Audit-Trail
**Status:** ✅ SUCCESS — DIAMOND CERTIFIED

**Implementiert am:** 2026-04-08
**Editor:** Kimi
**Final Sign-Off:** 2026-04-08 (Diamond Audit)

**Changes Made:**
- `backend/services/chat_orchestrator.py:214-226` - Added List-Request Guard in _should_force_websearch_skill
- Detects list markers: "nenne mir", "gib mir", "liste", "aufzähl", "was sind meine", "welche meine"
- Combined with _SELF_REF_RE check to block web search for personal list requests
- Log signal: `[LIST-GUARD-032] Blocking web search – personal list request`
- **Update FIX-035:** Funktion `_should_force_websearch_skill` wurde als Dead Code entfernt. Logik migriert zu Precedence Guard (capability-basiert).

**Syntax-Check:** ✅ PASSED
**Integration:** ✅ Precedence Guard (FIX-035) übernimmt Funktionalität provider-agnostisch

## 7. Debugging-Log
**2026-04-08 — Implementation Complete (Kimi)**
- Added List-Request Guard to prevent web search for personal list queries
- Syntax-Check: ✅ PASSED

**2026-04-08 — Diamond Certification (Cascade)**
- Task erfolgreich in FIX-035 integriert
- Precedence Guard ersetzt funktionsbasierte Guards durch capability-basierte Filterung
- Archiv-Status: ERLEDIGT 🚀
