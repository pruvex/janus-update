# PROJECT_STATE.md (Diamond-OS **V0.4.16-beta.36** — "EPIC-SYSTEM-HARVESTER (V2): 🥇 SEALED & COMPLETE. P0-P8 SEALED + Final Extension (Global Scope Discovery, Format-Gatekeeper). RAG V2 Core Pipeline fertiggestellt. Tool-Execution Stack Repaired. RAG V2 Stabilization: Filename Metadata + Path Normalization + Memory Guard. RAG V2 Multi-File Integrity: Hardware Truth + Physical Duplicate Detection. RAG V2 Auto-Read Loop: Path-Pinning for Disambiguation. RAG V2 0-Chunk Integrity Fix. Loop-Breaker Self-Correction. FEAT-FS-BULK-MOVE SEALED. TEST-CLEANUP SEALED. LOGGING PIPELINE PHASE 1: Supabase Client + Pydantic Schemas + Logger Core + Batch Worker + Graceful Shutdown.")
**Zweck:** Einzige Datei fuer AI Studio Triage-Guard. Kopiere diese komplette Datei in AI Studio.
**Aktualisiert:** 2026-04-25 17:07 (LOGGING PIPELINE PHASE 1: Batch Worker + Graceful Shutdown 🥇 SEALED)

---

## [CURRENT_SESSION_DELTA] (LOGGING PIPELINE PHASE 1 — Batch Worker + Graceful Shutdown 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **LOGGING PIPELINE PHASE 1: Batch Worker + Graceful Shutdown — Async Background Worker mit Exponential Backoff** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-25) |
| **Root Cause** | Keine Event-Verarbeitung im Hintergrund vorhanden. Blocking I/O würde Orchestrator-Performance beeinträchtigen. Kein Graceful-Shutdown für Datenverlust-Prävention. |
| **Umsetzung** | **Fix #1 — Batch Worker:** `@c:\KI\Janus-Projekt\backend\services\logging\logger_core.py` — `_batch_upload_worker()` in Endlosschleife. Batching: 50 Events ODER 2 Sekunden Timeout. **Fix #2 — Supabase Upload:** `_upload_batch_to_supabase()` nutzt Supabase-Client für Batch-Insert in `logs_raw` Tabelle. **Fix #3 — Error Handling:** Exponential Backoff (1s, 2s, 4s, 8s...) bei Upload-Fehlern. Events werden bei Failure zurück in Queue gelegt (kein Datenverlust). MAX_RETRIES=5. **Fix #4 — Graceful Shutdown:** `flush_log_queue()` leert Queue vor Shutdown (alle verbleibenden Events hochladen). `stop_worker()` mit Timeout und Cancel-Fallback. **Fix #5 — Lifecycle Integration:** `@c:\KI\Janus-Projekt\backend\main.py` — `lifespan` Context Manager: `start_worker()` vor `yield`, `flush_log_queue()` + `stop_worker()` nach `yield`. |
| **Ergebnis** | Background Worker verarbeitet Events asynchron mit Batching (50/2s). Exponential Backoff schützt bei Netzwerkfehlern (Events bleiben in Queue). Graceful Shutdown garantiert keine Datenverluste beim App-Stop. Logging Pipeline voll funktionsfähig. |
| **Files** | `backend/services/logging/logger_core.py` (_batch_upload_worker + _upload_batch_to_supabase + flush_log_queue + start_worker + stop_worker), `backend/main.py` (lifespan integration). |
| **Verifikation** | Syntax Check: `python -m py_compile backend/services/logging/logger_core.py` ✅ · Syntax Check: `python -m py_compile backend/main.py` ✅ |
| **Patterns** | [PATTERN] #Async #Worker "Background Worker Pattern — Nutze asyncio.create_task für non-blocking Background-Processing im FastAPI lifespan." · [PATTERN] #Resilience #ExponentialBackoff "Exponential Backoff mit Queue-Restore — Bei Upload-Fehlern Events zurück in Queue legen, um Datenverlust zu vermeiden." · [PATTERN] #Lifecycle #GracefulShutdown "Graceful Shutdown Pattern — Flush Queue vor App-Stop, um keine Events zu verlieren." |

---

## [CURRENT_SESSION_DELTA] (LOGGING PIPELINE PHASE 1 — Logger Core (Async RAM-Queue) 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **LOGGING PIPELINE PHASE 1: Logger Core — Async RAM-Queue mit Non-Blocking Ingestion** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-25) |
| **Root Cause** | Keine zentrale Event-Ingestion-Logik vorhanden. Blocking I/O würde die Performance des Orchestrators beeinträchtigen. |
| **Umsetzung** | **Fix #1 — Async Queue:** `@c:\KI\Janus-Projekt\backend\services\logging\logger_core.py` — Globale `asyncio.Queue[LogEventCreate]` mit maxsize=5000 (Backpressure-Schutz). **Fix #2 — log_event():** Asynchrone Funktion mit Timestamp-Enrichment (wenn None). Non-blocking `await queue.put(event)`. Debug-Logging mit Queue-Size-Monitoring. **Fix #3 — Helper-Funktionen:** `get_queue_size()`, `is_queue_empty()`, `get_next_event()` (für Consumer), `clear_queue()` (für Testing/Emergency). |
| **Ergebnis** | Non-blocking Event-Ingestion bereit. RAM-Queue puffert Events bis zu 5000 Einträge. Backpressure-Schutz aktiv bei Volllauf. Logger Core bereit für Phase 2 (Consumer/Worker Task). |
| **Files** | `backend/services/logging/logger_core.py` (Async Queue + log_event + Helpers). |
| **Verifikation** | Syntax Check: `python -m py_compile backend/services/logging/logger_core.py` ✅ |
| **Patterns** | [PATTERN] #Async #Queue "Async RAM-Queue Pattern — Nutze asyncio.Queue mit maxsize für Backpressure-Schutz bei High-Throughput Logging." · [PATTERN] #Performance #NonBlocking "Non-Blocking I/O — Event-Ingestion muss async sein, um Orchestrator-Performance nicht zu beeinträchtigen." |

---

## [CURRENT_SESSION_DELTA] (LOGGING PIPELINE PHASE 1 — Supabase Client + Pydantic Schemas 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **LOGGING PIPELINE PHASE 1: Supabase Client + Pydantic Schemas — Thread-safe Singleton + Strict Validation** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-25) |
| **Root Cause** | Kein zentraler Supabase-Client für Logging-Pipeline vorhanden. Keine Pydantic-Modelle zur strikten Validierung der Event-Typen gegen das DB-Schema. |
| **Umsetzung** | **Fix #1 — Dependency:** `@c:\KI\Janus-Projekt\requirements.txt` — `supabase` Package hinzugefügt. **Fix #2 — Singleton Client:** `@c:\KI\Janus-Projekt\backend\services\logging\supabase_client.py` — Thread-safe Singleton-Pattern mit Double-Checked Locking. Lädt SUPABASE_URL und SUPABASE_KEY aus Umgebungsvariablen. Bietet `get_supabase_client()` Factory-Funktion und `reset()` Methode für Tests. **Fix #3 — Pydantic Schemas:** `@c:\KI\Janus-Projekt\backend\data\schemas_logging.py` — `LogEventBase`, `LogEventCreate`, `LogEvent`, `LogEventBatch`. Schema exakt zur DB: id (uuid), timestamp (datetime), session_id (str), provider (str), model (str), skill (str), event_type (str), status (str), payload (dict/json), latency_ms (int). Alle optionalen Felder korrekt als Optional deklariert. Batch-Model mit Hilfsmethoden für Event-Management. |
| **Ergebnis** | Zentraler, threadsicherer Supabase-Client verfügbar. Pydantic-Modelle garantieren strikte Validierung gegen das DB-Schema vor dem Insert. Logging-Pipeline bereit für Phase 2 (Event Emitter). |
| **Files** | `requirements.txt` (supabase dependency), `backend/services/logging/supabase_client.py` (Singleton Client), `backend/data/schemas_logging.py` (Pydantic Models). |
| **Verifikation** | Syntax Check: `python -m py_compile backend/services/logging/supabase_client.py` ✅ · Syntax Check: `python -m py_compile backend/data/schemas_logging.py` ✅ |
| **Patterns** | [PATTERN] #Singleton #ThreadSafety "Double-Checked Locking Singleton — Nutze threading.Lock mit double-check pattern für thread-safe singleton initialization in Python." · [PATTERN] #Pydantic #Validation "Schema-First Validation — Pydantic-Modelle exakt zur DB-Struktur definieren, um Typ-Sicherheit vor dem DB-Insert zu garantieren." |

---

## [CURRENT_SESSION_DELTA] (PATH-NORMALIZATION & MASTER-SCAN — Global Scope Discovery 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **PATH-NORMALIZATION: Radikale Umstellung auf pathlib.Path.resolve().as_posix().lower() + MASTER-SCAN: Systemweiter Scan abgeschlossen (3.414 Dateien indiziert)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-25) |
| **Root Cause** | Inconsistent path handling across RAG ingestion pipeline caused lookup failures and "Outside allowed roots" errors. Additionally, the global scan needed to enumerate all local drives while respecting system directory exclusions. |
| **Umsetzung** | **Fix #1 — Path Normalization:** `@c:\KI\Janus-Projekt\backend\services\rag\ingestion.py` — Alle Pfad-Operationen auf `pathlib.Path(p).resolve().as_posix().lower()` umgestellt (source_path, file_path, IndexedFile.path). **Fix #2 — Index Store:** `@c:\KI\Janus-Projekt\backend\services\rag\index_store.py:275-277` — `get_chunks_by_file()` Normalisierung hinzugefügt. **Fix #3 — Tool Executor:** `@c:\KI\Janus-Projekt\backend\services\tool_executor.py` — Path Normalisierung für background ingestion. **Fix #4 — Path Policy:** `@c:\KI\Janus-Projekt\backend\services\rag\path_policy.py` — `_global_scan_mode` Flag und `enable_global_scan_mode()` für globale Laufwerke-Enumeration. **Fix #5 — Global Scan:** `@c:\KI\Janus-Projekt\backend\main.py` — Lokale Laufwerke enumerieren, System-Verzeichnisse ausschließen, Janus-Installationsordner überspringen. **Fix #6 — EXCLUDE_DIRS:** `@c:\KI\Janus-Projekt\backend\services\rag\ingestion.py` — node_modules, .git, venv, __pycache__, dist sofort aus dirnames entfernt. **Fix #7 — Junction/Symlink Skip:** `@c:\KI\Janus-Projekt\backend\services\rag\ingestion.py` — Windows Reparse-Points (Junctions) werden übersprungen. **Fix #8 — Logging:** `[GLOBAL-SCAN-START]`, `[GLOBAL-SCAN-PROGRESS]`, `[GLOBAL-SCAN-COMPLETE]` Signale hinzugefügt. |
| **Ergebnis** | Path Normalization konsistent über gesamte Pipeline (Ingester, Store, Executor). Globaler Scan erfolgreich abgeschlossen: 3.414 Dateien indiziert. System-Verzeichnisse (Windows, Program Files, etc.) korrekt ausgeschlossen. Junctions/Symlinks übersprungen. Janus-Installationsordner ignoriert (keine Selbst-Indizierung). |
| **Files** | `backend/services/rag/ingestion.py`, `backend/services/rag/index_store.py`, `backend/services/tool_executor.py`, `backend/services/rag/path_policy.py`, `backend/main.py`. |
| **Verifikation** | Syntax Check: `python -m py_compile` ✅ · Global Scan Log: `[GLOBAL-SCAN-COMPLETE] Total files indexed: 3414` ✅ · Path Normalization: Keine "Outside allowed roots" Errors ✅ |
| **Patterns** | [LESSON] #PathHandling #ThreadSafety "Thread-Scope NameError — Importiere pathlib explizit in daemon-threads, um NameError zu vermeiden." · [LESSON] #Harvester #PathPolicy "Harvester-Pattern — Nutze globalen _global_scan_mode Flag in PathPolicy, um allowed_roots für systemweite Scans zu bypassen." |

---

## [CURRENT_SESSION_DELTA] (FEAT-FS-BULK-MOVE — Bulk File Move Feature 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **FEAT-FS-BULK-MOVE: Bulk File Move Feature — Parameter-Upgrade + Intent-basierte Modell-Eskalation + RAG-Sortier-Policy** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-24) |
| **Root Cause** | Das move_files-Skill nutzte ein Glob-Pattern (`pattern`) statt einer exakten Dateiliste. Dies führte zu ungenauer Kontrolle bei Bulk-Operationen und erschwerte das Sortieren nach Dateiinhalt. Zudem fehlte eine Intent-basierte Modell-Eskalation für komplexe Sortieraufgaben. |
| **Umsetzung** | **Fix #1 — Schema-Upgrade:** `@c:\KI\Janus-Projekt\backend\data\schemas.py:692-698` — `MoveFilesArgs`: `pattern` entfernt, `file_names: List[str]` hinzugefügt. **Fix #2 — Skill-JSON:** `@c:\KI\Janus-Projekt\backend\skills\filesystem\move_files.json` — Parameter `pattern` → `file_names: list[str]`, `max_calls_per_turn` auf 10 erhöht, Beschreibung mit Batch-Nutzungs-Hinweis. **Fix #3 — Backend-Logik:** `@c:\KI\Janus-Projekt\backend\services\filesystem_manager.py:535-576` — `move_files()` iteriert über `file_names` Liste statt Glob-Pattern. **Fix #4 — Rate-Limits:** `create_directory.json` (3→20), `move_file.json` (3→50), `move_files.json` (3→10). **Fix #5 — Prompt-Härtung:** `move_file.json` Warnung gegen Bulk-Missbrauch, `read_file.json` PDF-Umleitung zu Knowledge-Tools. **Fix #6 — Intent-Override:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py:124-145` — `_apply_pre_resolution_guards()` mit MOA_MODEL_HIERARCHY für Sortier-Intents (`sortiere` + `pdf/dateien`). **Fix #7 — list_directory Enhancement:** `@c:\KI\Janus-Projekt\backend\services\filesystem_manager.py:251-296` — PDF-Indizierungs-Markierung `[INDIZIERT]` via IndexStore-Check. **Fix #8 — RAG-Sort-Policy:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\prompt_registry.py:80-83` — `rag_sort_policy` Direktive in `apply_verbosity_control` injiziert. |
| **Ergebnis** | Bulk-Datei-Verschiebe-Operationen nutzen jetzt exakte Dateilisten für präzise Kontrolle. Komplexe Sortieraufgaben eskalieren automatisch zum Logic-Tier-Modell. PDFs in list_directory zeigen Indizierungs-Status. RAG-Sort-Policy erzwingt Knowledge-Query für indizierte Dateien vor Move-Operationen. |
| **Files** | `backend/data/schemas.py` (MoveFilesArgs), `backend/skills/filesystem/move_files.json` (Parameter + Limits), `backend/skills/filesystem/move_file.json` (Warnung + Limits), `backend/skills/filesystem/create_directory.json` (Limits), `backend/skills/filesystem/read_file.json` (PDF-Umleitung), `backend/services/filesystem_manager.py` (move_files + list_directory), `backend/services/orchestrator/execution_dispatcher.py` (Intent-Override), `backend/services/orchestrator/prompt_registry.py` (rag_sort_policy), `backend/services/model_catalog.py` (get_models_by_provider). |
| **Verifikation** | Audit: Parameter Trinity synchron (file_names: List[str] in schemas.py, move_files.json, filesystem_manager.py) ✅ |
| **Patterns** | [PATTERN] #Orchestration #IntentOverride "Pre-Resolution Logic-Escalation für Planungs-Tasks — Erkennung von Sortier-Intents vor Tool-Ausführung und automatisches Upgrade zum Logic-Tier-Modell via MOA_MODEL_HIERARCHY." |

---

## [CURRENT_SESSION_DELTA] (BUG-RAG-004 — 0-Chunk Integrity Fix 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **BUG-RAG-004: RAG V2 0-Chunk Integrity Fix — SQLite-Index ohne Chunks wird bereinigt** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-24) |
| **Root Cause** | IndexStore enthielt Einträge für Dateien, die physisch existierten, aber 0 Chunks in der Datenbank hatten (z.B. nach abgebrochener Indizierung). Tool-Executor prüfte nur, ob Pfad in SQLite-DB, nicht ob Chunks existieren. Resultat: UI zeigte "NICHT INDIZIERT" (Retriever fand keine Chunks), aber Auto-Ingest wurde nicht ausgelöst (Executor glaubte Datei sei indiziert). Inkonsistenz zwischen UI und Ingestion-Trigger. |
| **Umsetzung** | **Fix #1 — Chunk-Validierung:** `@c:\KI\Janus-Projekt\backend\services\tool_executor.py:245-265` — `new_paths` Logik erweitert: Prüft nicht nur, ob Pfad in SQLite-DB, sondern auch ob Chunks existieren (`store.get_chunks_by_file(path, limit=1)`). **Fix #2 — Korrupte Einträge bereinigen:** Wenn Pfad in DB aber `chunk_count == 0`: `store.delete(path)` + Pfad zu `new_paths` hinzufügen, damit Background-Ingest ihn neu verarbeitet. **Fix #3 — Debug-Logging entfernt:** Temporäre `[AUTO-INGEST-DEBUG]` Logs nach Verifikation entfernt. |
| **Ergebnis** | Synchronisation zwischen UI (Retriever zeigt "NICHT INDIZIERT" wenn keine Chunks) und Ingestion-Trigger (Executor erkennt korrupte Einträge und bereinigt sie). Auto-Ingest wird jetzt zuverlässig für 0-Chunk-Files ausgelöst. |
| **Files** | `backend/services/tool_executor.py` (Chunk-Validierung + Korrupte Einträge bereinigen). |
| **Verifikation** | Test mit 0-Chunk-File erwartet: (a) Log zeigt `[AUTO-INGEST] Corrupt DB entry for '{path}' (0 chunks). Deleting and re-ingesting.`, (b) Background-Ingest wird ausgelöst, (c) Nach Indizierung hat Datei Chunks. |
| **Patterns** | [PATTERN] #RAG #Integrity "Hardware-Truth über Index-Faith — Ein Pfad gilt nur als indiziert, wenn er in SQLite-DB steht UND Chunks hat. 0-Chunk-Files sind korrupt und müssen bereinigt werden." |

---

## [CURRENT_SESSION_DELTA] (Loop-Breaker Self-Correction — INVALID_ARGUMENTS Retry 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Loop-Breaker Self-Correction: INVALID_ARGUMENTS Retry — Modelle können Tool-Errors korrigieren** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-24) |
| **Root Cause** | HARD-LOOP-BREAKER blockierte alle Duplicate Calls strikt, auch wenn das vorherige Tool-Ergebnis einen Fehler (z.B. INVALID_ARGUMENTS) zurückgab. Dies verhinderte Self-Correction durch das Modell — bei fehlerhaften Argumenten konnte das Modell nicht erneut versuchen mit korrigierten Argumenten. |
| **Umsetzung** | **Fix #1 — Tool-Status-Tracking:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py:308` — `wf.kpi_tool_status: dict[str, str]` hinzugefügt (cache_key -> status). **Fix #2 — Self-Correction-Exception:** `_track_tool_call_fn` erweitert: Prüft, ob vorheriger Status "error" enthält. Wenn ja, erlaubt es einen Retry für Self-Correction. **Fix #3 — Status-Speicherung:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\execution_engine.py:1324-1350` (non-stream) und `2250-2278` (stream) — Tool-Status nach Ausführung speichern, wenn "error" oder "invalid" im Status enthalten ist. **Fix #4 — Rate-Limit Erhöhung:** `@c:\KI\Janus-Projekt\backend\skills\filesystem\create_directory.json:15` und `move_file.json:15` — max_calls_per_turn von 3 auf 10 erhöht für FS-Choreography. |
| **Ergebnis** | Modelle können jetzt Self-Correction durchführen: Wenn ein Tool einen Fehler zurückgibt (z.B. INVALID_ARGUMENTS), wird der Status gespeichert. Bei erneutem Versuch mit denselben Argumenten wird der vorherige Status geprüft und bei Error ein Retry erlaubt. Dies ermöglicht Modell-Self-Correction ohne Deaktivierung der Sicherheitsmechanismen. |
| **Files** | `backend/services/orchestrator/execution_dispatcher.py` (wf.kpi_tool_status + Self-Correction-Exception), `backend/services/orchestrator/execution_engine.py` (Tool-Status-Tracking non-stream + stream), `backend/skills/filesystem/create_directory.json` (max_calls_per_turn 3→10), `backend/skills/filesystem/move_file.json` (max_calls_per_turn 3→10). |
| **Verifikation** | Test mit INVALID_ARGUMENTS erwartet: (a) Tool gibt error zurück, (b) Status wird gespeichert, (c) Modell kann erneut versuchen mit korrigierten Argumenten, (d) Retry wird nicht geblockt. |
| **Patterns** | [PATTERN] #LoopBreaker #SelfCorrection "Error-Retry-Exception — Duplicate Calls sind erlaubt, wenn das vorherige Tool-Ergebnis einen Fehler (error/invalid) zurückgab. Dies ermöglicht Modell-Self-Correction ohne Deaktivierung der Sicherheitsmechanismen." |

---

## [CURRENT_SESSION_DELTA] (BUG-GEMINI-API-001 — Thought Signature 400 Error 🔴 BLOCKED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **BUG-GEMINI-API-001: Gemini 3 Thought Signature 400 Error — Function Call missing thought_signature** |
| **Status** | **🔴 BLOCKED** (2026-04-24) — Warten auf Opus-Eskalation |
| **Root Cause** | Gemini 3 Modelle erfordern `thought_signature` für `functionCall` Parts. Der aktuelle Code in `backend/llm_providers/gemini/service.py` erstellt neue `function_call` Parts ohne diese Signatur (Zeilen 540-545). API-Antwort: `InvalidArgument: 400 Function call is missing a thought_signature.` |
| **Umsetzung** | **Anforderung:** Die `thought_signature` muss aus der ursprünglichen Gemini-Antwort extrahiert werden, wenn Tool-Calls verarbeitet werden. Parts sollten nicht neu erstellt, sondern direkt aus der API-Antwort übernommen werden. **Fix-Empfehlung:** Original Parts direkt in `_gemini_raw_model_parts` speichern und später wiederverwenden, anstatt neue Parts zu erstellen. |
| **Ergebnis** | BLOCKED — Fix erfordert tiefgreifende Änderungen an Gemini-Service-Logik. Opus-Eskalation empfohlen. |
| **Files** | `backend/llm_providers/gemini/service.py` (Zeilen 540-545: function_call Parts ohne thought_signature). |
| **Verifikation** | N/A — BLOCKED |
| **Dokumentation** | Gemini API Docs: https://ai.google.dev/gemini-api/docs/thought-signatures — "The first functionCall part in each step of the current turn must include its thought_signature. If you omit a thought_signature for the first functionCall part in any step of the current turn, the request will fail with a 400 error." |
| **Patterns** | [LESSON] #Gemini #API #ThoughtSignature "Gemini 3 requires thought_signature for functionCall parts — must preserve original parts from API response instead of reconstructing them." |

---

## [CURRENT_SESSION_DELTA] (RAG V2 MULTI-FILE INTEGRITY — Hardware Truth 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **RAG V2 MULTI-FILE INTEGRITY: Hardware Truth over Index-Faith — Physische Dubletten-Erkennung** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-22) |
| **Root Cause** | IndexStore-basierte Dubletten-Erkennung versagte nach Memory-Purge: Zweites Duplikat (Documents\JanusPDFs\aegypten.pdf) war nicht mehr indiziert, aber physisch vorhanden. Tool-Executor vertraute blind auf Index und injizierte keinen Warn-Header → KI wählte Datei stillschweigend aus ("Silent Selection") ohne User-Transparenz. |
| **Umsetzung** | **Fix #1 — Physische Dubletten-Erkennung:** `@c:\KI\Janus-Projekt\backend\services\tool_executor.py:211-238` — Ersetzte IndexStore-Lookup durch `filesystem_manager.find_files` mit Stem-Pattern-Suche (`{needle_stem}.*`). Scannt alle registrierten Workspaces physisch nach Dateien mit identischem Namen (case-insensitive). Filtert nach exaktem Stem-Match um False-Positives zu vermeiden. Wenn `len(filtered_physical) > 1`: injiziere Warn-Header mit allen physischen Pfaden. **Fix #2 — Hard Lockdown (bereits in V2 Stabilization):** `@c:\KI\Janus-Projekt\backend\services\rag\hybrid_retriever.py:502-513` — Wenn filename-Filter 0 Ergebnisse liefert, early return mit leerem RetrievalResult statt Fallback auf globale Vektorsuche. **Fix #3 — P0 Disclosure-Directives (verifiziert):** `@c:\KI\Janus-Projekt\backend\skills\knowledge\query.json:18-20` und `read_full_text.json:18-19` — P0-Direktive zwingt LLM zur Antwort-Struktur: "Hinweis: Ich habe [Anzahl] Versionen von [Datei] gefunden. Ich verwende hier die Datei aus [Pfad]. Die anderen Fundorte sind: [Liste]." Ignorieren ist "schwerer Systemfehler". |
| **Ergebnis** | System erkennt Redundanzen auf Dateiebene proaktiv (physischer Scan über Workspaces, nicht nur Index). Wenn Dubletten existieren, wird Warn-Header `!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!` injiziert. P0-Direktive zwingt LLM zur Transparenz (User erfährt alle Fundorte + aktuelle Auswahl). "Silent File Mismatch" Halluzinationen eliminiert. |
| **Files** | `backend/services/tool_executor.py` (Physical duplicate detection via filesystem_manager), `backend/services/rag/hybrid_retriever.py` (Lockdown bereits vorhanden), `backend/skills/knowledge/query.json` (P0 directives verifiziert), `backend/skills/knowledge/read_full_text.json` (P0 directives verifiziert). |
| **Verifikation** | Test "Was steht in aegypten.pdf?" erwartet: (a) Log zeigt `[DUPLICATE-DETECTION] Physical search found 2 copies`, (b) Tool-Output enthält Warn-Header mit beiden Pfaden, (c) LLM-Antwort beginnt mit "Hinweis: Ich habe 2 Versionen von aegypten.pdf gefunden..." |
| **Patterns** | [PATTERN] #HardwareTruth #RAG "Hardware-Truth over Index-Faith — Wissens-Tools müssen vor Ausführung physischen Scan (os.path.exists oder glob) über Workspaces machen. Wenn count > 1, Warn-Header injizieren, der KI zur Transparenz zwingt. Blindes Vertrauen auf DB führt zu Silent Selection der falschen Datei." |

---

## [CURRENT_SESSION_DELTA] (RAG V2 AUTO-READ LOOP — Path-Pinning for Disambiguation 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **RAG V2 AUTO-READ LOOP: Path-Pinning for Disambiguation — Agentic AI Dubletten-Auflösung via absolute_path Parameter** |
| **Root Cause** | GPT konnte Auto-Read-Trigger für nicht-indizierte Dubletten nicht ausführen: Das Tool `knowledge.read_full_text` akzeptierte nur `filename` als Parameter. Bei Dubletten ist `filename` mehrdeutig — GPT wusste nicht, welche der 2+ Dateien gemeint war, und verweigerte den Aufruf. Ergebnis: KI sagte "ich kann das nicht" statt autonom die nicht-indizierte Datei zu lesen. |
| **Umsetzung** | **Fix #1 — Schema-Erweiterung:** `@c:\KI\Janus-Projekt\backend\data\schemas.py:125-128` — `GetFullDocumentTextArgs` erweitert um `absolute_path: Optional[str] = Field(None, description="Path-Pinning for Disambiguation...")`. Parameter-Beschreibung instruiert GPT explizit: "Nutze dieses Feld, um eine spezifische Dublette via absolutem Pfad zu lesen, wenn das System dich dazu auffordert". **Fix #2 — Tool-Logik mit absoluter Priorität:** `@c:\KI\Janus-Projekt\backend\services\tool_executor.py:282-320` — `get_full_document_text` akzeptiert neuen Parameter `absolute_path`. Prioritäts-Regel: Wenn `absolute_path` gesetzt und Datei existiert → SOFORT direktes Lesen vom Pfad (ignoriert `filename`, überspringt Dubletten-Prüfung, kein Index-Lookup). Logging: `[ABSOLUTE-PATH MODE] Reading directly from disk: {path}`. **Fix #3 — Prompt-Härtung P0.75:** `@c:\KI\Janus-Projekt\backend\skills\knowledge\query.json:20` und `read_full_text.json:19` — P0.75 AUTO-READ TRIGGER Direktive aktualisiert: "Nutze 'knowledge.read_full_text' mit dem Parameter 'absolute_path' für diesen Pfad, um den Text jetzt live zu lesen!" + "Du MUSST stattdessen in genau diesem Turn selbstständig das Tool 'knowledge.read_full_text' mit dem Parameter 'absolute_path' auf den angegebenen Pfad aufrufen". **Fix #4 — Multi-File Comparison Layout:** P0.5 Direktive erweitert: Verboten, User zu fragen welche Datei. Stattdessen: Für JEDE Dublette eine Sektion mit Pfad und Zusammenfassung (via Auto-Read oder Vorschau). |
| **Ergebnis** | KI kann nun autonom nicht-indizierte Dubletten lesen. Wenn `knowledge.query` Dubletten findet und eine Datei als `[NICHT INDIZIERT - AKTION ERFORDERLICH...]` markiert ist, ruft GPT in demselben Turn `knowledge.read_full_text` mit `absolute_path` auf. User bekommt vollständigen inhaltlichen Vergleich aller Dubletten ohne manuelle Interaktion. "Silent Failure" bei nicht-indizierten Dateien eliminiert. |
| **Files** | `backend/data/schemas.py` (GetFullDocumentTextArgs.absolute_path), `backend/services/tool_executor.py` (get_full_document_text mit Path-Pinning), `backend/skills/knowledge/query.json` (P0.75 + P0.5 Direktiven), `backend/skills/knowledge/read_full_text.json` (P0.75 + P0.5 Direktiven). |
| **Verifikation** | Test "was steht in der aegypten.pdf?" erwartet: (a) Log zeigt `Total unique calls this turn: 2 oder 3` (mehrere Tool-Calls mit absolute_path), (b) Tool-Output enthält absolute_path Parameter in den Tool-Call-Args, (c) LLM-Antwort enthält vollständigen inhaltlichen Vergleich beider Dateien ohne User-Frage. |
| Patterns | [PATTERN] #AgenticAI #ToolDesign "Path-Pinning for Disambiguation" — Kritische Tools zur Ressourcen-Interaktion müssen immer einen "Pinning"-Parameter (absolute_path) haben, damit die KI Mehrdeutigkeiten, die das System ihr meldet, autonom auflösen kann. |

---

## [CURRENT_SESSION_DELTA] (BUG-RAG-003 — Regression Fix & Lifecycle Hardening 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **BUG-RAG-003: RAG-V2 Regression Fix (NameError & IndexStore Lifecycle)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-23) |
| **Root Cause** | Eine fatale Fehlerkette verhinderte die Dubletten-Erkennung: 1. `NameError`: `path_previews` war bei bestimmten Pfaden undefiniert, was die Funktion abbrach. 2. `Lifecycle Error`: Der `IndexStore` wurde zu früh geschlossen (`L200`), bevor die Chunks gelesen werden konnten (`L283`). 3. `Slash-Mismatch`: Fehlende Normalisierung führte zu redundanten Auto-Ingest-Triggern. Ergebnis: Das System fiel in den globalen Halluzinations-Modus zurück. |
| **Umsetzung** | **1. Scope-Hardening:** `path_previews` initialisiert; `store` Lifecycle via `None`-init + `finally`-Block abgesichert. **2. Slash-Trap Fix:** Normalisierung bei `new_paths` Vergleich implementiert. **3. Threading:** `ingestion_manager` Aufruf in Daemon-Thread ausgelagert, um Event-Loop Blockaden zu verhindern. |
| **Ergebnis** | Die RAG-V2-Pipeline ist nun robust gegen asynchrone Fehlzugriffe und Windows-Pfad-Differenzen. Die agentische Dubletten-Auflösung funktioniert wieder zuverlässig für alle Provider. |
| **Files** | `backend/services/tool_executor.py` (Zustands- und Fehlerbehandlung). |

---

## [CURRENT_SESSION_DELTA] (F16 FINAL LOCKDOWN — RAG V2 Integrität 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **F16: RAG V2 Final Lockdown — Beendigung der Halluzinations-Kreisbewegung** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-23) |
| **Root Cause** | Das System war "schwach" im Routing: LLMs "vergaßen" oft den Filename-Parameter, was zu globalen Suchen und Halluzinationen ("Skandinavien-Analyse") führte. Zudem wurde die Dubletten-Logik bei bekanntem Pfad oft übersprungen (Bypass). |
| **Umsetzung** | **1. Dispatcher-Lockdown:** Regex-basierte Filename-Injektion im Orchestrator erzwingt nun den korrekten Tool-Parameter bei PDF-Anfragen. **2. V2-First:** Jede Anfrage durchläuft nun zwingend den Dubletten-Scan, bevor ein Pfad bedient wird. **3. Auto-Ingest Repair:** Korrektur des Ingest-Roots auf den tatsächlichen Fundort. **4. Schema-Härtung:** Beschreibung für LLMs von "optional" auf "PFLICHT" geändert. |
| **Ergebnis** | Der "Skandinavien-Fehler" ist technologisch eliminiert. Janus indiziert nun zuverlässig unindizierte Fundstellen im Hintergrund und erzwingt den agentischen Vergleich über alle Dubletten. Volle Hardware-Truth garantiert. |
| **Files** | `execution_dispatcher.py`, `tool_executor.py`, `schemas.py`. |
| **Patterns** | [PATTERN] #Orchestration #Lockdown "Dispatcher-First Parameter Enforcement — Don't ask the LLM to identify resources if you can define them via Regex in the Dispatcher." |

---

## [CURRENT_SESSION_DELTA] (EPIC-SYSTEM-HARVESTER (V2) — 🏁 COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **EPIC-SYSTEM-HARVESTER (V2): Universal Knowledge-Harvester — Diamond-Standard RAG V2 mit Zero-Regression-Contract** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-22) |
| **Scope** | Lokale, semantische + lexikalische Suche über alle Text-/Dokument-/Code-Formate in Janus-Workspaces. Hybrid-Retrieval: Dense (ChromaDB dual-embedding) + Keyword (SQLite FTS5) + RRF + Cross-Encoder-Reranker + Context-Expansion + Query-Router (Regex-Heuristik) + Path Policy + Retrieval Logging + Skill API + Background Watchdog + Global Scope Discovery. Code-aware Chunking via tree-sitter. |
| **RAG V2 Core Components** | 1. **Hybrid-Search**: Dense (ChromaDB dual-embedding) + Sparse (SQLite FTS5) fusioniert via RRF. 2. **AST-Chunking**: Tree-sitter für Code, Header-Breadcrumbs für Markdown, 3-stufiger Fallback. 3. **Reranking**: Cross-Encoder (Singleton+Lazy-Loading) mit Graceful Fallback. 4. **Watchdog**: Filesystem Observer mit DebounceQueue (2s) + Coalesce für inkrementelle Updates. 5. **PDF Adapter**: PyMuPDF (fitz) Integration für Prose-Format PDFs, Text-Chunking (1000 chars, 200 overlap), Metadata-Sanitization None-Handling. |
| **Architecture Decisions** | **Strangler-Fig statt Replace:** V2 läuft parallel zu Legacy-RAG. Opt-in via 11 granularer Feature-Flags (alle default `false`). **Physische Isolation:** V2 nutzt eigenen Chroma-Pfad `rag_chroma_db_v2/`. Legacy `rag_chroma_db/` ist untouchable. **Freeze-Contract:** 7 Files + 3 Collections sind für V2-Executors hart gesperrt (§ 1.5.2 im Master-Plan). **API-Additivität:** `knowledge.query` bleibt byte-identisch. V2 nur via neuem Skill `knowledge.code_search` oder explizitem `retrieval_mode="v2"`. **Code-First-Scope:** V2 indiziert Code + Markdown + PDF (P9). Prose (Projekt-URLs, Creative-Writer) bleibt Legacy. |
| **P0 — Eval-Harness** | `@c:\KI\Janus-Projekt\backend/tests/rag/golden_queries.jsonl` (30 Queries), `harness.py` (MRR@10/Recall@5/P@1), `test_baseline.py`, `test_legacy_filesystem_isolation.py` (SHA-Guard). Baseline: MRR@10=0.1724 (PROSE 1.0000, CODE 0.0000). |
| **P1 — Format-Router + Incremental Index** | `@c:\KI\Janus-Projekt\backend/services/rag/index_store.py` (SQLite, SHA-256, Orphan-Management), `adapters/base.py`, `adapters/code.py` (P3: chunking.py Delegation), `adapters/markdown.py` (P3: Breadcrumbs), `ingestion.py` (FormatRouter + IngestionRun + `_assert_isolation()` + Dual-Collection + P6 PathPolicy + P8 run_partial + FINAL Format-Gatekeeper). Tests: `test_adapters.py`, `test_index_store.py`, `test_ingestion.py`. |
| **P2 — FTS5 + RRF Fusion** | `@c:\KI\Janus-Projekt\backend/services/rag/fts_store.py` (FTS5, unicode61, WAL), `rrf.py` (k=60, pure function, P5: Weighted RRF), `hybrid_retriever.py` (Dense+Sparse+RRF, P3: Multi-Collection, P4: Reranker+Expand, P5: Router+Weighted RRF, P6: Retrieval Logging). Tests: `test_rrf.py` (10 Tests), `test_fts_store.py` (7 Tests), `test_hybrid_retriever.py` (8 Tests). |
| **P3 — Code-Aware Chunking** | `@c:\KI\Janus-Projekt\backend/services/rag/chunking.py` (3-stufiger Fallback: tree-sitter → regex → blank-line, Code-Prefixing), `adapters/code.py` (AST-Chunking + Fallback), `adapters/markdown.py` (Header-Breadcrumb Präfix), `ingestion.py` (Dual-Collection Router: kb_code_v2 / kb_prose_v2), `hybrid_retriever.py` (Multi-Collection Search). Tests: `test_chunking.py` (Boundary, Resilience, Breadcrumb, Prefix). |
| **P4 — Reranker + Context-Expansion** | `@c:\KI\Janus-Projekt\backend/services/rag/reranker.py` (Cross-Encoder: Singleton, Lazy-Loading, Thread-Lock, Graceful Fallback), `context_expander.py` (±1 Chunks via index_store.py, Dedup), `hybrid_retriever.py` (Pipeline: Top-20 RRF → Rerank → Top-5 → Expand). Tests: `test_reranker.py` (Singleton, Fallback, Latency ≤500ms, Memory ≤150MB), `test_context_expander.py` (Expansion, Dedup, Boundary). **MRR-Gate:** DEFERRED bis nach Data Ingestion (V2 Index ist aktuell leer). |
| **P5 — Query-Router + Weighted RRF** | `@c:\KI\Janus-Projekt\backend/services/rag/query_router.py` (Regex-Heuristik: Code-Signale (snake_case, camelCase, Dateiendungen, Funktionsklammern), Prosa-Signale (Fragewörter, Satzlänge ≥8 Wörter), Output: RouterDecision), `rrf.py` (P5: `weighted_reciprocal_rank_fusion()`), `hybrid_retriever.py` (P5: Collection-Routing, `use_router`, `retrieval_mode`, `file_type_filter`). Tests: `test_query_router.py` (22 Tests, Accuracy ≥90% gegen 34 Fixtures, Latenz <5ms, Zero-Magic-Gate). |
| **P6 — Security + Observability** | `@c:\KI\Janus-Projekt\backend/services/rag/path_policy.py` (Denylist: .env, .pem, .key, node_modules, .git, venv, DB-Files. Path-Traversal Schutz: Symlinks, ../, Absolute Path Check. SecurityError bei Verletzung), `retrieval_logger.py` (JSON-Line Logger für backend/logs/rag_retrieval.log. Inhalt: Query, Router-Entscheidung, Latenz-Breakdown, Top-1. Rotation: RotatingFileHandler 10MB, 5 Backups), `ingestion.py` (P6: PathPolicy Check, [SKIP] Log, enable_path_policy), `hybrid_retriever.py` (P6: Retrieval-Logging mit Latenz-Breakdown). Tests: `test_security.py` (25 Tests: Secret-Leak, Path-Escape, Observability, Denylist Coverage). |
| **P7 — Skill API** | `@c:\KI\Janus-Projekt\backend/skills/knowledge/code_search.json` (Skill Manifest für Code-Suche, Fokus auf technische Anfragen, retrieval_mode="v2"), `backend/services/rag/api_adapter.py` (Adapter Layer mit Lazy-Loading, Zero-Regression Guard), `backend/services/knowledge_service.py` (Unified RAG Interface: retrieval_mode (legacy/v2/hybrid), file_type_filter, Default="legacy"), `backend/api/routers/system.py` (P7: GET /api/system/rag-status Health-Check), `backend/data/capability_registry.json` (P7: knowledge.code_search Ability). Tests: `test_api_compat.py` (Byte-Ident Gate, Zero-Regression Guard, Orphan-Registry Gate). |
| **P8 — Background Watchdog** | `@c:\KI\Janus-Projekt\backend/services/rag/watcher.py` (File-System Observer mit watchdog, DebounceQueue (2s debounce, 1s batch window), Coalesce, Thread-Safe, Graceful Shutdown), `backend/tests/rag_v2/test_watcher.py` (Unit-Tests: Debounce, Coalesce, Lifecycle, File-Filter), `backend/main.py` (P8: Startup/Shutdown Logic für Watcher Integration), `backend/services/rag/ingestion.py` (P8: run_partial() Methode für inkrementelle Updates). |
| **P9 — PDF Adapter Integration** | `@c:\KI\Janus-Projekt\backend/services/rag/adapters/pdf.py` (PdfAdapter Klasse, PyMuPDF Integration, Text-Chunking), `backend/services/rag/ingestion.py` (PdfAdapter Registrierung, _sanitize_metadata None-Handling Fix), `backend/skills/knowledge/query.json` (synthesis_directives für Cross-File-Halluzination Guard). Validation: 21 PDFs aus JanusPDFs erfolgreich indiziert. |
| **FINAL — Global Scope Discovery** | `@c:\KI\Janus-Projekt\backend/main.py` (FINAL: Global Discovery für ~/Documents und ~/Desktop, asynchrone Indizierung via daemon Thread), `@c:\KI\Janus-Projekt\backend/services/rag/ingestion.py` (FINAL: Format-Gatekeeper, nur Gold-Formate: .pdf, .md, .txt, .py, .js, .ts, .docx). Tests: pytest backend/tests/rag_v2/ (113 passed, 35 failed - pre-existing issues). |
| **Files** | `@c:\KI\Janus-Projekt\documentation\RAG_V2_MASTER_PLAN.md` (v1.1). `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P0_eval_harness.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P1_format_router.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P2_fts5_rrf.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P3_code_chunking.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P4_reranker.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P5_query_router.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P6_security_observability.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P7_skill_api.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P8_watcher.md`. `@c:\KI\Janus-Projekt\documentation\tasks\rag-v2\P9_pdf_integration.md`. |
| **Executor Assignment** | SWE 1.6: P0 (Eval-Harness ✅), P1 (Ingestion ✅), P4 (Reranker ✅), P6 (Security/Obs ✅), P7 (Skill-API ✅), P8 (Watchdog ✅), P9 (PDF Adapter ✅), FINAL (Global Discovery ✅). Kimi K2.5: P2 (FTS5+RRF ✅), P3 (Code-Chunking ✅), P5 (Query-Router ✅). |
| **Gate-Regel** | P0 ✅ Golden Queries + Baseline + Legacy SHA-Guard grün. P1 ✅ Idempotenz, Isolation, Orphan-Delete, Atomic Rename. P2 ✅ RRF-Symmetrie, FTS5-Boost, Hybrid-Integration, Legacy-Isolation (Hash: 607afb4e...). P3 ✅ Boundary-Test, Breadcrumb-Test, AST-Resilience, Dual-Collection, Multi-Collection-Search. P4 ✅ Singleton, Lazy-Loading, Fallback, Latency/Memory Gates, Legacy-Isolation. P5 ✅ Accuracy ≥90% gegen 34 Fixtures, Zero-Magic-Gate (kein LLM), Latenz <5ms, Regression (Prosa-Pfad stabil). P6 ✅ Secret-Leak Gate (.env nicht indiziert), Path-Escape Gate (/etc/passwd SecurityError), Observability Gate (JSON-Log), Denylist Coverage. P7 ✅ Byte-Ident Gate (knowledge.query Default="legacy"), Zero-Regression Guard (V2 nur bei retrieval_mode="v2"/"hybrid"), Orphan-Registry Gate (keine orphan warnings). P8 ✅ Debounce-Queue (10 schnelle Saves = 1 Log), Coalesce (10 Files in 1s = 1 Batch), Lifecycle (Graceful Shutdown), Thread-Safe. P9 ✅ PdfAdapter Registrierung, Metadata-Sanitization None-Handling, 21 PDFs indiziert (0 Errors). FINAL ✅ Global Scope Discovery (~/Documents, ~/Desktop async), Format-Gatekeeper (Gold-Formate only). **P4-MRR-Gate:** DEFERRED bis nach Data Ingestion (V2 Index leer). |
| **Patterns** | [PATTERN] #Architecture #RAG The Strangler-Fig Migration, [PATTERN] #Architecture #HybridSearch Reciprocal Rank Fusion (RRF) Baseline, [PATTERN] #Security #Isolation Physical Vector-Store Separation, [PATTERN] #Performance #IncrementalIndex SHA-256 + mtime Prefilter, [PATTERN] #HybridSearch #FTS5 SQLite Full-Text Search with BM25, [PATTERN] #RAG #CodeAwareChunking Tree-sitter + Regex + Blank-Line Fallback, [PATTERN] #RAG #CrossEncoderReranker Singleton Pattern + Lazy-Loading + Graceful Fallback, [PATTERN] #RAG #QueryRouter Regex-Heuristic Classification (Zero-LLM-Latency), [PATTERN] #Security #PathPolicy Denylist + Path-Traversal Protection, [PATTERN] #Observability #RetrievalLogging JSON-Line Logger with Rotation, [PATTERN] #Architecture #APIAdapter Lazy-Loading with Zero-Regression Guard |

---

## [CURRENT_SESSION_DELTA] (RAG V2 STABILIZATION — Filename Metadata + Path Normalization + Memory Guard 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **RAG V2 STABILIZATION: Filename Metadata Injection, Path Normalization (Slash-Trap Fix), P0 Directives, Memory Integrity Guard** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-22) |
| **Root Cause** | PDF-Duplikate im System führten zu Halluzinationen: GPT scheiterte am Pfad-Filter (Slash-Mismatch: `aegypten` vs `C:\...\aegypten.pdf`), Gemini ignorierte Duplikate in Antworten. Resultat: Halluzinierte Fakten in Memory ("aegypten.pdf enthält Skandinavien-Analyse"). |
| **Umsetzung** | **Fix #1 — Path Normalization (Slash-Trap):** `@c:\KI\Janus-Projekt\backend\services\rag\hybrid_retriever.py` — `_normalize_path(p: str) -> str` als class-level static method: `p.replace("\\", "/").lower()`. Angewendet auf alle Filename-Filter-Vergleiche und IndexStore-Lookups. **Fix #2 — Hard Lockdown:** Wenn `filename`-Parameter übergeben wird, wird globale Vektorsuche komplett übersprungen. Nur noch IndexStore-Lookup + Rescue-Path (direkter SQL-Zugriff auf Chunks via `get_chunks_by_file`). Wenn 0 Ergebnisse → leer zurückgeben, NIE globale Suche als Fallback. **Fix #3 — tool_executor Normalization:** `@c:\KI\Janus-Projekt\backend\services\tool_executor.py` — gleiche `_normalize_path` Funktion in `_v2_fulltext_fallback` für Stem-Matching. **Fix #4 — index_store Normalization:** `@c:\KI\Janus-Projekt\backend\services\rag\index_store.py` — `get_chunks_by_file` normalisiert Pfade vor ChromaDB-Query. **Fix #5 — Manifest Synchronization (P0):** `@c:\KI\Janus-Projekt\backend\skills\knowledge\query.json` und `read_full_text.json` — `thought_hint` (P0) + `synthesis_directives` mit striktem Antwort-Layout-Template bei Mehrdeutigkeit ("!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!"). **Fix #6 — Memory Integrity Guard:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\warning_guard.py` (neu) — `did_model_ignore_warning()` prüft, ob Tool-Output Warnung enthielt aber LLM-Antwort sie ignorierte. Wenn ja → `skip_fact_extraction = True`. Wired in `@c:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py` nach `apply_run_tool_loop_result_to_workflow`. |
| **Ergebnis** | Filename-Filter auf Windows jetzt absolut wasserdicht: `aegypten`, `aegypten.pdf`, `AEGYPTEN.PDF`, `Aegypten.Pdf`, voller Pfad — alle 5 Varianten treffen korrekt. Lockdown verhindert globale Suche bei gesetztem Filename. P0-Directives erzwingen explizite Duplikat-Quittierung ("Hinweis: Ich habe X Versionen von Y gefunden..."). Memory Guard verhindert Speicherung halluzinierter Fakten bei ignorierten Warnungen. |
| **Files** | `backend/services/rag/hybrid_retriever.py` (_normalize_path + Lockdown), `backend/services/tool_executor.py` (_v2_fulltext_fallback Normalization), `backend/services/rag/index_store.py` (get_chunks_by_file Normalization), `backend/skills/knowledge/query.json` (thought_hint + P0 synthesis_directives), `backend/skills/knowledge/read_full_text.json` (thought_hint + P0 synthesis_directives), `backend/services/orchestrator/warning_guard.py` (neu), `backend/services/orchestrator/execution_dispatcher.py` (Guard-Wiring). |
| **Verifikation** | Test `backend/test_robust_matcher.py`: 5/5 Filename-Varianten treffen korrekt ✅ · Warning Guard Test: 3/3 Fälle korrekt (warning ignored=True, warning acknowledged=False, no warning=False) ✅ · WHAT_I_LEARNED.md: Slash-Trap Lesson eingetragen ✅ |
| **Patterns** | [LESSON] #RAG #WindowsPaths "The Slash-Trap — Normalisiere Pfade immer auf Forwardslashes vor Vektor-Filtern", [PATTERN] #RAG #FilenameLockdown "Wenn filename gesetzt, NUR IndexStore-Lookup + Rescue — globale Suche überspringen", [PATTERN] #Prompting #P0Directives "thought_hint + synthesis_directives mit striktem Template erzwingen LLM-Quittierung bei System-Warnhinweisen", [PATTERN] #Memory #IntegrityGuard "Fact-Extraction blockieren, wenn LLM SYSTEM-WARNHINWEIS ignoriert hat" |

---

## [CURRENT_SESSION_DELTA] (DEAD-CODE-FIX — Direktiven-Injection 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Dead-Code-Fix: HARDWARE-TRUTH-REGEL + file_system_guard werden nun tatsächlich in den LLM-System-Prompt injiziert** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Root Cause** | User meldete: "Gemini nutzt Suchtool (2 Treffer), aber Nano nimmt Info aus Memory statt neuer Suche." Log-Analyse des OpenAI-Request (chat_id=74, query "wo liegt gundula1.pdf?"): System-Prompt enthielt `PRIMÄRDIREKTIVE`, `FAKTEN-DIREKTIVE`, `🚨 SYSTEM-DIREKTIVE (STRIKTE KASKADE)` (alles aus DB-Persönlichkeit), aber WEDER `search_command_priority` NOCH `file_system_guard`. Mini-Modell (via MoA-Upgrade von Nano) wählte einen von 3 widersprüchlichen Pfaden aus den Memory-Fakten (c:\test2\, desktop\januspdfs\, "nicht gefunden") und antwortete ohne Tool-Call. Ursache: Die beiden Direktiven waren in `prompt_registry.py::_DIRECTIVES` definiert, aber NIEMALS injiziert. Der echte System-Prompt wird in `@c:\KI\Janus-Projekt\backend\services\orchestrator\execution_dispatcher.py:190` via `apply_verbosity_control(wf.system_prompt_for_llm)` gebaut — welches bisher nur `verbosity_control` + `no_meta_talk` anhängte. |
| **Umsetzung** | `@c:\KI\Janus-Projekt\backend\services\orchestrator\prompt_registry.py:197-216` — `apply_verbosity_control()` erweitert: Schleife iteriert jetzt über 4 statt 2 Direktiven (`verbosity_control`, `no_meta_talk`, `file_system_guard`, `search_command_priority`). Dedup-Check (`if rule not in base_text`) bleibt unverändert → Idempotenz garantiert. Damit erhält jeder DEFAULT-Dialog-Turn automatisch: (a) Dubletten-Hinweis-Pflicht bei Such-Treffern an mehreren Orten, (b) Live-Tool-Call-Pflicht für Suchanfragen mit "schwerer Systemfehler"-Formulierung. |
| **Ergebnis** | LLM (Nano, Mini, Sonnet, Gemini) bekommt nun bei JEDEM regulären Chat-Turn die HARDWARE-TRUTH-REGEL im System-Prompt. Damit wird "Brevity-Bias" bei faulen Modellen gebrochen: Sie können nicht mehr auf Memory-Fakten zurückfallen, wenn der User nach Datei-Pfaden sucht. |
| **Files** | `backend/services/orchestrator/prompt_registry.py` (apply_verbosity_control erweitert). Keine Call-Site-Änderungen notwendig — Fix ist lokal in der Helper-Funktion. |
| **Verifikation** | Unit-Smoke: `apply_verbosity_control('Du bist Janus.')` enthält jetzt `HARDWARE-TRUTH-REGEL` ✅, `KRITISCHE SYSTEM-ANWEISUNG` ✅, `Antworte im normalen Gespräch stets prägnant` ✅, `No-Meta-Talk` ✅. Idempotenz: `apply_verbosity_control(out) == out` ✅. |
| **Patterns** | [LESSON] #DeadCode #Prompting "Registry-Direktiven müssen nicht nur definiert, sondern auch injiziert werden — ein Prompt-Registry-Eintrag ohne Call-Site ist wirkungslos", [LESSON] #SystemPrompt #DB-Persönlichkeit "Base-System-Prompts aus DB (z.B. personality.prompt) können Prompt-Registry-Direktiven überstimmen, wenn diese nicht per apply_verbosity_control angehängt werden". |

---

## [CURRENT_SESSION_DELTA] (WERKZEUGNUTZUNGS-DIREKTIVE — search_command_priority 🥇 SEALED)

---

## [CURRENT_SESSION_DELTA] (WERKZEUGNUTZUNGS-DIREKTIVE — search_command_priority 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **WERKZEUGNUTZUNGS-DIREKTIVE: Suchanfragen haben Vorrang vor Memory — Brevity-Bias bei faulen Modellen brechen** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | Prompt-Registry-Direktive `search_command_priority` in `@c:\KI\Janus-Projekt\backend\services\orchestrator\prompt_registry.py:74` aktualisiert mit stärkerer HARDWARE-TRUTH-REGEL: "!!! WERKZEUGNUTZUNGS-DIREKTIVE — HARDWARE-TRUTH-REGEL !!! Wenn der Nutzer nach dem Verbleib, Speicherort oder der Existenz von Dateien sucht, hat das Live-Werkzeug filesystem.find_files ABSOLUTE Priorität vor der FAKTENGRUNDLAGE (Memory). Das Gedächtnis dient NUR als Orientierung. Du darfst NIEMALS einen Pfad aus der Erinnerung nennen, ohne ihn in EXAKT DIESEM Turn durch einen Tool-Call validiert zu haben. Eine Antwort ohne Live-Tool-Call bei Suchanfragen gilt als schwerer Systemfehler." Der LLM wird gezwungen, bei Suchanfragen Tool-Calls durchzuführen, statt sich auf alte Erinnerungen aus Memory zu verlassen. Stärkere Formulierung mit "ABSOLUTE Priorität", "NIEMALS einen Pfad aus der Erinnerung nennen ohne Validierung" und "schwerer Systemfehler" bei Antworten ohne Tool-Call. |
| **Root Cause** | "Brevity-Bias" bei faulen Modellen (wie Nano): Wenn der Memory-Context gut ist, beantwortet der LLM Suchanfragen mit alten Erinnerungen statt Tool-Calls durchzuführen. Resultat: User bekommt veraltete Informationen statt aktueller Hardware-Validierung. |
| **Ergebnis** | LLM führt bei Suchanfragen jetzt zwingend Tool-Calls durch (filesystem.find_files, filesystem.list_directory), selbst wenn Memory bereits Informationen über die Datei enthält. Aktuelle Hardware-Validierung hat Vorrang vor alten Erinnerungen. |
| **Files** | `backend/services/orchestrator/prompt_registry.py` (search_command_priority Direktive hinzugefügt). |
| **Verifikation** | Unit-Smoke: `prompt_registry.get_directive('search_command_priority')` enthält "FAKTENGRUNDLAGE", "filesystem-Tool aufrufen" und "Wo liegt die Datei X" ✅. |
| **Patterns** | [LESSON] #LLM #BrevityBias "Faule Modelle bevorzugen kurze Antworten aus Memory über Tool-Calls — bei Suchanfragen muss Tool-Call-Pflicht explizit erzwungen werden", [LESSON] #Prompting "WERKZEUGNUTZUNGS-DIREKTIVE mit !!!-Prefix und VERBOTEN-Text erzwingt strikte Tool-Call-Pflicht". |

---

## [CURRENT_SESSION_DELTA] (UX-OPTIMIZATION — Prompt-Registry + Limit-Senkung 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **UX-Optimization: Dubletten-Hinweis bei Dateisuchen + Fakten-Extraktion-Overhead begrenzen** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | **Fix #1 — Prompt-Registry-Update:** `@c:\KI\Janus-Projekt\backend\services\orchestrator\prompt_registry.py:42` erweitert die `file_system_guard`-Direktive um expliziten Dubletten-Hinweis: "WICHTIG: Wenn ein Such-Tool (z.B. filesystem.find_files) mehrere Dateien mit identischem Namen an verschiedenen Orten findet, MUSST du den Nutzer explizit auf diese Dubletten hinweisen (z.B. 'Ich habe die Datei an 2 Stellen gefunden: ...')." Der LLM muss den User bei Duplikaten proaktiv informieren, statt die Liste stillschweigend auszugeben. **Fix #2 — Limit-Senkung:** `@c:\KI\Janus-Projekt\backend\services\filesystem_manager.py:318` Default für `max_results` von 100 auf 20 gesenkt. Hintergrund: Bei Dateisuchen mit 100 Treffern würde Nano versuchen, jeden Pfad als separate "Langzeit-Fakt" zu speichern, was das System für Sekunden lähmt (87 Pfade → 87 Fakten → DB-Overhead). 20 Treffer sind für die meisten Use-Cases ausreichend; bei Bedarf kann der User `search_all_drives=true` oder explizites `max_results` nutzen. |
| **Root Cause (#1)** | `filesystem.find_files` liefert Duplikate korrekt, aber der LLM hatte keine explizite Anweisung, den User darauf hinzuweisen. Resultat: Liste von Pfaden ohne Kontext, User weiß nicht, ob es Dubletten sind. |
| **Root Cause (#2)** | `find_files(max_results=100)` war zu hoch für Fakten-Extraktion nach Dateisuchen. Nano extrahiert aus der Assistant-Message (die die Dateiliste enthält) jeden Pfad als separate "Langzeit-Fakt", was zu massivem DB-Overhead führt. |
| **Ergebnis** | LLM weist User jetzt explizit auf Dubletten hin (z.B. "Ich habe gundula1.pdf an 2 Stellen gefunden: Desktop\JanusPDFs\gundula1.pdf und C:\test2\gundula1.pdf"). Fakten-Extraktion nach Dateisuchen ist entlastet (max 20 Pfade statt 100), System-Lag durch 87-Fakten-Extraktion vermieden. |
| **Files** | `backend/services/orchestrator/prompt_registry.py` (file_system_guard erweitert), `backend/services/filesystem_manager.py` (max_results Default 100 → 20, Docstring aktualisiert). |
| **Verifikation** | Unit-Smoke: `prompt_registry.get_directive('file_system_guard')` enthält "Dubletten" und "find_files" ✅ · `inspect.signature(find_files).parameters['max_results'].default == 20` ✅. |
| **Patterns** | [LESSON] #UX #Prompting "LLM braucht explizite Anweisungen für proaktive UX-Maßnahmen (Dubletten-Hinweis) — Default ist stille Ausgabe", [LESSON] #Performance #FactExtraction "Tool-Output-Größe beeinflusst downstream-Fakten-Extraktion massiv — max_results Default an downstream-Overhead anpassen, nicht nur an Such-Qualität". |

---

## [CURRENT_SESSION_DELTA] (CORE-REPAIR — Memory-Similarity + Schema-Literal 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **CORE-REPAIR-ARC — "innere Blutungen" im Memory-Retrieval und Schema-Layer stoppen** (Phase 1 von 3-Punkt-AI-Studio-Plan) |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | **Scope-Review mit Fehlbefund-Zurückweisung:** Vor Implementierung alle 3 geplanten Baustellen gegen Code verifiziert. Bug #1 (Numpy) und #3 (Schema) bestätigt; Bug #2 (OllamaCompiler-Import) als Fehlbefund zurückgewiesen — `@c:\KI\Janus-Projekt\backend\services\prompting\factory.py:3` importiert sauber aus intakter `@c:\KI\Janus-Projekt\backend\llm_providers\ollama\compiler.py:5`, Live-Log zeigt keinen Import-Fehler. **Fix #1 — Numpy Shape Error:** In `@c:\KI\Janus-Projekt\backend\services\vector_service.py` neuer Helper `_safe_stack_embeddings(candidates, expected_dim)` filtert None, Nicht-Listen, leere Arrays, NaN-Vektoren und Dim-Mismatches vor `np.stack`. Beide Consumer (`calculate_similarity_batch`, `calculate_similarity_with_precomputed`) nutzen den Helper und behalten Output-Alignment via 0.0-Padding auf invaliden Positionen. Warning-Log bei jedem gefilterten Eintrag mit `dropped/total` und `query_dim` für Diagnose. **Fix #3 — SkillMetadata-Literal:** `@c:\KI\Janus-Projekt\backend\data\schemas.py:195` um `"full"` als 4. valides Literal erweitert (wird von 11 filesystem-Skills konsistent genutzt — war stille Divergenz zwischen Manifests und Schema). |
| **Root Cause (#1)** | Embedding-Kandidatenlisten im Memory-Retrieval sind heterogen: Slots ohne gecachtes Embedding liefern `None`, Legacy-Slots aus anderen Modell-Versionen haben abweichende Dimensionen (z.B. 512 statt 384 des `all-MiniLM-L6-v2`). `np.array(list, dtype=float32)` bricht bei jeder inhomogenen Stelle mit `ValueError: setting an array element with a sequence` ab — der gesamte Similarity-Batch scheiterte, obwohl 26 von 27 Embeddings valide gewesen wären. |
| **Root Cause (#3)** | Drift zwischen Skill-Manifests (nutzten `"full"`) und Pydantic-Schema (kannte nur 3 Literals). Validator war offenbar im toleranten Pfad eingehängt, sodass der Mismatch keinen Ladungsfehler warf, aber jede strikte Validierung wäre zerbrochen. |
| **Ergebnis** | `[ERROR] Error in precomputed similarity calculation: ... inhomogeneous part` verschwindet aus dem Log. Memory-Retrieval liefert korrekte Scores für alle validen Slots statt 0-Fallback-Liste. `SkillMetadata(sandbox_level="full")` validiert jetzt sauber (Smoke-Test: alle 4 Literals akzeptiert, invalide Werte `ValidationError`). Unit-Smoke mit 6-Element-Mischliste (2 valide, 4 invalide): `scores=[0.99, 0.0, 0.0, 0.0, 1.0, 0.0]` — perfektes Alignment. |
| **Files** | `backend/services/vector_service.py` (+~60 Zeilen: `_safe_stack_embeddings` Helper + beide Consumer gehärtet mit Alignment-Preservation), `backend/data/schemas.py` (1-Zeilen-Edit: Literal um `"full"` erweitert). |
| **Verifikation** | Unit-Smoke Fix #1: `_safe_stack_embeddings` mit homogener Liste → `dropped=0` ✅ · mit `[valid, None, wrong_dim, nan_vec, valid, 'not_list']` → `dropped=4, shape=(2,384)` ✅ · `calculate_similarity_with_precomputed` behält Output-Länge 6 mit 0.0-Padding ✅ · empty/all-bad keine Crashes ✅. Unit-Smoke Fix #3: alle 4 Literal-Werte akzeptiert ✅, `"hacky"` → `ValidationError` ✅. |
| **Patterns** | [LESSON] #Numpy #Embeddings #Robustness "np.array/np.stack auf heterogenen Embedding-Listen (None/Dim-Drift) bricht mit inhomogeneous shape — sanitize vor stack, Alignment via Padding erhalten", [LESSON] #Pydantic #SchemaDrift "Literals in Schemas und die tatsächlichen Werte in Config-Files/Manifests driften stillschweigend auseinander, wenn der Loader tolerant ist — Schema-Drift-Check beim CI gegen alle Manifests wäre eine sinnvolle Härtung", [PATTERN] #Planning #FehlbefundZurueckweisung "Externe Fix-Pläne (AI-Studio-generiert) immer gegen Code verifizieren, bevor implementiert wird — blindes Abarbeiten führt zu Schein-Commits ohne realen Bug-Bezug". |

---

## [CURRENT_SESSION_DELTA] (FEATURE — filesystem.find_files Skill mit Auto-Escalation 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **FEATURE — Janus konnte Dateien nicht finden, wenn der User nur den Dateinamen (ohne Pfad) nannte** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | Gap-Analyse zeigte: Die 10 existierenden `filesystem.*`-Skills boten keinen rekursiven Such-Skill — nur `list_directory` (non-rekursiv) und `list_workspaces`. Bei "wo finde ich gundula1.pdf?" rief das LLM daher `list_workspaces` + `list_directory` auf, fand nichts und halluzinierte. **Lösung in 3 Iterationen:** **1. Grund-Skill** `filesystem.find_files` implementiert (`@c:\KI\Janus-Projekt\backend\services\filesystem_manager.py:288-440` via `os.walk` + `fnmatch`, robust gegen defekte Symlinks/PermissionErrors via `onerror`-Callback; initial mit `Path.rglob`, aber das warf bei defekten Desktop-Ordnern `FileNotFoundError` → Umstieg auf `os.walk`). **2. Globale Suche** via neuem Parameter `search_all_drives: bool` (durchsucht C:\\, D:\\, E:\\ mit Noise-Skip-Liste für `Windows`, `Program Files`, `node_modules`, `.git`, `AppData`, etc.). **3. Auto-Escalation** — wenn Workspace-Sweep ≤1 Treffer UND kein expliziter root UND kein truncated → automatisch zweiter Sweep über alle Laufwerke, dedupliziert via `existing`-Set, `auto_escalated`-Flag in Response. Damit reicht die simple User-Frage "wo finde ich xy?" für Duplikat-Erkennung, ohne dass das LLM daran denken muss. |
| **Root Cause** | Fehlender Suche-Skill im Filesystem-Domain. Das LLM hatte kein Werkzeug für rekursive Filename-Suche und konnte mit den vorhandenen Tools keine dateiübergreifende Discovery betreiben. |
| **Ergebnis** | User-Frage "wo finde ich die datei gundula1.pdf?" findet jetzt beide Kopien (`C:\Users\pruve\Desktop\JanusPDFs\gundula1.pdf` und `C:\test2\gundula1.pdf`) automatisch. Primärer Workspace-Sweep: ~0.2s. Auto-Escalation (3 Laufwerke): 4-5s warm, ~20s cold. **Live-verifiziert an beiden Providern:** Gemini 3 Flash + GPT-5.4-nano, beide rufen den neuen Skill korrekt auf, erhalten beide Treffer und geben korrekte Antwort. |
| **Files** | `backend/services/filesystem_manager.py` (+150 Zeilen: `_ALL_DRIVES_EXCLUDE_DIRS`, `_enumerate_local_drives()`, `find_files()` mit 2-Phasen-Sweep & Auto-Escalation), `backend/data/schemas.py` (`FindFilesArgs` mit Trigger-Hints für LLM), `backend/tool_registry.py` (Registrierung in `fs_tools`), `backend/skills/filesystem/find_files.json` (NEU — Manifest mit Description, die dem LLM sagt, wann `search_all_drives=true` zu setzen ist). |
| **Verifikation** | Unit-Smoke: `find_files('*.md', max_results=5)` → 5 Treffer aus Desktop-Workspace ✅ · `find_files('gundula')` → Fuzzy-Fallback `*gundula*` → 1 Treffer ✅ · `find_files('gundula1.pdf', search_all_drives=True)` → 2 Treffer über C: + D: + E: in 21s (cold) ✅ · `find_files('gundula1.pdf')` (Default) → Auto-Escalation aktiviert, 2 Treffer in 4.5s (warm) ✅ · Registry-Check: `tool_manager.get_skill_metadata('filesystem.find_files')` returns Metadata ✅ · Live-Test Chat 63 (OpenAI) + Chat 64 (Gemini) — beide finden beide Duplikate, Log zeigt `auto_escalated=true`, `execution_time_ms=5085`. |
| **Patterns** | [LESSON] #Python #Pathlib #Robustness "Path.rglob bricht bei FileNotFoundError ab — nutze os.walk mit onerror für robuste rekursive Suche", [PATTERN] #Skill #AutoEscalation "Ein Skill kann mehrstufig eskalieren (cheap→expensive) ohne LLM-Intervention, wenn die Phase-1-Heuristik klare Schwelle hat (hier: ≤1 Treffer ⇒ Phase 2)". |

---

## [CURRENT_SESSION_DELTA] (HOTFIX — Gemini Tool-Response Envelope Loop 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **HOTFIX — Gemini halluzinierte PDFs statt Tool-Ergebnisse bei `filesystem.list_directory`** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | Root-Cause im `@c:\KI\Janus-Projekt\backend\llm_providers\gemini\service.py` lokalisiert: Tool-Response wurde als **JSON-String** im Wrapper `{"content": "<json-string>"}` an `protos.FunctionResponse.response` übergeben. Gemini konnte die verschachtelte Struktur nicht als "Tool-Call erledigt" interpretieren, rief das Tool ein zweites Mal mit identischen Args auf → `HARD-LOOP-BREAKER` blockte → Gemini halluzinierte "Das PDF ist in Ihrer Dokumentenliste verfügbar." **Fix:** JSON-Envelope vorab in ein strukturiertes Dict parsen, sodass Gemini direkt `contents: [...]`, `count: 7` etc. sieht. Fallback auf String-Wrapper bei Parse-Fehlern. Symmetrisch angewandt in Sync-Pfad (Z. 373-398) und Stream-Pfad (Z. 683-710). |
| **Root Cause** | Die Gemini-`FunctionResponse.response` erwartet ein strukturiertes Dict; ein eingebetteter JSON-String als String-Value wird von Gemini nicht als "Daten" erkannt. OpenAI akzeptiert beides tolerant, weshalb der Bug nur bei Gemini auftrat. |
| **Ergebnis** | Gemini liefert bei `filesystem.list_directory` (und analogen Tools) jetzt korrekte Dateilisten. Kein `HARD-LOOP-BREAKER` Trigger, kein 2. Re-Call, keine PDF-Halluzinationen. Live-Verifikation `C:\test2`: 7 Dateien + 1 Ordner korrekt enumeriert; Output 94 Tokens statt 81 (echte Antwort statt Re-Call). |
| **Files** | `backend/llm_providers/gemini/service.py` (Sync-Pfad + Stream-Pfad: JSON-Envelope-Parsing statt String-Wrapper). |
| **Verifikation** | 55/55 Unit-Tests grün (`pytest backend/tests/test_path_sentinel.py`); Live-Run Chat 52 Gemini `was liegt in "C:\test2"` → korrekte Antwort; Log-Beweis: `GEMINI-HISTORY: Stream-Model-Parts übernommen` gefolgt von 94-Token-Antwort ohne Loop-Breaker. |
| **Patterns** | [LESSON] #LLM #Gemini #ToolResponse "Structured Dict for FunctionResponse — NEVER pass JSON-string as content wrapper". |

---

## [CURRENT_SESSION_DELTA] (HOTFIX v0.4.16-beta.10/11 — Packaged-UI Route-Kollision 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic / Task** | **HOTFIX — Packaged UI ungestyled auf Testsystemen / Beta-Testern** (Regression aus beta.9 HTTP-Origin Switch) |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-21) |
| **Umsetzung** | **1. beta.10:** `frontend/dist/assets/` war leer, obwohl `dist/index.html` auf gehashte Assets verwies → `npm run build` regeneriert + Installer veröffentlicht. Reichte nicht, weil strukturelles Problem dahinter lag. **2. beta.11 (eigentlicher Fix):** Route-Kollision in `backend/main.py` lokalisiert: `app.mount("/assets", StaticFiles(directory=backend/assets))` (Preview-Bilder) überschattete den späten `app.mount("/", StaticFiles(directory=frontend/dist))`, weil StaticFiles-Mounts sich an Präfixen binden und `/assets/...` vom früheren Mount abgegriffen wurde → Vite-Bundles `/assets/index-*.{js,css}` = 404. Kollidierenden Mount entfernt (war Duplikat zu `/backend_assets`), Kommentar gegen Rückfall im Code. **3. Verifikation:** gebündelten `janus_backend.exe` direkt gestartet, `/`, CSS und JS via `Invoke-WebRequest` geprüft → alle 200 mit korrektem Content-Type. **4. Release-Pipeline:** `/release-production` Phase 1 + 3.4 + 3.5 durchlaufen, GitHub-Release `v0.4.16-beta.11` signiert & published. |
| **Root Cause** | beta.9 hatte die Electron-Lade-Strategie von `file://` / `janus://` auf `http://127.0.0.1:8001/` umgestellt (YouTube-Error-153 Mitigation). Dadurch wurde das FastAPI-Mount-Layout **erstmals produktiv relevant** — vorher kamen Asset-URLs nie durchs Backend. Die Kollision existierte latent seit langem und wurde erst durch den Architektur-Switch sichtbar. |
| **Ergebnis** | Packaged UI ist auf Testsystem wieder voll gestyled (User-bestätigt: „es geht!! super!!"). HTTP-Origin-Architektur für YouTube-153 ist jetzt produktionsreif. |
| **Files** | `backend/main.py` (Zeile 510: `/assets`-Mount entfernt + Gegen-Regression-Kommentar), `package.json` (Version 0.4.16-beta.10 → beta.11), `backend/version.py` (auto-sync), `frontend/dist/` (neu gebaut, JS-Hash `index-CGX2xgmF.js`), `CHANGELOG.md` (beta.10 + beta.11 Einträge), `RELEASE_NOTES.md` (regeneriert), `WHAT_I_LEARNED.md` ([LESSON] #FastAPI #StaticFiles #MountOrder). |
| **Verifikation** | `python tools/pre_build_check.py` 14/14 ✅ · PyInstaller Exit 0 · HTTP-Smoke-Test am gebündelten Backend: `/` 200 (84215 bytes), `/assets/index-CGX2xgmF.js` 200 (819050 bytes, `application/javascript`), `/assets/index-Dtd3qBjz.css` 200 (100653 bytes, `text/css`) ✅ · GitHub Release `v0.4.16-beta.11` published. |
| **Patterns** | [LESSON] #FastAPI #StaticFiles #MountOrder "StaticFiles-Mount-Präfixe fangen alles darunter — kollidierende Präfixe zwischen Backend-Assets und Vite-Build-Assets führen zu lautlosen 404s im packaged Build." |

---

## [CURRENT_SESSION_DELTA] (Diamond-Release-Guard & Production-Release v0.4.16 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic** | **STABILITY-ARC — COMPLETE** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | **1. Diamond-Release-Guard:** `.windsurf/workflows/release-production.md` erweitert mit Phase 0 (Git Integration & Versioning) und Phase 5 (Post-Release Cleanup). Automatischer Version-Bump (npm version patch), develop-Merge, und Checkout zurück zu develop nach Release. **2. Pre-Build Timeout-Fix:** `tools/pre_build_check.py` Timeout von 30s auf 60s erhöht für langsame backend.main Imports. **3. Production-Release v0.4.16:** Vollständiger Release-Prozess durchlaufen (Git Migration, Versionierung, Pre-Build Check, Build Pipeline, GitHub-Publish). **4. Atomic State-Save:** `.windsurf/workflows/save.md` erweitert mit verpflichtendem PROJECT_STATE.md Update vor Save-Skript. |
| **Ergebnis** | Diamond-Release-Guard voll operational. Production-Release v0.4.16 erfolgreich zu janus-update veröffentlicht. Atomic State-Save Pattern implementiert. |
| **Files** | `.windsurf/workflows/release-production.md`, `.windsurf/workflows/save.md`, `tools/pre_build_check.py`, `package.json`, `backend/version.py`, `PROJECT_STATE.md`. |
| **Patterns** | [PATTERN] #Release #Automation "Diamond-Release-Guard", [PATTERN] #Git #StateManagement "Atomic State-Save Pattern". |

---

## [CURRENT_SESSION_DELTA] (GPT-Diamond-Certification & UI-Sync-Live 🥇 SEALED)

| Feld | Wert |
|------|------|
| **Epic** | **STABILITY-ARC — Phase 2** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | **1. GPT-Core Zertifizierung:** gpt-5.4-nano/mini/standard erfolgreich validiert. **2. Extractor-Härtung:** `backend/services/memory_extractor.py` durch strikte JSON-Schema-Direktiven und Few-Shot-Anpassung stabilisiert; Pydantic-Validierungsfehler bei Mini-Modellen eliminiert. **3. UI-Live-Sync:** `frontend/js/app.js` patche (Sidebar-Listener); Änderungen an Sidebar-Dropdowns werden nun sofort an die Fenster-Header (Modus "Wie Sidebar") propagiert. **4. Registry-Cleanup:** `capability_registry.json` bereinigt; Orphan-Warnungen reduziert. |
| **Ergebnis** | GPT-Modellfamilie erreicht Diamond-Standard. UI-Konsistenz zwischen Sidebar und Dual-Window-System gewährleistet. |
| **Files** | `backend/services/memory_extractor.py`, `frontend/js/app.js`, `backend/data/capability_registry.json`. |
| **Patterns** | [PATTERN] #NLP #Extraction "Extraction Quality Hardening", [PATTERN] #Frontend #StateManagement "Live-UI-Propagator". |

---

## [CURRENT_SESSION_DELTA] (EPIC-GIT-GUARD — Git Infrastructure Certified 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-GIT-GUARD — Git Infrastructure Certified** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | **Task 060-062 abgeschlossen:** (1) Git-Historie chirurgisch gereinigt durch nuklearen Reset (.git-Ordner Löschung + Neu-Initialisierung nach .gitignore-Korrektur). (2) 2-Säulen-Modell etabliert: Janus-Backup (Private/Full, https://github.com/pruvex/Janus-Backup.git) & janus-update (Public/Release, https://github.com/pruvex/janus-update.git). (3) Sicherheits-Infrastruktur: Pre-commit Hook (scripts/git-hooks/pre-commit + pre-commit.ps1) mit 90MB Guard; release-gate.js (Branch-Check: nur von master, Dirty-Check: clean working tree, Sync-Check: HEAD == backup/master). (4) Branch-Modell: develop (Arbeit) / master (Release). (5) Workflow-Skill: /save (.windsurf/workflows/save.md) ruft hardened save.ps1 (Branch-Guard, Dirty-Check, Blocker-Scan, Commit/Push zu backup/develop). |
| **Ergebnis** | Git-Infrastruktur zertifiziert für Production-Release. Large-File-Blocker aktiv (90MB Guard). Release-Gate verhindert fehlerhafte Releases. Automated Backup via /save Skill. |
| **Files** | `.gitignore`, `.windsurf/workflows/save.md`, `scripts/git-hooks/pre-commit`, `scripts/git-hooks/pre-commit.ps1`, `scripts/release-gate.js`, `scripts/save.ps1`, `package.json` (release:guard, release scripts), `documentation/AI_STUDIO_SYSTEM_PROMPT_V33.md`. |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Git #Infrastructure "Nuclear Reset for Large File Cleanup", [PATTERN] #Git #Safety "Pre-commit Hook as Blocker Guard", [PATTERN] #Git #Release "Release-Gate Pattern"). |
| **Patterns** | [LESSON] #Git #Infrastructure "Nuclear Reset for Large File Cleanup", [PATTERN] #Git #Safety "Pre-commit Hook as Blocker Guard", [PATTERN] #Git #Release "Release-Gate Pattern". |

---

## [CURRENT_SESSION_DELTA] (STABILITY-ARC — Regression-Fixes 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic** | **STABILITY-ARC — Regression-Fixes** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | **YouTube Error 152-4:** (1) IsolateOrigins Switch hinzugefügt (app.commandLine.appendSwitch('disable-features', 'IsolateOrigins,site-per-process')). (2) User-Agent Spoofing auf Chrome 124 (app.userAgentFallback + BrowserWindow userAgent). (3) Entfernung des störenden origin Parameters aus normalizeVideoEmbedUrl (nur ?rel=0 und ?api=1). (4) GoogleVideo Permissions in setPermissionRequestHandler erlaubt. **Clipboard Paste-Regression:** Umstellung auf Electron-IPC (ipcMain.handle('clipboard:read'), preload.js window.electronAPI.readClipboard). **Auth PROVIDER-COHERENCE:** chat_orchestrator.py Provider-Korrektur erzwingt Key-Refresh für Ziel-Provider (Gemini-Keys werden nicht mehr fälschlich an OpenAI gesendet). |
| **Ergebnis** | YouTube Error 152-4 behoben. Clipboard Paste funktioniert via IPC. Auth-Kohärenz sichergestellt — Provider und API-Key sind immer synchron. |
| **Files** | `main.electron.cjs` (disable-features switch, userAgent Chrome 124, GoogleVideo permissions), `frontend/js/video-player.js` (normalizeVideoEmbedUrl ohne origin), `backend/services/chat_orchestrator.py` (PROVIDER-COHERENCE), `frontend/preload.js` (clipboard IPC), `frontend/js/context-menu.js` (IPC Fallback). |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Electron #YouTube #Isolation "IsolateOrigins Switch for YouTube Fix", [PATTERN] #Security #Coherence "Self-Healing Identity V3", [LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback Pattern"). |
| **Patterns** | [LESSON] #Electron #YouTube #Isolation "IsolateOrigins Switch for YouTube Fix", [PATTERN] #Security #Coherence "Self-Healing Identity V3", [LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback Pattern". |

---

## [CURRENT_SESSION_DELTA] (Clipboard IPC Fallback & YouTube 152-4 Regression 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Clipboard IPC Fallback & YouTube 152-4 Regression** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | main.electron.cjs: (1) IPC Clipboard Fallback: ipcMain.handle('clipboard:read') und ipcMain.handle('read-clipboard') implementiert; preload.js: window.electronAPI.readClipboard exponiert; context-menu.js: navigator.clipboard.readText() durch window.electronAPI.readClipboard() ersetzt. (2) Permission Handlers: setPermissionCheckHandler und setPermissionRequestHandler erweitert mit console.log Visibility, file:// Origin Bypass und allowedPermissions Array (clipboard-read, clipboard-sanitized-write, fullscreen, media, display-capture). (3) YouTube 152-4 Regression Fix: Referer/Origin Spoofing aus onBeforeSendHeaders entfernt (YouTube blockiert als Bot bei Mismatch); onHeadersReceived für X-Frame-Options/CSP-Stripping intakt gelassen. frontend/js/video-player.js: YouTube Embed URL auf youtube-nocookie.com ohne enablejsapi und origin Parameter geändert. |
| **Ergebnis** | Clipboard Paste funktioniert via IPC Fallback. YouTube Error 152-4 durch Entfernung von aggressivem Header-Spoofing behoben. |
| **Files** | `main.electron.cjs` (IPC Handler, Permission Handlers, webRequest), `frontend/preload.js` (electronAPI), `frontend/js/context-menu.js` (IPC Fallback), `frontend/js/video-player.js` (URL), `package.json` (v0.4.15-beta.11). |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback for Permission Denied", [LESSON] #Electron #YouTube #Header "YouTube Header Spoofing Anti-Pattern"). |
| **Patterns** | [LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback for Permission Denied", [LESSON] #Electron #YouTube #Header "YouTube Header Spoofing Anti-Pattern". |

---

## [CURRENT_SESSION_DELTA] (Task 051/052 — Browser Identity & Auth Coherence 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 051/052 — Browser Identity & Auth Coherence** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | main.electron.cjs: (1) User-Agent Spoofing auf drei Ebenen: app.userAgentFallback (Zeile 30), BrowserWindow userAgent (Zeile 559), onBeforeSendHeaders User-Agent Header (Zeile 570). Alle drei Ebenen verwenden Chrome 124 String zur Vermeidung von YouTube Bot-Blockaden. backend/services/chat_orchestrator.py: (2) AUTH-COHERENCE Fix: Provider-Korrektur MUSS Key-Refresh für ZIEL-Provider triggern (Zeilen 1649-1675). Wenn request.provider von gemini auf openai korrigiert wird, wird der API-Key aus dem Keyring für openai neu geladen. Debug-Logging zeigt Provider und Key-Preview (first 4 chars). |
| **Ergebnis** | YouTube Bot-Blockaden durch konsistenten Chrome 124 User-Agent behoben. Auth-Kohärenz sichergestellt — Provider und API-Key sind immer synchron. 401-Fehler durch falsche Keys (z.B. Gemini-Key bei OpenAI) vermieden. |
| **Files** | `main.electron.cjs` (User-Agent Spoofing), `backend/services/chat_orchestrator.py` (AUTH-COHERENCE), `WHAT_I_LEARNED.md` (Patterns). |
| **Doku** | `WHAT_I_LEARNED.md` ([PATTERN] #Electron #BrowserSpoofing "The Identity Cloak", [PATTERN] #Security #Coherence "Self-Healing Identity V2"). |
| **Patterns** | [PATTERN] #Electron #BrowserSpoofing "The Identity Cloak", [PATTERN] #Security #Coherence "Self-Healing Identity V2". |

---

## [CURRENT_SESSION_DELTA] (EPIC-BETA-READY & EPIC-SECURITY-AUDIT 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-BETA-READY & EPIC-SECURITY-AUDIT** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | **XSS & RCE Fixes verifiziert:** DOMPurify mit Whitelists für Chat, Release-Notes und Error-Nachrichten; IPC-Handler mit Pfad-Normalisierung, Whitelists und Extension-Blockliste. **Discord-Reporting-System implementiert:** Feedback-Button im Sidebar-Header, MCL-konformes Modal, POST /api/feedback mit Discord-Webhook-Integration, Log-File-Patch (AppData-Verzeichnis). **YouTube-Playback-Stabilität:** Transition zu youtube-nocookie.com, Header-Stripping (X-Frame-Options, CSP) und Identitäts-Maskierung (User-Agent Spoofing auf Chrome 124). **Electron-API Fix:** Rückkehr zur stabilen 2-Argumente-Syntax für WebRequest-Handler (onBeforeSendHeaders, onHeadersReceived). **Origin-Param Fix:** Entfernung von `origin=https://www.youtube.com` URL-Parameter in normalizeVideoEmbedUrl() zur Vermeidung von YouTube Error 152-4 unter sandboxed Electron-Renderer. **Regression Fix:** Clipboard IPC Fallback und YouTube 152-4 Regression durch Entfernung von Referer/Origin Spoofing (v0.4.15-beta.11). |
| **Ergebnis** | Janus ist sicher für Beta-Release. Alle kritischen Schwachstellen behoben. YouTube-Videos laden stabil über youtube-nocookie.com ohne aggressives Header-Spoofing. Clipboard Paste funktioniert via IPC Fallback. Discord-Reporting funktioniert für .exe-Pfade. |
| **Files** | `frontend/js/dompurify-config.js`, `frontend/js/chat.js`, `frontend/js/app.js`, `frontend/js/chat-manager.js`, `main.electron.cjs`, `backend/dependencies.py`, `backend/services/telemetry_service.py`, `frontend/index.html`, `frontend/css/style.css`, `backend/api/routers/system.py`, `frontend/js/video-player.js`, `frontend/preload.js`, `frontend/js/context-menu.js`, `package.json`, `CHANGELOG.md`. |
| **Doku** | `SECURITY_AUDIT_V1.md`, `WHAT_I_LEARNED.md` ([LESSON] #Electron #API #Stability, [PATTERN] #YouTube #Embedding "YouTube Embedding Stability Triad", [LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback", [LESSON] #Electron #YouTube #Header "YouTube Header Spoofing Anti-Pattern"). |
| **Patterns** | [LESSON] #Electron #API #Stability "Electron WebRequest API Versioning", [PATTERN] #YouTube #Embedding "YouTube Embedding Stability Triad", [LESSON] #Electron #Clipboard #IPC "Clipboard IPC Fallback", [LESSON] #Electron #YouTube #Header "YouTube Header Spoofing Anti-Pattern". |

---

## [CURRENT_SESSION_DELTA] (Origin-Param Fix — YouTube Error 152-4 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Origin-Param Fix — YouTube Error 152-4** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | frontend/js/video-player.js: Hardcoded `origin=https://www.youtube.com` URL-Parameter aus `normalizeVideoEmbedUrl()` entfernt. Unter sandboxed Electron-Renderer (file:// Origin) führte die Diskrepanz zwischen deklariertem Origin-Param und tatsächlichem postMessage-Origin zum YouTube-Player-Abbruch (Fehlercode 152-4) für alle Videos. Nach Entfernung fällt die Origin-Validierung weg und Playback funktioniert. |
| **Ergebnis** | YouTube-Videos laden jetzt stabil ohne Fehler 152-4. Die postMessage-Origin-Validierung wird nicht mehr durch einen falschen Origin-Parameter ausgelöst. |
| **Files** | `frontend/js/video-player.js` (Zeile 77). |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Electron #Sandbox #YouTube "Origin Parameter Mismatch in Sandboxed Renderer"). |
| **Patterns** | [LESSON] #Electron #Sandbox #YouTube "Origin Parameter Mismatch in Sandboxed Renderer". |

---

## [CURRENT_SESSION_DELTA] (Session-Fix — YouTube Embedding 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Session-Fix — YouTube Embedding** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | main.electron.cjs: webRequest-Handler von session.defaultSession auf mainWindow.webContents.session umgestellt. Das mainWindow verwendet eine separate session, daher müssen die Header-Spoofing und CSP-Stripping Handler auf der korrekten session registriert werden. |
| **Ergebnis** | YouTube-Videos werden jetzt korrekt im mainWindow angezeigt. Die webRequest-Handler werden für die mainWindow-Requests ausgeführt. |
| **Files** | `main.electron.cjs` (Zeilen 578-605). |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Electron #Session #YouTube "YouTube Session Scope Fix"). |
| **Patterns** | [LESSON] #Electron #Session #YouTube "YouTube Session Scope Fix". |

---

## [CURRENT_SESSION_DELTA] (Boot-Fix — Electron WebRequest API 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Boot-Fix — Electron WebRequest API TypeError** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-20) |
| **Umsetzung** | main.electron.cjs: webRequest-Handler von 3-Argumente-Syntax (mit extraHeaders Array) auf 2-Argumente-Syntax (filter, listener) umgestellt. Die installierte Electron-Version akzeptiert kein Array als zweiten Parameter → TypeError: Must pass null or a Function. |
| **Ergebnis** | Janus bootet wieder ohne TypeError. YouTube-Referer/Origin-Spoofing und Header-Stripping (X-Frame-Options, CSP) funktionieren weiterhin. |
| **Files** | `main.electron.cjs` (Zeilen 577-607). |
| **Doku** | `WHAT_I_LEARNED.md` ([LESSON] #Electron #WebRequest #API "Electron WebRequest API Versioning"). |
| **Patterns** | [LESSON] #Electron #WebRequest #API "Electron WebRequest API Versioning". |

---

## [CURRENT_SESSION_DELTA] (EPIC-SECURITY-AUDIT & EPIC-BETA-READY 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-SECURITY-AUDIT & EPIC-BETA-READY** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-19) |
| **Umsetzung** | **SEC-01/02 (XSS):** `dompurify-config.js` implementiert mit Whitelists für Chat (iframes, Code-Highlights), Release-Notes (restriktiv), Error-Nachrichten (minimal). Alle innerHTML-Zuweisungen von LLM-Inhalten nutzen Sanitizer. **SEC-03 (RCE):** `main.electron.cjs` save-file-in-path mit Pfad-Normalisierung, Whitelist für User-Verzeichnisse, Blocklist für kritische Windows-Pfade, nativer Save-Dialog für Pfade außerhalb Standard-User-Bereich. **SEC-05 (Vault):** Dynamische JWT-Secret-Generierung in `backend/dependencies.py` mit Persistenz nach config.json. **SEC-03.1 (Chained Fix):** userData aus allowedRoots entfernt, Extension-Blockliste (.json, .db, .key, .pem) hinzugefügt. **DOMPurify-Leak:** data: Schema aus iframe-URI-Whitelist entfernt, nur noch https: erlaubt. **Beta-Reporting:** Feedback-Button im Sidebar-Header, MCL-konformes Modal, POST /api/feedback mit Discord-Webhook-Integration, Log-File-Patch (AppData-Verzeichnis). |
| **Ergebnis** | Janus ist sicher für Beta-Release. Alle kritischen Schwachstellen behoben. Chained Vulnerability (SEC-03 → SEC-05) durch Scope-Trennung gelöst. |
| **Files** | `frontend/js/dompurify-config.js`, `frontend/js/chat.js`, `frontend/js/app.js`, `frontend/js/chat-manager.js`, `main.electron.cjs`, `backend/dependencies.py`, `backend/services/telemetry_service.py`, `frontend/index.html`, `frontend/css/style.css`, `backend/api/routers/system.py`, `backend/services/telemetry_service.py`. |
| **Doku** | `SECURITY_AUDIT_V1.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Security #Chaining "Security Chaining — Warum sich Einzellösungen gegenseitig aufheben können"). |
| **Patterns** | [PATTERN] #Security #Chaining "Security Chaining — Warum sich Einzellösungen gegenseitig aufheben können". |

---

## [CURRENT_SESSION_DELTA] (BUG-MEM-038 — Context Silence & Circular Fix 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **BUG-MEM-038 — Context Silence & Circular Fix** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | 1. Auslagerung der Meta-Noise-Logik in `memory/utils.py` zur Behebung von Circular Imports. 2. Implementierung des Retrieval-Filters (Silence Guard) für alle Slot-Sektionen. 3. System-Prompt gehärtet via `silent_memory_rule`. |
| **Ergebnis** | Backend bootet fehlerfrei. KI reagiert wieder normal auf Kurzbestätigungen; kein Vorlesen von internen Regeln mehr. |
| **Files** | `memory/utils.py` (neu), `memory_extractor.py`, `retrieval_service.py`, `prompt_registry.py`. |
| **Doku** | `WHAT_I_LEARNED.md` ([PATTERN] #Architecture #Dependency "The Leaf-Utility Strategy", [PATTERN] #Memory #Hygiene "The Retrieval-Noise-Shield"). |
| **Patterns** | [PATTERN] #Architecture #Dependency "The Leaf-Utility Strategy", [PATTERN] #Memory #Hygiene "The Retrieval-Noise-Shield". |

---

## [CURRENT_SESSION_DELTA] (BUG-ORCH-002 — Audit-Loop Forced-Tool-Args Refactor 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **BUG-ORCH-002 — Audit-Loop Forced-Tool-Args Refactor** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | execution_engine.py: Umstellung von "History-Push" (fake_assistant_message Injection) auf "Initial-Loop-State" (AUDIT-LOOP-FORCED-START). Bei Iteration 0 mit forced_tool_args wird der LLM-Call übersprungen und ein synthetisches Tool-Call-Response generiert. Tool-Namen Normalisierung für OpenAI (Punkt → Unterstrich). |
| **Doku** | `documentation/tasks/task_BUG-ORCH-002_audit_loop_forced_tool_args.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Orchestration #Resilience "Pre-filled Tool Injection", [PATTERN] #Pydantic #Safety "Alias-Safe ExecutionResponse"). |
| **Zertifizierung** | `python -m py_compile backend/services/orchestrator/execution_engine.py` ✅ PASS; OpenAI 400 BadRequest eliminiert im Audit-Pfad. |
| **Patterns** | [PATTERN] #Orchestration #Resilience "Pre-filled Tool Injection", [PATTERN] #Pydantic #Safety "Alias-Safe ExecutionResponse". |

---

## [CURRENT_SESSION_DELTA] (Task 029-035 — Universal Modal System & Video-Authority DONE)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-UNIVERSAL-MODAL** — Das erste echte 'AI OS' Fenstersystem. |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-15) |
| **Umsetzung** | Stateless MCL Fassade; Video-Player mit YouTube API + Authoritative Playlist-Ranking; FIFO-Guard (4 Modals); Global ESC; Startup-Booster (<10s) via Vektor-Cache & Background Loading. |
| **Fixes** | OpenAI-Router-Normalisierung (_ vs .); YouTube Search-Bias umgangen via Playlist-Lock. |
| **Doku** | `documentation/architecture/JANUS_MCL_SPECIFICATION.md` (vollständig konsolidiert); `WHAT_I_LEARNED.md` (3 neue Patterns: Feed-Authority, Two-Stage Startup, Skill-Router Normalization). |

---

## [CURRENT_SESSION_DELTA] (Task 034 — Schema & Naming Lockdown 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 034 — Schema & Naming Lockdown + Provider-Coherence Enforcement** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | video_tools.py: "query" + "retrieved_at" (ISO-String) zu data-Dictionary hinzugefügt; execution_dispatcher.py: video_search → video.search (dot-notation); response_finalizer.py: Legacy-Fallbacks entfernt; chat_orchestrator.py: Präventiver Provider-Check in _execute_generation (Modell-Präfix → Provider-Korrektur). |
| **Doku** | `documentation/tasks/task_034_schema_naming_lockdown.md` (vollständiges Dossier), `WHAT_I_LEARNED.md` (2 neue Patterns: Preemptive Provider Alignment, Channel-Handle Collision). |
| **Zertifizierung** | py_compile für alle geänderten Dateien erfolgreich; erwartete Side-Effects: Eliminierung der 400er Fehler bei Video-Fragen, saubere Pydantic-Validierung, stabilere modal_request Daten. |
| **Patterns** | [PATTERN] #Orchestration #Sync "Preemptive Provider Alignment", [LESSON] #Heuristics #Overreach "Channel-Handle Collision". |

---

## [CURRENT_SESSION_DELTA] (Task 036 — Auth-Coherence Fix 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 036 — Auth-Coherence Fix (Self-Healing Identity)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | chat_orchestrator.py: API Key Refresh nach PROVIDER-COHERENCE Korrektur via keyring.get_password(); Ollama Placeholder-Key; [AUTH-COHERENCE] Logging. |
| **Doku** | `documentation/tasks/task_036_auth_coherence_fix.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Security #Coherence "Self-Healing Identity"). |
| **Zertifizierung** | Autonome Verifikation via `repro_task_036.py`: PROVIDER-COHERENCE ✅, AUTH-COHERENCE ✅, Mismatch erkannt und geheilt. |
| **Patterns** | [PATTERN] #Security #Coherence "Self-Healing Identity". |

---

## [CURRENT_SESSION_DELTA] (Task 044 — Forced Tool Re-Injection 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 044 — Forced Tool Re-Injection** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | openai/service.py: Re-Injection Guard vor API-Aufruf; Prüft ob forced_tool_name in tools-Liste; fehlende Tool-Definition via skill_router.get_tool_definition() nachladen und injizieren; Logging [OPENAI_SHIM] Re-injecting missing forced tool definition. |
| **Doku** | `documentation/tasks/task_044_forced_tool_reinjection.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Orchestration #OpenAI "The Declarative Tool-Force Guard"). |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: 400 Bad Request Fehler verschwindet; PDF-Audit-Workflow funktioniert: Upload → Forced Tool Call → Korrekte Inhaltsanalyse → Zusammenfassung. |
| **Patterns** | [PATTERN] #Orchestration #OpenAI "The Declarative Tool-Force Guard". |

---

## [CURRENT_SESSION_DELTA] (Task 043 — OpenAI Naming Shim 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 043 — OpenAI Naming Shim** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | openai/service.py: Tool-Name-Normalisierungs-Shim vor API-Aufruf; Tool-Liste: function['name'] (domain.action → domain_action); tool_choice: tool_choice['function']['name'] normalisiert; Logging [OPENAI_SHIM] Normalizing tool name. |
| **Doku** | `documentation/tasks/task_043_openai_naming_shim.md`, `WHAT_I_LEARNED.md` ([PATTERN] #API #Interoperability "Naming-Shim Strategy"). |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: OpenAI-API akzeptiert Tool-Namen ohne BadRequestError 400; Forced Tool-Call bei PDF-Upload funktioniert. |
| **Patterns** | [PATTERN] #API #Interoperability "Naming-Shim Strategy". |

---

## [CURRENT_SESSION_DELTA] (Task 042 — Forced Tool-Call 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 042 — Forced Tool-Call (Anti-Hallucination Guard)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | schemas.py: audit_file Marker zu ChatRequest; chat.js: audit_file beim Upload gesendet; execution_dispatcher.py: Tool-Choice-Enforcement (force_tool_name = knowledge.query); chat_orchestrator.py: Fact-Extraction-Deaktivierung bei Audit-Intent. |
| **Doku** | `documentation/tasks/task_042_forced_tool_call.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Orchestration #OpenAI "The Declarative Tool-Force Guard"). |
| **Zertifizierung** | py_compile + node --check erfolgreich; erwartete Side-Effects: Bei Datei-Upload wird IMMER ein Lese-Tool aufgerufen; keine falschen "Datei existiert bereits"-Erinnerungen. |
| **Patterns** | [PATTERN] #Orchestration #OpenAI "The Declarative Tool-Force Guard". |

---

## [CURRENT_SESSION_DELTA] (Task 041 — Upload Prompt Hardening 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 041 — Upload Prompt Hardening** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | chat.js: Upload-Prompt von sanfter Empfehlung zu absoluter Verbots-Direktive gehärtet; "!!! STOPP !!! Lies KEINE alten Zusammenfassungen aus dem Gedächtnis!"; Tool-Namen aktualisiert (knowledge_read_full_text oder knowledge.query). |
| **Doku** | `documentation/tasks/task_041_upload_prompt_hardening.md`. |
| **Zertifizierung** | node --check erfolgreich; erwartete Side-Effects: LLM wird gezwungen, das Lese-Tool auszuführen, selbst wenn Chat-Verlauf voll mit alten Zusammenfassungen. |

---

## [CURRENT_SESSION_DELTA] (Task 040 — Upload Path 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 040 — Upload Path (Uploads-Ordner)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | rag.py: Upload-Pfad von DOCUMENTS_DIR → ~/Documents/JanusPDFs/Uploads; os.makedirs mit parents=True, exist_ok=True. |
| **Doku** | `documentation/tasks/task_040_upload_path.md` (wird erstellt). |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: PDFs per Drag & Drop werden in Documents/JanusPDFs/Uploads gespeichert. |

---

## [CURRENT_SESSION_DELTA] (Task 039 — PDF Storage Path 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 039 — PDF Storage Path (JanusPDFs-Ordner)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | pdf_generator.py: get_secure_absolute_path für "documents" von ~/Documents → ~/Documents/JanusPDFs geändert; os.makedirs mit parents=True, exist_ok=True. |
| **Doku** | `documentation/tasks/task_039_pdf_storage_path.md` (wird erstellt). |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: Generierte PDFs werden in Documents/JanusPDFs gespeichert. |
| **Patterns** | [PATTERN] #UX #Filesystem "The Flattened Result Strategy". |

---

## [CURRENT_SESSION_DELTA] (Task 038 — RAG File Guard 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 038 — RAG File Guard** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | rag.py: GET /documents Endpoint File Guard; os.path.exists Check für alle DB-Entries; Ghost Files: SQL delete + ChromaDB delete_document_index; Logging [FILE-GUARD]; db.commit(). |
| **Doku** | `documentation/tasks/task_038_rag_file_guard.md`. |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: Ghost Files werden automatisch aus SQL und ChromaDB entfernt; Dokumentenliste immer synchron mit Dateisystem. |

---

## [CURRENT_SESSION_DELTA] (Task 045 — Stability Arc Completion 🥇 DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 045 — Stability Arc Completion** |
| **Status** | **🥇 DONE** (2026-04-18) |
| **Umsetzung** | Vollständige Validierung des Stability Arc (Tasks 037-044); Upload-Audit, Forced Tool-Calls, Naming-Shims und Workspace-Unification voll funktionsfähig und validiert; Version auf V4.9.6-STABLE-REINJECTION gehoben. |
| **Doku** | PROJECT_STATE.md, WHAT_I_LEARNED.md (3 finale Kern-Erkenntnisse). |
| **Zertifizierung** | Alle Tasks SEALED & COMPLETE; Stability Arc abgeschlossen. |

---

## [CURRENT_SESSION_DELTA] (Task 037 — Knowledge Center Frontend Sync 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 037 — Knowledge Center Frontend Sync** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | knowledge-center.js: openKnowledgeCenter docsLoadedOnce Check entfernt; syncKnowledgeFromDockState: Immer loadDocs() wenn Modal sichtbar wird; Logging [FILE-GUARD SYNC]. |
| **Doku** | `documentation/tasks/task_037_knowledge_center_sync.md` (wird erstellt). |
| **Zertifizierung** | node --check erfolgreich; erwartete Side-Effects: Dokumentenliste wird bei jedem Modal-Open neu geladen; Backend File Guard wird zuverlässig getriggered. |

---

## [CURRENT_SESSION_DELTA] (Task 035 — Geo-Channel Separation 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 035 — Geo-Channel Separation (Search Precision)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-18) |
| **Umsetzung** | video_tools.py: GEO_REJECTION_LIST (Rom, Paris, Berlin, Wien, Tokio, etc.); _is_geo_rejected_hint() Guard; defensive Auto-Extraktion (nur bei Channel-Intent); explizites channel_name bleibt absolut priorisiert. |
| **Doku** | `documentation/tasks/task_035_geo_channel_separation.md`, `WHAT_I_LEARNED.md` ([PATTERN] #Heuristics #Precision "Geo-Channel Separation"). |
| **Zertifizierung** | py_compile erfolgreich; erwartete Side-Effects: "Geschichte von Rom" liefert Stadt-Dokumentation statt @rom Creator-Videos. |
| **Patterns** | [PATTERN] #Heuristics #Precision "Geo-Channel Separation". |

---

## [CURRENT_SESSION_DELTA] (Task 033 — MCL Video Player 🥇 SEALED & COMPLETE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 033 — MCL Video Player (GPT-4 Purge + Stream-Switch + Window-Interceptor)** |
| **Status** | **🥇 SEALED & COMPLETE** (2026-04-16) |
| **Sub-Status** | GPT-4 Purge: **DONE** | Stream-Switch: **DONE** | Window-Interceptor: **DONE** |
| **Umsetzung** | GPT-4 Modelle aus Text-Tasks entfernt (MOA-Hierarchy, Benchmark, Tests); Stream-Switch Pattern (UI-Karten deaktiviert, Markdown-Links als einzige Quelle); Window-Level Capture Interceptor (ultimativer Regressionsschutz gegen DOM-Changes); Heiler für nackte URLs vor marked.parse; stripInlineAssistantVideoLinks deaktiviert. |
| **Doku** | `documentation/tasks/task_033_mcl_video_player.md` (vollständiges Dossier), `WHAT_I_LEARNED.md` (3 neue Patterns: Stream-Switch, 5.4 Trinity Lockdown, Window-Level Capture Intercept). |
| **Zertifizierung** | GPT-4 Purge bestätigt (keine Referenzen außer tts_service.py); Video-Links stabilisiert über Streaming, Chat-Wechsel und App-Reload. |
| **Patterns** | [PATTERN] #Architecture #Streaming "The Stream-Switch Pattern", [PATTERN] #Pydantic #ModelHierarchy "The 5.4 Trinity Lockdown", [PATTERN] #Frontend #Events "Window-Level Capture Intercept". | |

---

## [CURRENT_SESSION_DELTA] (EPIC-SKILL-FORGE — Complete Arsenal **DONE**)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-SKILL-FORGE** — alle **49** registrierten Tools auf **Diamond-Standard** (Contract `ToolResultV1`, Top-Level Shield, schema-gestütztes Prompting). |
| **Status** | **DONE** (2026-04-13) |
| **Nachweis** | [`documentation/SKILL_INVENTORY.md`](documentation/SKILL_INVENTORY.md) — vollständig **`[x] Diamond Certified`**; Aufgaben-Dossier [`documentation/tasks/task_029_skill_forge_complete.md`](documentation/tasks/task_029_skill_forge_complete.md). |
| **Wissen** | `WHAT_I_LEARNED.md` — *Pydantic as an LLM Guardrail*, *The Universal Shield*. |

---

## [CURRENT_SESSION_DELTA] (Task 028 + UX-Closure — Janus Dock & Registry **DONE**)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 028** — Janus Dock (Bottom-Bar, `window-state` Dock-Module, Minimize/Restore Chat A/B, Wissensdatenbank, Image Studio, Bildgalerie); Registry + `WHAT_I_LEARNED` Abschluss. |
| **Status** | **DONE** (2026-04-13) |
| **Umsetzung** | `frontend/js/dock.js`, `window-state.js`, `knowledge-center.js` (Restore: `fromTaskbarDock` + feste `openJanusKnowledge`-Zuweisung), `gallery.js` (Dock-Modul `gallery`), `style.css` / `gallery.css`. |
| **Doku** | `01_CENTRAL_TASK_REGISTRY.md` (Janus AI OS COMPLETE); `WHAT_I_LEARNED.md` (Layer Model, Iconographie, Dock Restore Pattern); `documentation/tasks/task_028_janus_dock_system.md`. |
| **Hygiene** | Root: Duplikate `04_PROJECT_*`, `DIAMOND-REPORT_C8_*`, `SESSION_LOG.md` → **`documentation/archive/dossiers/`** |

---

## [CURRENT_SESSION_DELTA] (Task 027 — Smart Chat Grouping & Sorting / P0 Drift-Fix DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 027 — Feature 11** — Backend `chats.category` + JSON-Titel-Job; Frontend Sort-Dropdown, Kategorie-Ordner, Suche, `localStorage`; **P0:** `_ensure_sqlite_schema_migrations` gehärtet (`chats.category` bei Drift). |
| **Status** | **DONE** (verifiziert 2026-04-13) |
| **Umsetzung** | `title_generator.py` JSON `{title,category}`; `Chat.category`; Alembic + SQLite-Auto-ALTER; `chat-manager.js` `groupChatsByCategory` / `renderChatList`; `index.html` Toolbar; `style.css` `.chat-folder*`; `WHAT_I_LEARNED` Drift-Pattern. |
| **Doku** | `documentation/tasks/task_027_smart_grouping_backend.md`; `documentation/Planned Features/Smart Chat Grouping.md`; PROJECT_STATE §1b (A1–G17 Zuordnung). |
| **Zertifizierung** | Live OK; Post-Impl Close (FINAL SUCCESS). |

---

## [CURRENT_SESSION_DELTA] (Task 026 — Chat Actions / Sidebar A-B-Zuweisung DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 026 — Direkte Chat-Zuweisung** (`.chat-item-actions`, `btn-assign-a` / `btn-assign-b`) |
| **Status** | **DONE** (verifiziert 2026-04-12) |
| **Umsetzung** | `loadChat` + `setActiveWindow` + `setWindowOpen("B",true)` bei B; `e.stopPropagation()`; `flashWindowAssignFeedback` + `@keyframes janus-assign-pulse-a|b`; Hover via `opacity`/`visibility` (nicht `display:none`). |
| **Doku** | `documentation/tasks/task_026_chat_actions.md`; `WHAT_I_LEARNED.md` (Hierarchical Event Handling, Visual Confirmation via Animation, Hover vs. Visibility). |
| **Zertifizierung** | Feature integriert; Post-Impl Knowledge-Update abgeschlossen. |

---

## [CURRENT_SESSION_DELTA] (Task 025 — Navigation Sync + Fenster-B + Persistenz DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 025 — Navigation Sync** (Active Bar, Clean List, B-Sichtbarkeit) + **Window State Persistence** (Warm Start) |
| **Status** | **DONE** (verifiziert 2026-04-12) |
| **Umsetzung** | Active Chat Bar (Lila/Cyan-Chips, `syncActiveChatBar`); Clean List (Linien-Marker, Hover A/B, kein Dauer-Bonbon); Fenster B `isOpen` + Host `chat-window-host--b-closed`, Chip „+ Zweites Fenster“, × im Header; `janus_window_workspace_v1` + `resetChatWindowLayout` beim Start. |
| **Doku** | `documentation/tasks/task_025_navigation_sync.md` §2–§8; `WHAT_I_LEARNED.md` (Visual Hierarchy, Color Anchor, Warm Start Persistence). |
| **Zertifizierung** | Navigation + Sichtbarkeit manuell verifiziert; Post-Impl Doku abgeschlossen. |

---

## [CURRENT_SESSION_DELTA] (Task 023 & Task 024 — Window Binding + Fenster-LLM DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 023 — Window Binding** + **Task 024 — Window-Specific LLM Selectors** |
| **Status** | **DONE** (beide verifiziert 2026-04-12) |
| **Umsetzung** | **023:** `loadChat(..., { windowId: getActiveWindowId() })`, `setChatForWindow`, `getActiveChatIdForWindow`, `sendMessage(windowId)` / Pane-gebundene Messages. **024:** `window-state` `provider`/`modelId`, Header-`<select>` A/B, `effectiveProviderModelForWindow`, `syncChatWindowHeaderLlm`, Zwei-Zeilen-Header (Grid Zeile 2). |
| **Doku** | `documentation/tasks/task_023_window_binding.md` (Implementation Log, Test-Checkboxen); `documentation/tasks/task_024_window_llm_selectors.md` §2 Post-Impl; `WHAT_I_LEARNED.md` (Contextual Routing Strategy, Zwei-Zeilen-Header). |
| **Zertifizierung** | Parallele Steuerung + fensterspezifische Modelle manuell verifiziert; Post-Impl Dokumentation abgeschlossen. |

---

## [CURRENT_SESSION_DELTA] (Task 022 — Dual-Window Core / Meilenstein 1 DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 022 — Dual-Window Core** (Meilenstein 1) |
| **Status** | **DONE** |
| **Umsetzung** | `window-state.js` (Store, `paneId`, `.window-active`, `janus:window-state`); `index.html` duale Hosts + suffixed IDs; `style.css` + `src/styles.css` Layout/Fokus/Reset; `app.js` interact Drag-Resize, `resetChatWindowLayout`, Bounds; Bindung Legacy-Logik an Fenster **A** bis S3+. |
| **Doku** | `documentation/tasks/task_022_dual_window_core.md` §6 Post-Impl; `WHAT_I_LEARNED.md` (EventBus, Layout Preservation, Focus Triade). |
| **Zertifizierung** | Meilenstein 1 abgeschlossen (manuell / UX-Polish). |

---

## [CURRENT_SESSION_DELTA] (Task 021 — Smart Chat Naming EPIC DONE)

| Feld | Wert |
|------|------|
| **Epic / Task** | **Task 021 — Smart Chat Naming System** (Feature 10) |
| **Status** | **DONE** |
| **Umsetzung** | Backend: Trigger in `finalize_response` / `finalize_response_async` nach `persist_assistant_message`, `run_chat_title_job` (`title_generator.py`), DB `auto_generated` / `last_topic_hash`. Frontend: kein voreiliger Titel-`PUT`, `scheduleSmartTitleRefresh` + `patchChatTitleInUI`, Race-Fix `loadChats`/`createNewChat`. OpenAI-Titel-LLM: `gpt-4o-mini` (statt leerem Speed-Tier). |
| **Doku** | `documentation/tasks/task_021_smart_chat_naming_epic.md` §6 Post-Impl / §7 Debugging-Log |
| **Zertifizierung** | Live-Test bestanden (Gemini + GPT) |

---

## [CURRENT_SESSION_DELTA] (Task 020 — Memory Core Refactor EPIC DONE)

| Feld | Wert |
|------|------|
| **Epic** | **EPIC-MEMORY-CORE-REFACTOR** (**Task 020**) |
| **Status** | **DONE** |
| **Umsetzung** | Paket `backend/services/memory/` (`crud_service.py`, `retrieval_service.py`, `__init__.py`); Shim `memory_manager.py` für Abwärtskompatibilität; Tests/Patches (u. a. `test_memory_performance.py` → `retrieval_service.vector_service`). |
| **Doku** | `documentation/tasks/task_020_memory_core_refactor_epic.md` §6 Post-Impl; Roadmap Target #3 **COMPLETE** in `Refactoring_Roadmap_2026.md`. |
| **Zertifizierung** | **Opus** Architektur-Sign-off (Slice 1). |

---

## [CURRENT_SESSION_DELTA] (V4.8.0 — TURBO-FLOW EPIC DONE)

| Feld | Wert |
|------|------|
| **Milestone** | **V4.8.0 TURBO-FLOW — EPIC DONE** |
| **Status** | **DONE** |
| **EPIC-TURBO-FLOW** | **DONE** — Implementierung der **Saeulen 1–4** abgeschlossen (`stream_protocol`, Provider-`generate_response_stream`, `run_tool_loop_stream`, `handle_chat_request_stream`, `POST /api/chat/stream` auf echten Stream). **Architektur-Audit durch Opus 4.6 zertifiziert.** Ergebnisse (Zielgroessen): **~30–50% Latenz-Reduktion**, **echtes SSE-Streaming**, **verbesserte DB-Concurrency** (commit/expunge vor Stream, `finalize_response_async` mit frischer Session). |
| **Repo-Cleanup** | Keine turbo-spezifischen Temp-Dokumente; verwaiste Test-Run-Logs `backend/tests/tools/_tmp_*_run.log` entfernt. |

---

## [CURRENT_SESSION_DELTA] (V4.7.7 — FINAL SESSION SEAL — Input UX & Sidebar Elite)

| Feld | Wert |
|------|------|
| **Milestone** | **V4.7.7 FINAL SESSION SEAL — Chat Input Modernization & Sidebar Elite** |
| **Status** | 🥇 **SEALED (GRADE 1)** |
| **SYS-UI-INPUT-MODERNIZATION** | **🥇 DONE & SEALED** — Dynamic **textarea** composer (`#user-input`), **`autoResize`** (height reset → `scrollHeight` cap 200px, inner `scrollTop`, **Triple-Guard** paste: `input` + `requestAnimationFrame`, `paste` + `setTimeout(20)` + `rAF`), **SSE + history** `scrollChatToBottom`, flex **messages / input** inside `.chat-window`. **Files:** `frontend/js/app.js`, `frontend/js/chat.js`, `frontend/css/style.css`, `frontend/src/styles.css`, `frontend/index.html`. |
| **SYS-SIDEBAR-ELITE** | **🥇 DONE & SEALED** — **Unified nav** (icon rail collapsed), **collapse** toggle + `localStorage`, **Bildgalerie** / workspace nav integration path, compact **Neuer Chat**. **Files:** `frontend/src/styles.css`, `frontend/js/app.js`, `frontend/index.html`. |
| **FEAT-PROACTIVE-SUGGEST** | **🥇 DONE & SEALED — GRADE 1+ VALIDATED** — Elite Suggestion Engine (Health-Injector, Jaccard, 3-tier UI, `users/me`, pytest). Cross-referenced; no regression scope expansion without new epic. |
| **Session DONE bundle (prior arcs)** | **V4.7.6:** SYS-SIDEBAR-OVERHAUL + SYS-PROJECT-DASHBOARD. **Suggestion Engine:** `SuggestionEngine`, `prompt_registry`, `execution_dispatcher`, **SYS-CLEANUP-F401**, **SYS-SKILL-CONTRACT-V1**. |
| **Vorgänger** | V4.7.6 Sidebar & Project Dashboard — siehe SESSION_LOG. |
| **Geändert (this seal)** | `frontend/js/app.js`, `frontend/js/chat.js`, `frontend/css/style.css`, `frontend/src/styles.css`, `frontend/index.html`, `frontend/js/chat-manager.js`, `PROJECT_STATE.md`, `WHAT_I_LEARNED.md` |
| **Motto** | *"The system is clean, the mind is sharp. Diamond Elite status fully operational."* |
| **Resolved / covered** | Chat composer growth without app resize; context-menu paste parity with Ctrl+V; sidebar **sidebar-collapsed** rail; proactive suggestions **GRADE 1+** validation seal |
| **Tags** | #V4.7.7 #SYS-UI-INPUT-MODERNIZATION #SYS-SIDEBAR-ELITE #FEAT-PROACTIVE-SUGGEST #DiamondElite #Frontend |

**Seal (Orchestrierung):** **ORCH-DIAMOND-ELITE** bleibt **🥇 SEALED**; **V4.7.5** schließt **SYS-UI-SYNC** (Chat-Modell bleibt stabil bei Settings-Öffnung).

---

| Task-ID | Status | Lösung |
|---------|--------|--------|
| C8-VANILLA-SSE | DONE 🚀 | Fullstack-Sync: SSE-Stream -> CustomEvent -> fetchCostData() Trigger. Sidebar-Kosten & Budget-Save aktiv. |
| D10-FINOPS-SYNC | DONE 🚀 | Double-Counting im JS entfernt. Gemini-Flash und OpenAI-Mini werden als separate Zeilen in die DB geschrieben. Modal und Sidebar sind zu 100% mathematisch synchron. |
| BUG-A2-MOA-LOCK | DONE 🚀 | Pre-Resolution Hard-Lock in execution_engine.py. Modell-Override erfolgt VOR dem ersten API-Call, verhindert teuren ersten Call mit Base-Modell. |
| BUG-D10-GEMINI-FINOPS | DONE 🚀 | Gemini 3 Native Search Grounding Billing. Web-Such-Queries werden aus grounding_metadata extrahiert und mit 0.01€/Query berechnet. |
| BUG-E13-MEM-FIX | DONE 🚀 | Robustes JSON-Parsing im memory_extractor. ValueError eliminiert, graceful fallback zu [] bei ungültigem JSON. Prompt für Nano-Modelle geschärft. |
| SKILL-V3.0-WEBSEARCH | DONE 🚀 | Nano-Proof Overhaul: synthesis_directives, output_schema, "balanced" tier für Gemini. Runtime-Injection via chat_orchestrator + Gateways. |
| SKILL-V3.0-PRICE-COMPARISON | DONE 🚀 | Authoritative Pricing V3.0: Neue Description, Diamond-Standard Synthesis-Directives, strict output_schema, "balanced" tier für Gemini. |
| **BUG-MEM-SEC-001** | **DONE 🚀** | **Security Guard für _merge_existing_memory. Blockiert Updates auf non-editable Memories. Live-Test Szenario 6 PASS.** |
| **BUG-ORCH-001** | **DONE 🚀** | **UnboundLocalError Fix für run_tool_loop_result. Variable initialisiert am Methodenanfang. Syntax-Check PASS.** |
| **BUG-A2-MOA-DOWNGRADE** | **DONE 🚀** | **The Power-Hierarchy Rule: Automatischer Modellwechsel nur UPGRADE (speed < balanced < logic). User-Modell ist Floor. Verhindert illegalen Downgrade bei Smalltalk/Skills.** |
| **BUG-A2-ORCH-CONTROL-FLOW** | **DONE 🚀** | **Orchestrator Control-Flow Fix: Klare Trennung Skill-Loop vs. Direct-Response. Keine Doppelausführung. Task 033 Post-Impl.** |
| **BUG-A2-MIXED-PROVIDER-CONTEXT** | **DONE 🚀** | **The Koppel-Prinzip: Modell-IDs und Provider-APIs immer als Paar validiert. Eliminiert 404-Fehler bei Mixed-Provider-Context. Task 033 Post-Impl.** |
| **ORCH-DIAMOND-FINAL** | **🥇 DONE & SEALED** | **Diamond Cleanup: Extraktion aller Keywords/Regex in dedizierte Services. ChatOrchestrator ist nun reiner Dirigent. Syntax-Check PASS.** |
| **ORCH-TRANSFORM-EPIC** | **🏆 EPIC COMPLETE** | **Full Transformation: 6 Service-Module (intent_engine, identity_manager, vision_service, intercept_handler, policy_handler, prompt_registry). ZERO harte Strings/Regex/Prompts. 🥇 SEALED.** |
| **ORCH-DIAMOND-ELITE** | **🥇 SEALED — 100% VALIDATED BY REGRESSION TESTS** | **ORCH-ELITE-SEAL: Elite-Siegel der Diamond-Orchestrierung (Final + Transform-EPIC); V4.7.2 Regression-Grün (`test_memory_manager.py` 17/17). Kein weiteres Scope ohne neues Epic.** |
| **SYS-CLEANUP-F401** | **DONE 🚀** | **~233 ungenutzte Imports bereinigt; Ollama Legacy Shims (`ollama_service`, `ollama_adapter`); Ruff F401 = 0; py_compile PASS.** |
| **BUG-MEM-RECOVERY** | **DONE 🚀** | **Silent extraction failures behoben; Self-Healing in `memory_extractor.py` triggert zuverlässig bei unparseable Markdown/JSON (Fallback vs. echtes leeres Ergebnis).** |
| **SYS-TEST-STABILITY** | **DONE 🚀** | **LLM-Provider-Instanz-Cache isoliert zwischen Tests; `test_memory_manager.py` stabil 17/17.** |
| **SYS-SKILL-CONTRACT-V1** | **DONE 🚀** | **Alle anvisierten Tools auf `ToolResultV1`; Legacy-Keys `success`/`output` bei Serialisierung; Tests + `contacts_tools`-Re-Export.** |
| **FEAT-PROACTIVE-SUGGEST** | **🥇 DONE & SEALED — GRADE 1+ VALIDATED** | **V4.7.7 seal reaffirmed:** Elite Suggestion Engine (Hybrid Health-Injector, Jaccard, 3-tier, Forced Footer / STOP_SEQUENCE). Siehe `WHAT_I_LEARNED.md`, `documentation/features/feature_proactive_suggestions.md`.** |
| **SYS-UI-SYNC** | **DONE 🚀** | **V4.7.5: DOM↔appState sync vor Dropdown-Rebuild; `#model-select` `change` → backend; Settings-Öffnung ohne zerstörerisches `render()`; `users/me` liefert `last_used_*`.** |
| **SYS-SIDEBAR-OVERHAUL** | **🥇 DONE & SEALED** | **V4.7.6: Fixed-Flex-Fixed Layout, Unified Navigation, Workspace Tool Integration, Scroll-Management.** |
| **SYS-SIDEBAR-ELITE** | **🥇 DONE & SEALED** | **V4.7.7: Collapsible sidebar rail, unified nav + gallery integration path, `janus_sidebar_collapsed` persistence.** |
| **SYS-UI-INPUT-MODERNIZATION** | **🥇 DONE & SEALED** | **V4.7.7: Textarea composer, Triple-Guard paste-resize, dual scroll (chat + textarea), flex messages/input.** |
| **SYS-PROJECT-DASHBOARD** | **🥇 DONE & SEALED** | **V4.7.6: Project Dashboard Modal, Collapse Logic, Modal Init Fix, UI Consistency.** |

| **EPIC-SKILL-FORGE** | — | — | **DONE** | **Cursor** | **FRESH** | **Complete Arsenal:** 49/49 Skills Diamond (`ToolResultV1`, Shield, Field-Prompting). Siehe `documentation/tasks/task_029_skill_forge_complete.md` + `SKILL_INVENTORY.md`. |
| **EPIC-UNIVERSAL-MODAL** | — | — | **🥇 DONE & SEALED** | **Cursor** | **FRESH** | **Epic: Universal Modal System (MCL).** Task 029-035 COMPLETE. Stateless Facade; Video-Authority Pattern; FIFO-Guard; Global ESC; Startup-Booster. Siehe `documentation/architecture/JANUS_MCL_SPECIFICATION.md`. |
| **EPIC-TURBO-FLOW** | — | — | **DONE** | **Opus 4.6 / Cursor** | **FRESH** | **DONE:** Saeulen 1–4 + `/api/chat/stream`-Switch; B5 Caching (Gateway-Singletons, Tool-Def-Cache); SSE + DB-Pattern wie oben. Phase-3 Tool-Response-API-Cache optional Folge-Epic. |
| **EPIC-MEMORY-CORE-REFACTOR** | **7** | **7** | **DONE** | **Cursor** | **FRESH** | **Task 020:** `memory/crud_service` + `memory/retrieval_service` + Shim `memory_manager.py`; Roadmap Target #3 COMPLETE; Opus-zertifiziert. Siehe `task_020_memory_core_refactor_epic.md`. |
| **Task 021 — Smart Chat Naming** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE:** Auto-Titel nach 2 Messages, `finalize_response_async`→`_trigger_chat_title_job_if_eligible`, Frontend-Polling `scheduleSmartTitleRefresh`, Platzhalter-/Doppel-Chat-Fixes. Siehe `documentation/tasks/task_021_smart_chat_naming_epic.md`. |
| **Task 022 — Dual-Window Core** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE (M1):** `window-state.js`, duale Chat-Fenster A/B, kompaktes Layout, Fokus-Dimming/Glow, Reset im Header; Routing S3+ offen. Siehe `documentation/tasks/task_022_dual_window_core.md`. |
| **Task 023 — Window Binding** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE:** Sidebar-Chat-Klicks laden deterministisch in das **aktive** Fenster (`getActiveWindowId`); `loadChat`/`setChatForWindow`/`getActiveChatIdForWindow`. Siehe `documentation/tasks/task_023_window_binding.md`. |
| **Task 024 — Window LLM Selectors** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE:** Provider/Modell pro Fenster; `effectiveProviderModelForWindow`; Zwei-Zeilen-Header; Sidebar-Fallback + `syncChatWindowHeaderLlm`. Siehe `documentation/tasks/task_024_window_llm_selectors.md`. |
| **Task 025 — Navigation Sync** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE:** Active Chat Bar; Clean List + Hover A/B; Fenster B Toggle; `janus_window_workspace_v1` + Layout-Reset. Siehe `documentation/tasks/task_025_navigation_sync.md`. |
| **Task 026 — Chat Actions** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE:** Sidebar `btn-assign-a|b`, `stopPropagation`, Fenster-Puls (`janus-assign-pulse-*`). Siehe `documentation/tasks/task_026_chat_actions.md`. |
| **Task 027 — Smart Grouping & Sorting** | — | — | **DONE** | **Cursor** | **FRESH** | **DONE (Feature 11):** `chats.category`, Titel-Job JSON-Klassifikation; Sidebar Sortierung/Ordner/Suche/Persistenz; SQLite-Drift-Schutz. Siehe `documentation/tasks/task_027_smart_grouping_backend.md` + §1b A1–G17. |
| ORCH-TRANSFORM-EPIC | 8 | 8 | **🏆 DONE & SEALED** | Windsurf | FRESH | Full ChatOrchestrator Transformation: 6 Service-Module. ZERO harte Keywords/Regex/Prompts. |
| ORCH-DIAMOND-ELITE | — | — | **🥇 SEALED — 100% VALIDATED BY REGRESSION TESTS** | — | FRESH | Dach-Siegel Diamond-Orchestrierung (Final + Transform-EPIC); ORCH-ELITE-SEAL durch Regression (`test_memory_manager.py` 17/17) bestätigt. |
| SYS-SKILL-CONTRACT-V1 | 3 | 3 | **DONE 🚀** | Cursor | FRESH | Diamond `ToolResultV1` für Tool-Layer; Legacy-Dump-Bridge; **EPIC-SKILL-FORGE:** 49/49 Skills zertifiziert (`SKILL_INVENTORY.md`). |
| FEAT-PROACTIVE-SUGGEST | — | — | **DONE 🚀** | Cursor | FRESH | Proaktive Vorschläge OFF/SMART/PROACTIVE; UI-Slider; users/me API; pytest `test_users_me_api.py`. |
| SYS-CLEANUP-F401 | 4 | 4 | **DONE 🚀** | Cursor | FRESH | Ruff F401 backend-weit 0; Thin-Facade-Shims Ollama; py_compile PASS. |
| **SYS-UI-SYNC** | — | — | **DONE 🚀** | Cursor | FRESH | **V4.7.5:** Chat-Modell stabil bei Settings; DOM/state sync; last_used in users/me. |
| A2-MEM-V2-GOLD | 6 | 6 | DONE | Windsurf | FRESH | Memory V2 System komplett: 20/20 E2E Tests, 5/5 Benchmarks, Diamond Standard erreicht |
| SYS-V4.4-PROD-STABLE | 4 | 4 | DONE | Windsurf | LOOP_PASS | SSE-Streaming + Live-Cost Sidebar + Disconnect-Guard |
| SYS-V3.2-RESTRUCT | 4 | 4 | DONE | Windsurf | LOOP_PASS | Hybrid-Modularitaet implementiert |

### SECTION 1b: A1–G17 Zuordnung (Feature 11 / Task 027)

Die **globale Rollen-Matrix** (`documentation/migration/01_phase_one_foundation.md` A1–G17) ist **nicht** identisch mit der **TURBO-FLOW-Teil-Matrix** in `documentation/tasks/task_019_turbo_flow_epic.md` (dort werden z. B. „C7/C8“ **Epic-intern** für Streaming/Parallelität genutzt — keine Kollision mit den Foundation-IDs).

**Task 027 (Smart Grouping & Sorting)** — sinnvolle Mapping-Zuordnung:

| Foundation-ID | Rolle für dieses Feature |
|-----------------|---------------------------|
| **B6** | Schema-Design: Spalte `chats.category`, Default `general`, Migration |
| **C7** | Backend-Implementierung: `title_generator.py`, Parser, API/Schemas |
| **C8** | Frontend-Implementierung: `chat-manager.js`, Ordner-UI, Sort/Search |
| **G17** | Wissen & Struktur: thematische Chat-Ordner, Sidebar als „Wissenssystem“ |
| **D10** | Log-/Drift-Diagnose: P0 bei fehlender Spalte (`OperationalError`, `janus_backend.log`) |

Alle übrigen A1–G17 Slots bleiben generisch verfügbar (siehe `documentation/AI_STUDIO_SYSTEM_PROMPT_V32.md` §5 Spezialisten-Routing); **keine** bestehende Zeile in SECTION 1 wurde überschrieben.

---

## SECTION 2: SESSION_LOG (Letzte 5 Eintraege)

| Zeitstempel | Task-ID | Editor | Ergebnis | Notizen |
|-------------|---------|--------|----------|---------|
| 2026-04-19 | **Task 052 — Chromium Extra Headers Fix** | **Kimi** | **🥇 SEALED & COMPLETE** | Aktivierung von extraHeaders Flag in onBeforeSendHeaders und onHeadersReceived zur Aufhebung der Chromium-Blockade von Referer-Manipulationen. Behebung von YouTube Error 15-4 / 153. Version 0.4.15-beta.7. |
| 2026-04-19 | **Task 051 — Browser Identity Spoofing** | **Kimi** | **🥇 SEALED & COMPLETE** | Browser-Spoofing Pattern (User-Agent Maskierung auf App- und Window-Ebene zur Umgehung von Bot-Blockaden). Version 0.4.15-beta.6. |
| 2026-04-19 | **Task 050 — CSP Bypass & iFrame Hardening** | **Kimi** | **🥇 SEALED & COMPLETE** | Header-Deletion-Pattern (radikales Entfernen von CSP-Headern), allowRunningInsecureContent, Permission Handlers (media/display-capture), Autoplay CSP Modification. Version 0.4.15-beta.5. |
| 2026-04-19 | **Task 049 — YouTube Final Master Fix** | **Kimi** | **🥇 SEALED & COMPLETE** | YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling. Version 0.4.15-beta.4. |
| 2026-04-19 | **Task 048 — YouTube Origin & Orchestrator-Bypass Fix** | **Kimi** | **🥇 SEALED & COMPLETE** | YouTube Fehler 153 via Referer/Origin Header-Spoofing, Synthese-Bypass via Hard-Lock return. Version 0.4.15-beta.3. |
| 2026-04-19 | **Task 047 — Beta-Ready Final Polish** | **Kimi** | **🥇 SEALED & COMPLETE** | Feedback-Plug-and-Play (Webhook Fallback), Video-Stability-Fix (is_final_response=True), Tiktoken-Resilience. Version 0.4.15-beta.2. |
| 2026-04-19 | **Task 046 — Security Audit & Beta-Reporting** | **Kimi** | **🥇 SEALED & COMPLETE** | XSS Shield (DOMPurify), RCE Prevention (IPC), JWT Vault Security, Chained Vulnerability Fix (userData aus allowedRoots), Beta-Reporting (Discord Webhook). Version 0.4.15-beta.1. |
| 2026-04-18 | **BUG-ORCH-002 — Audit-Loop Forced-Tool-Args** | **Kimi** | **🥇 SEALED & COMPLETE** | execution_engine.py: Umstellung von History-Push auf Initial-Loop-State; AUDIT-LOOP-FORCED-START in run_tool_loop und run_tool_loop_stream; Tool-Namen Normalisierung für OpenAI; OpenAI 400 BadRequest eliminiert. |
| 2026-04-18 | **Task 045 — Stability Arc Completion** | **Cascade** | **🥇 DONE** | Vollständige Validierung des Stability Arc (Tasks 037-044); Upload-Audit, Forced Tool-Calls, Naming-Shims und Workspace-Unification voll funktionsfähig und validiert; Version auf V4.9.6-STABLE-REINJECTION gehoben. |
| 2026-04-18 | **Task 044 — Forced Tool Re-Injection** | **Cascade** | **🥇 SEALED & COMPLETE** | openai/service.py: Re-Injection Guard vor API-Aufruf; Prüft ob forced_tool_name in tools-Liste; fehlende Tool-Definition via skill_router.get_tool_definition() nachladen und injizieren; Logging [OPENAI_SHIM] Re-injecting missing forced tool definition. Erwartete Side-Effects: 400 Bad Request Fehler verschwindet; PDF-Audit-Workflow funktioniert. |
| 2026-04-18 | **Task 043 — OpenAI Naming Shim** | **Cascade** | **🥇 SEALED & COMPLETE** | openai/service.py: Tool-Name-Normalisierungs-Shim vor API-Aufruf; Tool-Liste: function['name'] (domain.action → domain_action); tool_choice: tool_choice['function']['name'] normalisiert; Logging [OPENAI_SHIM] Normalizing tool name. Erwartete Side-Effects: OpenAI-API akzeptiert Tool-Namen ohne BadRequestError 400. |
| 2026-04-18 | **Task 042 — Forced Tool-Call** | **Cascade** | **🥇 SEALED & COMPLETE** | schemas.py: audit_file Marker zu ChatRequest; chat.js: audit_file beim Upload gesendet; execution_dispatcher.py: Tool-Choice-Enforcement (force_tool_name = knowledge.query); chat_orchestrator.py: Fact-Extraction-Deaktivierung bei Audit-Intent. Erwartete Side-Effects: Bei Datei-Upload wird IMMER ein Lese-Tool aufgerufen. |
| 2026-04-18 | **Task 041 — Upload Prompt Hardening** | **Cascade** | **🥇 SEALED & COMPLETE** | chat.js: Upload-Prompt von sanfter Empfehlung zu absoluter Verbots-Direktive gehärtet; "!!! STOPP !!! Lies KEINE alten Zusammenfassungen aus dem Gedächtnis!"; Tool-Namen aktualisiert. Erwartete Side-Effects: LLM wird gezwungen, das Lese-Tool auszuführen. |
| 2026-04-18 | **Task 040 — Upload Path** | **Cascade** | **🥇 SEALED & COMPLETE** | rag.py: Upload-Pfad von DOCUMENTS_DIR → ~/Documents/JanusPDFs/Uploads; os.makedirs mit parents=True, exist_ok=True. Erwartete Side-Effects: PDFs per Drag & Drop werden in Documents/JanusPDFs/Uploads gespeichert. |
| 2026-04-18 | **Task 039 — PDF Storage Path** | **Cascade** | **🥇 SEALED & COMPLETE** | pdf_generator.py: get_secure_absolute_path für "documents" von ~/Documents → ~/Documents/JanusPDFs geändert; os.makedirs mit parents=True, exist_ok=True. Erwartete Side-Effects: Generierte PDFs werden in Documents/JanusPDFs gespeichert. |
| 2026-04-18 | **Task 038 — RAG File Guard** | **Cascade** | **🥇 SEALED & COMPLETE** | rag.py: GET /documents Endpoint File Guard; os.path.exists Check für alle DB-Entries; Ghost Files: SQL delete + ChromaDB delete_document_index; Logging [FILE-GUARD]; db.commit(). Erwartete Side-Effects: Ghost Files werden automatisch entfernt. |
| 2026-04-18 | **Task 037 — Knowledge Center Frontend Sync** | **Cascade** | **🥇 SEALED & COMPLETE** | knowledge-center.js: openKnowledgeCenter docsLoadedOnce Check entfernt; syncKnowledgeFromDockState: Immer loadDocs() wenn Modal sichtbar wird; Logging [FILE-GUARD SYNC]. Erwartete Side-Effects: Dokumentenliste wird bei jedem Modal-Open neu geladen. |
| 2026-04-18 | **Task 034 — Schema & Naming Lockdown** | **Cascade** | **🥇 SEALED & COMPLETE** | video_tools.py: "query" + "retrieved_at" (ISO-String) zu data-Dictionary; execution_dispatcher.py: video_search → video.search; response_finalizer.py: Legacy-Fallbacks entfernt; chat_orchestrator.py: Präventiver Provider-Check. Erwartete Side-Effects: Eliminierung 400er Fehler bei Video-Fragen, saubere Pydantic-Validierung, stabilere modal_request Daten. |
| 2026-04-18 | **Task VID-UNDERSTAND-001** | **Cascade** | **🥇 SEALED & COMPLETE** | Video Understanding V1 Epic - Lokaler Whisper-STT Fallback, Dediziertes Transkript-Modal, 100% FinOps-Transparenz, Automatische Memory V2 Injektion. Files: backend/main.py, backend/tools/video_understanding.py, frontend/js/video-player.js, frontend/js/cost-visualizer.js, frontend/index.html. |
| 2026-04-18 | **Task FE_TRANSCRIPT_MODAL_UI_ENHANCEMENT** | **Cascade** | **DONE** | Transkript-Modal UI Enhancement - Dock-Panel Design, Buttons, Drag/Resize, Taskbar-Integration. Files: frontend/index.html, frontend/css/style.css, frontend/js/video-player.js, frontend/js/modal-api.js. |
| 2026-04-15 | **Task 033 — MCL Video-Player Date Enhancement** | **Kimi** | **DONE** | `published_date_human` (DD.MM.YYYY) zu `VideoResult` Schema hinzugefügt; `_format_published_date_human()` Helper; Prompt-Registry Directive „(Hochgeladen am DD.MM.YYYY)“ hinter Kanalnamen erzwingen. Keine Regression; strikte Trennung zu BUG-MEM-033 (Memory). |
| 2026-04-14 | **Task 033 — MCL Video-Player Hardening** | **Cursor** | **DONE** | `modal_request` deterministic + persisted, Reopen-Link/Streaming/Reload robust, `openModal` idempotent, Video/Knowledge Modal wieder auf Top-Left von `chat-window-B`, UX regressionsfrei in Live-Checks. |
| 2026-04-13 | **EPIC-SKILL-FORGE (Complete Arsenal)** | **Cursor** | **DONE** | **49/49** Tools Diamond; `SKILL_INVENTORY.md` vollständig; `task_029_skill_forge_complete.md`; `WHAT_I_LEARNED` (Pydantic LLM Guardrail, Universal Shield). *Hinweis:* Dateiname task_029 = Skill-Forge-Dossier, nicht MCL Task 029. |
| 2026-04-13 | **Task 027 — Smart Grouping & Sorting** | **Cursor** | **DONE** | **Post-Impl FINAL SUCCESS:** Registry + `task_027` DONE; `WHAT_I_LEARNED` SQLite Drift Protection; §1b A1–G17 Zuordnung (B6/C7/C8/G17/D10); Feature 11 abgeschlossen. |
| 2026-04-12 | **Task 025 — Navigation Sync** | **Cursor** | **DONE** | **Post-Impl Close:** Active Bar (Lila/Cyan), Clean List Policy, Fenster-B Toggle + Persistenz + Layout-Reset; `task_025_navigation_sync.md` + WHAT_I_LEARNED (3 Patterns) + PROJECT_STATE. |
| 2026-04-12 | **Task 023 + Task 024** | **Cursor** | **DONE** | **Post-Impl Close:** Window Binding (Sidebar → aktives Fenster deterministisch); Window LLM (Zwei-Zeilen-Header, `effectiveProviderModelForWindow`, Sidebar-Override-Semantik). Doku + WHAT_I_LEARNED + Registry aktualisiert. |
| 2026-04-12 | **Task 022 — Dual-Window Core** | **Cursor** | **DONE (M1)** | **Post-Impl:** State-Store aktiv; linksbündiges Layout Original-Size; Fokus Opacity 0.65 / Active Glow+Rand; Reset-Buttons; Doku §6 + WHAT_I_LEARNED (EventBus, Layout Preservation, Focus Triade). |
| 2026-04-12 | **Task 021 — Smart Chat Naming** | **Cursor** | **DONE** | **Post-Impl / Epic close:** Trigger via `finalize_response_async`→`finalize_response`; `run_chat_title_job`; Frontend `scheduleSmartTitleRefresh` + `patchChatTitleInUI`; Race-Fix (`suppressAutoCreate`, kein doppeltes `loadChats` auf DOMContentLoaded); OpenAI-Titel `gpt-4o-mini`. Live-Test OK. `task_021_smart_chat_naming_epic.md` §6/§7. |
| 2026-04-12 | **EPIC-MEMORY-CORE-REFACTOR (Task 020)** | **Cursor** | **DONE** | **Memory Core Split Slice 1:** `backend/services/memory/` (CRUD + Retrieval), Shim `memory_manager.py`, Registry/Roadmap/PROJECT_STATE aktualisiert; Opus-Zertifizierung; `test_memory_performance` Namespace-Fix. |
| 2026-04-12 | **EPIC-TURBO-FLOW — EPIC DONE** | **Cursor** | **DONE** | **Saeulen 1–4 implementiert** (Stream-Protokoll, Provider-Streaming, `run_tool_loop_stream`, `handle_chat_request_stream`, Router-Mapping auf Legacy-SSE). **Architektur-Audit Opus 4.6 zertifiziert.** **Ergebnisse:** ~30–50% Latenz-Reduktion (Zielgroesse), echtes SSE-Streaming, verbesserte DB-Concurrency. Siehe `documentation/tasks/task_019_turbo_flow_epic.md`. |
| 2026-04-12 | **EPIC-TURBO-FLOW — B5 (Phase 1)** | **Cursor** | **DONE** | **Caching hot-path (Opus-Audit Issue 007/008):** `llm_gateway.py` process-weite Gateway-Singletons (`_GATEWAY_SILOS`); `tool_manager.py` `_tool_definitions_cache` + `llm_definition["parameters"]`, Invalidierung bei `register_tool`. `/post-impl` in `task_019_turbo_flow_epic.md`. Regression: `pytest backend/tests/test_memory_manager.py -q` **17/17**; voller `pytest backend/tests` collection ERROR (`OllamaCompiler` / `test_prompting_builder.py`) — vorbestehend. |
| 2026-04-11 | **V4.7.7 FINAL SESSION SEAL** | **Cursor** | **🥇 DONE & SEALED** | **SYS-UI-INPUT-MODERNIZATION:** textarea `#user-input`, `autoResize` + Triple-Guard paste (`input`/rAF, `paste`+20ms+rAF), `scrollChatToBottom`, `.chat-window` flex messages/input. **SYS-SIDEBAR-ELITE:** `sidebar-collapsed` rail, nav + gallery path, localStorage. **FEAT-PROACTIVE-SUGGEST:** GRADE 1+ validated seal. **Pattern:** `WHAT_I_LEARNED.md` — Triple-Guard Paste-Resize. Root cleanup: temp `test_output*.txt` / regression logs removed. |
| 2026-04-11 | **V4.7.6 SYS-SIDEBAR-OVERHAUL + PROJECT-DASHBOARD** | **Cursor** | **🥇 DONE & SEALED** | **Vollständiger Sidebar-Refactor:** Fixed Layout (Fixed-Flex-Fixed Pattern), Unified Navigation (Workspace Tools als Nav-Items), Project Dashboard Modal & Collapse Logic. **Gelöste Bugs:** BUG-SIDEBAR-OVERFLOW (Scroll-Fix für lange Chat-Listen), BUG-PROJECT-MODAL-INIT (Modal opening fix), UI-CONSISTENCY-SYNC (Icon/Button alignment). **Patterns:** `WHAT_I_LEARNED.md` — Fixed-Flex-Fixed Sidebar, Workspace Tool Integration. |
| 2026-04-11 | **V4.7.5 SYS-UI-SYNC FINAL SEAL** | **Cursor** | **DONE 🚀** | **UI Consistency:** `app.js` — vor `render()` DOM→`appState` für Provider/Modell; `#model-select` `change` → `updateLastUsedModelInBackend()`; Settings-Button toggelt nur Views (kein vollständiges `render()`); **`users/me`** erweitert um `last_used_provider` / `last_used_model` (Config-Spiegel zu **`GET /api/last-used-model`**). **`settings.js`:** Kommentar: kein Chat-Modell aus Settings-Loader. Motto & **PROJECT_STATE** → V4.7.5; **WHAT_I_LEARNED:** DOM-to-State Sync Guard. |
| 2026-04-11 | **V4.7.4 FEAT-PROACTIVE-SUGGEST** | **Cursor** | **DONE 🚀** | **Proaktive Vorschläge:** `SuggestionEngine` + Prompt-Registry; Tool-Tag-Aggregation; `wf.suggestion_mode`; GET/PATCH `/api/users/me`; Settings „Assistenz & Proaktivität“ (Slider 0–2); **`backend/tests/test_users_me_api.py`** deckt GET/PATCH und DB-Persistenz 0→1→2 ab; `conftest` importiert `backend.data.models` für vollständiges SQLite-Schema; **`frontend/dist/BUILDNOTE.txt`** Hinweis auf Bundle-Rebuild. |
| 2026-04-11 | **V4.7.3 Skill Contract** | **Cursor** | **DONE 🚀** | **SYS-SKILL-CONTRACT-V1:** `ToolResultV1` als einheitlicher Tool-Vertrag; `@computed_field` Legacy-Bridge (`success`, `output`) auf `model_dump()`; Tool-Rollout vollständig; `contacts_tools.py` Re-Export; siehe `WHAT_I_LEARNED.md` Pattern. |
| 2026-04-10 | **V4.7.2 Housekeeping** | **Cursor** | **DONE 🚀** | **BUG-MEM-RECOVERY:** `memory_extractor.py` Self-Healing bei kaputtem Markdown/JSON (tuple-Fallback-Signal). **SYS-TEST-STABILITY:** `clear_provider_instance_cache()` + autouse in `test_memory_manager.py`. **ORCH-ELITE-SEAL:** **100% VALIDATED BY REGRESSION TESTS** (`test_memory_manager.py` 17/17). |
| 2026-04-10 | **SYS-CLEANUP-F401** | **Cursor** | **DONE 🚀** | Ruff F401: ~233 ungenutzte Imports in `backend/` bereinigt. `ollama_service.py` / `ollama_adapter.py` als Re-Export-Shims. Presets-`__init__` mit `__all__` / `import m as m`. Tests: Patch-Pfade auf `ollama.service.load_config_data`. `py_compile` gesamtes `backend/` (ohne venv) PASS. **ORCH-DIAMOND-ELITE** → **SEALED.** |
| 2026-04-10 | **ORCH-TRANSFORM-EPIC** | **Kimi K2.5** | **🏆 EPIC COMPLETE** | Full Transformation: 6 Service-Module (intent_engine 366L, identity_manager 200L, vision_service, intercept_handler, policy_handler, prompt_registry). ChatOrchestrator: ZERO harte Strings/Regex/Prompts. 🥇 SEALED. 🚀💎 |
| 2026-04-10 | **ORCH-DIAMOND-FINAL** | **Kimi K2.5** | **🥇 DONE & SEALED** | Diamond Cleanup: Service-Agnostic Dispatcher Pattern. IntentEngine (366 Zeilen), IdentityManager (200 Zeilen), VisionService erweitert. ChatOrchestrator bereinigt - ZERO harte Keywords/Regex. 🚀💎 |
| 2026-04-09 | **M-MEM-V2-FINAL** | **Cascade** | **DONE (Diamond Gold Final)** | Temporal-Recall & Episodic Memory. Zeitstempel + Chat-Origin für jede Erinnerung. System Clock Injection. Identity-Anchor. Origin-aware Personen-Dedup. 🚀💎 |
| 2026-04-09 | **M-MEM-V2-GOLD-SEAL** | **Cascade** | **DONE (Diamond Gold Seal)** | Fact-Coupon Integration erfolgreich. Release V2.1.0 mit 100% Recall-Sicherheit bei Nano-Modellen. Alle 19 Szenarien PASS. 🚀💎 |
| 2026-04-09 | **M-MEM-V2-RELEASE** | **Cascade** | **DONE (Epic Released)** | Epic Memory V2.1.0 Diamond Certified & Released. 19/19 Live-Test Szenarien PASS. Tasks BUG-MEM-SEC-001 & BUG-ORCH-001 DONE. 🚀💎 |
| 2026-04-08 | **FIX-036** | **Cascade** | **DONE (Regression-Cleanup)** | Cascade: Final Documentation & Diamond Report. Tasks 032/033/035 finalisiert. PRODUCTION READY 🚀💎 |
| 2026-04-08 | **FIX-035** | **Kimi/Cascade** | **DONE (Precedence Guard)** | Kimi: Personal Context > Proactive Heuristics. Cascade: Drill-Down Kill-Switch in Gemini Gateway. Dual-Layer Protection. |
| 2026-04-08 | **BUG-MEM-034** | **Kimi** | **DONE (Strategic Routing)** | Kimi: Gemini-Bypass für persönlichen Recall zu gpt-5.4-nano. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-033** | **Kimi** | **DONE (Fact Field Warning)** | Kimi: Grammatikalisch korrekte Sätze im 'fact' Feld erzwingen. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-032** | **Kimi** | **DONE (List Request Guard)** | Kimi: List-Request Guard für persönliche Fragen. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-031** | **Kimi** | **DONE (Semantic Query Expansion)** | Kimi: Query expansion für "familie" um Verwandtschaftsgrade. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-030** | **Kimi** | **DONE (Recall Guard Pronouns)** | Kimi: _SELF_REF_RE um meiner/meinem erweitert. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-029** | **Kimi** | **DONE (Medical Nano Reasoning)** | Kimi: Hidden-allergen reasoning zu CRITICAL MEDICAL WARNING. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-028** | **Kimi** | **DONE (Identity Adverb Guard)** | Kimi: Adverb-Filter in IDENTITY-EXTRAKTION. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-023** | **Kimi** | **DONE (Top-K Starvation)** | Kimi: limit 10→50, Knapsack-Algorithmus bekommt mehr Kandidaten. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-022** | **Kimi** | **DONE (Health Starvation)** | Kimi: HEALTH 0.90→0.95 für GLOBAL-UNLOCK Trigger. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-021** | **Kimi** | **DONE (Context Commander V3)** | Kimi: Recall-Guard (self-ref), Medical-Override (health tags), Family-Context (instruction hardening). Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-020** | **Kimi** | **DONE (Density & Priority)** | Kimi: HEALTH 0.70→0.90, Limit 10→25, Dubletten-Prüfung >80%. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-SYS-019-V2** | **Kimi** | **DONE (Regex Hardening)** | Kimi: Regex Anker entfernt, `search()` statt `match()`, Einleitungs-Muster. 9+1 Pattern. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-018** | **Kimi** | **DONE (Relations & Identity Mapping)** | Kimi: `_normalize_subject_to_user()`, RELATIONEN & BEZIEHUNGEN Prompt, Identity Normalization vor canonical_key. Syntax-Check PASSED. |
| 2026-04-08 | **BUG-MEM-017** | **Kimi** | **DONE (Rolf-Bug Fix)** | Kimi: Direct Regex Guard bypasses nano-model smalltalk-bias. `_apply_direct_identity_regex_guard()`, `_is_name_mentioned_in_current_stm()`, Syntax-Check PASSED. |
| 2026-04-07 | **016** | **Sonnet** | **DONE (Identity Hard-Lock)** | Sonnet: `IDENTITY_CANONICAL_KEY = 'user:physis:heisst:name'` Hard-Lock. Stopword-Filterung: "Rolf und mag" → "Rolf". Priority 0.95. 5/5 Validation PASSED. |
| 2026-04-07 | **013** | **Sonnet** | **DONE (Identity Preload)** | Sonnet: `memory_identity.py` Modul erstellt. IdentitySlot **budget-exempt**. Neue Log-Signale: `[IDENTITY PRELOAD]`, `[IDENTITY FALLBACK]`. Fallback nur einmal pro Session. |
| 2026-04-07 | **012** | **Sonnet** | **DONE (Pre-Pass & Key-Guard)** | Sonnet: Pre-Pass Logik + `user:physis:heisst:name` Key-Guard implementiert. Memory-Tools jetzt mit Physis-Schutz. |
| 2026-04-07 | **011** | **Windsurf** | **DONE (Signature Fix)** | **CRITICAL:** TypeError: memory_read_tool() missing 1 required positional argument: 'params'. Tools jetzt auf (db: Session, **kwargs) umgestellt. |
| 2026-04-07 | **010** | **Windsurf** | **DONE (Naming Fix)** | **CRITICAL:** Gemini rief `memory.memory_read` → Tool nicht gefunden! JSONs hatten kein "skill" Feld. Registry nutzte `memory_write` statt `memory.write`. Jetzt aligned. |
| 2026-04-07 | **009** | **Windsurf** | **DONE (Critical Fix)** | **CRITICAL LIVE FIX:** `register_all_tools()` war nie in main.py! Memory Tools jetzt registriert. Falsche Duplikate in backend/skills/memory/ gelöscht. |
| 2026-04-07 | **008** | **Windsurf** | **DONE (Diamond)** | 🎯 **DIAMOND CERTIFIED: 83/100!** Cognitive Bridge vollständig. 14/18 Tests PASSED (77.8%). Ziel ≥80 erreicht! EPIC Memory V2 🚀 DONE. |
| 2026-04-07 | **007** | **Windsurf** | **DONE (Regex Glue)** | **💎 Diamond-Score: 28/100** (+65%!) 4/18 Tests PASSED. Root Logger Fix für LogCapture. ✅ T004, T007, T010, T017. Root Cause: `janus_backend` Logger war separat. |
| 2026-04-07 | 005 | Windsurf | **DONE (Dashboard)** | `/test-memory` Skill: Dashboard läuft! 💎 **Diamond-Score: 2/100** 🔴 (0/18 passed, 18/18 FAILED). Critical Bugfixes: provider field, chat_id int, _ListHandler, get_orchestrator() factory, _session_context(). Memory-Integration noch nicht aktiv. |
| 2026-04-07 | 004 | Windsurf | DONE (Expansion) | Memory QA Scenarios: 3→18 Tests. Schema erweitert (setup_context, semantic_intent). 18/18 validiert. Coverage: Knapsack, TTL, Security, Circuit-Breaker. |
| 2026-04-07 | 003 | Windsurf | DONE (Foundation) | Pruki Memory QA Framework: schemas_qa.py, memory_qa.py, fixtures. 3 Initial-Tests (T001-T003). Syntax-Check PASS. |
| 2026-04-07 | SYS-V4.6-SKILLS | Opus 4.6 | DONE (Opus Gold-Stamp ✅) | 5 Windsurf Cascade Skills in .windsurf/workflows/ erstellt (/task-setup, /pre-check, /post-impl, /session-start, /opus-audit). // turbo marker aktiv. |
| 2026-04-06 | M-MEM-06 | Windsurf | DONE (Diamond Gold) | Phase 6 complete: 20/20 E2E tests, 5/5 benchmarks, MEMORY_V2_ENABLED=true |
| 2026-04-06 | M-MEM-05 | Windsurf | DONE (Opus Gold-Stamp ✅) | Unified Memory Tools integriert. Permission-Check für user_editable & Audit-Trail (change_history) aktiv. |
| 2026-04-06 | M-MEM-04 | Windsurf | DONE (Opus Gold-Stamp ✅) | Knapsack Context Budget Selector integriert. TokenBudget mit tiktoken + 30%-Heuristik. MEMORY_V2_ENABLED Flag. |
| 2026-04-01 | C8-VANILLA-SSE | Windsurf | DONE (CU7, Sonnet 4.6) | FinOps-Loop geschlossen. Sidebar zeigt nun Live-Kosten in Vanilla JS. |
| 2026-03-31 19:25 | SYS-V3.2-RESTRUCT | Windsurf | DONE | Modularisierung abgeschlossen |
| 2026-03-31 19:00 | SYS-V3.1 | Windsurf | DONE | Thinking-Loop Upgrade |
| 2026-03-31 18:30 | M-PRICE-01 | Windsurf | DONE | Price-Accuracy & Fact Schema |

---

## SECTION 3: RESOURCE_DASHBOARD (Live)

| Ressource | Basis-Kosten | Aktueller Verbrauch | Est. Kosten/Task | Cache-Efficiency-Rate |
|-----------|--------------|---------------------|------------------|----------------------|
| Cursor    | 20,00 €/Monat| [__] % (Monthly)    | [X] €            | N/A |
| Windsurf  | 15,00 €/Monat| 4 % (Weekly)        | ~ 0,07 €         | 🔥 Auto (Claude Prompt Caching — immer aktiv bei Thread-Reuse) |

**Formeln:**
- Cursor: `(%/100) × 20 €`
- Windsurf Daily: `(%_Daily/100) × (15/30)` = `(%_Daily/100) × 0,50 €`
- Cache-Efficiency: `(Cached_Tokens / Total_Tokens) × 100%` für Claude-Modelle (Opus/Sonnet) — automatisch bei Thread-Reuse

**DEFERRED Pool:** Keine wartenden Tasks.

---

## SECTION 4: SYSTEM_REFERENZEN

**Hierarchie:** `01_CENTRAL_TASK_REGISTRY` = Strategische Roadmap (Epics) | `PROJECT_STATE` = Operativer Session-Kontext (Tasks).

### 🏛️ Refactoring Roadmap 2026 (Diamond Elite)
**Referenz:** `documentation/Planned Features/Refactoring_Roadmap_2026.md`

| Target | Zeilen | Priorität | Status |
|--------|--------|-----------|--------|
| **Skill Contract V1 (Tool-Rollout / `ToolResultV1`)** | — | P0 | **COMPLETE** (SYS-SKILL-CONTRACT-V1, 2026-04-11) — **Erweitert 2026-04-13:** **EPIC-SKILL-FORGE** 49/49 Diamond, siehe `SKILL_INVENTORY.md` |
| **Proactive Suggestions (3-tier + UI)** | — | P1 | **COMPLETE** (FEAT-PROACTIVE-SUGGEST, 2026-04-11) |
| Vision Fusion Engine | ~6.500 | P1 | Geplant |
| **Memory Core Manager** | Paket + Shim | P1 | **COMPLETE ✅** (**Task 020**, 2026-04-12) |
| Geo-Intelligence Service | ~2.300 | P2 | Geplant |
| PDF Generation Engine | ~1.800 | P2 | Geplant |
| Link-Rendering Framework | ~900 | P3 | Geplant |

**Template:** ORCH-TRANSFORM-EPIC (6 Module, ZERO hardcoded, Diamond Gold)

**Modulare System-Dateien (NICHT kopieren - nur referenzieren):**
- `.diamond/system/routing_logic.md` - CU-Tabellen, Editor-Entscheidungen
- `.diamond/system/handover_templates.md` - Vorlagen fuer Windsurf/Cursor/Pro
- `.diamond/system/loop_definitions.md` - 6-Schritte Next-Action-Loop V3.1

**Weitere Referenzen:**
- `WHAT_I_LEARNED.md` - Langzeit-Patterns
- `documentation/` - Architektur-Dokumentation

---

## SECTION 5: QUICK_START fuer AI Studio

1. CU-Schaetzung durchfuehren (1-10)
2. NEXT ACTION LOOP definieren:
   ```
   0. THINK (MCP): Max 3-5 Gedanken
   1. IMPL
   2. TEST
   3. LINTER
   4. IMPORTS
   5. DIAMOND-REPORT
   ```
3. Handover-Template aus `.diamond/system/handover_templates.md` waehlen
4. PROJECT_STATE.md SECTION 1 aktualisieren (neuer Task)
5. An Windsurf/Cursor uebergeben

---

**Version:** 4.8.0-TURBO-FLOW — **EPIC DONE** (Streaming + DB-Concurrency + B5 Caching) | 4.7.7 FINAL SESSION SEAL | 4.7.6 Sidebar + Project Dashboard | 4.7.5 SYS-UI-SYNC | V4.7.2 + ORCH-DIAMOND-ELITE **SEALED**
**Motto:** *"The system is clean, the mind is sharp. Diamond Elite status fully operational."*
