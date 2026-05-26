# Task P3: Code-Aware Chunking + Markdown Breadcrumbs + Dual-Collection Prep

**Sektion 1 — Ziel**
Verwandle den "dummen" Code-Parser in einen AST-bewussten Chunking-Spezialisten. Tree-sitter Integration mit regex-basiertem Fallback. Code-Prefixing (Module-Pfad, Symbol-Name, Imports). Markdown Header-Breadcrumbs als Präfix im Chunk-Text. Dual-Collection Router Vorbereitung (kb_code_v2 vs kb_prose_v2).

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/chunking.py` (zentrale Chunking-Logik, 3-stufiger Fallback: tree-sitter → regex → blank-line)
- MODIFY `backend/services/rag/adapters/code.py` (delegiert an chunking.py, konvertiert Chunk → RawChunk)
- MODIFY `backend/services/rag/adapters/markdown.py` (Header-Breadcrumb als Präfix im Chunk-Text: `## H1 > H2 > H3\n\n<content>`)
- MODIFY `backend/services/rag/ingestion.py` (Dual-Collection Router: `_route_format_to_collection`, `_get_collection`, COLLECTION_CODE / COLLECTION_PROSE)
- MODIFY `backend/services/rag/hybrid_retriever.py` (Multi-Collection Vector Search: `_vector_search_collection`, `_get_collection_names`)
- NEU `backend/tests/rag_v2/test_chunking.py` (Boundary-Test, AST-Resilience, Code-Prefixing, Breadcrumb-Test)

**Sektion 3 — Out-of-Scope**
- Keine Jina-Code Embeddings (P4)
- Keine Cross-Encoder Reranking (P4)
- Keine Query-Router (P5)
- Keine tatsächliche tree-sitter Installation (System hat keine tree-sitter bindings; regex-Fallback ist aktiv)

**Sektion 4 — Impact-Analyse**

- `chunking.py`: Neue zentrale Chunking-Engine, keine Legacy-Abhängigkeiten
- `adapters/code.py`: Ersetzt blank-line splitting durch chunking.py Delegation
- `adapters/markdown.py`: Erweitert um Breadcrumb-Präfix im Text (nicht nur Metadaten)
- `ingestion.py`: Dual-Collection Router vorbereitet; P3 nutzt noch MiniLM für beide Collections
- `hybrid_retriever.py`: Multi-Collection Vector Search für kb_code_v2 + kb_prose_v2
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_chunking` läuft grün (Boundary-Test, Breadcrumb-Test, AST-Resilience)
- [x] `python -m backend.tests.rag_v2.test_adapters` läuft grün (CodeAdapter + MarkdownAdapter)
- [x] `python -m backend.tests.rag_v2.test_ingestion` läuft grün (Dual-Collection, Idempotenz)
- [x] `python -m backend.tests.rag_v2.test_hybrid_retriever` läuft grün (Multi-Collection)
- [x] `python -m backend.tests.rag_v2.test_rrf` läuft grün
- [x] `python -m backend.tests.rag_v2.test_fts_store` läuft grün
- [x] `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert)
- [x] Code-Chunk Boundary: Kein Chunk endet mitten in einer `def`/`class` Zeile
- [x] Code-Prefixing: Jeder Chunk enthält `# Module: <path>`, `# Symbol: <name>`, `# Imports:`
- [x] Markdown-Breadcrumb: Unterkapitel-Chunks enthalten `## Parent > Child > Sub` als Präfix
- [x] Dual-Collection: Code-Dateien → `kb_code_v2`, Markdown → `kb_prose_v2`

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_chunking
python -m backend.tests.rag_v2.test_adapters
python -m backend.tests.rag_v2.test_ingestion
python -m backend.tests.rag_v2.test_hybrid_retriever
python -m backend.tests.rag_v2.test_rrf
python -m backend.tests.rag_v2.test_fts_store
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/chunking.py`
- Revert `adapters/code.py` auf P1 blank-line splitting
- Revert `adapters/markdown.py` Breadcrumb-Präfix
- Revert `ingestion.py` Single-Collection Logik
- Revert `hybrid_retriever.py` Single-Collection Logik
- Kein Einfluss auf Legacy-System
