# EPIC: Memory Core Refactor (Task 020)

## 1. Ziel & Kontext

**Ziel:** Zerlegung des **MemoryManager**-God-Objects (`backend/services/memory_manager.py`) in **modulare Teil-Services** nach **Diamond-Standard** (Separation of Concerns, schmale öffentliche API, hohe Testbarkeit).

**Status:** **DONE** (Slice 1 — CRUD + Retrieval + Shim; Opus-Architektur-Zertifizierung)

**Roadmap-Referenz:** `documentation/Planned Features/Refactoring_Roadmap_2026.md` — **TOP 5 / Target #3** (Memory Core Manager, CU **7**, P1).

**Kontext:** Nach **SYS-CLEANUP-F401** und **ORCH-TRANSFORM-EPIC** ist `memory_manager.py` einer der größten verbleibenden Monolithen unter `backend/services/`. Die Roadmap nennt **CRUD**, **Retrieval**, **Enrichment** und **Compaction** als Trennlinien; die öffentliche API bleibt vorerst **fan-in-kritisch** (viele Importe aus Tools, Orchestrator, Extraktion).

---

## 2. Impact-Analyse & Abhängigkeiten

- **Basiert auf:**
  - **EPIC-MEM-V2** / A2-MEM-V2-GOLD (semantisches Modell, Tools, Knapsack — darf nicht gebrochen werden)
  - **Refactoring Roadmap 2026** Target #3 (Architektur-Zielbild)
  - Optional: **ORCH-TRANSFORM-EPIC** als Muster (Service-Extraktion + Re-Exports)

- **Beeinflusst (hohe Fan-in — vorsichtige Schnittführung):**
  - `backend/services/memory_extractor.py`
  - `backend/tools/*` mit Memory-Bezug
  - `backend/services/chat_orchestrator.py` / Kontext-Pfade
  - Tests: `backend/tests/test_memory_manager.py` und abhängige Integrationstests

- **Risiko-Einschätzung:** **HIGH** (zentrale Datenpfade, viele statische/dynamische Importe)

---

## 3. Betroffene Dateien (Initial — TBD bei Pre-Check)

| Bereich | Vorschlag / Ist |
|--------|-------------------|
| Monolith (ersetzt) | `backend/services/memory_manager.py` ist **Thin-Shim** (`from backend.services.memory import *` + `models` / `vector_service` / `memory_cache` für Legacy-Patches) |
| Paketstruktur (Slice 1) | `backend/services/memory/` — `crud_service.py`, `retrieval_service.py`, `__init__.py` (explizite Re-Exports, `__all__`) |
| Follow-up (optional) | Enrichment / Compaction weiter auslagern, wenn Schnittgrenzen festliegen |
| Verbundene Module | `memory_identity.py`, `context_manager.py`, ggf. `memory_observability.py` — Abgrenzung in Phase 1 klären |

---

## 4. Umsetzungsschritte (Diamond-Flow)

### Architektur-Ziel (aus Roadmap)

| Teil-Service | Verantwortung (Richtlinie) |
|--------------|----------------------------|
| **CRUD** | Persistenz, Validierung, Berechtigungen wo zentral |
| **Retrieval** | Abfragen, Vektor/Top-K, Knapsack-Anbindung (Schnittstellen zu bestehendem Kontext) |
| **Enrichment** | Dedup, Guards, Circuit-Breaker, Priorität — wo heute im Manager vermischt |
| **Compaction** | TTL, Aufräumen, ggf. Hintergrund-Jobs — klar getrennt von Retrieval |

- [x] **Phase 1 (Pre-Check):** Import-Graph / Fan-in berücksichtigt; Umsetzung in Slices (kein Big-Bang).
- [x] **Phase 2 (Design):** Schnitt CRUD vs Retrieval; öffentliche API über `backend.services.memory` + Shim.
- [x] **Phase 3 (Implementierung — Slice 1):** `crud_service.py` + `retrieval_service.py` extrahiert; `memory_manager.py` als Shim; Refactor-only.
- [x] **Phase 4 (Testing):** `test_memory_manager.py` / Security-Tests angepasst (Patch-Namespace); Performance-Tests: Patches auf `retrieval_service.vector_service` + `get_query_embedding`.
- [x] **Phase 5 (Post-Check):** `/post-impl` — dieser Abschnitt §6.
- [x] **Phase 6 (Audit):** **Opus-Zertifizierung** für Architektur-Slice 1 (Diamond-konform).

---

## 5. Test-Vorgaben

- [x] **Regression:** `backend/tests/test_memory_manager.py` — grün (inkl. angepasster Patch-Pfade auf `crud_service` / `retrieval_service` wo nötig).
- [x] **Security:** `test_memory_security.py` — Patch auf `crud_service.memory_cache`; Assertions an Merge-Logik angeglichen.
- [ ] **Gesamt-Suite:** `pytest backend/tests` — weiterhin ggf. Collection-Blocker (`OllamaCompiler` / `test_prompting_builder.py`) — vorbestehend, außerhalb Task-020.
- [x] **Performance / Namespace:** `test_memory_performance.py` — `patch('backend.services.memory.retrieval_service.vector_service')`, `get_query_embedding.return_value = np.zeros(384)`, `find_most_similar_indices_precomputed` gemockt.

---

## 6. Ergebnis & Audit-Trail (Post-Impl)

**Abschlussdatum:** 2026-04-12

| Thema | Ergebnis |
|-------|----------|
| **Zerlegung** | **`crud_service.py`** (Schreiben/Löschen: `save_memory_snippet`, `update_memory_snippet`, `touch_memory_snippet`, `transfer_facts_to_new_subject`, Archiv/Prune, Hilfen wie `_merge_existing_memory`, `compute_hash`, …) und **`retrieval_service.py`** (Diamond-Retrieval: `retrieve_diamond_slots`, `retrieve_diamond_context`, `get_last_subject_from_chat`, Token-Schätzung, Turbo-Flow mit Batch-Query + precomputed Embeddings) — **abgeschlossen**. |
| **Shim** | **`memory_manager.py`:** Deprecation-Docstring; `from backend.services.memory import *`; Re-Bind von `models`, `vector_service`, `memory_cache` für **Abwärtskompatibilität** (bestehende Imports und unittest-Patch-Pfade). |
| **`memory/__init__.py`** | Explizite Re-Exports + `__all__` (kein `import *` im Paket-Init). |
| **Tests** | Namespace-Fix in **`test_memory_performance.py`**: Patches zeigen auf **`backend.services.memory.retrieval_service.vector_service`**; Mock für **`get_query_embedding`** ergänzt. |
| **Zertifizierung** | **Opus-Architektur-Zertifizierung** für den Slice-1-Refactor eingegangen (Diamond-Standard: klare Trennung, kompatible Oberfläche). |

**Hinweis:** Enrichment (`memory_enricher`) und Compaction waren bereits eigene Module; vollständige Auslagerung „Enrichment/Compaction“ aus dem ehemaligen Monolithen ist für Folge-Slices offen, falls gewünscht.

---

## 7. Debugging-Log

_Bei Bedarf: Fan-in-Treffer, zirkuläre Import-Versuche, Rollback-Slices._
