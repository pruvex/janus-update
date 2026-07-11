TASK-MEM-M4
- Source Spec: `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`
- Backlog Item: `N/A`
- Feature: Memory Phase C Session-Search FTS5
- Generated At: 2026-07-10

## Generated Tasks

### TASK-MEM-M4.1 Implement Memory Phase C Session-Search as one bounded FTS5 slice
- Ziel:
  - Fuehre Session-Search fuer Chat-Messages als einen kleinen, produktionsnahen Memory-C-Slice ein, inklusive FTS5-Store, zentralem Write-Hook, Backfill-Script, Tool, Skill-Registry und episodischem Intent-Routing.
- Scope:
  - Nur die Session-Search Phase C gemaess Memory Spec Section 6: separates `session_fts.db`, FTS5-Index ueber Message-Content, on-demand Tool `session_search`, Sanitizer-Reuse aus `memory_tools.py`, fokussierte Tests und das Flag `MEMORY_SESSION_SEARCH_ENABLED=false` als Default.
  - Kein Frozen Core, kein USER.md-Export, keine Recall-gap-Arbeit fuer M1, keine Transport-/OAuth-/OpenRouter-Produktarbeit, keine allgemeine Memory-Policy-Neuausrichtung.
- Files:
  - `backend/services/memory/session_fts_store.py`
  - `backend/services/memory/session_search_service.py`
  - `backend/tools/session_search_tools.py`
  - `backend/skills/system/session_search.json`
  - `backend/tool_registry.py`
  - `backend/data/crud.py`
  - `backend/services/orchestrator/intent_engine.py`
  - `backend/tests/test_session_fts_store.py`
  - `backend/tests/test_session_search_tools.py`
  - `backend/tests/test_memory_regression.py` (nur wenn der Session-Search-Routingpfad oder Sanitizer-Reuse direkt abgesichert werden muss)
  - `backend/scripts/backfill_session_fts.py`
- Steps:
  1. Implementiere einen separaten FTS5-Store fuer Chat-Messages mit `message_id`, `chat_id`, `role`, `created_at` als UNINDEXED-Metadaten und `content` als tokenisiertem Feld.
  2. Fuehre einen zentralen Write-Hook im Message-Persistenzpfad ein, damit neue User-/Assistant-Messages bei aktivem Flag direkt in den Session-FTS-Store geschrieben werden.
  3. Implementiere ein bounded `session_search`-Service/Tool mit `query`, `limit`, optionalem `chat_id` und optionalem `since_days`, inklusive Sanitizer-Reuse gegen Secrets und Snippet-Limit.
  4. Registriere das Tool samt Skill-JSON und binde episodische Recall-Signale so an, dass Session-Search nur fuer passende Verlauf-/Zitat-/Was-haben-wir-besprochen-Queries angeboten wird.
  5. Ergaenze ein Backfill-Script fuer bestehende Messages und fokussierte Tests fuer FTS-Store, Tool, Sanitizer, optionale Chat-Filter und Flag-off-Paritaet.
- Acceptance Criteria:
  - Ein separater `session_fts.db`-Store indexiert `messages.content` via FTS5 und liefert Treffer mit `chat_id`, `role` und `created_at` als Metadaten.
  - Neue Messages werden bei aktivem Flag ueber den zentralen Persistenzpfad ohne Batch-Abhaengigkeit indexiert.
  - Das Tool `session_search` liefert on-demand episodische Treffer mit auf maximal 500 Zeichen begrenzten Snippets.
  - Sensitive Inhalte werden in Ergebnissen fail-closed gefiltert; Secret-/Password-Strings erscheinen nicht im Tool-Output.
  - `MEMORY_SESSION_SEARCH_ENABLED` defaultet auf `false`, und Flag-off behaelt das bisherige Produktverhalten bei.
- Tests:
  - `python -m pytest backend/tests/test_session_fts_store.py -v`
  - `python -m pytest backend/tests/test_session_search_tools.py -v`
  - `python -m pytest backend/tests/test_memory_regression.py -q`
  - `python -m py_compile backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py backend/data/crud.py backend/services/orchestrator/intent_engine.py backend/tool_registry.py backend/scripts/backfill_session_fts.py`
- Model: 5.6 Terra
- Reason:
  - Roadmap `M4 MC` und Memory Spec Section 6 binden dieselbe naechste Track-A-Slice: Session-Search bringt den groessten offenen Memory-C-Nutzen, bleibt aber als ein klarer FTS/Tool/Routing-Block noch kompakt genug fuer einen einzelnen bounded Implementierungsdurchlauf.
- Closeout:
  - Final Audit PASS ist in `documentation/tasks/TASK-MEM-M4.1_final_audit.md` dokumentiert. Die Memory-Phase-C-Slice ist task-scharf abgeschlossen: ein separater FTS5-Store wird ueber den kanonischen Message-Persistenzpfad beschrieben, das bounded `session_search`-Tool ist registriert und episodische Recall-Signale koennen den Toolpfad gezielt verwenden.
  - Die lokale Evidenz umfasst fokussierte Store-/Tool-Tests, den gebundenen Memory-Regression-Block (`20 passed`), Compile- und scoped-diff-Checks sowie enabled-runtime Janus-Nachweise fuer Chat-uebergreifenden `Acme GmbH`-Recall und Passwort-Verweigerung. Der Default des Flags bleibt `false`; der Live-Proof lief isoliert mit aktiviertem Flag.
  - Kein Frozen Core, kein USER.md-Export, keine Transport-/OAuth-/OpenRouter-Produktarbeit und keine allgemeine Memory-Policy-Erweiterung werden durch diesen PASS impliziert. Alternative Passwort-Paraphrasen mit Routing-Drift bleiben als angrenzende Routing-Schuld dokumentiert.
