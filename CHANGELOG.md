# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
und dieses Projekt folgt der [Semantic Versioning](https://semver.org/spec/v2.0.0.html) Richtlinie.

## [Unreleased]

## [0.4.17-beta.22] - 2026-05-09

### Fixed
- **BACKLOG-017:** ChromaDB-Module fehlen im PyInstaller-Bundle. PyInstaller spec um ChromaDB-Submodule erweitert: `collect_data_files('chromadb')`, `collect_data_files('chromadb', include_py_files=True)`, `hiddenimports=['chromadb.telemetry.product.posthog', 'chromadb.api.rust']`. Vektor-Service und Skill-Router starten ohne ChromaDB-Import-Fehler. Manual Janus Test PASS. Files: `janus_backend.spec`. Version: 0.4.17-beta.22.

## [0.4.17-beta.21] - 2026-05-09

### Fixed
- **BACKLOG-018:** CLIP-Model-Download blockiert nicht mehr First-Start. Lazy-Loading Pattern implementiert: CLIP-Model (338MB, ViT-B-32.pt) wird asynchron im Hintergrund nach App-Start geladen via Daemon-Thread in FastAPI-Lifespan. Vision-Service prüft `model_loader.is_ready()` vor CLIP-Inference und überspringt bei `False`. App startet sofort auf allen Systemen unabhängig von Internetgeschwindigkeit. Files: `backend/services/vision/model_loader.py` (NEU), `backend/services/vision_service.py` (MODIFIZIERT), `backend/main.py` (MODIFIZIERT). Manual Janus Test PASS.

## [0.4.17-beta.20] - 2026-05-08

### Fixed
- **BACKLOG-016:** Video-Links funktionieren jetzt nach Chat-Wechsel. IndentationError in `backend/data/crud.py` behoben (Zeile 111-112). `video_list_metadata` wird jetzt korrekt in `metadata_json` persistiert. Persistenzpfad vollständig: Backend CRUD → Schemas → Frontend Reload → Rendering. `frontend/js/chat-manager.js` reicht `video_list_metadata` beim Chat-Reload durch. `frontend/js/chat.js` rendert Video-Links aus `video_list_metadata` nach Chat-Wechsel. Manual Janus Test PASS.

## [0.4.17-beta.19] - 2026-05-08

### Fixed
- **Task 030:** Video-Liste Chat-Wechsel Persistenz-Fix. Video-Details (Titel, Kanal, Views, Upload-Datum) werden jetzt korrekt nach einem Chat-Wechsel beibehalten. Sender-Bedingung erweitert auf "bot" || "model", appendVideoReopenLink Parameter videoListMetadata hinzugefügt, wireVideoReopenLink übergibt videoListMetadata an appendVideoReopenLink, appendMessage generiert Markdown mit Header (wie SSE-Stream) beim Chat-Reload. Backend-Logging hinzugefügt zur Verfolgung von video_list_metadata. max_results=3 → max_results=payload.max_results in video_tools.py.

## [0.4.17-beta.18] - 2026-05-08

### Fixed
- **BACKLOG-015:** Modell-Wechsel-Benachrichtigung verbessert. Klarere Kommunikation mit Titel "⚠️ Modell nicht verfügbar", Erklärung warum das Modell nicht verfügbar ist und dass automatisch gewechselt wurde. Handlungsoptionen: "Fallback behalten" und "Modell wählen" (öffnet Einstellungen). Verbessertes Design mit max-width, padding, border-radius, box-shadow. Längere Anzeigezeit (10 Sekunden). Provider-Wechsel-Probleme behoben: Keine falschen Fehlermeldungen mehr beim Provider-Wechsel, Dropdown nicht mehr leer. UX-Entscheidung: Kleinstes Modell beim Provider-Wechsel auswählen (sicherer, verhindert versehentliche Nutzung teurer Modelle).

## [0.4.17-beta.17] - 2026-05-07

### Fixed
- **BACKLOG-011:** Video-Modal False-Positive Fix + Gemini List-Mode Override. URL-Detection Fallback in `response_finalizer.py` deaktiviert, modal_request wird ausschließlich aus video.search tool_results abgeleitet. Zusätzlich Backend-Override in `tool_executor.py` erzwingt `mode="list"` für `video.search`, da Gemini den Schema-Default ignoriert und immer `"single"` setzt. Gemini zeigt jetzt mehrere Videos aufgelistet und das Modal öffnet automatisch mit dem ersten Video.

## [0.4.17-beta.16] - 2026-05-07

### Fixed
- **BACKLOG-010:** Deterministischer Tool-Loop Guard für Desktop Image Move. Nach `filesystem.create_directory` führt die Engine automatisch `filesystem.find_files` für *.jpg und *.png sowie `filesystem.move_files` aus, wenn das Ziel ein Desktop-Ordner ist. Provider-agnostisch (getestet mit gpt-5.4-nano und Gemini). Umgeht LLM-Instruction-Dependenz.

## [0.4.17-beta.15] - 2026-05-07

### Fixed
- **BACKLOG-009 (Partial):** Neue `path_resolution_hint` Direktive in `prompt_registry.py` hilft gpt-5.4-nano bei der Auflösung häufiger Windows-Pfade (desktop, documents, downloads, pictures). Pfad-Auflösung funktioniert jetzt ohne Rückfragen. Vollständige Ausführung der Filesystem-Operationen bleibt ein separates Problem (BACKLOG-010).

## [0.4.17-beta.14] - 2026-05-07

### Fixed
- **BACKLOG-008:** Filesystem-Intent blockiert jetzt RAG-Intent, um unnötige Logic-Tier-Upgrades bei reinen Dateisystem-Operationen zu verhindern. Filesystem-Operationen werden mit gpt-5.4-nano ausgeführt, ohne Upgrade auf gpt-5.4. Pfad-Auflösungs-Problem als separates BACKLOG-009 ausgelagert.

## [0.4.17-beta.13] - 2026-05-07

### Fixed
- **BACKLOG-005:** Filesystem-Intent hat jetzt Vorrang vor Bild-Intent bei gemischten Keywords. "Bilder" im Kontext von Dateisystem-Operationen wird korrekt als Filesystem-Intent erkannt, nicht als Bild-Intent. Skill-Descriptions für find_files und move_files verbessert für bessere Tool-Call-Effizienz.

## [0.4.17-beta.12] - 2026-05-07

### Fixed
- **BACKLOG-001:** Test-Dateien aus Projekt-Root nach tests/ verschoben (test_cluster_4.py, test_geometrie_check.py, test_logging_fix.py, test_openai_tools.py, test_face_root.jpg, test_personalities_root.json).
- **Security:** Hardcoded OpenAI API-Key aus tests/test_openai_tools.py entfernt. Test überspringt jetzt sauber, wenn OPENAI_API_KEY nicht gesetzt ist.
- **BACKLOG-003:** Alte Release-Installer aus release/ entfernt (janus-setup-0.4.17-beta.4.exe, janus-setup-0.4.17-beta.9.exe, janus-setup-0.4.17-beta.10.exe). Nur janus-setup-0.4.17-beta.11.exe verbleibt. ~1.46 GB Speicherplatz freigegeben.

## [0.4.17-beta.11] - 2026-05-05

### Added
- **UI:** Added real-time download progress and status indicators to the sidebar footer.

### Changed
- **UX:** Optimized update status messages for better readability in narrow sidebars.

## [0.4.17-beta.10] - 2026-05-05

### Fixed
- **Auto-Update:** Final bridge release with hardened multi-hash validation and atomic pipeline sync. This version is required for all future automatic updates.

## [0.4.17-beta.9] - 2026-05-05

### Changed
- **Auto-Update:** Hardened build pipeline to always perform a full rebuild of all components before release. Disabled differential downloads to increase update stability and prevent checksum mismatches.

## [0.4.17-beta.8] - 2026-05-05

### Fixed
- **Auto-Update:** Fixed a critical client-side validation bug where the updater only checked for SHA256 hashes, causing a HASH_MISMATCH when the server provided a SHA512 hash from latest.yml. The validator is now multi-hash-aware.

## [0.4.17-beta.7] - 2026-05-05

### Fixed
- **Auto-Update:** Hardened the release pipeline to use a single-source-of-truth for hashes, preventing future HASH_MISMATCH errors. The generate:update-manifest script now derives its hash from the latest.yml file generated by electron-builder.

## [0.4.17-beta.6] - 2026-05-05

### Fixed
- **System:** Fixed CDN caching and hash validation issues in the auto-update pipeline. (Clean slate version bump).

## [0.4.17-beta.5] - 2026-05-05

### Fixed
- **TASK-069.16: Update Error-Handling Scope** — Fixed ReferenceError in Electron main process update IPC handler by replacing undefined `win` variable with `mainWindow` and adding null check.
- **TASK-069.17-069.20: Release Manifest Integrity** — Hardened update-pipeline with atomic manifest generation, strict file existence checks, and fresh SHA256 calculation. Manifest now generated only after successful build.
- **TASK-069.21: Production Build Prep** — DevTools now open only when `NODE_ENV === 'development`. Version bumped to 0.4.17-beta.5 for final production build.

## [0.4.17-beta.4] - 2026-05-05

### Added
- **TASK-069: Capability Overview Response (SEALED)** — Deterministic answers to „Was kannst du?“ from `backend/data/capability_registry.json` via Help Fast-Path (no LLM): normalized intent triggers with casefold and trailing punctuation stripping (TASK-069.14), `get_verified_capabilities_for_overview()` with `verified` + `confidence ≥ 0.7`, fixed category order and „Sonstiges“ mapping, Markdown format `## Das kann ich aktuell`. Tests: unit `test_capability_registry_logic.py`, `test_intent_engine.py` (normalization hardening), integration help fast-path, Playwright `tests/e2e/capability-overview.spec.js` (button-click hardening). Audit: PASS WITH FIXES. Version: 0.4.17-beta.4.

## [0.4.17-beta.3] - 2026-05-04

### Fixed
- **Build Fix** — Added electron/**/* to build.files in package.json to include electron/update-manager.cjs, electron/update-state.cjs, and electron/update-security.cjs in the release artifact. This fixes "Cannot find module './electron/update-manager.cjs'" error in installed version.

## [0.4.17-beta.2] - 2026-05-04

### Added
- **TASK-068: Auto Update System (SEALED)** — Deterministic Auto Update System for Electron with state machine persistence, SHA256 manifest validation, secure IPC bridge, and state-driven UI. T1-T8 complete. Files: electron/update-state.cjs, electron/update-security.cjs, electron/update-manager.cjs, main.electron.cjs, frontend/preload.js, frontend/js/update-ui.js, frontend/js/app.js, frontend/css/update-ui.css, frontend/index.html, scripts/generate_update_manifest.cjs, documentation/release/auto_update_manifest_contract.md. Tests: Node unit tests (16 passed), Playwright E2E (7 passed). Version: 0.4.17-beta.2. Audit: PASS WITH FIXES.

### Fixed
- **E2E test validation** — Replaced inline-duplicated UI logic test with task-conformant .spec.js that tests the real app initialization and update-ui.js module.
- **ES Module import failure** — Added missing `export { initUpdateUI };` in frontend/js/update-ui.js to fix ES module import in app.js.
- **Test artifact in repo** — Changed update-state.test.cjs to use temporary directory instead of project root for janus-update-state.json.
- **Lockfile version outdated** — Synchronized package-lock.json root version fields to 0.4.17-beta.2 (were outdated at 0.4.14-beta.1).


## [0.4.17-beta.1] - 2026-05-04

### Added
- **TASK-066: Memory Context Bleed Prevention (SEALED)** — Threshold-Tuning for Memory-Retrieval: Raised minimum priority threshold from 0.50 to 0.65 in memory_budget.py (default priority) and crud_service.py (legacy_priority, enriched_priority) to reduce context bleed (irrelevant old entries in prompt). Improves response quality for small models like Gemini Flash. Files: memory_budget.py, crud_service.py. Tests: 28/28 passed.
- **TASK-064: Calendar Mutation Detection (SEALED)** — Breaking the Calendar Listing Prison. Added is_calendar_mutation detection to IntentEngineV2 to distinguish between pure calendar queries (listing) and calendar mutations (updates). When is_calendar_mutation is true, the system no longer forces calendar.list_events tool_choice, allowing the model to reach calendar.find_and_update_event for mutation operations. Files: intent_engine.py, execution_dispatcher.py. Tests: 486 passed.
- **TASK-063: Proactive Calendar Updates (SEALED)** — Proactive Calendar Updates implementation. Sharpened calendar update keywords in IntentEngineV2 ("bring", "ergänze", "ergänzen", "hinzufügen", "mit"). Added calendar.find_and_update_event as mandatory skill for calendar intents in CapabilityRegistry. Added proactive calendar mutation rule in prompt_registry.py to prioritize calendar updates over pure memory logging. Files: intent_engine.py, capability_registry.py, prompt_registry.py. Tests: 483 passed.
- **TASK-062: Intent-to-Selector Gap Fix (SEALED)** — Fixed Intent-to-Selector gap. Sharpened calendar keywords in IntentEngineV2 ("habe ich", "was habe ich", "was steht an", "steht an", "meine termine", "meinen termin", "meinen terminen"). Verified CapabilityRegistry returns calendar.list_events as mandatory for calendar intents. Added safety net in ExecutionDispatcher to inject calendar.list_events if is_calendar_intent is true but selector returned empty. Files: intent_engine.py, execution_dispatcher.py. Tests: 483 passed.
- **TASK-061: SkillSelector Intent-Aware (SEALED)** — SkillSelector is now Intent-Aware & Policy-Driven. Integration of IntentEngineV2 detection results into SkillSelector.get_relevant_skills() for intent-based skill filtering. File: chat_orchestrator.py (lines 1238, 1328). Tests: 479 passed.
- **TASK-060: Agent Planner Overhaul (Harmonized)** — Harmonisierung von AgentPlanner und SkillSelector mit IntentEngineV2 und CapabilityRegistry. Einführung von PlannerContext/PlannerProviderProfile für strukturierte Planner-Handoff, Kalender-Guard (forbidden_skill_ids) zum Entfernen inkompatibler Skills bei Kalender-Queries, 14-Tage Wochentag-Kalender zur Vermeidung von Datums-Schätzungen, CapabilityRegistry-Integration in OrchestratorExecutionEngine. Files: prompt_registry.py (calendar_read_priority VERBOTEN-Regeln), execution_dispatcher.py (Kalender-Guard), schemas.py (PlannerContext/PlannerProviderProfile), execution_engine.py (_build_planner_capability_groups, _build_planner_context, _build_planner_provider_profile), chat_orchestrator.py (capability_registry Initialisierung vor SkillSelector). Tests: 477 passed.
- **TASK-058: Calendar Modal (Phases 1-4 COMPLETE + Sync Hardening + Protocol Hardening)** — Calendar Modal mit Agenda/Day/Week Views, Inline Editing, AI Engine mit LLM-Integration, Delta-Sync, MCL/Dock Integration. Backend: REST-API (`GET/POST/PUT/DELETE /api/calendar/events`, `POST /api/calendar/ai/plan`), Service Layer mit Tool-Result Helper-Funktionen, AI Engine (provider-agnostisch via llm_gateway), deterministisches JSON-Parsing. Frontend: Timeline-Rendering (60px/hour), Optimistic UI mit Rollback, Filter (heute/Woche/Monat/Custom), Detail-Panel, AI Overlay mit Plan-Vorschau, Quick Actions, Polling (60s), Sync-Status-Indikator. 21/21 Tests grün.
- **Google Sync Hardening (TASK-058)** — Pagination (maxResults=250, pageToken-Loop) für vollständige Event-Listen. PATCH-with-Verify-and-Fallback für Metadaten-Updates mit CRLF-normalisiertem Textvergleich. conferenceDataVersion=1 für Meet-Termine mit Retry auf 0 bei 400-Fehlern. Output-Only-Key-Filterung (kind, etag, htmlLink, created, updated, hangoutLink, creator entfernt) vor PUT. Forensische Logging-Signale: organizer.self=false (unterschiedliches eingeladenes Konto), verify-mismatch (Ort/Beschreibung/Summary nach PATCH). Frontend: calendar-refresh CustomEvent nach createCalendarEvent, adaptive event cards (ultra-short/short/normal), detail panel with inline editing, duration buttons (15m/30m/1h/2h/3h), all-day checkbox, --cal-hour-height CSS variable (60px/hour) als Source-of-Truth. Pattern #GoogleCalendarSyncReliability in WHAT_I_LEARNED.md dokumentiert.
- **Protocol Hardening (TASK-058)** — #GeminiV3Protocol: thought_signature preservation in execution_engine.py via Raw-Parts retention. #GeminiNameSanitization: dot/underscore tolerance for tool names (system.weather ↔ system_weather) with reverse-mapping. #CalendarSnapshotIntegrity: invalidate_calendar_snapshot() after create/update/delete mutations, calendar_read_priority directive, CALENDAR-LIVE-TRUTH forced tool-call on calendar intent.

### Changed
- **Bulk File Move Feature** - Parameter-Upgrade (pattern → file_names), Intent-basierte Modell-Eskalation (MOA-Hierarchie), RAG-Sort-Policy, PDF-Indizierungs-Markierung in list_directory, Rate-Limits erhöht. Task FEAT-FS-BULK-MOVE.
- **Logging Pipeline Phase 1: Metadata Fixes** - Provider und Model werden jetzt konsistent an additional_context übergeben bei allen ToolExecutor-Instanziierungen. Logging zeigt korrekte Werte (nicht mehr "unknown"). ChatRequest-Attribut-Fix: req.chosen_model → req.model. Task D10.


## [0.4.16-beta.16] - 2026-04-21

### Fixed
- **Dead-Code-Fix: HARDWARE-TRUTH-REGEL + file_system_guard werden nun tatsächlich in den LLM-System-Prompt injiziert** — Root-Cause: `prompt_registry.py::search_command_priority` und `file_system_guard` waren definiert, aber nirgends injiziert. Der reale System-Prompt wird in `execution_dispatcher.py:190` via `apply_verbosity_control(wf.system_prompt_for_llm)` gebaut, welches bisher NUR `verbosity_control` + `no_meta_talk` anhängte. Resultat: Nano/Mini-Modelle beantworteten Datei-Such-Anfragen aus Memory-Fakten ohne Tool-Call, obwohl der User die HARDWARE-TRUTH-REGEL explizit angefordert hatte (im Log sichtbar: System-Prompt enthielt `PRIMÄRDIREKTIVE` + `🚨 SYSTEM-DIREKTIVE (STRIKTE KASKADE)` aus DB-Persönlichkeit, aber KEINE HARDWARE-TRUTH-REGEL). Fix: `apply_verbosity_control()` injiziert nun zusätzlich `file_system_guard` + `search_command_priority` (dedupliziert, idempotent). Damit erhält jeder DEFAULT-Dialog-Turn die Dubletten-Hinweis-Pflicht und die Live-Tool-Call-Pflicht für Such-Anfragen.

### Changed
- **Prompt-Registry: HARDWARE-TRUTH-REGEL für Suchanfragen verschärft** — `prompt_registry.py::search_command_priority` aktualisiert mit stärkerer Formulierung: "!!! WERKZEUGNUTZUNGS-DIREKTIVE — HARDWARE-TRUTH-REGEL !!! Wenn der Nutzer nach dem Verbleib, Speicherort oder der Existenz von Dateien sucht, hat das Live-Werkzeug filesystem.find_files ABSOLUTE Priorität vor der FAKTENGRUNDLAGE (Memory). Das Gedächtnis dient NUR als Orientierung. Du darfst NIEMALS einen Pfad aus der Erinnerung nennen, ohne ihn in EXAKT DIESEM Turn durch einen Tool-Call validiert zu haben. Eine Antwort ohne Live-Tool-Call bei Suchanfragen gilt als schwerer Systemfehler." Behebt "Brevity-Bias" bei faulen Modellen (wie Nano) mit strikterer "schwerer Systemfehler"-Formulierung.
- Version bumped to 0.4.16-beta.16.

## [0.4.16-beta.15] - 2026-04-21

## [0.4.16-beta.14] - 2026-04-21

### Fixed
- **Core-Repair: Numpy Shape Error im Memory-Retrieval** — `calculate_similarity_with_precomputed()` / `calculate_similarity_batch()` in `backend/services/vector_service.py` crashten regelmäßig mit `setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (N,) + inhomogeneous part` bei jedem Chat-Query. Ursache: `np.array(candidate_embeddings, dtype=float32)` bricht ab, sobald auch nur ein Memory-Slot ein `None`-Embedding oder eine abweichende Vektor-Dimension hat (kommt bei Slots ohne gecachtes Embedding oder Legacy-Embeddings anderer Modell-Versionen vor). Fix: Neuer Helper `_safe_stack_embeddings()` filtert invalide Einträge (None, falscher Shape, Dim-Mismatch, NaN) vor `np.stack`. Beide API-Funktionen behalten die Output-Länge bei (0.0-Padding an gefilterten Positionen), damit Caller-Alignment intakt bleibt. Bei gefilterten Einträgen wird ein WARNING mit Count + Query-Dim geloggt.
- **Core-Repair: SkillMetadata-Literal-Divergenz** — `schemas.py::SkillMetadata.sandbox_level` erlaubte nur `"unrestricted" | "workspace_only" | "read_only_fs"`, während **11 filesystem-Skill-Manifests** konsistent `"full"` nutzten. Pydantic validierte den Wert still nicht (tolerate-Loader-Pfad), aber jede zukünftige Strict-Validierung wäre gebrochen. Fix: `"full"` als valides Literal hinzugefügt (semantisch: volle FS-Rechte innerhalb der Path-Sentinel-Workspace-Grenze, distinkt von `"workspace_only"` oder `"read_only_fs"`).

### Changed
- **Prompt-Registry: Dubletten-Hinweis für Dateisuchen** — `prompt_registry.py::file_system_guard` erweitert mit expliziter Anweisung: Wenn ein Such-Tool (z.B. `filesystem.find_files`) mehrere Dateien mit identischem Namen an verschiedenen Orten findet, MUSST der LLM den Nutzer explizit auf diese Dubletten hinweisen (z.B. "Ich habe die Datei an 2 Stellen gefunden: ..."). Verbessert UX bei Duplikat-Erkennung.
- **find_files: max_results Default von 100 auf 20 gesenkt** — `filesystem_manager.py::find_files(max_results=20)` statt 100, um Fakten-Extraktion-Overhead nach Dateisuchen zu begrenzen. Bei 100 Pfaden würde Nano versuchen, jeden als separate "Langzeit-Fakt" zu speichern, was das System für Sekunden lähmt. 20 Treffer sind für die meisten Use-Cases ausreichend; bei Bedarf kann der User `search_all_drives=true` oder explizites `max_results` nutzen.
- Version bumped to 0.4.16-beta.14.
- **Core-Repair: Numpy Shape Error im Memory-Retrieval** — `calculate_similarity_with_precomputed()` / `calculate_similarity_batch()` in `backend/services/vector_service.py` crashten regelmäßig mit `setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (N,) + inhomogeneous part` bei jedem Chat-Query. Ursache: `np.array(candidate_embeddings, dtype=float32)` bricht ab, sobald auch nur ein Memory-Slot ein `None`-Embedding oder eine abweichende Vektor-Dimension hat (kommt bei Slots ohne gecachtes Embedding oder Legacy-Embeddings anderer Modell-Versionen vor). Fix: Neuer Helper `_safe_stack_embeddings()` filtert invalide Einträge (None, falscher Shape, Dim-Mismatch, NaN) vor `np.stack`. Beide API-Funktionen behalten die Output-Länge bei (0.0-Padding an gefilterten Positionen), damit Caller-Alignment intakt bleibt. Bei gefilterten Einträgen wird ein WARNING mit Count + Query-Dim geloggt.
- **Core-Repair: SkillMetadata-Literal-Divergenz** — `schemas.py::SkillMetadata.sandbox_level` erlaubte nur `"unrestricted" | "workspace_only" | "read_only_fs"`, während **11 filesystem-Skill-Manifests** konsistent `"full"` nutzten. Pydantic validierte den Wert still nicht (tolerate-Loader-Pfad), aber jede zukünftige Strict-Validierung wäre gebrochen. Fix: `"full"` als valides Literal hinzugefügt (semantisch: volle FS-Rechte innerhalb der Path-Sentinel-Workspace-Grenze, distinkt von `"workspace_only"` oder `"read_only_fs"`).

### Changed
- Version bumped to 0.4.16-beta.14.

## [0.4.16-beta.13] - 2026-04-21

### Added
- **Neuer Skill `filesystem.find_files`** — rekursive Dateisuche über alle freigegebenen Workspaces mit Auto-Escalation auf alle lokalen Laufwerke (C:\, D:\, E:\) bei ≤1 Treffer. Schließt die Lücke, dass Janus bei "wo finde ich datei xy?" bisher nichts finden konnte (vorhandene `list_directory` war non-rekursiv). Features: Glob-Pattern (`*.pdf`, `*gundula*`), Fuzzy-Substring-Fallback (reiner Name → `*name*`), Path-Sentinel-Schutz, Noise-Ordner-Skip (`Windows`, `Program Files`, `node_modules`, `.git`, `AppData`, etc.), Duplikat-Dedup via `existing`-Set, explizites `search_all_drives` für bewusste Opt-In-Suche, `auto_escalated`-Flag in Response.
- `_enumerate_local_drives()` Helper und `_ALL_DRIVES_EXCLUDE_DIRS` Noise-Liste in `backend/services/filesystem_manager.py`.
- `FindFilesArgs` Pydantic-Schema in `backend/data/schemas.py` mit LLM-Trigger-Hints für `search_all_drives` (User-Formulierungen "überall", "Duplikate", "ganzer Rechner").
- Skill-Manifest `backend/skills/filesystem/find_files.json` mit `latency_class: slow` und `max_calls_per_turn: 2`.

### Changed
- `backend/tool_registry.py`: `filesystem.find_files` in `fs_tools` registriert.
- Version bumped to 0.4.16-beta.13.

### Fixed
- Interne Robustheit bei rekursiver Suche: Umstieg von `Path.rglob` auf `os.walk` + `fnmatch` mit `onerror`-Callback, da `rglob` bei defekten Symlinks/unerreichbaren Desktop-Ordnern (`C:\Users\pruve\Desktop\kikitest.`) mit `FileNotFoundError` abbricht, statt einzelne Pfade zu überspringen.

## [0.4.16-beta.11] - 2026-04-21

### Fixed
- **Packaged UI komplett ungestyled auf Testsystemen** — Route-Kollision in `backend/main.py`: `/assets` war auf `backend/assets/` (Preview-Bilder) gemountet und hat damit Vite's gehashte Frontend-Bundles `/assets/index-*.{js,css}` aus `frontend/dist/assets/` mit 404 überschattet, sobald Electron aus `http://127.0.0.1:8001/` lädt. Fix: kollidierenden `/assets`-Mount entfernt, `/backend_assets` bleibt kanonisch für Preview-Bilder. (Keine Call-Sites in Projekt-Code betroffen.) Inline-Kommentar in `backend/main.py` verhindert Wiedereinführung.
- End-to-End verifiziert via direktem HTTP-Test am gebündelten `janus_backend.exe`: `/`, `/assets/index-*.js` und `/assets/index-*.css` liefern alle 200 mit korrektem Content-Type.

### Changed
- Version bumped to 0.4.16-beta.11

## [0.4.16-beta.10] - 2026-04-21

### Fixed
- **Leere `frontend/dist/assets/` in vorherigen Builds** — Vite-Build wurde neu ausgeführt, weil `dist/assets/` auf dem Build-System leer war, aber `dist/index.html` noch auf gehashte Asset-Dateinamen verwies. Folge in beta.9: installierter PyInstaller-Backend lieferte `index.html` aus, aber alle Asset-URLs liefen auf 404, UI wurde ungestyled gerendert. (Hinweis: Der eigentliche strukturelle Bug war erst in beta.11 behoben, siehe oben — beta.10 hat nur die leere `dist/assets/` repariert.)

### Changed
- Version bumped to 0.4.16-beta.10

## [0.4.15-beta.11] - 2026-04-20

### Fixed
- Clipboard IPC Fallback: navigator.clipboard.readText() durch window.electronAPI.readClipboard() ersetzt (Permission Denied Fix). main.electron.cjs: ipcMain.handle('clipboard:read') und ipcMain.handle('read-clipboard') implementiert; preload.js: window.electronAPI exponiert.
- YouTube Error 152-4 Regression: Referer/Origin Spoofing aus onBeforeSendHeaders entfernt (YouTube blockiert als Bot bei Mismatch). onHeadersReceived für X-Frame-Options/CSP-Stripping intakt gelassen.
- Permission Handlers: setPermissionCheckHandler und setPermissionRequestHandler erweitert mit console.log Visibility, file:// Origin Bypass und allowedPermissions Array.
- frontend/js/video-player.js: YouTube Embed URL auf youtube-nocookie.com ohne enablejsapi und origin Parameter geändert.

### Changed
- Version bumped to 0.4.15-beta.11

## [0.4.15-beta.10] - 2026-04-20

### Fixed
- YouTube Error 152-4 Fix: Hardcoded `origin=https://www.youtube.com` URL-Parameter aus `normalizeVideoEmbedUrl()` entfernt. Unter sandboxed Electron-Renderer (file:// Origin) führte die Diskrepanz zwischen deklariertem Origin-Param und tatsächlichem postMessage-Origin zum YouTube-Player-Abbruch (Fehlercode 152-4) für alle Videos. Nach Entfernung fällt die Origin-Validierung weg und Playback funktioniert.

### Changed
- Version bumped to 0.4.15-beta.10

## [0.4.15-beta.9] - 2026-04-20

### Fixed
- YouTube Embedding Session Fix: webRequest-Handler von session.defaultSession auf mainWindow.webContents.session umgestellt. Das mainWindow verwendet eine separate session, daher müssen die Header-Spoofing und CSP-Stripping Handler auf der korrekten session registriert werden.

### Changed
- Version bumped to 0.4.15-beta.9

## [0.4.15-beta.8] - 2026-04-20

### Fixed
- Electron Boot-Fix: TypeError in webRequest-Handler behoben. Umstellung von 3-Argumente-Syntax auf 2-Argumente-Syntax (filter, listener) für onBeforeSendHeaders/onHeadersReceived. Die installierte Electron-Version akzeptiert kein extraHeaders-Array als zweiten Parameter.

### Changed
- Version bumped to 0.4.15-beta.8

## [0.4.15-beta.7] - 2026-04-19

**Security & Beta-Readiness Release** — XSS & RCE Fixes verifiziert, Discord-Reporting-System implementiert, YouTube-Playback-Stabilität gehärtet

### Fixed
- Chromium Extra Headers Fix: Aktivierung von extraHeaders Flag in onBeforeSendHeaders und onHeadersReceived zur Aufhebung der Chromium-Blockade von Referer-Manipulationen. Behebung von YouTube Error 15-4 / 153.

### Changed
- Version bumped to 0.4.15-beta.7


## [0.4.15-beta.6] - 2026-04-19

### Fixed
- Browser Identity Spoofing: Browser-Spoofing Pattern (User-Agent Maskierung auf App- und Window-Ebene zur Umgehung von Bot-Blockaden), youtube-nocookie.com Header-Synchronisation

### Changed
- Version bumped to 0.4.15-beta.6


## [0.4.15-beta.5] - 2026-04-19

### Fixed
- CSP Bypass & iFrame Hardening: Header-Deletion-Pattern (radikales Entfernen von CSP-Headern), allowRunningInsecureContent, Permission Handlers (media/display-capture), Autoplay CSP Modification for file:// paths
- YouTube Error 152: YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling for file:// paths
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.5


## [0.4.15-beta.4] - 2026-04-19

### Fixed
- YouTube Error 152: YouTube-Nocookie Transition, Header-Stripping (X-Frame-Options), Cross-Domain Spoofing (googlevideo.com), PreloadMediaEngagementData Disabling for file:// paths
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.4


## [0.4.15-beta.3] - 2026-04-19

### Fixed
- YouTube Error 153: Added protocol.registerSchemesAsPrivileged and Referer/Origin header spoofing for youtube.com requests in main.electron.cjs
- Orchestrator Synthesis-Bypass: Hard-lock immediate return when is_final_response=True to prevent synthesis in execution_engine.py

### Changed
- Version bumped to 0.4.15-beta.3


## [0.4.15-beta.2] - 2026-04-19

### Added
- Beta-Ready Final Polish: Feedback-Plug-and-Play with Discord webhook fallback, Video-Stability-Fix (is_final_response=True for all modes), Tiktoken-Resilience for compiled environments
- DEFAULT_FEEDBACK_WEBHOOK constant in telemetry_service.py for out-of-the-box bug reporting
- Tiktoken fallback (len(text) // 4) in tts_service.py and context_manager.py for environments without C library

### Changed
- Version bumped to 0.4.15-beta.2
- is_final_response=True set for all successful video searches (single and list modes)


## [0.4.15-beta.1] - 2026-04-19

### Security
- XSS Shield via DOMPurify with whitelists for Chat, Release-Notes, and Error messages (SEC-01/02)
- RCE Prevention in IPC handler with path normalization, whitelists, and extension blocklist (SEC-03)
- JWT Vault Security with dynamic secret generation and persistence (SEC-05)
- Chained Vulnerability Fix: userData removed from allowedRoots to prevent config.json overwrite (SEC-03.1)
- DOMPurify data: schema removed from iframe URI whitelist (only https: allowed)

### Added
- Beta-Reporting System with Feedback button, MCL-compliant modal, and Discord webhook integration
- Log file path fix for telemetry service (AppData directory instead of hardcoded path)
- Modal layering fix (z-index 9999999 with inline styles)

### Changed
- Version bumped to 0.4.15-beta.1


## [0.4.14-beta.1] - 2026-04-19

### Bugfixes
- Datenbank-Migration für chats.auto_added und memories.source_type hinzugefügt

## [0.4.13-beta.1] - 2026-04-19

### Bugfixes
- Download-Timeout auf 10 Minuten erhöht (von 120s Standard)
- GitHub API User-Agent und fullChangelog hinzugefügt

## [0.4.12-beta.1] - 2026-04-19

### Bugfixes
- CLIP Datei bpe_simple_vocab_16e6.txt.gz wird jetzt aus backend/assets in clip-Verzeichnis kopiert (Runtime-Fix)

## [0.4.11-beta.1] - 2026-04-19

### Bugfixes
- Update-Check Timeout (10s) hinzugefügt - App startet weiter, wenn GitHub API nicht antwortet
- Splashscreen zeigt Update-Status an (Prüfe auf Updates, Lade Update, Installiere)

## [0.4.10-beta.1] - 2026-04-19

### Bugfixes
- CLIP Datei bpe_simple_vocab_16e6.txt.gz Pfad korrigiert (direkte Datei statt Ordner)

## [0.4.9-beta.1] - 2026-04-19

### Bugfixes
- CLIP Daten-Dateien manuell zu PyInstaller Build hinzugefügt (collect_data_files hat nicht funktioniert)

## [0.4.8-beta.1] - 2026-04-19

### Bugfixes
- CLIP Daten-Dateien (bpe_simple_vocab_16e6.txt.gz) zu PyInstaller Build hinzugefügt

## [0.4.7-beta.1] - 2026-04-19

### Bugfixes
- Entfernung von face_recognition Import (nicht verwendet, verursachte Crash bei 0.4.3-beta.1)
- electron-updater jetzt auf App-Start ausgeführt (vor Backend-Start) - verhindert Deadlock bei kritischen Fehlern
- Release-Notes jetzt automatisch auf GitHub veröffentlicht
- torchvision nicht mehr ausgeschlossen (wird von CLIP benötigt)

## [0.4.3-beta.1] - 2026-04-19

### Implementation
- Auslagerung der Meta-Noise-Logik in `memory/utils.py` zur Behebung von Circular Imports
- Implementierung des Retrieval-Filters (Silence Guard) für alle Slot-Sektionen
- System-Prompt gehärtet via `silent_memory_rule`
