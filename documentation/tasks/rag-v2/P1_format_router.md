# Task P1: Format-Router + Incremental Index + Deletion (Code-First)

**Sektion 1 — Ziel**
Implementiere die Strangler-Fig Ingestion mit inkrementellem Indexer, Format-Router und Orphan-Management. Physisch isoliert in `rag_chroma_db_v2/`.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/__init__.py`
- NEU `backend/services/rag/index_store.py` (SQLite, SHA-256, Orphan-Management)
- NEU `backend/services/rag/adapters/__init__.py`
- NEU `backend/services/rag/adapters/base.py` (BaseAdapter Interface)
- NEU `backend/services/rag/adapters/code.py` (CodeAdapter — blank-line splitting, P3 placeholder)
- NEU `backend/services/rag/adapters/markdown.py` (MarkdownAdapter — heading boundary splitting)
- NEU `backend/services/rag/ingestion.py` (FormatRouter + IngestionRun + Isolation Guard)
- NEU `backend/tests/rag_v2/__init__.py`
- NEU `backend/tests/rag_v2/test_adapters.py`
- NEU `backend/tests/rag_v2/test_index_store.py`
- NEU `backend/tests/rag_v2/test_ingestion.py`

**Sektion 3 — Out-of-Scope**
- Keine Tree-sitter Integration (P3)
- Keine Dual-Embeddings (P3)
- Keine PDF/DOCX/CSV Adapter (Flag `RAG_V2_INCLUDE_PROSE=false`)
- Keine Modifikation von Freeze-List-Files

**Sektion 4 — Impact-Analyse**

- Neuer Service-Layer — kein Eingriff in `rag_manager.py`, `vector_service.py`, `api/routers/rag.py`
- V2-Chroma-Pfad: `{app_data_dir}/rag_chroma_db_v2/` (physisch isoliert)
- **Isolation Guard**: `_assert_isolation()` bricht ab, wenn Pfad `rag_chroma_db/` enthält
- SQLite DB: `{app_data_dir}/knowledge_index_v2.db`
- Feature-Flag `RAG_V2_INGESTION` (später implementiert)

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_adapters` läuft grün
- [x] `python -m backend.tests.rag_v2.test_index_store` läuft grün
- [x] `python -m backend.tests.rag_v2.test_ingestion` läuft grün
- [x] Idempotenz: Zweiter Run auf identischem Ordner → `indexed=0, skipped=N`
- [x] Modifikation: File ändern → `indexed=1` im nächsten Run
- [x] Orphan: File löschen → `deleted=1` im nächsten Run
- [x] Rename: `deleted=1, indexed=1` (Alt gelöscht, neu indiziert)
- [x] **Legacy-Isolation**: `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert)

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_adapters
python -m backend.tests.rag_v2.test_index_store
python -m backend.tests.rag_v2.test_ingestion
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/` komplett
- Lösche `{app_data_dir}/rag_chroma_db_v2/`
- Lösche `{app_data_dir}/knowledge_index_v2.db`
- Kein Einfluss auf Legacy-System
