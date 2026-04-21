# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
und dieses Projekt folgt der [Semantic Versioning](https://semver.org/spec/v2.0.0.html) Richtlinie.

## [Unreleased]

## [0.4.16-beta.14] - 2026-04-21

### Fixed
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
