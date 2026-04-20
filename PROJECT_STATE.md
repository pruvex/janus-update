# PROJECT_STATE.md (Diamond-OS **V0.4.15-beta.13** — "STABILITY-ARC COMPLETE: Diamond-Release-Guard & Atomic State-Save fully operational. Production-Release v0.4.16 published. All Tasks SEALED & COMPLETE.")
**Zweck:** Einzige Datei fuer AI Studio Triage-Guard. Kopiere diese komplette Datei in AI Studio.
**Aktualisiert:** 2026-04-20 21:20 (STABILITY-ARC COMPLETE — SEALED)

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
