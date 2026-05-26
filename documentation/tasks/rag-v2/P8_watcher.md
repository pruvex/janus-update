# Task P8: Background Watchdog — File-System Observer

**Sektion 1 — Ziel**
Implementiere den Background-Watchdog für automatisches Re-Indexing bei Datei-Änderungen. Ziel ist es, Änderungen im Dateisystem in Echtzeit zu erkennen und den V2-Index inkrementell zu aktualisieren, ohne den Haupt-Thread oder die Query-Performance zu blockieren.

**Sektion 2 — Scope (Files)**

- NEU `backend/services/rag/watcher.py` (File-System Observer mit watchdog, Debounce-Queue (2s), Coalesce (1s Batch), Thread-Safe)
- NEU `backend/tests/rag_v2/test_watcher.py` (Unit-Tests: Debounce-Queue, Coalesce, Lifecycle, File-Filter)
- MODIFY `backend/main.py` (P8: Startup/Shutdown Logic für Watcher Integration)
- MODIFY `backend/services/rag/ingestion.py` (P8: run_partial() Methode für inkrementelle Updates)

**Sektion 3 — Out-of-Scope**
- Keine Multi-Workspace Unterstützung (P9)
- Keine Rate-Limiting (P9)

**Sektion 4 — Impact-Analyse**

- `watcher.py`: DebounceQueue mit 2s debounce pro Datei und 1s batch window. RAGEventHandler filtert relevante Dateien (.py, .md, .txt, etc.) und denylist (.env, .pem, node_modules, etc.). RAGWatcher startet watchdog Observer in separatem Thread. `_on_batch_ready()` offloaded indexing to separatem Thread um Observer nicht zu blockieren.
- `ingestion.py`: `run_partial(file_paths: List[str])` Methode für inkrementelle Re-Indexing. Prüft Path-Policy, löscht alte Chunks bei Re-Indexing, aktualisiert last_run_id.
- `main.py`: Watcher Startup in lifespan() (nach Memory Maintenance Tasks). Liest workspace_root aus config (filesystem_workspaces). Graceful Shutdown bei App-Stop.
- Kein Touch an Freeze-List-Files

**Sektion 5 — Acceptance Criteria**

- [x] `python -m backend.tests.rag_v2.test_watcher` läuft grün (4 Tests)
- [x] Debounce-Queue: 10 schnelle Speichervorgänge lösen nur eine Log-Meldung aus
- [x] Coalesce: 10 Datei-Änderungen in 1s lösen einen Batch-Run aus
- [x] Lifecycle: Watcher startet/stopt sauber (keine Zombie-Threads)
- [x] File-Filter: Nur relevante Dateien (.py, .md, .txt) werden verarbeitet
- [x] Partial Update: ingestion.run_partial() re-indexiert nur angegebene Dateien
- [ ] Sync-Gate: Manuelle .py Änderung ≤5s im FTS-Index reflektiert (Integrationstest, benötigt laufendes System)
- [ ] Performance-Gate: p95 Retrieval-Latenz +10% max bei aktivem Watcher (Integrationstest)
- [ ] Stress-Gate: 100 File-Events in 1s keine Lock-Errors (Integrationstest)

**Sektion 6 — Verifikation**

```powershell
python -m backend.tests.rag_v2.test_watcher
# Integrationstests (benötigen laufendes System):
# - Sync-Gate: Manuell Datei ändern, ≤5s auf FTS-Index prüfen
# - Performance-Gate: Retrieval-Latenz mit/ohne Watchdog messen
# - Stress-Gate: 100 Files in 1s erstellen, auf Lock-Errors prüfen
```

**Sektion 7 — Rollback**
- Entferne `backend/services/rag/watcher.py`
- Entferne `backend/tests/rag_v2/test_watcher.py`
- Revert `main.py` (entferne Watcher Startup/Shutdown)
- Revert `ingestion.py` (entferne run_partial())
- Kein Einfluss auf Legacy-System
