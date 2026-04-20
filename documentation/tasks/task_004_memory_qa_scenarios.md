# Task 004: Memory QA Scenarios Expansion

## 1. Ziel & Kontext
Erweiterung der Memory QA Test-Suite von 3 auf 18 Test-Szenarien für vollständige Abdeckung des Memory V2 Systems. Neue Tests decken Knapsack, TTL/Zombies, Dedup-Merge, Security, Circuit-Breaker und komplexe Real-Life-Szenarien ab.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** Task 003 (Memory QA Framework Foundation), M-MEM-06 (Memory V2 Regression)
- **Beeinflusst:** QA Framework Test-Suite, Memory V2 Feature-Tests
- **Risiko-Einschätzung:** LOW (nur JSON-Fixtures, keine Code-Änderung)

**Backward-Refs:**
→ task_005_memory_qa_dashboard.md: Dashboard-Integration nutzt 18-Test-Suite für Health-Score

## 3. Betroffene Dateien
- `backend/data/fixtures/memory_test_suite.json` (modifiziert)

## 4. Umsetzungsschritte (Diamond-Flow)
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausgeführt.
- [x] **Phase 2 (Implementierung):** 15 neue Test-Szenarien (T4-T18) hinzugefügt
- [x] **Phase 3 (Testing):** JSON-Validierung, Schema-Compliance — 18/18 Tests validiert
- [x] **Phase 4 (Post-Check):** `/post-impl` ausgeführt.
- [ ] **Phase 5 (Audit - Optional):** Nicht erforderlich

## 5. Test-Vorgaben
- [x] Syntax: `python -c "from backend.data.schemas_qa import MemoryTestCase; ..."` → 18/18 PASS
- [ ] Regression: `python -m pytest backend/tests -q`

## 6. Ergebnis & Audit-Trail
**Files Changed:**
- `backend/data/schemas_qa.py` — Schema erweitert: setup_context, tags_present, semantic_intent, memory_type, max_latency_ms, min_budget_utilization
- `backend/data/fixtures/memory_test_suite.json` — 18 Test-Szenarien (T001-T018) mit vollständiger Memory V2 Abdeckung

**What was done:**
QA Test-Suite von 3 auf 18 Szenarien erweitert. Neue Tests decken: Knapsack Budget (T004, T011), Multi-Person Logic (T005), TTL/Zombie Purge (T006-T007), Dedup-Merge (T008), LRU Eviction (T010), Security Guard (T012), Skill Integration (T014), Circuit Breaker (T017), Real-Life Diamond Scenario (T018). Alle 18 Tests passieren Pydantic Validierung.

**Test Result:**
- Schema Validation: PASS (18/18 Tests)
- Diamond Standard: Erweiterte Felder für komplexe Szenarien

**Metrics:**
- Total Tests: 18
- Foundation Tests: 3 (T001-T003)
- Expansion Tests: 15 (T004-T018)
- Coverage Areas: 12 (Enricher, Cache, Knapsack, TTL, Security, Circuit-Breaker, etc.)

## 7. Debugging-Log
Keine Probleme. Schema-Erweiterung backward-kompatibel durch default_factory=list für neue List-Felder.
