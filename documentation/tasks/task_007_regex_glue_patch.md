# Task 007: Regex Glue Patch — Log Alignment

## 1. Ziel & Kontext
Die Memory QA Tests T007 und T017 sowie weitere Tests matchen nicht, weil LogCapture den falschen Logger-Namen verwendet und die Log-Formate nicht exakt mit den erwarteten Regex-Patterns übereinstimmen.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 005 (Dashboard läuft, Score 17/100)
- **Beeinflusst:** memory_qa.py LogCapture, SYSTEM-Command Handler
- **Risiko-Einschätzung:** LOW (nur Log-Strings, keine Logik-Änderung)

## 3. Betroffene Dateien
- `backend/services/memory_qa.py` — LogCapture Logger-Name fix, Log-Format Alignment

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** Patterns aus Test-Suite extrahiert
- [x] **Phase 2 (Implementierung):** LogCapture auf Root Logger "" umgestellt (fängt ALLE Logs ab)
- [x] **Phase 3 (Testing):** /test-memory ausgeführt — **Score: 28/100** (+65% improvement!)
- [x] **Phase 4 (Post-Check):** Task-Log aktualisiert (Score < 50 aber massive Verbesserung)
- [ ] **Phase 5 (Audit - Optional):** Nicht erforderlich

## 5. Test-Vorgaben
- [x] **Score: 28/100** (Ziel >50 nicht erreicht, aber +65% improvement)
- [x] **T007 (ZOMBIE PURGE):** ✅ PASSED (score=1.0)
- [x] **T010 (LRU EVICTION):** ✅ PASSED (score=1.0)
- [x] **T017 (CIRCUIT BREAKER):** ✅ PASSED (score=1.0)
- [x] **T004 (KNAPSACK):** ✅ PASSED (score=1.0)

## 6. Ergebnis & Audit-Trail
**Files Changed:**
- `backend/services/memory_qa.py` — LogCapture Root Logger Fix

**What was done:**
- LogCapture auf Root Logger ("") umgestellt, damit ALLE Logs gefangen werden
- Root Logger Level auf DEBUG gesetzt während Tests
- `_original_root_level` hinzugefügt für Cleanup
- 4 SYSTEM-Command Tests passen jetzt!

**Test Result:**
- **Vorher:** 2/18 PASSED (11.1%) — Diamond-Score: 17/100
- **Nachher:** 4/18 PASSED (22.2%) — Diamond-Score: 28/100
- **Improvement:** +65%

**PASSED Tests:**
- ✅ T004: Context Recommendation (KNAPSACK matched)
- ✅ T007: ZOMBIE PURGE (Deleted memories log gefunden)
- ✅ T010: LRU EVICTION ([CACHE EVICT] priority= matched)
- ✅ T017: CIRCUIT BREAKER (State: → OPEN matched)

**Remaining Issues:**
- T001-T003, T005-T006, T008-T009, T011-T018: Erwarten Memory-Integration im ChatOrchestrator, aber API-Calls schreiben keine Memory-Logs

## 7. Debugging-Log
**2026-04-07 18:15 — Root Logger Fix deployed**
- **Problem:** `janus_backend` Logger war separat von `janus` Hierarchie
- **Lösung:** LogCapture auf Root Logger ("") mit DEBUG Level
- **Ergebnis:** `[CACHE EVICT]`, `[ZOMBIE PURGE]`, `[CIRCUIT BREAKER]` Logs werden jetzt gefangen
