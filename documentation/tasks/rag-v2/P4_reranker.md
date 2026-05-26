# Task P4: Cross-Encoder Reranker + Context Expansion

**Sektion 1 — Ziel**
Implementiere den Reranker-Layer und die Context-Expansion. Transformation von "gefundenen Schnipseln" in "hoch-relevante, kontextreiche Antworten". Pipeline: Top-20 (RRF) → Rerank → Top-5 → Expand → Final.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/reranker.py` (Cross-Encoder: Singleton-Pattern, Lazy-Loading, Thread-Lock, Graceful Fallback)
- NEU `backend/services/rag/context_expander.py` (Context Expansion: ±1 Chunks via index_store.py, Deduplizierung)
- MODIFY `backend/services/rag/hybrid_retriever.py` (Pipeline-Integration: Top-20 RRF → Rerank → Top-5 → Expand)
- NEU `backend/tests/rag_v2/test_reranker.py` (Unit-Tests: Singleton, Lazy-Loading, Fallback, Latency ≤500ms, Memory ≤150MB)
- NEU `backend/tests/rag_v2/test_context_expander.py` (Unit-Tests: Expansion, Dedup, Boundary, Stats)
- MODIFY `backend/tests/rag_v2/test_hybrid_retriever.py` (index_db_path Parameter, use_reranker/expand_context Flags)

**Sektion 3 — Out-of-Scope**
- Keine Jina-Code Embeddings (P4 nutzt noch MiniLM für Reranker)
- Keine Query-Router (P5)
- Keine Background-Watchdog (P8)

**Sektion 4 — Impact-Analyse**

- `reranker.py`: Singleton Cross-Encoder mit sentence-transformers (cross-encoder/ms-marco-MiniLM-L-6-v2). Graceful Fallback bei Ladefehlern.
- `context_expander.py`: Context Expansion via index_store.py (±1 Chunks). Deduplizierung verhindert doppelte chunk_ids.
- `hybrid_retriever.py`: Neue Pipeline: vector_k=20 + keyword_k=20 → RRF (Top-20) → Rerank (Top-5) → Expand (±1) → Final.
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_reranker` läuft grün (Singleton, Lazy-Loading, Fallback)
- [x] `python -m backend.tests.rag_v2.test_context_expander` läuft grün (Expansion, Dedup, Boundary)
- [x] `python -m backend.tests.rag_v2.test_hybrid_retriever` läuft grün (Pipeline-Integration)
- [x] `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert: 607afb4e...)
- [x] Reranker Singleton-Pattern: `CrossEncoderReranker.get_instance()` returns same object
- [x] Graceful Fallback: Bei sentence-transformers Import-Error oder Modell-Ladefehler wird original Ranking zurückgegeben
- [x] Context Expansion: Top-5 Chunks expandieren zu ±1 Nachbarn ohne Duplikate
- [x] Pipeline-Integration: `HybridRetriever.query()` mit `use_reranker=True`, `expand_context=True`
- [ ] MRR-Gate: harness.py Run ≥15% Steigerung vs P3 (Ziel: MRR ≥ 0.23) — **DEFERRED** bis nach Data Ingestion (V2 Index ist aktuell leer)

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_reranker
python -m backend.tests.rag_v2.test_context_expander
python -m backend.tests.rag_v2.test_hybrid_retriever
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**MRR-Gate Validierung (DEFERRED bis nach Data Ingestion):**
```powershell
# Nach Data Ingestion:
python backend/tests/rag/harness.py --query backend/tests/rag/golden_queries.jsonl --chroma_path rag_chroma_db_v2 --collection kb_code_v2
# Erwartet: MRR@10 ≥ 0.23 (≥15% Steigerung vs P3 Baseline 0.1724)
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/reranker.py`
- Entferne `backend/services/rag/context_expander.py`
- Revert `hybrid_retriever.py` auf P3 Pipeline (ohne Reranker/Expand)
- Entferne `test_reranker.py`, `test_context_expander.py`
- Kein Einfluss auf Legacy-System
