---
**Task-ID:** M-MEM-06
**Modell:** Kimi K2.5 / Opus 4.6 (Windsurf)
**Audit:** Opus 4.6 (Lead Architect Review 2026-04-06)
**Ref:** `documentation/features/memory_v2.md` Section 6, 7, 8

**IST (Codebase-Zustand):**
- Phase 1-5 implementiert, aber kein Gesamtsystem-Test. Einzelne Test-Dateien existieren (`test_memory_cache_lru.py`), aber kein E2E-Durchlauf über alle Phasen.
- Performance-Metriken unbekannt. Keine Baseline für Retrieval-Latenz oder Cache-Hit-Rate unter Last.
- Janus ist eine Desktop-Electron-App (kein Staging-Server). Deployment = lokale DB-Migration + Feature-Flag-Aktivierung.
- `WHAT_I_LEARNED.md` hat bisher nur das Cache-Pattern. Memory-spezifische Patterns (Enricher, Knapsack, Guard) fehlen.

**SOLL (nach Phase 6):**
- Vollständige E2E Regression-Suite: 20 Tests über alle 5 vorherigen Phasen.
- Performance-Benchmarks mit reproduzierbarer Methodik (Seed-Data, 100 Iterationen, P95 < 50ms).
- Feature-Flag `MEMORY_V2_ENABLED` Gate Verification: Verified V1-Fallback bei `false`, V2-Activation bei `true`.
- Knowledge-Base und Projekt-Status vollständig aktualisiert.
- Feature-Flag `MEMORY_V2_ENABLED=true` aktiviert.

**IMPL-LOOP:**
```
[IMPL → TEST → LINTER → IMPORTS → DIAMOND-REPORT]
```

---

# 1. Ziel

Beweise, dass alle 5 Phasen als Gesamtsystem funktionieren. Dokumentiere Performance-Baselines. Aktiviere das System für den Produktivbetrieb.

---

# 2. Abhängigkeiten

**REQUIRES (alles muss implementiert sein):**
- Phase 1: DB-Spalten (priority, memory_type, ttl, tags, source_skill, user_editable, canonical_key) ✅
- Phase 2: RAM-Cache mit LRU-Eviction + TTL-Cleanup ✅
- Phase 3: Enricher, Guard, Circuit-Breaker, Embedding-Cache, Observability
- Phase 4: MemorySlot, TokenBudget, Knapsack, Feature-Flag, Debug-Endpoint
- Phase 5: 4 Unified Tools + Permission-Matrix

**BLOCKS:** Nichts — dies ist die letzte Phase.

**Referenced by:**
- task_003_memory_qa_framework.md: QA Framework basiert auf M-MEM-06 Observability

---

# 3. Betroffene Dateien

**Neu:**
- `backend/tests/test_memory_regression.py` — E2E Suite (20 Tests)
- `backend/tests/test_memory_performance.py` — Benchmark-Suite
- `DIAMOND-REPORT_MEMORY_V2_FINAL.md` — Final Report

**Modifiziert:**
- `WHAT_I_LEARNED.md` — 5 neue Patterns
- `PROJECT_STATE.md` — M-MEM-03 bis M-MEM-06 Status
- `01_CENTRAL_TASK_REGISTRY.md` — Epic abschließen (6/6 Tasks)
- `documentation/features/epic_memory_v2.md` — Alle Tasks [x]

---

# 4. E2E Regression Test Plan

```bash
pytest backend/tests/test_memory_regression.py -v
```

### 4.1 Integration Tests (10 Tests)

| # | Test | Prüft Phase | Assertion |
|---|------|------------|-----------|
| 1 | Full Extraction Flow | P1+P3 | `extract_and_save_fact_from_interaction()` → DB-Entry hat priority≠0.5 |
| 2 | Enricher Priority | P3 | Fakt "Name ist Max" → priority=0.95 |
| 3 | Guard Clamping | P3 | source_skill="skill.x" → priority≤0.85 |
| 4 | Dedup Merge | P3 | Gleicher Hash → priority=MAX(old,new), tags=UNION |
| 5 | Cache Put+Hit | P2+P3 | High-priority save → cache.get() returns entry |
| 6 | Cache Invalidate | P2+P3 | Merge → cache.get() returns None |
| 7 | Budget Selection | P4 | 50 MemorySlots, budget=2100 → selected<2100 tokens |
| 8 | Knapsack Skip-Big | P4 | 1×3000tk + 5×100tk, budget=2100 → selected=5 |
| 9 | Tool Write→Read | P5 | `memory_write({fact})` → `memory_read({query})` finds it |
| 10 | Tool Update Blocked | P5 | user_editable=false → update returns error |

### 4.2 Resilience Tests (5 Tests)

| # | Test | Prüft | Assertion |
|---|------|-------|-----------|
| 11 | Circuit-Breaker OPEN | P3 | 3× Exception → `can_execute()` returns False |
| 12 | Circuit-Breaker HALF_OPEN | P3 | Nach 120s → 1 Probe erlaubt |
| 13 | Circuit-Breaker Recovery | P3 | Probe Success → state=CLOSED |
| 14 | Feature-Flag Rollback | P4 | `MEMORY_V2_ENABLED=false` → alter Code-Pfad |
| 15 | Empty DB Handling | P4 | 0 Memories → empty context, kein Crash |

### 4.3 Concurrent & Edge-Case Tests (5 Tests)

| # | Test | Prüft | Assertion |
|---|------|-------|-----------|
| 16 | Concurrent Writes | P2+P3 | 10 Threads → kein KeyError, kein Deadlock |
| 17 | TTL Cleanup | P2 | Expired Memory → `purge_expired_memories()` entfernt es |
| 18 | Zombie Stats | P2 | `get_zombie_stats()` → accurate counts |
| 19 | Embedding Cache Hit | P3 | Same embedding parsed 2× → cache hit |
| 20 | Observability Snapshot | P3 | `memory_metrics.snapshot()` → alle Counter ≥ 0 |

---

# 5. Performance-Benchmarks

```bash
python backend/tests/test_memory_performance.py
```

### 5.1 Methodik (REPRODUZIERBAR)

```python
import time

def seed_test_data(db, count=10_000):
    """Generiert count Memories mit random priority/tags/embeddings."""
    for i in range(count):
        db.add(Memory(
            snippet=f"Test fact {i}",
            priority=random.uniform(0.3, 1.0),
            memory_type=random.choice(["CORE", "GENERAL", "TEMPORAL"]),
            tags=[random.choice(["identity", "pet", "health", "style"])],
            embedding_json=json.dumps([random.random() for _ in range(384)]),
            text_hash=f"hash_{i}",
            chat_id=1,
        ))
    db.commit()

def benchmark(func, iterations=100):
    """Runs func iterations times, returns P50/P95/P99 in ms."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        times.append((time.perf_counter() - start) * 1000)
    times.sort()
    return {
        "p50": times[len(times)//2],
        "p95": times[int(len(times)*0.95)],
        "p99": times[int(len(times)*0.99)],
    }
```

### 5.2 Zielwerte

| Benchmark | Seed-Data | Iterations | P95 Ziel | FAIL wenn |
|-----------|-----------|------------|----------|-----------|
| `retrieve_diamond_slots()` | 10.000 Memories | 100 | < 50ms | > 100ms |
| `memory_cache.get()` (Hit) | 500 cached | 100 | < 5ms | > 10ms |
| `select_slots_by_budget()` | 200 Slots | 100 | < 20ms | > 50ms |
| `parse_embedding()` (Cached) | 2048 entries | 100 | < 0.5ms | > 2ms |
| `enrich_fact()` | — | 100 | < 1ms | > 5ms |

### 5.3 Testbar via:
```python
def test_retrieve_p95():
    seed_test_data(db, 10_000)
    result = benchmark(lambda: retrieve_diamond_slots(db, 1, "test query"))
    assert result["p95"] < 50, f"P95={result['p95']}ms exceeds 50ms target"
```

---

# 6. Success Metrics (KPIs)

| KPI | Ziel | Messmethode |
|-----|------|-------------|
| Test Passing Rate | > 95% (19/20) | `pytest --tb=short` |
| P95 Retrieve Latenz | < 50ms | Performance-Benchmark |
| Cache Hit Rate (priority≥0.8) | > 95% | `memory_cache.get_stats().hit_rate` |
| Priority Guard Trigger Rate | < 5% aller Writes | `memory_metrics.snapshot()["guard_clamps"]` / total writes |
| Zombie-Memories nach Cleanup | 0 | `get_zombie_stats()["total"]` |
| Circuit-Breaker OPEN Events | < 3/Woche | `memory_metrics.snapshot()["breaker_opens"]` |
| Embedding Cache Hit Rate | > 90% | `embedding_cache_stats()["hit_rate"]` |
| Feature-Flag Rollback Time | < 1s | Toggle flag → next request uses old path |

---

# 7. Dokumentation & Abschluss

### 7.1 `WHAT_I_LEARNED.md` — 5 Patterns hinzufügen:

1. **Thread-Safe LRU Cache** (bereits vorhanden ✅)
2. **Deterministic Enricher** — Regelbasierte Priority statt harter If-Else-Ketten
3. **Knapsack Context** — continue statt break für optimale Token-Nutzung
4. **Circuit-Breaker** — 3-State (CLOSED/OPEN/HALF_OPEN) mit Timeout-Recovery
5. **Permission Guard** — user_editable Check vor jedem Tool-Update

### 7.2 Projekt-Status Updates:

- `01_CENTRAL_TASK_REGISTRY.md`: M-MEM-03 bis M-MEM-06 → DONE, Progress: 6/6
- `PROJECT_STATE.md`: Finaler Eintrag mit Datum
- `epic_memory_v2.md`: Alle 6 Tasks `[x]`

### 7.3 Final Report: `DIAMOND-REPORT_MEMORY_V2_FINAL.md`

Inhalt: Architektur-Überblick, alle Dateien, Test-Ergebnisse, Performance-Baselines, bekannte Limitierungen.

---

# 8. Audit-Trail

**Status:** ⏳ PENDING (Phase 6/6)
**Opus-Audit:** 2026-04-06 — Benchmark-Methodik definiert, "Staging" durch lokale Validierung ersetzt (Electron-App).

**WARNUNG:** Janus ist eine Desktop-App. Es gibt keinen Staging-Server. "Deployment" = `alembic upgrade head` auf lokaler DB + `MEMORY_V2_ENABLED=true`.

**Logging-Prefixe:**
- `[REGRESSION]` — Test Results (Pass/Fail/Skip)
- `[PERFORMANCE]` — Benchmark P50/P95/P99
- `[DEPLOY]` — Feature-Flag Status, Migration Status
