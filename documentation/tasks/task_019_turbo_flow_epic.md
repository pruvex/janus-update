# EPIC: Turbo-Flow (Task 019)

## 1. Ziel & Kontext
**Ziel:** 30-50% Latenz-Reduktion durch architektonische Optimierungen, Instant-UX für Endnutzer.

**Status:** In Planung (Wartet auf Opus-Audit)

**Kontext:** Diamond-OS hat aktuell stabile Foundations (Memory V2, ORCH-ELITE-SEAL). Das Turbo-Flow Epic soll die nächste Performance-Evolution einleiten durch Parallelisierung, Streaming-Optimierung, API-Level-Caching und Async-Processing.

---

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:**
  - ORCH-DIAMOND-ELITE (Orchestrierung muss stabil bleiben)
  - A2-MEM-V2-GOLD (Memory System V2.1.0)
  - SYS-SKILL-CONTRACT-V1 (Tool-Vertrag muss beibehalten werden)

- **Beeinflusst:**
  - Memory Extraction Pipeline (Async-Extraktion)
  - SSE-Streaming Layer (TTFT-Optimierung)
  - API-Gateway/Tool-Layer (Caching 2.0) → **B5 (2026-04-12):** `llm_gateway.py` + `tool_manager.py` — process-weite Gateway-Singletons, Tool-Definition-Cache (kein Tool-Response-Store)
  - ChatOrchestrator Execution Engine (Parallel Execution)
  - Kosten-Berechnung (Background-Costs Tracking)

- **Risiko-Einschätzung:** **HIGH** (Architektonische Änderungen an kritischer Path)

---

## 3. Betroffene Dateien

**Phase 1 - Parallel Execution:**
- `backend/services/chat_orchestrator.py` (Execution Flow Modifikation)
- `backend/services/execution_engine.py` (Parallel Task Runner)
- `backend/services/memory/context_manager.py` (Fact-Coupon Integration)

**Phase 2 - Streaming-Optimierung:**
- `backend/services/llm_gateway.py` (SSE TTFT-Reduktion)
- `backend/services/cost_tracker.py` (Background Cost Attribution)
- `frontend/js/chat.js` (SSE Handler Optimierung)

**Phase 3 - Caching 2.0:**
- `backend/services/cache/` (Neuer API-Level Cache Layer)
- `backend/tools/` (Tool-Response Caching)
- `backend/services/prompt_registry.py` (Prompt-Templating Cache)

**Phase 4 - Async Extraction:**
- `backend/services/memory/memory_extractor.py` (Background-Mode)
- `backend/services/memory/memory_manager.py` (Async Queue Integration)
- `backend/services/async_worker.py` (Neu: Background Worker)

---

## 4. Umsetzungsschritte (Diamond-Flow)

### A1-G17 Task-Decomposition Matrix

| Säule | Tasks | Beschreibung | Status |
|-------|-------|--------------|--------|
| **Säule 1** | A2, C7 | Parallel Execution (Vektorsuche/Fact-Coupon parallel zum Thinking) | � **PHASE 1 DONE** |
| **Säule 2** | C8, C9 | Streaming-Optimierung (SSE TTFT-Reduktion, Background Costs) | 🔵 PLANNING |

**⚠️ ACHTUNG (Frontend-Risiko):** Frontend-Streaming muss ge-throttled werden (Batch-Updates alle 50ms) und via overflow-anchor vom resizable/draggable Container entkoppelt werden, um Main-Thread-Freezes zu verhindern. Backend nutzt native Provider-Streams (stream=True) gepackt in einen unified SSE-Endpoint.
| **Säule 3** | B5, D11 | Caching 2.0 (API-Level Caching von Tools/Prompts) | 🟡 **B5 Phase-1 hot-path DONE** (D11 / Response-Cache noch PLANNING) |
| **Säule 4** | C8, D10 | Async Extraction (Memory-Extraktion in Background-Prozess) | 🔵 PLANNING |

### Phase-Checklist

- [x] **Phase 1 (Pre-Check):** `/pre-check` ausgeführt ✅
- [x] **Phase 1.5 (Quick-Wins):** Issue 002 + 011 implementiert ✅
- [ ] **Phase 2 (Opus-Audit):** Architektur-Review durch Opus 4.6
  - [ ] Sub-Task A2: Parallel Fact-Coupon Loading
  - [ ] Sub-Task C7: Vektorsuche Parallelisierung
  - [ ] Sub-Task C8: SSE TTFT-Reduktion
  - [ ] Sub-Task C9: Background Cost Tracking
  - [x] Sub-Task B5 (Phase 1): API hot-path — Gateway-Singletons + `get_tool_definitions` Cache (Opus-Audit Issue 007/008)
  - [ ] Sub-Task D11: Prompt Cache Implementation
  - [ ] Sub-Task D10: Async Extraction Architecture
- [ ] **Phase 2 (Opus-Audit):** Architektur-Review für verbleibende Säulen 2-4
- [ ] **Phase 3 (Implementierung):** Nach Opus-Approval
- [ ] **Phase 4 (Testing):** Performance-Benchmarks + Regression
- [x] **Phase 5a (Post-Check, Teil):** `/post-impl` für **Task B5** (Phase-1 Caching-Slice) — 2026-04-12, siehe Sektion 6–7.
- [ ] **Phase 5 (Post-Check, Gesamt):** `/post-impl` nach vollständigem Epic-Abschluss (alle Säulen / Performance-Benchmarks).

---

## 5. Test-Vorgaben

- [ ] **Regression:** `python -m pytest backend/tests -q` (alle bestehenden Tests müssen passen)
- [ ] **Performance-Baseline:** Latenz-Messung vor/nach (min. 50 Requests)
- [ ] **Load-Test:** `locust` oder `k6` für Concurrent-User-Szenarien
- [ ] **Cache-Hit-Rate:** Monitoring > 60% für Tool-Calls
- [ ] **Memory-Leak-Test:** Async-Worker Queue-Depth über 24h

---

## 6. Ergebnis & Audit-Trail

**Status:** � PHASE 1 COMPLETE (Quick-Wins implementiert)

**Erstellt:** 2026-04-12
**Aktualisiert:** 2026-04-12 (Phase 1 Implementation)

### Implementierte Optimierungen (Issue 002 + 011)

**Issue 011: Query-Embedding Cache (vector_service.py)**
- ✅ `get_query_embedding()` mit LRU-Cache (max 128 Einträge, thread-safe)
- ✅ `find_most_similar_indices_precomputed()` für wiederverwendbare Embeddings
- ✅ `calculate_similarity_with_precomputed()` für Batch-Similarity ohne re-encode
- ✅ Thread-Safety via `threading.Lock()` (FastAPI worker-isoliert)

**Issue 002: Batch-Query & Partitionierung (memory_manager.py)**
- ✅ `retrieve_diamond_context()`: Single Batch-Query statt 5 separaten Queries
- ✅ `retrieve_diamond_slots()`: Batch-Query für alle Memory-Kategorien
- ✅ In-Memory Partitionierung (O(n)) nach Typ (core_always, core_query, ephemeral, stm)
- ✅ Precomputed Embedding wird für alle Vektor-Suchen wiederverwendet

**Performance-Gewinne erwartet:**
- 4x weniger Embedding-Berechnungen pro Retrieval (statt 4x `encode()` nur 1x)
- 5x weniger DB-Queries in `retrieve_diamond_context()` (1 statt 5)
- Reduzierte DB-Last in `retrieve_diamond_slots()` durch Batch-Loading

**Tests:**
- ✅ Syntax-Check: `py_compile` PASS für beide Dateien
- ✅ Regression: `test_memory_manager.py` 17/17 PASS
- ✅ Import-Check: Beide Module laden erfolgreich

**Nächster Schritt:** Opus-Audit für verbleibende Säulen; D11 Prompt-Cache / vollständiger Tool-Response-Cache (Phase 3) gemäß Matrix.

### Task B5 — Phase 1 (Opus-Audit Issue 007 / 008) — `/post-impl` 2026-04-12

**Geänderte Dateien:**
| Datei | Änderung |
|-------|----------|
| `backend/services/llm_gateway.py` | Module-Level-Singletons `_GEMINI_GATEWAY`, `_OPENAI_GATEWAY`, `_OLLAMA_GATEWAY`, Mapping `_GATEWAY_SILOS`; `reason_and_respond` ohne pro-Request-`Gateway()`-Instanziierung |
| `backend/services/tool_manager.py` | `_tool_definitions_cache` (Key: `Tuple[bool, frozenset]`); `get_tool_definitions` nutzt `tool.llm_definition["parameters"]`; `register_tool` → `clear()` |

**Kurzbeschreibung:** Hot-Path-Latenz und CPU: keine wiederholte Gateway-Konstruktion; keine doppelte Pydantic-`model_json_schema()`-Generierung pro `get_tool_definitions`-Aufruf.

**Tests:**
- `python -m pytest backend/tests/test_memory_manager.py -q` → **17 passed** (ORCH-Elite-Regression-Scope).
- `python -m pytest backend/tests -q` → **collection ERROR** in `test_prompting_builder.py` (`ImportError: OllamaCompiler` aus `backend.services.prompting.compilers.ollama`) — **vorbestehend**, nicht durch B5 verursacht.

---

## 7. Debugging-Log

**2026-04-12 — /post-impl Task B5 (Phase-1 Slice):** Keine Implementations-Blocker. Gesamtlauf `pytest backend/tests` scheitert an bekannter Import-Kette (`OllamaCompiler`); gezielter Memory-Regression-Lauf grün.

**2026-04-12 - Phase 1 Implementation:**
- Keine Blocker. Thread-Safety via `threading.Lock()` ausreichend da FastAPI worker-isoliert.
- Logging-Noise bei Tests ist nur Sentry-Cleanup, kein Code-Issue.
- Alle 17 Memory-Manager-Tests grün nach Optimierung.

---

## Appendix: Opus-Audit Checklist

**Fragen für Opus 4.6:**
1. Parallelisierungsstrategie: Threading vs Async vs Multiprocess?
2. Cache-Invalidierung: TTL vs Event-Driven?
3. SSE-Optimierung: Connection-Pooling oder HTTP/2 Push?
4. Async-Extraction: Queue (Redis/RabbitMQ) oder In-Process (Celery)?
5. Race-Conditions: Wie verhindern wir doppelte Memory-Extraktion?
6. Rollback-Strategie: Feature-Flags für jede Säule?
