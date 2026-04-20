# Task BUG-MEM-024: Cache Invalidation Fix

## 1. Ziel & Kontext
**Ziel:** Cache-Invalidation Logik verbessern, um veraltete Memory-Einträge zuverlässig aus dem RAM-Cache zu entfernen.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** MemoryRAMCache V2.1.0, TTL Cleanup Service
- **Beeinflusst:** Memory-Retrieval Performance, Cache-Hit-Raten
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- `backend/services/memory_cache.py`
- `backend/services/memory_manager.py`
- TBD

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** [Haupt-Implementierungsschritte hier eintragen]
- [ ] **Phase 3 (Testing):** `python -m pytest backend/tests/test_memory_cache_lru.py -v`
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q`
- [ ] Targeted: `python -m pytest backend/tests/test_memory_cache_lru.py -v`

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
