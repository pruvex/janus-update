# Task P2: FTS5 Keyword-Index + RRF Fusion (Hybrid Retriever)

**Sektion 1 — Ziel**
Implementiere den Hybrid-Retriever, der Dense (ChromaDB Vektor) + Sparse (FTS5 Keyword) via Reciprocal Rank Fusion (RRF, k=60) kombiniert. Ziel: MRR-Lift gegenüber P0-Baseline.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/fts_store.py` (SQLite FTS5 Virtual Table, unicode61 remove_diacritics 2, WAL-Mode, synchronous=NORMAL)
- NEU `backend/services/rag/rrf.py` (Reciprocal Rank Fusion, pure function, k=60)
- NEU `backend/services/rag/hybrid_retriever.py` (ChromaDB + FTS5 Orchestration, RRF Fusion, Top-K Rückgabe)
- MODIFY `backend/services/rag/ingestion.py` (FTS5-Write Hook: `_index_file` ruft `fts.add_chunks()` nach ChromaDB-Insert, `_delete_file_index` ruft `fts.delete_chunks()`)
- NEU `backend/tests/rag_v2/test_rrf.py` (RRF Unit-Tests: Symmetrie, Single-Source, Asymmetrie, k-Influence)
- NEU `backend/tests/rag_v2/test_fts_store.py` (FTS5 Unit-Tests: add/search/delete, unicode61, BM25-Ranking, Replace)
- NEU `backend/tests/rag_v2/test_hybrid_retriever.py` (Integrationstests: empty index, vector search, keyword-boost, provenance, top-k limit)

**Sektion 3 — Out-of-Scope**
- Keine Dual-Embeddings (P3)
- Keine Cross-Encoder Reranking (P4)
- Keine Query-Router Regex-Heuristik (P5)
- Keine Watchdog/Background-Ingestion (P8)

**Sektion 4 — Impact-Analyse**

- `ingestion.py` erweitert um FTSStore-Instanz und Hook-Calls — keine Änderung an Interface oder Freeze-List-Files
- FTS5 DB: `{app_data_dir}/knowledge_fts_v2.db` (physisch isoliert)
- Kein Touch von `vector_service.py`, `rag_manager.py`, `rag_chroma_db/`
- Legacy-Isolation: SHA-Hash von `rag_chroma_db/` unverändert verifiziert

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_rrf` läuft grün (7 Tests)
- [x] `python -m backend.tests.rag_v2.test_fts_store` läuft grün (7 Tests)
- [x] `python -m backend.tests.rag_v2.test_hybrid_retriever` läuft grün (5 Tests)
- [x] `python -m backend.tests.rag_v2.test_ingestion` läuft grün (P1 + FTS5-Hook)
- [x] RRF-Symmetrie: `fuse([[a,b], [b,a]])` gibt identische Scores für a und b
- [x] FTS5-Boost: Exaktes Symbol (z.B. Variablenname) wird von FTS5 gefunden und via RRF gehoben
- [x] Legacy-Isolation: `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert: 607afb4e...)

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_rrf
python -m backend.tests.rag_v2.test_fts_store
python -m backend.tests.rag_v2.test_hybrid_retriever
python -m backend.tests.rag_v2.test_ingestion
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/fts_store.py`, `rrf.py`, `hybrid_retriever.py`
- Revert `ingestion.py` Änderungen (FTSStore-Import und Hook entfernen)
- Lösche `{app_data_dir}/knowledge_fts_v2.db`
- Kein Einfluss auf Legacy-System
