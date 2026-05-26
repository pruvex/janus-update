# Task P7: Skill API — Unified RAG Interface

**Sektion 1 — Ziel**
Implementiere den API-Layer für RAG V2. Einführung des neuen Skills knowledge.code_search und additive Erweiterung von knowledge.query.

**Sektion 2 — Scope (Files)**

- NEU `backend/skills/knowledge/code_search.json` (Skill Manifest für Code-Suche, Fokus auf technische Anfragen)
- NEU `backend/services/rag/api_adapter.py` (Adapter Layer für V2, Lazy-Loading, Zero-Regression Guard)
- NEU `backend/services/knowledge_service.py` (Unified RAG Interface, retrieval_mode Parameter, file_type_filter, Default="legacy")
- NEU `backend/tests/rag_v2/test_api_compat.py` (API Kompatibilitäts-Test: Byte-Ident Gate, Zero-Regression Guard, Orphan-Registry Gate)
- MODIFY `backend/api/routers/system.py` (P7: GET /api/system/rag-status Health-Check Endpunkt)
- MODIFY `backend/data/capability_registry.json` (P7: knowledge.code_search Ability hinzugefügt)

**Sektion 3 — Out-of-Scope**
- Keine Rate-Limiting (P8 Watchdog)
- Keine Frontend-Integration (P9)

**Sektion 4 — Impact-Analyse**

- `code_search.json`: Skill Manifest für Code-Suche mit Fokus auf technische Anfragen ("Wo ist Funktion X?", "Code-Referenzen"). retrieval_mode="v2" hardcoded.
- `api_adapter.py`: Adapter Layer mit Lazy-Loading von V2 Komponenten. `_get_v2_retriever()` lädt hybrid_retriever nur beim ersten Aufruf. `query_v2()` wrapper für V2 Queries. `get_v2_status()` für Health-Checks.
- `knowledge_service.py`: Neue Unified RAG Interface mit `query()` Funktion. Parameter: `retrieval_mode` (Literal["legacy", "v2", "hybrid"] = "legacy"), `file_type_filter` (list[str] | None = None). **Zero-Regression Guard**: Wenn retrieval_mode="legacy", wird V2 NICHT initialisiert. `_query_legacy()` ruft rag_manager.py auf. `_query_v2()` ruft api_adapter auf.
- `system.py`: GET /api/system/rag-status Endpunkt. Returns Status beider Chroma-Instanzen (legacy + V2), Anzahl indizierter Files in V2, FTS5-Status.
- `capability_registry.json`: Added knowledge.code_search ability to knowledge_hub section.
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_api_compat` läuft grün (3 Tests)
- [x] Byte-Ident Gate: knowledge.query ohne neue Parameter hat Standard-Werte (retrieval_mode="legacy", file_type_filter=None)
- [x] Zero-Regression Guard: V2 wird nur initialisiert wenn retrieval_mode="v2" oder "hybrid"
- [x] Orphan-Registry Gate: Keine orphan warnings in capability_registry.json
- [x] Legacy-Isolation: `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash: 607afb4e...)
- [x] /api/system/rag-status Endpunkt implementiert (returns legacy + v2 status)
- [x] code_search.json Skill Manifest erstellt (Fokus: Code-Search, retrieval_mode="v2")

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_api_compat
python -m backend.tests.rag.test_legacy_filesystem_isolation
python -m backend.tests.test_e2e_diamond_journeys  # E2E Test (optional, dauert länger)
```

**Sektion 7 — Rollback**
- Entferne `backend/skills/knowledge/code_search.json`
- Entferne `backend/services/rag/api_adapter.py`
- Entferne `backend/services/knowledge_service.py`
- Revert `system.py` (entferne /api/system/rag-status)
- Revert `capability_registry.json` (entferne knowledge.code_search)
- Entferne `test_api_compat.py`
- Kein Einfluss auf Legacy-System
