# Task P6: Security & Observability — Path Policy + Retrieval Logging

**Sektion 1 — Ziel**
Implementiere den Schutz- und Diagnose-Layer. Workspace-Sentinel Integration (Pfad-Sicherheit), sensible Dateien (Secrets) vom Index ausschließen, jeden Retrieval-Vorgang für die Forensik loggen.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/path_policy.py` (Denylist: .env, .pem, .key, node_modules, .git, venv, DB-Files. Path-Traversal Schutz: Symlinks, ../, Absolute Path Check)
- NEU `backend/services/rag/retrieval_logger.py` (JSON-Line Logger für backend/logs/rag_retrieval.log. Inhalt: Query, Router-Entscheidung, Latenz-Breakdown, Top-1 Ergebnis. Rotation: RotatingFileHandler 10MB, 5 Backups)
- NEU `backend/tests/rag_v2/test_security.py` (Pen-Tests: Secret-Leak Gate, Path-Escape Gate, Observability Gate, Denylist Coverage)
- MODIFY `backend/services/rag/ingestion.py` (P6: PathPolicy Check in run-Schleife, [SKIP] Log für denied Files, enable_path_policy Parameter)
- MODIFY `backend/services/rag/hybrid_retriever.py` (P6: Retrieval-Logging mit Latenz-Breakdown: vector_ms, keyword_ms, rrf_ms, rerank_ms, expand_ms, total_ms)

**Sektion 3 — Out-of-Scope**
- Keine Rate-Limiting (P8 Watchdog)
- Keine Health-Check Endpunkte (P7 Skill-API)

**Sektion 4 — Impact-Analyse**

- `path_policy.py`: Hard Denylist für Secrets (.env, .pem, .key), Dependencies (node_modules, venv), VCS (.git), Databases (.db, .sqlite). Path-Traversal Schutz via resolve() + relative_to(). SecurityError bei Verletzung.
- `retrieval_logger.py`: Singleton JSON-Line Logger mit RotatingFileHandler (10MB, 5 Backups). Log-Events: query, ingestion_skip, ingestion_success.
- `ingestion.py`: P6 Integration mit enable_path_policy Parameter (default True). Denied Files werden mit [SKIP] Log-Eintrag übersprungen. stats["denied"] Counter.
- `hybrid_retriever.py`: P6 Retrieval-Logging mit Latenz-Breakdown (vector_ms, keyword_ms, rrf_ms, rerank_ms, expand_ms, total_ms). Router-Decision und Top-1 Ergebnis im Log.
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_security` läuft grün (25 Tests)
- [x] `python -m backend.tests.rag_v2.test_query_router` läuft grün
- [x] `python -m backend.tests.rag_v2.test_rrf` läuft grün
- [x] `python -m backend.tests.rag_v2.test_hybrid_retriever` läuft grün
- [x] `python -m backend.tests.rag.test_legacy_filesystem_isolation` → grün (Hash unverändert: 607afb4e...)
- [x] Secret-Leak Gate: .env Datei wird NICHT in indexed_files DB oder FTS-Index indiziert
- [x] Path-Escape Gate: /etc/passwd oder ../config.json wirft SecurityError
- [x] Observability Gate: Jeder hybrid_retriever.query() Call produziert validen JSON-Log-Eintrag
- [x] Denylist Coverage: node_modules, venv, .git, __pycache__, .pem, .key, .db, .sqlite werden alle abgelehnt
- [x] Allowlist: .gitignore, .dockerignore, .env.example werden zugelassen
- [x] Path-Traversal: Symlinks außerhalb Root werden abgelehnt (SecurityError)

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_security
python -m backend.tests.rag_v2.test_query_router
python -m backend.tests.rag_v2.test_rrf
python -m backend.tests.rag_v2.test_hybrid_retriever
python -m backend.tests.rag.test_legacy_filesystem_isolation
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/path_policy.py`
- Entferne `backend/services/rag/retrieval_logger.py`
- Revert `ingestion.py` (entferne P6 Integration)
- Revert `hybrid_retriever.py` (entferne P6 Logging)
- Entferne `test_security.py`
- Kein Einfluss auf Legacy-System
