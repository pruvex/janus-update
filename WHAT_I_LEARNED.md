# KNOWLEDGE BASE: WHAT I LEARNED
**Zweck:** Langzeitgedächtnis für AI Studio, Cursor und Windsurf.
**Regel:** Jeder gelöste Bug darf nur EINMAL gelöst werden.

## [LESSON] #LLM #Gemini #ToolResponse "Structured Dict for FunctionResponse — NEVER pass JSON-string as content wrapper"
- **Kontext:** Der Gemini-Provider (`backend/llm_providers/gemini/service.py`) übersetzt OpenAI-kompatible Tool-Messages (`role: "tool"`) in `protos.FunctionResponse`. Die `content`-Felder in unseren Tool-Results sind historisch **JSON-Strings** (`'{"status":"ok","data":{"contents":[...]}}'`), weil die Executor-Schicht alles uniform serialisiert.
- **Problem:** Beim ersten Versuch wurde schlicht `response={"content": message.get("content")}` an `protos.FunctionResponse` übergeben. Gemini bekam also ein Dict, dessen einziger Wert ein undurchsichtiger JSON-String ist. Gemini interpretierte das **nicht** als "Tool hat Daten geliefert" — im zweiten Roundtrip rief Gemini dasselbe Tool mit identischen Args erneut auf. Der `HARD-LOOP-BREAKER` im Orchestrator blockte den Duplicate-Call → Gemini halluzinierte eine irrelevante Antwort ("Das PDF ist in Ihrer Dokumentenliste verfügbar."). OpenAI war davon nie betroffen, weil OpenAI JSON-Strings im `content`-Feld tolerant parst.
- **Lösung:** Tool-Content vor dem Einhängen in `protos.FunctionResponse.response` deserialisieren. Gemini sieht dann die **reale Struktur** (`contents`, `count`, `path`, …) und erkennt den Tool-Call als abgeschlossen:
  ```python
  raw_content = message.get("content")
  if isinstance(raw_content, dict):
      parsed_response = raw_content
  else:
      try:
          parsed_response = json.loads(str(raw_content))
          if not isinstance(parsed_response, dict):
              parsed_response = {"content": parsed_response}
      except Exception:
          parsed_response = {"content": str(raw_content) if raw_content is not None else ""}

  gemini_history_for_api.append({
      "role": "user",
      "parts": [protos.Part(function_response=protos.FunctionResponse(
          name=final_name,
          response=parsed_response,
      ))],
  })
  ```
  Fallback auf `{"content": "<string>"}` nur, wenn der Inhalt nicht parsbar ist — so bleibt das Verhalten für non-JSON-Tools stabil.
- **Regressions-Guard:** Symmetrisch in **beiden** Pfaden nötig (Sync: `_gemini_generate_response`, Stream: `_gemini_stream_build_request`). Wer nur einen Pfad fixt, merkt es erst in Produktion.
- **Tripwire:** Symptom ist spezifisch — `HARD-LOOP-BREAKER` Log-Eintrag + Output-Token-Zahl deutlich niedriger (Re-Call) + halluzinierte Antwort ohne Bezug zur User-Frage. Wenn man nur die UI-Antwort sieht, wirkt es wie ein reines Prompting-Problem — der Log entlarvt es.
- **Erkennungssignatur im Log:**
  ```
  [HARD-LOOP-BREAKER] BLOCKED duplicate tool call: filesystem.<x>
  ```
  in Kombination mit einem **vorherigen** erfolgreichen `TOOL CALL RESULT` für dasselbe Tool+Args → eindeutig dieser Bug.
- **Location:** `backend/llm_providers/gemini/service.py` (Sync ~Z. 373-398, Stream ~Z. 683-710), gefixt 2026-04-21
- **Confidence:** High (Live-Run Chat 52 mit `C:\test2` grün, 7 Dateien korrekt enumeriert, kein Loop-Breaker-Trigger)
- **Tags:** Gemini, ToolResponse, FunctionResponse, LLM, Provider, LoopBreaker, JSON, Envelope

## [LESSON] #FastAPI #StaticFiles #MountOrder "Silent Mount-Prefix Shadowing"
- **Kontext:** Janus-Backend mountet in `backend/main.py` sowohl Backend-Preview-Bilder (`/assets` → `backend/assets/`) als auch Frontend-Bundles (`/` → `frontend/dist/`, mit `html=True`). Vite-Production-Builds emittieren gehashte JS/CSS nach `frontend/dist/assets/index-*.{js,css}`, d.h. Asset-URLs auf dem Client lauten `/assets/index-*.js`.
- **Problem:** Das frühere `/assets`-Mount fängt ALLES unterhalb seines Präfixes ab — inklusive `/assets/index-*.js` — und gibt 404, weil die Dateien nicht in `backend/assets/` liegen. Im packaged Build (Electron lädt aus `http://127.0.0.1:8001/`) werden CSS/JS dadurch unsichtbar geshadowed → UI rendert komplett ohne Styles. In Dev unsichtbar, weil Vite-Dev-Server (Port 5173) das Backend-Mount-Layout nicht verwendet.
- **Lösung:** Kollidierende Präfixe zwischen Backend-Previews und Vite-Build-Assets eliminieren. Entweder Backend-Previews auf einen eigenen Pfad (z.B. `/backend_assets/` oder `/previews/`) verschieben, oder den Vite-Output in ein anderes Verzeichnis (`build.assetsDir`) umleiten. In dieser Codebase: `/assets`-Mount entfernt (war Duplikat zu `/backend_assets`).
  ```python
  # NICHT machen — shadowed Vite-Bundles:
  # app.mount("/assets", StaticFiles(directory="backend/assets"))
  app.mount("/backend_assets", StaticFiles(directory="backend/assets"))
  # ... später:
  app.mount("/", StaticFiles(directory="frontend/dist", html=True))
  ```
- **Regressions-Guard:** Inline-Kommentar direkt an der Mount-Stelle, der erklärt WARUM `/assets` nicht zurückkommen darf. Zusätzlich: Verifikation im Build-Flow durch direkten HTTP-Call an das gebündelte `janus_backend.exe` mit einer expliziten Prüfung auf `/assets/index-*.{js,css}` → 200.
- **Tripwire:** Bug wurde erst sichtbar, nachdem Electron die Lade-Strategie von `file://` / `janus://` auf `http://127.0.0.1:8001/` umgestellt hatte (YouTube-Error-153 Mitigation, v0.4.16-beta.9). Vorher kamen Asset-URLs nie durch das Backend. **Lektion:** Bei Architektur-Switches immer das Mount-/Routing-Layout auf Präfix-Kollisionen mit neu relevant werdenden Clients prüfen.
- **Location:** `backend/main.py` (ehemals Zeile 510), behoben in v0.4.16-beta.11
- **Confidence:** High (vor-/nach-verifiziert via HTTP-Smoke-Test am packaged Build)
- **Tags:** FastAPI, StaticFiles, MountOrder, Vite, Packaging, Electron, Regression

## [PATTERN] #Electron #BrowserSpoofing "The Identity Cloak"
- **Kontext:** Electron-Apps werden oft von YouTube und anderen Plattformen blockiert (Fehler 152), weil der User-Agent auf "Electron" oder eine nicht-standardisierte Zeichenfolge zeigt, die als Bot/Scraper erkannt wird.
- **Problem:** YouTube erkennt Electron-Apps als nicht-legitime Browser und blockiert iFrame-Embedding aus file:// Pfaden oder unsicheren Origins. Header-Spoofing allein reicht nicht aus, wenn der User-Agent selbst verdächtig ist.
- **Lösung:** **Browser-Spoofing Pattern** — Maskierung des User-Agents auf drei Ebenen:
  1. **App-Ebene:** `app.userAgentFallback` auf aktuellen Chrome String setzen
  2. **Window-Ebene:** `userAgent` in BrowserWindow Optionen auf Chrome String setzen
  3. **Header-Ebene:** `User-Agent` Header in onBeforeSendHeaders explizit setzen
  4. **Header-Synchronisation:** youtube-nocookie.com zu onBeforeSendHeaders/onHeadersReceived URL-Filtern hinzufügen
  - Chrome String: `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36`
- **Ergebnis:** Janus wird als legitimer Chrome Browser erkannt, Bot-Blockaden werden umgangen, YouTube Fehler 152 behoben.
- **Location:** `main.electron.cjs` (Zeile 30, Zeile 559, Zeile 570)
- **Confidence:** High (Task 051)
- **Tags:** BrowserSpoofing, IdentityCloak, UserAgent, Electron, YouTube, Task051

## [PATTERN] #Security #Coherence "Self-Healing Identity V2"
- **Kontext:** Chat-Orchestrator korrigiert den Provider automatisch basierend auf dem Modell-Präfix (z.B. `gpt-4` → `openai`, `gemini-pro` → `gemini`). Wenn der Provider korrigiert wird, muss auch der API-Key für den NEUEN Provider geladen werden.
- **Problem:** Wenn `request.provider` von `gemini` auf `openai` korrigiert wird, aber der API-Key nicht aktualisiert wird, wird der Gemini-Key an die OpenAI-API gesendet → 401 Unauthorized.
- **Lösung:** **Provider-Korrektur MUSS Key-Refresh triggern** — Nach der Provider-Korrektur IMMER den API-Key aus dem Keyring für den ZIEL-Provider neu laden:
  ```javascript
  if detected_provider and detected_provider != provider:
      ctx.request.provider = detected_provider
      # CRITICAL: Always reload key for NEW provider
      new_api_key = keyring.get_password('Janus-Projekt', detected_provider)
      if new_api_key:
          ctx.request.api_key = new_api_key
          logger.info("[AUTH-COHERENCE] Loading key for %s: %s...", detected_provider, new_api_key[:4])
  ```
- **Ergebnis:** Auth-Kohärenz wird gewährleistet — Provider und API-Key sind immer synchron. 401-Fehler durch falsche Keys werden vermieden.
- **Location:** `backend/services/chat_orchestrator.py` (Zeilen 1649-1675)
- **Confidence:** High (Task 052)
- **Tags:** Security, Coherence, Auth, Provider, Keyring, Task052

## [LESSON] #Electron #WebRequest #API "Electron WebRequest API Versioning"
- **Kontext:** YouTube-Embedding in Electron-App erfordert webRequest-Handler für Referer/Origin-Spoofing und Header-Stripping (X-Frame-Options, CSP).
- **Problem:** Die 3-Argumente-Syntax `onBeforeSendHeaders(filter, optionsArray, callback)` mit `['blocking', 'requestHeaders', 'extraHeaders']` führt zu `TypeError: Must pass null or a Function` in der installierten Electron-Version. Electron erwartet entweder 2 Argumente (filter, listener) oder der zweite Parameter muss null/Funktion sein, kein Array.
- **Lösung:** **2-Argumente-Form (filter, listener) verwenden** — die einzige stabile Form für diese Codebase:
  ```javascript
  session.defaultSession.webRequest.onBeforeSendHeaders(
    filter,
    (details, callback) => {
      details.requestHeaders['Referer'] = 'https://www.youtube.com/';
      callback({ cancel: false, requestHeaders: details.requestHeaders });
    }
  );
  ```
  `extraHeaders` wird in modernen Electron-Versionen automatisch aktiviert, wenn Header modifiziert werden. Die 3-Argumente-Form ist nicht kompatibel mit älteren Electron-Versionen.
- **Location:** `main.electron.cjs` (Zeilen 577-607)
- **Confidence:** High (Boot-Fix 2026-04-20)
- **Tags:** Electron, WebRequest, API, Versioning, TypeError, BootFix

## [LESSON] #Electron #Session #YouTube "YouTube Session Scope Fix"
- **Kontext:** YouTube-Embedding in Electron-App erfordert webRequest-Handler für Referer/Origin-Spoofing und Header-Stripping. Der Boot-Fix korrigierte die API-Syntax, aber Videos wurden immer noch nicht angezeigt.
- **Problem:** webRequest-Handler wurden auf `session.defaultSession` registriert, aber das mainWindow verwendet eine separate session (`mainWindow.webContents.session`). Die Header-Spoofing und CSP-Stripping Handler wurden daher nicht für die mainWindow-Requests ausgeführt.
- **Lösung:** **webRequest-Handler auf mainWindow.webContents.session registrieren** statt auf session.defaultSession:
  ```javascript
  mainWindow.webContents.session.webRequest.onBeforeSendHeaders(
    filter,
    (details, callback) => {
      details.requestHeaders['Referer'] = 'https://www.youtube.com/';
      details.requestHeaders['Origin'] = 'https://www.youtube.com';
      callback({ cancel: false, requestHeaders: details.requestHeaders });
    }
  );
  ```
  Das gleiche gilt für `onHeadersReceived`. Die permission-Handler (`setPermissionCheckHandler`, `setPermissionRequestHandler`) waren bereits korrekt auf der mainWindow session.
- **Location:** `main.electron.cjs` (Zeilen 578-605)
- **Confidence:** High (Session-Fix 2026-04-20)
- **Tags:** Electron, Session, YouTube, WebRequest, Scope, HeaderSpoofing

## [LESSON] #Electron #API #Stability "Die 3-Argumente-Falle"
- **Kontext:** Die 3-Argumente-Form von webRequest-Handler (filter, optionsArray, callback) mit `['blocking', 'requestHeaders', 'extraHeaders']` ist in neueren Electron-Dokumentationen dokumentiert.
- **Problem:** In bestimmten Electron-Versionen (z.B. installierte Version im Projekt) löst die 3-Argumente-Form einen fatalen `TypeError: Must pass null or a Function` aus. Die API-Signatur ist nicht abwärtskompatibel — der zweite Parameter muss null oder eine Funktion sein, kein Array.
- **Lösung:** **Die 2-Argumente-Form (filter, listener) ist der robuste Diamond-Standard**:
  ```javascript
  mainWindow.webContents.session.webRequest.onBeforeSendHeaders(
    filter,
    (details, callback) => {
      details.requestHeaders['Referer'] = 'https://www.youtube.com/';
      callback({ cancel: false, requestHeaders: details.requestHeaders });
    }
  );
  ```
  `extraHeaders` wird in modernen Electron-Versionen automatisch aktiviert, wenn Header modifiziert werden. Die 2-Argumente-Form ist universell kompatibel.
- **Location:** `main.electron.cjs` (Zeilen 578-605)
- **Confidence:** High (Boot-Fix + Session-Fix 2026-04-20)
- **Tags:** Electron, API, Stability, WebRequest, TypeError, 2ArgumentStandard

## [PATTERN] #YouTube #Embedding "YouTube Embedding Stability Triad"
- **Kontext:** YouTube-Videos in Electron-Apps einbetten über iFrame ist anfällig für Blockaden (Fehler 152, 153, 152-4) durch Bot-Erkennung, CSP-Header und Origin-Mismatches.
- **Problem:** Einzelne Maßnahmen (z.B. nur Domain-Wechsel zu youtube-nocookie.com) reichen nicht aus — YouTube blockiert weiterhin über verschiedene Mechanismen (User-Agent, Referer, X-Frame-Options, CSP).
- **Lösung:** **Dreiklang aus drei Maßnahmen im Main-Prozess**:
  1. **Domain-Wechsel auf nocookie:** `youtube.com` → `youtube-nocookie.com` (weniger strikte Tracking-Blockaden)
  2. **Header-Spoofing (Referer/Origin):** `onBeforeSendHeaders` manipuliert `Referer` und `Origin` auf `https://www.youtube.com` um Bot-Erkennung zu umgehen
  3. **Header-Stripping im Main-Prozess:** `onHeadersReceived` entfernt `X-Frame-Options`, `Content-Security-Policy`, `X-XSS-Protection` aus YouTube-Antworten um iFrame-Embedding zu erlauben
- **Zusätzlich:** User-Agent Spoofing auf Chrome 124 auf App- und Window-Ebene, sowie Permission-Handler für media/display-capture.
- **Location:** `main.electron.cjs` (Zeilen 530-605), `frontend/js/video-player.js` (normalizeVideoEmbedUrl)
- **Confidence:** High (EPIC-BETA-READY + EPIC-SECURITY-AUDIT 2026-04-20)
- **Tags:** YouTube, Embedding, HeaderSpoofing, CSPStripping, UserAgent, Electron, StabilityTriad

## [PATTERN] #Security #Chaining "Security Chaining — Warum sich Einzellösungen gegenseitig aufheben können"
- **Kontext:** SEC-03 (RCE Prevention in IPC) und SEC-05 (JWT Vault Security) wurden als isolierte Fixes implementiert. SEC-03 erlaubte Schreiben in userData-Verzeichnis, SEC-05 persistierte JWT-Secret in config.json im userData-Verzeichnis.
- **Problem:** Die beiden Fixes heben sich gegenseitig auf. Ein Angreifer, der über SEC-03-Bypass (z.B. XSS → Renderer-Kompromittierung) IPC-Kontrolle erlangt, kann über den `save-file-in-path` Handler die `config.json` mit einem selbstgewählten JWT-Secret überschreiben. Nach dem nächsten Backend-Neustart lädt `_get_or_generate_jwt_secret()` den manipulierten Secret — der Angreifer kann beliebige valide JWTs signieren und den kompletten Auth-Layer umgehen.
- **Lösung:** **Scope-Trennung (Option B empfohlen):** Entferne `userData` komplett aus der `allowedRoots`-Whitelist des `save-file-in-path` Handlers. Der Handler ist für User-Assets (PDFs, Bilder) gedacht, nicht für App-Config. Zusätzliche Extension-Blockliste (.json, .db, .key, .pem) als Defense-in-Depth.
- **Ergebnis:** Chained Vulnerability eliminiert. App-Config ist nicht mehr über den IPC-Channel erreichbar.
- **Location:** `main.electron.cjs` (save-file-in-path Handler, Zeilen 802-871), `backend/dependencies.py` (_get_or_generate_jwt_secret)
- **Confidence:** High (EPIC-SECURITY-AUDIT Chained Fix)
- **Tags:** SecurityChaining, ScopeSeparation, IPCSecurity, JWTVault, SEC-03, SEC-05

## [PATTERN] #Architecture #Dependency "The Leaf-Utility Strategy"
- **Problem:** Circular Imports entstehen oft, wenn High-Level Services (Extractor) kleine Hilfsfunktionen enthalten, die von Low-Level Services (Retrieval) benötigt werden.
- **Lösung:** Extrahiere reine Logik-Hilfsfunktionen und Konstanten in eine `utils.py` oder `constants.py` am "Blatt" der Abhängigkeits-Hierarchie. Diese Datei darf selbst keine anderen internen Services importieren.
- **Kontext:** BUG-MEM-038 (Meta-Noise Filter) wurde von `memory_extractor.py` nach `memory/utils.py` verschoben, um den Import-Kreislauf mit `retrieval_service.py` zu durchbrechen.
- **Location:** `backend/services/memory/utils.py` (neu), `backend/services/memory_extractor.py`, `backend/services/memory/retrieval_service.py`
- **Confidence:** High (BUG-MEM-038 Circular Import Fix)
- **Tags:** CircularImport, DependencyManagement, UtilsExtraction, BUG-MEM-038

## [PATTERN] #Memory #Hygiene "The Retrieval-Noise-Shield"
- **Kontext:** Selbst wenn die Datenbank "verschmutzt" ist (z.B. durch alte Meta-Anweisungen), darf dies die KI-Antwort nicht korrumpieren.
- **Lösung:** Wende Filter-Logik (`_is_meta_noise`) nicht nur beim Schreiben (Ingestion), sondern konsequent bei jedem Lesevorgang (Retrieval) an. Dies garantiert einen sauberen LLM-Kontext, unabhängig vom DB-Zustand.
- **Location:** `backend/services/memory/retrieval_service.py` (alle Slot-Sektionen: Cache, High-Prio, Health, Global, Ephemeral, STM), `backend/services/orchestrator/prompt_registry.py` (`silent_memory_rule`)
- **Confidence:** High (BUG-MEM-038 Context Silence Guard)
- **Tags:** MemoryHygiene, RetrievalFilter, MetaNoise, ContextSilence, BUG-MEM-038

## [PATTERN] #Orchestration #Sync "Preemptive Provider Alignment"
- **Kontext:** Backend validiert request.provider gegen den model_catalog und korrigiert bei Drift automatisch vor dem Call (z.B. GPT-Modell an Gemini-Provider).
- **Problem:** PROVIDER-MODEL-MISMATCH Fehler entstehen, wenn request.model zu einem anderen Provider gehört als request.provider (z.B. GPT-5.4 an Gemini-Provider). Dies führt zu 400er Fehlern bei Video-Queries und ungültigen Gateway-Calls.
- **Lösung:** Präventiver Provider-Check in ChatOrchestrator._execute_generation VOR dem Gateway-Call. Erkennt Provider aus Model-Präfix (gpt- → openai, gemini- → gemini, claude- → anthropic, :/llama/llava → ollama) und korrigiert request.provider automatisch bei Mismatch.
- **Ergebnis:** PROVIDER-MODEL-MISMATCH wird präventiv verhindert. Provider-Coherence garantiert vor dem ersten API-Call.
- **Location:** `backend/services/chat_orchestrator.py` (_execute_generation, lines 1513-1539)
- **Confidence:** High (Task 034)
- **Tags:** ProviderCoherence, ModelAlignment, PreemptiveCheck, Task034

## [LESSON] #Heuristics #Overreach "Channel-Handle Collision"
- **Kontext:** Kurze geografische Begriffe (Rom, Paris, Ulm) können mit Youtube-Handles kollidieren.
- **Problem:** Channel-Resolution in video_tools.py interpretiert geografische Begriffe als YouTube-Channel-Namen, obwohl sie keine echten Handles sind. Dies führt zu unnötigen Channel-Lock-Versuchen und verschlechterter Suchqualität.
- **Lösung:** Eine Whitelist oder ein Mindest-Kontext-Check für Channel-Locks ist erforderlich. Geografische Begriffe sollten nicht als Channel-Hints behandelt werden, es sei denn, es gibt explizite Kontext-Indikatoren (z.B. "von Kanal X", "Channel Y").
- **Location:** `backend/tools/video_tools.py` (_extract_channel_hint, _clean_channel_hint_for_resolution)
- **Confidence:** Medium (Task 034 observation)
- **Tags:** VideoSearch, ChannelResolution, HeuristicOverreach, Task034

## [PATTERN] #Architecture #MoA "The Power-Hierarchy Rule"
- **Kontext:** Mixture-of-Agents (MoA) mit automatischem Modellwechsel basierend auf Query-Komplexität.
- **Problem:** Smalltalk oder Skill-Aufrufe könnten das Modell von User-Präferenz (z.B. GPT-4o) auf ein kleineres Modell (z.B. GPT-4o-mini) "downgraden" — illegal und verletzt User-Choice.
- **Lösung:** Ein automatischer Modellwechsel darf nur ein **UPGRADE** sein: `speed < balanced < logic`. Das vom User gewählte Modell ist die **Untergrenze (Floor)**. Der Orchestrator prüft: `if proposed_tier < user_tier: keep user_tier`.
- **Ergebnis:** Verhindert illegalen Downgrade bei Smalltalk/Skills. User-Choice ist Law.
- **Location:** `backend/services/chat_orchestrator.py` (MoA-Pre-Resolution Guard)
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** MoA, ModelHierarchy, UserChoice, FloorGuard, BUG-A2-MOA-DOWNGRADE

## [PATTERN] #Pydantic #LLM #StrictSchema "Schema Strictness over Prompting"
- **Kontext:** Nano/Mini-Modelle (GPT-4o-mini, Gemini-Nano) leiden unter **Parameter-Amnesie** — sie "vergessen" optionale Felder wie `channel_name` trotz ausführlicher Prompts.
- **Problem:** Prompting allein reicht nicht. Optionale Felder mit Defaults (`default=None`) werden von kleinen Modellen ignoriert oder mit Halluzinationen gefüllt.
- **Lösung:** **Schema Strictness**: 
  1. Entferne alle Defaults in Pydantic für kritische Felder → `channel_name: str = Field(...)` (required)
  2. Definiere harte `required` Arrays im JSON-Schema → `["query", "wants_latest", "channel_name"]`
  3. Steel-Concrete Descriptions: "MUSS", "PFLICHTFELD", "STRENGSTENS VERBOTEN"
- **Ergebnis:** Extraktion (z.B. `channel_name`) wird erzwungen — das Schema selbst ist der Guard.
- **Location:** `backend/data/schemas.py` (VideoSearchInput), `backend/skills/system/video_search.json` (input_schema)
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** Pydantic, StrictSchema, NanoModel, ParameterAmnesie, SteelConcrete, RequiredFields

## [PATTERN] #Architecture #ProviderConsistency "The Koppel-Prinzip"
- **Kontext:** Provider-APIs (OpenAI, Gemini, Ollama) haben unterschiedliche Modell-IDs und Endpunkte.
- **Problem:** 404-Fehler entstehen, wenn z.B. ein Gemini-Modell an die OpenAI-API gesendet wird (z.B. `gemini-1.5-pro` an `api.openai.com`).
- **Lösung:** **Koppel-Prinzip**: Modell-IDs und Provider-APIs müssen im Orchestrator **immer als Paar** validiert werden. Jedes Modell-Objekt im Catalog trägt seinen `provider`. Der Orchestrator routet nur zu passenden Providern.
- **Ergebnis:** Eliminiert Mixed-Provider-Context-Fehler. Provider-Coherence garantiert.
- **Location:** `backend/config/model_catalog.json`, `backend/services/chat_orchestrator.py` (Provider-Routing)
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** ProviderCoherence, KoppelPrinzip, ModelRouting, BUG-A2-MIXED-PROVIDER-CONTEXT

## [PATTERN] #MCL #Video #Persistence Backend-Source-of-Truth + UI Fallback Chain
- **Kontext:** Video-Flow mit `video.search` ueber mehrere Provider (GPT/Gemini), Streaming-Updates, Chat-Wechsel und App-Restarts.
- **Problem:** Wenn `modal_request` nur implizit/instabil aus Modelltext entsteht, brechen Reopen-Link und Modal-Reopen in Randfaellen (Provider-Differenzen, SSE-Timing, Historien-Reload) sporadisch weg.
- **Lösung:** Zwei-Stufen-Architektur:
  1. **Backend deterministisch:** `modal_request` direkt aus erfolgreichen Tool-Resultaten ableiten und in Message-Metadaten persistieren.
  2. **Frontend resilient:** Reopen-Link immer mit Fallback-Kette bedienen (`lastVideoModalRequest` -> per-Chat Cache -> `data-video-url`).
- **Ergebnis:** Reopen-Funktion bleibt stabil ueber Streaming, Chat-Switch und Full Reload.
- **Location:** `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/status_sync.py`, `backend/data/crud.py`, `frontend/js/chat.js`, `frontend/js/chat-manager.js`
- **Confidence:** High (Live validiert)
- **Tags:** Task033, modal_request, SSE, Persistence, FallbackChain

## [PATTERN] #Architecture #Streaming "The Stream-Switch Pattern"
- **Kontext:** Video-Suche mit `video.search` im List-Mode liefert SSE-Streaming-Antworten mit Metadaten (`videos[]`, `mode: "list"`). Das Modell soll Markdown-Links `[Video ansehen](URL)` generieren, aber der Frontend-Renderer versucht zusätzlich, UI-Karten zu rendern.
- **Problem:** Wenn der Frontend-Renderer UI-Karten (`renderVideoListCards`) nach dem Streaming rendert, überschreibt nachfolgende `innerHTML`-Calls diese Karten wieder → Links verschwinden oder werden zu grauem Text. Inkonsistenz zwischen Live-Streaming und Chat-Wechsel.
- **Lösung:** **Stream-Switch Pattern**:
  1. Backend erzwingt Block-Response für Listen (keine UI-Karten im Stream, nur Markdown-Links).
  2. Frontend deaktiviert `renderVideoListCards` im SSE-Done-Handler.
  3. Heiler für nackte URLs: `Video ansehen (URL)` → `[Video ansehen](URL)` vor `marked.parse`.
  4. Nur noch Markdown-Links im Text, keine zusätzlichen UI-Komponenten.
- **Ergebnis:** Link-Integrität über Streaming, Chat-Wechsel und App-Reload garantiert. Konsistentes Rendering.
- **Location:** `backend/skills/system/video_search.json` (synthesis_directives), `frontend/js/chat.js` (SSE-Handler, Heiler, deaktivierte Karten)
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** Task033, StreamSwitch, MarkdownLinks, LinkIntegrity, SSE, VideoList

## [PATTERN] #Pydantic #ModelHierarchy "The 5.4 Trinity Lockdown"
- **Kontext:** Das System nutzt GPT-5 Modelle (`gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.4`) für Text-Tasks. GPT-4 Modelle (`gpt-4o`, `gpt-4o-mini`) sind nur für Vision und TTS erlaubt.
- **Problem:** Alte Konfigurationen und Test-Dateien enthalten noch Referenzen zu `gpt-4o-mini` für balanced/logic Tiers → Modell-Drift zu GPT-4, Prompt-Integrität gefährdet.
- **Lösung:** **5.4 Trinity Lockdown**:
  1. `MOA_MODEL_HIERARCHY` in `moa.py` korrigieren: balanced → `gpt-5.4-nano`, logic → `gpt-5.4`.
  2. Alle Hardcoded-Referenzen in `benchmark_skill.py` zu `gpt-5.4-nano` ändern.
  3. Test-Dateien (`test_moa_routing.py`, `memory_qa.py`) zu GPT-5 Modelle migrieren.
  4. TTS-Exception: `gpt-4o-mini` in `tts_service.py` bleibt erlaubt (Audio-Typ).
- **Ergebnis:** Ausschluss von GPT-4 Modellen für Text-Tasks erzwingen. Prompt-Integrität erhalten.
- **Location:** `backend/llm_providers/shared/moa.py`, `backend/scripts/benchmark_skill.py`, `backend/tests/test_moa_routing.py`, `backend/services/memory_qa.py`
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** Task033, ModelHierarchy, GPT4Purge, GPT5Trinity, MOA, BenchmarkFix

## [PATTERN] #Frontend #Events "Window-Level Capture Intercept"
- **Kontext:** YouTube-Links in Chat-Antworten müssen das Video-Modal öffnen. Links werden über Markdown gerendert (`[Video ansehen](URL)`) und können durch DOM-Changes (innerHTML-Überschreibungen, Hydration-Calls) instabil werden.
- **Problem:** Event-Listener auf Link-Ebene werden durch nachfolgende DOM-Changes entfernt oder überschrieben → Links reagieren nicht mehr. Chat-Wechsel oder Streaming-Updates zerstören die Interaktivität.
- **Lösung:** **Window-Level Capture Intercept**:
  1. Globaler Event-Listener auf `window` (nicht `document`) in Capture Phase (`true`).
  2. `e.target.closest('a')` um Link-Target zu finden (funktioniert auch bei Klicks auf Kind-Elemente).
  3. YouTube-URL-Erkennung (`youtube.com`, `youtu.be`) → `e.preventDefault()`, `e.stopPropagation()`.
  4. Direkter Aufruf von `openModal({ type: "video", payload: { url: href } })`.
  5. Keine DOM-Changes im Listener, nur Modal-Trigger.
- **Ergebnis:** Ultimativer Regressionsschutz gegen DOM-Changes. Links funktionieren sofort und bleiben stabil über Streaming, Chat-Wechsel und App-Reload.
- **Location:** `frontend/js/chat.js` (Window-EventListener am Ende der Datei)
- **Confidence:** High (Task 033 Post-Impl)
- **Tags:** Task033, WindowCapture, EventIntercept, RegressionProtection, VideoLinks, DOMResilience

## [PATTERN] #Frontend #UX The Triple-Guard Paste-Resize
- **Kontext:** Chat composer als wachsendes `<textarea>` (max. 200px); **Rechtsklick → Einfügen** kann Layout hinter **`input`** zurückbleiben (Browser wendet Wert verzögert an).
- **Problem:** Nur **`input`** oder nur **`setTimeout(0)`** reicht nicht zuverlässig: Kontextmenü-Paste und sehr große Einfügevorgänge messen **`scrollHeight`** manchmal vor finaler Layout-Berechnung → falsche Höhe, kein Shrink, Cursor „unsichtbar“.
- **Lösung:** **Triple-Guard** kombinieren:
  1. **`input`** + **`requestAnimationFrame(() => autoResize.call(textarea))`** — nach dem nächsten Paint, wenn der Browser den Wert und die Box aktualisiert hat.
  2. **`paste`** + **`setTimeout(() => autoResize.call(textarea), 20)`** — zweite Sicherheit für Kontextmenü / große Daten (Wert liegt sicher im DOM).
  3. **`paste`** + **`requestAnimationFrame(() => autoResize.call(textarea))`** — zusätzlicher Frame gegen engine-spezifische Layout-Lags.
  Ergänzend: **`autoResize`** beginnt immer mit **`this.style.height = 'auto'`**, dann **`scrollHeight`**, Cap 200px, **`overflowY`**, **`this.scrollTop = this.scrollHeight`**, danach **`scrollChatToBottom`** für die Haupt-Chat-Liste.
- **Location:** `frontend/js/app.js` (Listener), `frontend/js/chat.js` (`export function autoResize`)
- **Confidence:** High (V4.7.7 FINAL SESSION SEAL)
- **Tags:** SYS-UI-INPUT-MODERNIZATION, V4.7.7, Textarea, Paste, requestAnimationFrame, ContextMenu

## [PATTERN] #UI #Layout #Sidebar Fixed-Flex-Fixed Layout Pattern
- **Kontext:** Sidebar mit Header (Logo/Brand), Content (scrollbare Chat-Liste), Footer (Einstellungen/Status). Problem: Content wächst unendlich, Footer wird aus dem Viewport geschoben.
- **Problem:** Standard-CSS (`height: 100vh`, `overflow: visible`) lässt die Sidebar bei langen Chat-Listen über das Fenster hinauswachsen → Header verschwindet, Footer nicht erreichbar.
- **Lösung:** **Fixed-Flex-Fixed** Pattern mit Flexbox:
  - **Header:** `flex-grow: 0; flex-shrink: 0;` (fixe Höhe)
  - **Content:** `flex-grow: 1; flex-shrink: 1; overflow-y: auto;` (nimmt verfügbaren Platz, scrollt bei Bedarf)
  - **Footer:** `flex-grow: 0; flex-shrink: 0;` (fixe Höhe, immer sichtbar)
  - Container: `display: flex; flex-direction: column; height: 100vh;`
- **Location:** `frontend/css/sidebar.css` (`.sidebar-container`, `.sidebar-header`, `.sidebar-content`, `.sidebar-footer`)
- **Confidence:** High (Diamond Elite UI Pattern)
- **Tags:** SYS-SIDEBAR-OVERHAUL, V4.7.6, CSS, Flexbox, Layout, ScrollManagement

## [PATTERN] #UX #Navigation #Workspace Workspace Tool Integration
- **Kontext:** Einstellungen vs. aktive Arbeits-Modi — User verwirrt durch Vermischung von Konfiguration und Workspace-Funktionen.
- **Problem:** Checkboxen oder Toggle-Switches für Workspace-Tools (z. B. Bildgalerie, Projekt-Dashboard) sind unintuitiv — User erwarten Navigation, nicht Einstellungen.
- **Lösung:** **Transformation in vollwertige Navigations-Items:**
  - Workspace-Tools werden als **erste-class Navigation** neben Chat angeboten
  - Icons + Labels statt Checkboxen
  - Aktiver Zustand visuell hervorgehoben (wie aktiver Chat)
  - Einheitliches Interaktionsmuster: Klick → Öffnet Tool/Modal (kein Settings-Panel)
- **Benefits:** Klare Trennung Einstellungen/Arbeit, intuitive Discovery, reduzierte kognitive Belastung
- **Location:** `frontend/js/sidebar.js` (Workspace Tool Rendering), `frontend/css/sidebar.css` (Nav-Item Styling)
- **Confidence:** High (Diamond Elite UX Pattern)
- **Tags:** SYS-SIDEBAR-OVERHAUL, V4.7.6, UX, Navigation, Workspace, UnifiedUI

## [PATTERN] #Frontend #StateManagement DOM-to-State Sync Guard
- **Kontext:** Komplexe UIs, in denen ein erneutes Rendern oder ein `innerHTML = ""` Dropdowns/Controls neu aufbaut — z. B. Provider/Modell-Auswahl im Chat-Header.
- **Problem:** Der Nutzer ändert nur das **DOM** (z. B. „Gemini Flash“), während **`appState.last_active.model`** noch den alten Wert aus dem letzten **`loadLastUsedModel()`** trägt. Beim nächsten **`render()`** wird die Liste aus **`appState`** wiederhergestellt → sichtbarer **Flip** (z. B. zurück zu „Pro“), sobald z. B. die Einstellungen geöffnet werden und **`render()`** ausgelöst wird.
- **Lösung:** **Vor** jeder Funktion, die die Komponente leert oder neu füllt, die **aktuellen Werte aus dem DOM** in den globalen Anwendungszustand (**`appState`**) schreiben (Provider + Modell). Ergänzend: **`change`**-Listener auf dem Select, der **`appState`** und optional **`PUT /api/last-used-model`** synchron hält. Wo möglich: **kein vollständiges `render()`** nur für einen View-Wechsel (nur Sichtbarkeit toggeln), damit das Dropdown gar nicht zerstört wird.
- **Location:** `frontend/js/app.js` (`render()`, Settings-Button, `#model-select` change)
- **Confidence:** High
- **Tags:** SYS-UI-SYNC, V4.7.5, VanillaJS, StateSync

## [PATTERN] #EliteArchitecture #Deduplication #HealthInjector Hybrid Jaccard Deduplication + LLM Summarization
- **Kontext:** Health-Injector injiziert Gesundheitsfakten (Nussallergie, Medikamente) unabhängig vom Query in alle Chats.
- **Problem:** Gesundheitsfakten können in verschiedenen Kategorien gespeichert sein (korrekt als "Gesundheit", falsch als "Allgemein") und bei der Injektion doppelt erscheinen. Zusätzlich: Mehrere ähnliche Fakten (z. B. 3 Variationen von "Nussallergie") verschwenden Context-Budget.
- **Lösung:** **Zweistufiger Hybrid-Ansatz:**
  1. **Technische Filterung:** **Hybrid-Abfrage** (Kategorie OR Snippet-Keywords: `nuss`, `allergie`, `krankheit`, `medizin`, `reaktion`) + **Jaccard-Deduplizierung** mit 70% Threshold. Priorisierung nach `priority` und `id` (neueste zuerst). Ähnliche Fakten (>70% Jaccard) werden übersprungen.
  2. **Kognitive Zusammenfassung:** `_SUGGESTION_SUMMARIZATION_RULE` — LLM-Prompt-Regel, die ähnliche Fakten zu **EINEM** prägnanten Punkt zusammenfasst (z. B. "Schwere Nussallergie" statt 3x Dubletten).
- **Location:** `backend/services/memory_manager.py:_dedupe_health_memories_jaccard()`, `_HEALTH_JACCARD_DEDUP_THRESHOLD = 0.70`; `backend/services/orchestrator/prompt_registry.py:_SUGGESTION_SUMMARIZATION_RULE`
- **Confidence:** High (Elite Pattern — technisch + kognitiv)
- **Tags:** V4.7.4, HealthInjector, Jaccard, Deduplication, Summarization, HybridPattern, MemoryManager

## [PATTERN] #EliteArchitecture #PromptEngineering #ForcedFooter Suggestion Engine Compliance + Reminder
- **Kontext:** Proactive Suggestion Engine V4.7.4 — Mode 0 (OFF) sollte *keine* Vorschläge generieren, Mode 2 sollte *immer* den Footer `💡 Meine Ideen für dich:` erzeugen.
- **Problem:** Soft-Prompts (`Keine Vorschläge`, `Nur Fakten`) werden von GPT-5.4-nano / Mini-Modellen ignoriert (**kognitive Trägheit**). Das LLM fügt trotz Mode 0 einen proaktiven Footer hinzu und ignoriert die "Datenbank-API"-Rolle — selbst bei explizitem Verbot.
- **Lösung:** Der **Forced Footer Reminder** — ein harter, struktureller Prompt-Suffix, der das Ende der Antwort *zwingend* definiert. Statt zu *bitten*, wird das Format **per System-Befehl erzwungen** mit:
  1. **Role-Play Verpflichtung:** "Du bist eine DATENBANK-API" (kein freundlicher Assistent)
  2. **STOP_SEQUENCE_COMMAND:** `[STOP_SEQUENCE_COMMAND]: Terminate your output immediately after the data`
  3. **Explizite Fehlerandrohung:** `Jedes weitere Wort...führt zur Fehlermeldung`
  4. **Reminder-Prinzip:** Bei Nano/Mini-Modellen **kognitive Trägheit** überwinden durch Wiederholung der Befehle in verschiedenen Formulierungen (Steel-Concrete Language)
- **Location:** `backend/services/orchestrator/prompt_registry.py` (`suggestion_mode_0`, `suggestion_mode_2`, `_SUGGESTION_SUMMARIZATION_RULE`)
- **Confidence:** High (Elite Pattern — überwindet kognitive Trägheit bei schwachen Modellen)
- **Tags:** V4.7.4, PromptEngineering, LLM-Compliance, Orchestrator, ForcedFooter, ReminderPattern, NanoModels

## [PATTERN] #Pydantic #LLM #ToolSchema Pydantic as an LLM Guardrail
- **Kontext:** Function-Calling: Das Modell erzeugt JSON für Tool-Argumente. Ohne klare Semantik raten kleine oder überlastete Modelle bei Format, Zeitzonen und domänenspezifischer Syntax.
- **Problem:** Vage oder fehlende Beschreibungen führen zu falsch formatierten Datumswerten, nutzlosen Suchstrings und Sprach-Mix in Prompts (z. B. deutsche Bildbeschreibung an APIs, die auf Englisch optimiert sind) — nachgelagerte Validierung schlägt fehl oder das Tool liefert leere Ergebnisse.
- **Lösung:** **`Field(description="...")` gezielt als „Mini-Prompt“** nutzen: explizit erwartetes Format nennen (z. B. **ISO-8601** / Kalender-Hinweise), **Operatoren und Beispiele** für APIs (z. B. **Gmail-`q`** mit `from:`, `subject:`, `is:unread`, `after:YYYY/MM/DD`), und **Sprachempfehlungen** wo der Provider es braucht. Je präziser die Feldhilfe, desto höher die Wahrscheinlichkeit, dass der erste Tool-Call nutzbar ist — Pydantic validiert danach und verwandelt „fast richtig“ in harte Fehler statt stiller Fehlfunktion.
- **Location:** `backend/data/schemas.py` (Tool-Args), Skill-JSON unter `backend/skills/` wo applicable
- **Confidence:** High (Skill-Forge / Complete Arsenal)
- **Tags:** EPIC-SKILL-FORGE, DiamondTools, PromptEngineering, JSONSchema

## [PATTERN] #Python #Resilience #Tools The Universal Shield (Top-Level try/except)
- **Kontext:** Tools rufen externe APIs (Gmail, Wetter, Bildgenerierung), Dateisystem oder DB auf — jede Schicht kann unerwartete Exceptions werfen (Netzwerk, Timeouts, Auth-Refresh, Disk voll, Parsing).
- **Problem:** Unabgefangene Exceptions steigen bis in den Request-Handler durch und können **ganze Chat-Requests** oder Worker abbrechen; der Nutzer sieht einen generischen 500er statt einer strukturierten Tool-Antwort.
- **Lösung:** Pro öffentlicher Tool-Funktion ein **äußerstes `try` / `except Exception`** (oder äquivalent ein einziger umhüllender Block), der **immer** in den kanonischen Fehlerpfad mündet — z. B. **`ToolResultV1`** mit `status="error"`, **`ToolErrorDetails`** (`code`, `message`, `details`), Logging mit `exc_info=True`. Innere `try`-Blöcke dürfen spezifisch bleiben; der **äußere Schild** fängt alles, was sonst entwichen wäre. Das ist die **stärkste einzeilige Verteidigung** gegen Backend-Abstürze durch Drittanbieter und Umwelt.
- **Location:** `backend/tools/*.py`, `backend/services/*_manager.py` (Diamond-Tool-Implementierungen)
- **Confidence:** High (Skill-Forge / Complete Arsenal)
- **Tags:** EPIC-SKILL-FORGE, Resilience, ErrorHandling, ToolResultV1

## [PATTERN] #Pydantic #Compatibility Computed-Field Bridge
- **Kontext:** Migration zu einem neuen Datenschema ohne Legacy-Break (LLMs, alte Tests, Prompts die `success` / `output` erwarten).
- **Problem:** Doppelte Felder im Modell (`status` + `success`, `message` + `output`) würden Validierung und Wahrheitsquellen verwässern.
- **Lösung:** In Pydantic v2 **`@computed_field`** auf Properties nutzen, die **nur bei Serialisierung** in `model_dump()` / `model_dump_json()` erscheinen — z. B. `success: bool` aus `status == "ok"`, `output: str` aus `message or ""`. Das interne Modell bleibt kanonisch (`status`, `message`, `data`, `error`). Optional **`@model_validator(mode="before")`**, um eingehende Dicts von redundanten Legacy-Keys zu bereinigen, damit `model_validate()` robust bleibt.
- **Location:** `backend/data/schemas_tools.py` (`ToolResultV1`)
- **Confidence:** High
- **Tags:** SYS-SKILL-CONTRACT-V1, V4.7.3, Serialization, CompatibilityLayer

## [PATTERN] #SQLAlchemy #JSON #Mutation In-Place JSON Mutation Tracking
- **Kontext:** Speichern von Listen/Dicts in JSON-Columns.
- **Problem:** SQLAlchemy erkennt In-Place-Mutationen (`list.append()`) nicht als "dirty", wenn dasselbe Objekt zugewiesen wird.
- **Fix:** Erzwinge immer eine Kopie des Objekts: `current = list(old_list or [])`. Nach der Mutation das NEUE Objekt zuweisen, damit der Dirty-Check triggert.
- **Location:** `backend/tools/memory_tools.py` 
- **Confidence:** High

## [PATTERN] #Python #Refactoring Thin Facade / Shim Pattern
- **Kontext:** Logik in Sub-Pakete verschoben (z. B. `ollama/service.py`, `ollama/adapter.py`), bestehende Import-Pfade (`ollama_service.py`, `ollama_adapter.py`) und Tests sollen stabil bleiben.
- **Problem:** Monolithische Duplikate oder Ruff `--fix` können Syntax brechen; lokale Funktionen shadowen Imports und referenzieren nicht existierende Modul-Globals (z. B. `_CAPABILITY_CACHE`).
- **Lösung:** Legacy-Datei als **dünnes Re-Export-Shim**: `from backend…subpkg import Symbol` bzw. in Package-`__init__.py` explizit `from .module import X as X` und/oder `__all__`, damit Ruff F401 zufrieden ist und Side-Effect-Submodule (`from . import foo as foo`) weiter registrieren. **unittest.mock.patch** immer auf das Modul richten, in dem der Name zur Laufzeit gebunden ist (z. B. `backend…ollama.service.load_config_data`, nicht den Shim).
- **Location:** `backend/llm_providers/ollama_service.py`, `backend/llm_providers/ollama_adapter.py`, `backend/llm_providers/ollama/__init__.py`, `backend/data/presets/`
- **Confidence:** High
- **Tags:** SYS-CLEANUP-F401, Ruff, CompatibilityLayer

## [PATTERN] #Python #Resilience Tuple-based Error Propagation
- **Kontext:** Distinguishing between "Successful Empty Result" and "Unparseable Fallback Result".
- **Lösung:** Return `tuple[result, is_fallback]`. This allows downstream logic to trigger retry/healing mechanisms even if the fallback value itself is technically valid JSON (like `[]`).
- **Location:** `backend/services/memory_extractor.py` — `_extract_json_array_text`, `_generate_fact_extraction_items_with_self_healing`
- **Confidence:** High
- **Tags:** BUG-MEM-RECOVERY, SYS-TEST-STABILITY, V4.7.2

## [PATTERN] #Python #Caching #ThreadSafety Thread-Safe LRU Cache Pattern
- **Kontext:** In-Memory Cache für High-Priority Daten.
- **Problem:** `OrderedDict` ist nicht thread-safe bei zusammengesetzten Operationen (get + move_to_end).
- **Fix:** Nutze ein `threading.Lock()` innerhalb der Singleton-Instanz. Jede Operation (get, put, invalidate) MUSS den Lock via `with self._lock:` halten, um Race-Conditions (KeyError) zu vermeiden.
- **Location:** `backend/services/memory_cache.py` 
- **Confidence:** High (Opus 4.6 Verified)

## [PATTERN] #Setup #DiamondOS #Foundation System-Initialisierung Diamond OS
- **Kontext:** Rules, Skripte, Foundation (Diamond OS V2.1)
- **Fehlerklasse:** —
- **Ursache:** —
- **Fix:** Infrastruktur auf Diamond-Standard V2.1 gehoben; docs/lessons_learned.md nach WHAT_I_LEARNED.md migriert (V3.3)
- **Merged from:** docs/lessons_learned.md (2026-03-28)

## [PATTERN] #SSE #FastAPI #React Chunk-Parsing Guard
- **Kontext:** SSE-Streaming mit JSON-Metadaten zwischen Backend und Frontend
- **Fehlerklasse:** Unvollständige Chunks, JSON-Parse-Errors, UI/Metadata-Kollision
- **Ursache:** Keine Typ-Differenzierung zwischen UI-Inhalt und Hintergrund-Daten
- **Fix:** Nutze immer 'type'-Keys (text, metadata, done) in SSE-Chunks
  - `type: 'text'` → UI-Rendering (fließend, partial-Flag für Chunking)
  - `type: 'metadata'` → Sidebar/State-Update (Kosten, Usage)
  - `type: 'done'` → Stream-Cleanup, Final State
  - `type: 'error'` → Fehler-Anzeige im UI
- **Backend** (`chat.py`): `yield f"data: {json.dumps({'type': 'metadata', 'usage': {}, 'cost': {}})}\n\n"`
- **Frontend** (`ChatView.tsx`): `const data = JSON.parse(line.slice(6)); if (data.type === 'metadata') onCostUpdate(data.cost)`
- **Confidence:** High
- **Tags:** #V4.4 #GoldStandard #Streaming

## [PATTERN] #SequentialThinking #MCP #UI MCP-Sequential-Thinking-Guard
- Symptom: UI-Hangs während langen Thinking-Sessions mit MCP sequential_thinking Tool
- Root Cause: >5 Gedanken oder >45s pro Gedanke führen zu Sync-Hangs bei Kimi
- Fix: Max. 3-5 prägnante Gedanken, spätestens bei Thought 3 Lösungshypothese, bei >45s/Thought → sofort Umsetzung
- Files: Alle Task-Dokumentationen
- Confidence: High

## [PATTERN] #API #Validation #Logic Safe External API Mapping
- Symptom: Inconsistent external data
- Root Cause: Unvalidated API response fields
- Fix: Always validate required fields before mapping
- Files: backend/services/*
- Confidence: High

---

## [RESOURCE_METRICS]
**Zweck:** Tracking von Ressourcen-Verbrauch pro Task fuer Trend-Analyse.

| Datum | Task-ID | Editor | CU | Verbrauch | Impact |
|-------|---------|--------|----|-----------|--------|
| 2026-04-01 | C8-VANILLA-SSE | Windsurf | 7 | Sonnet 4.6 | FinOps-Loop geschlossen. Sidebar zeigt nun Live-Kosten in Vanilla JS. |
| 2026-04-01 | SYS-ARCH-REVIEW | Windsurf | 5 | 4% (W) | System-Prompt auf V4.4 gehoben |
| 2026-03-31: Price Verification Phase
- **Problem**: Websearch liefert veraltete Snippets (idealo.de Metabeschreibungen)
- **Lösung**: HTML-Crawl Verification-Phase für Top-Ergebnis
  - `backend/tools/finance_tools.py`: `_verify_price_from_url()` implementiert
  - Meta-Tags (OpenGraph), JSON-LD Schema.org, HTML-Elemente Parsing
  - 10% Toleranz für Preis-Mismatch Detection
  - Skip für Amazon/eBay (Bot-Schutz)
  - `backend/data/schemas.py`: `live_verified`, `live_price`, `verification_status` Felder
  - `backend/skills/system/price_comparison.json`: Prompt-Fix für live_verified Priorisierung
- **Tags**: #API, #Logic, #PriceAccuracy | SYS-V3.3-HEALTH-CHECK | Cursor | 5 | ~4% Monatsquota | Systemstabilitaet validiert |

## 2026-04-01: API Response Usage Mapping Fixed
- **Problem**: Usage/Cost war im Backend korrekt, aber Frontend zeigte nichts
- **Ursache**: ExecutionResponse-Schema hatte keine usage/cost Felder; chat_orchestrator.py mappte sie nicht ins API-Response
- **Fix 1** (schemas.py Line 33-35): Felder zum Schema hinzufügen
  - `usage: Dict[str, Any]`
  - `cost: Dict[str, Any]`
- **Fix 2** (chat_orchestrator.py Line 4410-4452): Extraktion und Aggregation
  - Extrahiere usage/cost aus run_tool_loop_result
  - Extrahiere _search_costs aus Tool-Results (finance_tools.py)
  - Addiere Search-Costs zu total_cost
  - Logger zeigt: "API-USAGE-FIX: LLM-Cost 0.0015€ + Search-Cost 0.05€ = Total 0.0515€"
- **Fix 3** (chat_orchestrator.py Line 4467-4474): Behalte Usage/Cost im Websearch-Renderer bei
- **Tags**: #FastAPI, #Finance, #ResponseMapping, #Pydanticd

## 2026-04-01: Regression Fixed
- **Problem**: Model-Upgrade (gpt-5.4-nano -> gpt-4o-mini) und Usage-Mapping waren beschädigt
- **Ursache**: Code wurde versehentlich gelöscht/reverted
- **Fix 1** (execution_engine.py): Model-Upgrade Logik für optimal_model_tier = "balanced" wiederhergestellt
  - `gpt-5.4-nano` -> `gpt-4o-mini` wenn Skill balanced Model benötigt
  - Logging: "TOOL-LOOP: Model upgraded for skill '%s' from '%s' to '%s'"
- **Fix 2** (chat_orchestrator.py): Usage/Cost-Hard-Lock implementiert
  - Aggregated usage/cost aus run_tool_loop_result wird EXKLUSIV verwendet
  - Search-Costs (0.01€/Query) werden addiert
  - Background-Task (memory_extractor) darf Usage NICHT überschreiben
  - Logger: "API-USAGE-FIX: LLM-Cost %.4f€ + Search-Cost %.4f€ = Total %.4f€"
- **Tags**: #Regression, #FastAPI, #ModelOverride, #UsageProtectiond

## 2026-04-01: Usage Aggregation Fixed
- **Problem**: Usage und Cost wurden bei jedem Loop-Schritt überschrieben statt addiert
- **Ursache**: In `run_tool_loop()` wurde nur die letzte Response ausgewertet
- **Fix 1** (execution_engine.py Line 511-514): Aggregations-Variablen initialisieren
  - `aggregated_tokens_input = 0`
  - `aggregated_tokens_output = 0`  
  - `aggregated_total_cost = 0.0`
- **Fix 2** (execution_engine.py Line 542-559): In jeder Iteration addieren
  - Extrahiere `usage_data` und `cost_data` aus Response
  - Addiere zu aggregierten Werten
  - Debug-Logging für Tracking
- **Fix 3** (execution_engine.py Line 781-792): Aggregierte Werte zurückgeben
  - `usage={input_tokens, output_tokens, total_tokens}`
  - `cost={total_cost}`
- **Fix 4** (finance_tools.py): Search-Costs 0.01€ pro Websuche
  - `search_query_count` für alle Suchen (Anchor, Varianten, Refurbished, Fallback)
  - `_search_costs` Metadata im Output für Sidebar
- **Sidebar Deep Dive Active**: ✅ Summierte Kosten über alle Iterationen
- **Tags**: #FinOps, #Logic, #UsageAggregation, #SearchCosts
- **Pattern**: Anchor + Variants + Bulk-Verify für Preisvergleiche
- **Problem**: Einzelne Suche liefert nur 1 Ergebnis; parallele Varianten-Suchen ohne Anchor verlieren den günstigsten Einstiegspreis
- **Lösung** (3-Phasen-Architektur):
  ```
  Phase 1: ANCHOR-SUCHE (seriell)
    - Initial-Suche mit breitem Query (z.B. "MacBook M3 Preis neu")
    - Speichert günstigstes Ergebnis als "Bestpreis-Einstieg"
    - Unabhängig von Varianten-Suchen
  
  Phase 2: VARIANTEN-SUCHEN (parallel/seriell)
    - Gezielte Suchen für spezifische Modelle (Air 13, Air 15, Pro 14)
    - Ergebnisse werden zu results-Liste hinzugefügt
  
  Phase 3: MERGE & SORT
    - Anchor wird an Position 0 eingefügt (falls noch nicht vorhanden)
    - Liste nach price aufsteigend sortiert
    - Günstigster Preis steht garantiert an erster Stelle
  
  Phase 4: BULK-VERIFICATION (parallel)
    - asyncio.gather für alle URLs gleichzeitig
    - 6s Timeout-Guard
    - Jede Variante bekommt live_verified Flag
  ```
- **Implementierung**: `backend/tools/finance_tools.py` Line 359-620
- **Key Insight**: Anchor-Suche MUSS vor Varianten-Suchen laufen, nicht als Fallback
- **Tags**: #Architecture, #SearchPattern, #PriceComparison, #DataAggregation
- **Problem**: Der günstigste MacBook-Preis (z.B. 799€ "Anchor") wurde verworfen, weil die Initial-Suche nur bei `not results` ausgeführt wurde
- **Ursache**: Varianten-Suchen füllten `results` zuerst, deshalb wurde Runde 1 (Initial-Suche) übersprungen
- **Lösung**: Drei-Schritte-Strategie:
  1. **ANCHOR-SUCHE** (Line 410-445): Initial-Suche IMMER zuerst ausführen, unabhängig von results
     - Speichere Ergebnis in `anchor_result` mit `variant="Bestpreis-Einstieg"`
  2. **VARIANTEN-SUCHE** (Line 447-496): Zusätzliche Varianten parallel suchen
     - Ergebnisse werden zu `results` hinzugefügt (nicht ersetzen)
  3. **MERGE & SORT** (Line 498-594):
     - Anchor zu results hinzufügen (wenn noch nicht vorhanden)
     - `results.sort(key=lambda x: x.price)` - Günstigster Preis steht an erster Stelle
- **Erwarteter Chat-Output**:
  ```
  - Bestpreis-Einstieg: ab 799 € (Quelle: idealo.de)
  - Air 15 Zoll: ab 1099 € (Quelle: amazon.de)
  - Pro 14 Zoll: ab 1599 € (Quelle: apple.com)
  ```
- **Tags**: #Logic, #UX, #PriceAnchor, #DataPreservation
- **Problem**: Nur Top-Ergebnis wurde live-verifiziert, nicht alle MacBook-Varianten
- **Lösung**: Parallel crawling aller Varianten mit asyncio.gather
- **Implementierung**:
  - `_verify_single_variant()` - Wrapper mit internem Try-Except (Line 279-303)
    - WICHTIG: Ein 503-Fehler bei einer Variante bricht NICHT die anderen ab
  - Bulk-Phase (Line 473-539):
    - Sammelt alle URLs mit Varianten-Index
    - `asyncio.gather(*verification_tasks, return_exceptions=True)`
    - 6s Latency-Guard via `asyncio.wait_for(timeout=6.0)`
    - Lieber veralteter Preis als Timeout-Fehler
  - Jede Variante bekommt eigenes `live_verified`, `live_price`, `verification_status`
- **Erwartete Logs**:
  ```
  PRICE-COMPARISON: Starte BULK-Verification für 3 Varianten (Timeout: 6s)
  PRICE-COMPARISON: Variante 0 Status: verified (live_price: 1049.0)
  PRICE-COMPARISON: Variante 1 Status: 503_failed
  PRICE-COMPARISON: Variante 2 Status: verified (live_price: 1799.0)
  ```
- **Chat-Output**: Alle 3 Varianten mit ✅ oder ⚠️ je nach Verifikations-Status
- **Tags**: #Asyncio, #Performance, #BulkVerification, #ParallelScraping
- **Problem 1**: Log zeigt gpt-5.4-nano statt gpt-4o-mini trotz Override in execution_engine.py
- **Ursache**: OpenAI-Silo (`_run_full_tool_loop`) nutzt `resolve_moa_model()` und ignoriert das Modell-Override
- **Fix 1**: OpenAI-Silo prüft jetzt auf `MODEL_OVERRIDE:` Marker in chat_history
  - `backend/llm_providers/openai/gateway.py` Line 180-204
  - Wenn Override gefunden → `forced_model` wird verwendet statt MoA-Resolution
  - Log: "💎 OpenAI-Silo: Model override detected from execution_engine"
- **Problem 2**: Tool-Output enthält nur 1 Ergebnis statt 3 MacBook-Varianten
- **Fix 2**: MacBook-Diversifizierung in `backend/tools/finance_tools.py` Line 332-381
  - Bei "macbook" + "m3" im Produktnamen: 3 parallele Suchen für Air 13, Air 15, Pro 14

## [LESSON] #Database #Migration Explicit Schema Migration for New Columns
- **Kontext**: SQLAlchemy Models definieren neue Spalten (auto_generated in Chat, source_type in Memory), aber die bestehende Datenbank hat diese Spalten nicht.
- **Problem**: Bei App-Update entstehen OperationalError "no such column" wenn die Migration nicht ausgeführt wurde. Base.metadata.create_all() fügt nur neue Tabellen hinzu, keine neuen Spalten in bestehenden Tabellen.
- **Lösung**: Explizite ALTER TABLE Statements in `_ensure_sqlite_schema_migrations()` in database.py:
  1. Prüfen ob Tabelle existiert: `insp.has_table("chats")`
  2. Prüfen ob Spalte existiert: `"column_name" not in chat_cols`
  3. ALTER TABLE ausführen wenn Spalte fehlt
  4. Logging für Audit-Trail
- **Ergebnis**: Schema-Migration wird bei jedem App-Start automatisch ausgeführt, keine manuellen SQL-Skripte nötig.
- **Location**: `backend/data/database.py` (_ensure_sqlite_schema_migrations, lines 84-120)
- **Confidence**: High (Hotfix 0.4.14-beta.1)
- **Tags**: Database, Migration, SQLAlchemy, SchemaEvolution, Hotfix

## [LESSON] #Configuration #Security #PyInstaller Secure API Key Distribution for Beta Testers
- **Kontext**: Beta-Tester sollen YouTube-API-Key "out of the box" nutzen können, ohne manuelle Konfiguration.
- **Problem**: API-Key in .env steht im Klartext. Wenn .env nicht in PyInstaller eingebunden wird, müssen Beta-Tester manuell konfigurieren.
- **Lösung**: Mehrstufige Priorisierung für API-Key-Lade-Logik:
  1. **Priority 1**: local_config.json in AppData (nicht im Git, für User-spezifische Keys)
  2. **Priority 2**: .env Datei (im Projekt, wird in PyInstaller eingebunden)
  3. **Priority 3**: Windows Keyring (für alternative Speicherung)
- **PyInstaller-Einbindung**: .env zu janus_backend.spec datas hinzufügen
- **Pfad-Logik**: Mehrere Pfade prüfen (Dev vs PyInstaller mit sys._MEIPASS vs CWD)
- **Sicherheit**: .env ist bereits in .gitignore → wird nicht ins Git gepushed
- **Ergebnis**: Beta-Tester erhalten Installer mit vor-konfiguriertem Key, keine manuelle Einrichtung nötig.
- **Location**: `janus_backend.spec` (.env Einbindung), `backend/tools/video_tools.py` (_get_youtube_api_key, set_youtube_api_key)
- **Confidence**: High (Hotfix 0.4.14-beta.1)
- **Tags:** Configuration, PyInstaller, Security, APIKeys, BetaTesting, OutOfTheBox
  - Jede Variante mit eigenem `variant_label` (z.B. "Air 13 Zoll")
  - Auto-Detektion falls Variante nicht explizit gesetzt
- **Expected Output**: 
  - Log: "TOOL-LOOP: Model upgraded..." → "💎 OpenAI-Silo: Model override detected..."
  - Chat: Liste mit 3 MacBook-Varianten + Links
- **Tags**: #Search, #Routing, #ModelOverride, #VariantDiversification
- **Problem**: LLM lässt Links weg (Brevity Bias), ignoriert Varianten, schreibt Fließtext statt Listen
- **Ursache**: Synthesis-Directives waren zu "nett", keine strikten Format-Pflichten
- **Fix**:
  - `backend/skills/system/price_comparison.json`:
    - "DU BIST EIN LISTEN-GENERATOR. Fließtext ist STRENG VERBOTEN."
    - "Jeder einzelne Punkt MUSS mit einem funktionierenden Link enden."
    - MacBook Few-Shot: Exakte Chat-Ausgabe als Vorlage (3 Varianten, 3 Links)
  - `backend/tools/finance_tools.py`:
    - EXTREME HIGHLIGHTING: `!!! VERIFIED_BEST_PRICE !!!`, `!!! VERIFIED_PRICE_ATTENTION !!!`
    - `_output_format_hint` und `_link_requirement` als Pflicht-Anweisung
    - Der LLM kann den verifizierten Preis jetzt nicht mehr übersehen
- **Expected Output Format**:
  ```
  Bestpreis-Einstieg: MacBook Air M3 13 ab 1.049 EUR
  
  - MacBook Air M3 13 Zoll: ab 1.049 EUR ✅ (Quelle: [idealo.de](URL))
  - MacBook Air M3 15 Zoll: ab 1.299 EUR ✅ (Quelle: [idealo.de](URL))
  - MacBook Pro M3 14 Zoll: ab 1.799 EUR (Quelle: [amazon.de](URL))
  ```
- **Tags**: #UX, #FewShot, #StrictSynthesis, #LinkEnforcement

## 2026-04-01: Emergency Fix V3.5.1 - UnboundLocalError tool_calls
- **Problem**: `tool_calls` wurde in `run_tool_loop()` auf Line 532 referenziert, bevor es definiert war (UnboundLocalError)
- **Ursache**: Model-Tier-Override Code wurde vor dem `reason_and_respond_fn()` Call platziert, aber `tool_calls` kommt erst aus der Response
- **Fix**: 
  - Code verschoben: Model-Override jetzt NACH `tool_calls = response.get("tool_calls")` 
  - Kommentar hinzugefügt: "This must happen AFTER we get tool_calls from the response"
  - Logik: Override passiert nachdem Tool-Calls aus Response extrahiert wurden, aber bevor `if not tool_calls: break`
- **Datei**: `backend/services/orchestrator/execution_engine.py` Line 530-574
- **Validation**: py_compile passed, Syntax OK
- **Tags**: #Logic, #Emergency, #ScopeFix

## 2026-04-01: Skill Routing & UX Fix
- **Problem**: Model-Tier wurde ignoriert, Preis-Ausgabe ohne Varianten-Struktur
- **Lösung**: 
  - `backend/services/orchestrator/execution_engine.py`: 
    - `_resolve_model_for_skill()` Methode hinzugefügt
    - `run_tool_loop()`: Model-Tier-Override basierend auf Skill-Metadaten
    - Log zeigt jetzt: "TOOL-LOOP: Model upgraded for skill 'X' from 'Y' to 'Z'"
  - `backend/skills/system/price_comparison.json`:
    - VERBOT: Stelle keine Gegenfragen
    - Liste IMMER Varianten (Air vs Pro)
    - Nutze ✅ für live-verifizierte Preise und ⚠️ für 503-Fehler
    - MacBook M3 Few-Shot Beispiel mit 3 Varianten (Air 13, Air 15, Pro 14)
  - `backend/tools/finance_tools.py`:
    - HTML Price Elements: Top 3 → Top 8 für bessere Coverage
    - `_live_verified_marker` und `_verification_note` für LLM-Sichtbarkeit
- **Test-Erwartung**: "Was kostet ein MacBook M3?" → Log zeigt gpt-4o-mini, Antwort zeigt Air/Pro Liste
- **Tags**: #Routing, #UX, #ModelTier, #PriceComparison | SYS-V3.3-HEALTH-CHECK | Cursor | 5 | ~4% Monatsquota | Systemstabilitaet validiert |

## 2026-04-01: Deep Dive Streaming & Final Override Active

## [PATTERN] #Frontend #Dock #Taskbar Taskbar-Integration Pattern
- **Kontext:** Modale (knowledge-center, image-studio, gallery, transcript) sollen minimiert werden und in der Taskbar erscheinen, um wieder geöffnet zu werden.
- **Problem:** Ohne korrekte Integration wird das Modal beim Minimieren einfach geschlossen oder verschwindet ohne Möglichkeit zur Wiederherstellung.
- **Lösung:** **Taskbar-Integration Pattern:**
  1. **HTML:** Taskbar-Button mit eindeutiger ID (z.B. `dock-transcript`) und Icon hinzufügen
  2. **CSS:** Button nur anzeigen, wenn minimiert: `#dock-bar #dock-transcript.dock-item:not(.is-minimized) { display: none; }`
  3. **JS (Registration):** `setDockModuleExists(MODULE_ID, true)` aufrufen, um das Modul im Dock-System zu registrieren
  4. **JS (Synchronization):** Dock-Status-Synchronisation mit `subscribeWindowState()` und Klasse `.is-minimized` auf Taskbar-Button setzen/entfernen
  5. **JS (Event-Listener):** Taskbar-Button-Event-Listener, der `dockOpen(MODULE_ID)` aufruft
  6. **JS (Minimize):** Minimize-Button ruft `dockMinimize(MODULE_ID, true)` auf
- **Ergebnis:** Modal wird korrekt minimiert, erscheint in Taskbar, und kann über Taskbar wieder geöffnet werden.
- **Location:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/video-player.js`, `frontend/js/modal-api.js`
- **Confidence:** High (Task FE_TRANSCRIPT_MODAL_UI_ENHANCEMENT)
- **Tags:** TaskbarIntegration, DockSystem, DockPanel, MinimizeRestore, FE_TRANSCRIPT_MODAL

## [PATTERN] #Frontend #UI #DockPanel Dock-Panel Design Pattern
- **Kontext:** Modale sollen konsistent aussehen und funktionieren (Header, Buttons, Drag/Resize).
- **Problem:** Modale haben unterschiedliche Designs und Funktionalitäten, was inkonsistente UX führt.
- **Lösung:** **Dock-Panel Design Pattern:**
  1. **HTML-Struktur:** Header mit Drag-Strip, Buttons (Close, Minimize, Reset), Resize-Handles (n, e, s, w, ne, nw, se, sw)
  2. **CSS-Styling:** Dock-Panel Klassen (`dock-panel`, `dock-panel--open`, `dock-panel-header`, etc.)
  3. **Initialposition:** Fixed positioning mit `top` und `left` (z.B. `top: 480px, left: 892px`)
  4. **Drag-Funktionalität:** interact.js oder nativer Drag-Handler über Header
  5. **Resize-Funktionalität:** interact.js oder nativer Resize-Handler über Handles
  6. **Dock-System-Integration:** `setDockModuleExists`, `DOCK_HOST_ELEMENT_IDS`, Dock-Status-Synchronisation
- **Ergebnis:** Konsistentes Design und Funktionalität über alle Modale hinweg.
- **Location:** `frontend/index.html`, `frontend/css/style.css`, `frontend/js/video-player.js`
- **Confidence:** High (Task FE_TRANSCRIPT_MODAL_UI_ENHANCEMENT)
- **Tags:** DockPanel, DesignPattern, DragResize, ConsistentUI, FE_TRANSCRIPT_MODAL

## [PATTERN] #Architecture #UX The Async Proxy-Skill Pattern
- **Kontext:** Langlaufende CPU-Tasks (Whisper STT für Video-Transkripte) würden den Chat-Orchestrator blockieren und die UX verschlechtern.
- **Problem:** Synchrones Ausführen von STT im Chat-Flow führt zu langen Wartezeiten und blockiert andere Anfragen.
- **Lösung:** **Async Proxy-Skill Pattern:**
  1. **Dedizierter API-Endpoint:** `POST /api/video/analyze` für asynchrone Ausführung
  2. **Eigenes Modal:** Transkript-Modal (MCL-Standard) für UI-Feedback
  3. **Non-Blocking:** Orchestrator bleibt frei, Task läuft im Hintergrund
  4. **Button-First UX:** Analyse nur über UI-Button (Brain-Button) auslösbar
- **Ergebnis:** Chat bleibt responsive, Video-Analyse läuft im Hintergrund, UX ist intuitiv.
- **Location:** `backend/main.py`, `backend/tools/video_understanding.py`, `frontend/js/video-player.js`
- **Confidence:** High (Task VID-UNDERSTAND-001)
- **Tags:** AsyncProxy, STT, Whisper, VideoUnderstanding, NonBlocking, UX

## [PATTERN] #Frontend #CSS MCL Geometric Nesting
- **Kontext:** Abhängige Fenster (z.B. Transkript-Modal) sollen unter dem Master-Modal (Video-Player) positioniert werden.
- **Problem:** Browser-Berechnungsfehler (1011px bug) bei absoluter Positionierung und overflow-hidden führen zu falscher Darstellung.
- **Lösung:** **MCL Geometric Nesting:**
  1. **Absolute Positionierung:** Kind-Modale mit `position: absolute` relativ zum Vater
  2. **Overflow Visible:** Vater-Modal mit `overflow: visible` statt `hidden`
  3. **Geometrische Berechnung:** Kind-Modale an Unterkante des Vater-Modals binden
  4. **Z-Index Management:** Über `DOCK_HOST_ELEMENT_IDS` und Dock-System
- **Ergebnis:** Browser-Bug umgangen, Kind-Modale korrekt positioniert, keine Darstellungsfehler.
- **Location:** `frontend/css/style.css`, `frontend/js/modal-api.js`
- **Confidence:** High (Task VID-UNDERSTAND-001)
- **Tags:** MCL, GeometricNesting, CSS, Positioning, BrowserBug

## [PATTERN] #FinOps #Architecture Background Cost Bridge
- **Kontext:** Asynchrone API-Endpoints (z.B. `/api/video/analyze`) werden nicht vom Orchestrator verwaltet, daher keine automatische Kosten-Persistierung.
- **Problem:** Kosten für Hintergrund-Analysen gehen verloren, FinOps-Transparenz ist unvollständig.
- **Lösung:** **Background Cost Bridge:**
  1. **DB-Session Injection:** `db: Session = Depends(get_db)` im Endpoint
  2. **Manuelle Persistierung:** `cost_service.create_cost_entry()` im Tool aufrufen
  3. **Source Type:** `source_type="skill"` für korrekte Kategorisierung
  4. **Context Details:** `context_details=f"video.understand (video_id={video_id}, task={task})"` für Traceability
  5. **Frontend Refresh:** CustomEvent `janus:cost-update` triggert `window.fetchCostData()`
- **Ergebnis:** 100% FinOps-Transparenz für Hintergrund-Analysen, Dashboard zeigt alle Kosten.
- **Location:** `backend/main.py`, `backend/tools/video_understanding.py`, `frontend/js/video-player.js`, `frontend/js/cost-visualizer.js`
- **Confidence:** High (Task VID-FINOPS-001, VID-FINOPS-002)
- **Tags:** FinOps, CostTracking, Async, DB, BackgroundBridge
- **Problem 1**: Finale Synthese nutzte immer noch request.model (gpt-5.4-nano) statt aufgewertetes Modell
- **Problem 2**: Frontend-React Sidebar bekam keine Gesamtkosten weil Metadata-Chunk fehlte
- **Fix 1** (execution_engine.py Line 978-1005): FINAL-SYNTHESIS-MODEL-OVERRIDE
  - `_run_final_synthesis()` akzeptiert `final_model` Parameter
  - Nutzt aufgewertetes Modell (gpt-4o-mini) für finale Antwort-Generierung
  - Log: "FINAL-SYNTHESIS-MODEL-OVERRIDE: Using upgraded model '%s'"
- **Fix 2** (execution_engine.py Line 781-810): DEEP-DIVE-STREAM-METADATA
  - `ExecutionResponse` enthält jetzt usage/cost in final_response_metadata
  - Frontend React kann am Stream-Ende Gesamtkosten extrahieren
  - Format: `{"type": "metadata", "usage": {...}, "cost": {...}}`
- **Tags**: #Streaming, #FinalOverride, #Metadata, #React, #FinOps

---

## [RESOURCE_LOG]
**Legend:**
- [TBD] = To Be Determined (nach ausreichend Benchmark-Daten)
- Baseline-Aufnahme pro Tag: Min. 3 Tasks mit gleichem Tag für statistische Signifikanz

| Task | IDE | Modell | CU | Tags | Tokens | %-Quota | Kosten (€) |
|------|-----|--------|----|------|--------|---------|------------|
| Audit | Cursor | Cl. 4.6 Thinking | 5 | #Setup | 2.5M | 4% (M) | 0,80 € |
| [TBD] | Windsurf | GPT-4o | [X] | #UI | [TBD] | [X]% (D) | [TBD] |
| [TBD] | Windsurf | Kimi K2.5 | [X] | #Logic | [TBD] | [X]% (D) | [TBD] |

---

## [IDE_BENCHMARK_GAPS]
**Zweck:** Gap-Analysis Matrix für autonomes A/B-Testing zwischen IDEs.

| Tag | IDE: Cursor (€) | IDE: Windsurf (€) | Winner (LQI) |
|-----|-----------------|-------------------|--------------|
| #API| 0,80 € (Audit) | 0,15 € (Review)   | Windsurf (High) |
| #Logic| [FEHLT]       | 0,15 € (Review)   | Windsurf |
| #UI | [FEHLT] | [FEHLT] | TBD |
| #Setup| 0,80 € | [FEHLT] | TBD |
| #SequentialThinking| [FEHLT] | [FEHLT] | TBD |

**Kritikalität:** Je mehr "FEHLT" pro Tag, desto höher die Priorität für Benchmark-Tasks.
**LQI** = Loop Quality Index (Success Rate / Cost)

---

## [IDE_BENCHMARK_LOG]
**Zweck:** Vergleichende Effizienz-Analyse zwischen Windsurf (Claude 4.6) und Cursor (Claude 4.6).
**Conversion:** Daily% × 30 = Monthly% | Weekly% × 4 = Monthly% | Cursor-Basis: 50 Fast-Requests/Monat

### Gap-Analysis Matrix (V3.3)
**Zweck:** Schnelle Identifikation von Datenlücken für A/B-Testing.

| Tag | IDE: Cursor (Data) | IDE: Windsurf (Data) | Winner |
|-----|--------------------|----------------------|--------|
| #Setup | [4% / 0,80€] | [FEHLT] | TBD |
| #API | [FEHLT] | [FEHLT] | TBD |
| #UI | [FEHLT] | [FEHLT] | TBD |
| #Logic | [FEHLT] | [FEHLT] | TBD |
| #SequentialThinking | [FEHLT] | [FEHLT] | TBD |

**Kritikalität:** Je mehr "FEHLT" pro Tag, desto höher die Priorität für Benchmark-Tasks.

### Detail-Log
| Task-Typ | Modell | IDE | Tokens | %-Quota (Relativ) | Est. € / Task | Success |
|----------|--------|-----|--------|-------------------|---------------|---------|
| Audit | 4.6 Thinking | Cursor | 2.5M | 4% (Monthly) | ~0.80 € | ✅ |
| MCP-Build| 4.6 Thinking | Windsurf| [TBD] | [X]% (Daily/Weekly)| [TBD] | [TBD] |

## [PATTERN] #Task033 #VideoList #Debugging Force-Choice Deep Unpacking [IN-PROGRESS]
- **Kontext:** Task 033 Video-Listen-Feature — Backend liefert korrekte Video-Listen, aber UI öffnet Modal nicht beim Klick auf "Video ansehen"
- **Status:** 🔄 IN-PROGRESS / Debugging-Phase
- **Erkenntnisse bisher:**
  1. **Force-Choice Pattern**: `tool_choice: { type: 'function', function: { name: 'video.search' } }` erzwingt deterministischen Skill-Aufruf
  2. **Deep Unpacking Pattern**: `**tool_result.get('output', {})` in `chat.py` expandiert verschachtelte Video-Listen korrekt für Frontend-Rendering
  3. **MCL Global Listener**: `document.addEventListener('click', ...)` mit `capture: true` fängt Link-Klicks vor Bubble-Phase ab
- **Geänderte Dateien:**
  - `backend/services/chat.py` (Unpacking: `**tool_result.get('output', {})`)
  - `frontend/js/chat.js` (Globaler Click-Interceptor + MCL-Styling Hook)
  - `backend/skills/system/video_search.json` (Strict Schema mit required fields, Steel-Concrete Directives)
- **Nächster Schritt:** Browser DevTools Netzwerk-Tab Analyse — prüfen ob `modal_request` mit `type: "video"` im SSE-Stream ankommt
- **Tags:** #Task033, #VideoList, #Debugging, #ForceChoice, #DeepUnpacking, #MCL

## [PATTERN] #FinOps #Gateway Missing Tool-Loop Persistence
- **Kontext:** OpenAI Gateway `_run_full_tool_loop()` akkumuliert Kosten über Planungsrunden (gpt-5.4-mini), persistiert sie aber nicht
- **Fehlerklasse:** Sidebar zeigt niedrigere Summe als Deepdive (Mini-Kosten fehlen in DB)
- **Ursache:** Gateway hat `db` Session nicht erhalten und rief `create_cost_entry()` nie auf
- **Fix:** 
  - `reason_and_respond()` übergibt `db` an `_run_full_tool_loop()` (gateway.py Line 113)
  - Vor jedem Return: `create_cost_entry()` mit akkumulierten Kosten (gateway.py Lines 313-328, 339-354)
  - `source_type="conversation"` für Mini-Planungskosten, `context="websearch"` für Web-Searches
- **Tags:** #FinOps, #Gateway, #KPI, #Persistence

## [PATTERN] #Architecture #FinOps MoA Pre-Resolution Hard-Lock
- **Kontext:** execution_engine.py `run_tool_loop()` upgrade-Model erst nach erster Response (teuer)
- **Fehlerklasse:** Erster Gateway-Call nutzt Base-Modell (z.B. Pro) statt Skill-Modell (Flash)
- **Ursache:** Model-Tier-Override passierte NACH `reason_and_respond()`, zu spät für ersten Call
- **Fix:**
  - Pre-Resolution VOR dem while-Loop (execution_engine.py Lines 534-549)
  - `_resolve_model_for_skill()` für jedes `allowed_skill_ids`
  - Sofortiges `gateway_kwargs["model"] = resolved_model` wenn unterschiedlich
  - Log: `🔥 MOA-HARD-LOCK: Overriding base model 'X' with Skill-Model 'Y'`
- **Tags:** #Architecture, #FinOps, #MoA, #HardLock

## [PATTERN] #Gemini #FinOps Native Search Grounding Billing
- **Kontext:** Gemini 3 API mit nativem Web-Grounding liefert `grounding_metadata.web_search_queries`
- **Fehlerklasse:** Such-Kosten nicht erfasst, Kosten-Leck im Deep-Dive
- **Ursache:** Gateway ignorierte `web_search_queries` in Response-Metadaten
- **Fix:**
  - Extraktion: `response["grounding_metadata"]["web_search_queries"]`
  - Filter leerer Strings: `[q for q in queries if q.strip()]`
  - Berechnung: `search_cost = len(valid_queries) * 0.01`
  - Aufaddierung zu `_loop_cost_eur` und separate Persistence mit `source_type="websearch"`
- **Tags:** #Gemini, #FinOps, #Grounding, #SearchBilling

## [PATTERN] #Skills #NanoProof DATEN-SYNTHESIZER Role Formulation
- **Kontext:** Skill-Direktiven für Websearch/Price-Comparison in V3.0
- **Fehlerklasse:** Nano-Modelle (gpt-5.4-nano, gemini-3-flash) produzieren Fließtext statt strukturiertem JSON
- **Ursache:** Synthesis-Directives zu "nett" formuliert, keine strikte Rollen-Pflicht
- **Fix:**
  - Direktive MUSS mit "DU BIST EIN DATEN-SYNTHESIZER" beginnen
  - "Fließtext ist STRENG VERBOTEN" als explizites Verbot
  - Nummeriertes Format (1. [BESTPREIS] / 2. [LISTE] / 3. [QUELLEN])
  - Output-Schema als Pflicht-Anhang: "Deine Antwort MUSS diesem JSON-Schema entsprechen"
  - Link-Pflicht: "Jeder Punkt MUSS mit einem klickbaren Markdown-Link enden"
- **Runtime-Bridge:** synthesis_directives und output_schema_hint werden automatisch in System-Prompt injiziert (chat_orchestrator.py SKILL-DIRECTIVE INJECTION)
- **Tags:** #Skills, #NanoProof, #Synthesis, #SchemaEnforcement, #V3.0

## [PATTERN] #MemoryV2 #Enricher Deterministic Enricher Pattern
- **Kontext:** Rule-basierte Metadata-Anreicherung für Memories.
- **Problem:** Harte If-Else-Ketten sind schwer wartbar und nicht erweiterbar.
- **Fix:** Nutze eine Liste von `PriorityRuleEntry` Objekten mit `condition: Callable[[Dict], bool], priority: float, description: str`. Erste passende Regel gewinnt. Trenne Regel-Definition von Ausführung.
- **Location:** `backend/services/memory_enricher.py`
- **Confidence:** High

## [PATTERN] #MemoryV2 #Knapsack Optimal Token Budget Selection
- **Kontext:** Memory-Context mit begrenztem Token-Budget zusammenstellen.
- **Problem:** Greedy-Algorithmus bricht bei erstem Überlauf ab, verpasst kleinere passende Slots.
- **Fix:** Knapsack-Prinzip: `continue` statt `break` bei Übergröße. Sortiere nach Priority desc, dann Size asc. Kleinere Slots können später noch passen.
- **Location:** `backend/services/memory_budget.py`
- **Confidence:** High

## [PATTERN] #MemoryV2 #Resilience Extraction Circuit Breaker
- **Kontext:** Automatisierte Extraktion nach jedem User-Turn.
- **Problem:** Provider-Ausfälle führen zu redundanten API-Fehlern und Latenz.
- **Fix:** 3-State Circuit-Breaker: CLOSED → OPEN (nach 3 Fehlern) → HALF_OPEN (nach 120s Timeout). In OPEN: Extraktion überspringen. In HALF_OPEN: Einzelner Probe-Call.
- **Location:** `backend/services/memory_extractor.py`
- **Confidence:** High

## [PATTERN] #MemoryV2 #Security Permission Guard for User-Editable
- **Kontext:** Memory-Updates durch Tools/Skills.
- **Problem:** System-Memories (z.B. extrahierte Fakten) dürfen nicht durch User-Tools modifiziert werden.
- **Fix:** `user_editable` Boolean-Flag in DB. Update-Tool prüft: `if not memory.user_editable: return NOT_EDITABLE error`. Immutability für System-Memories.
- **Location:** `backend/tools/memory_tools.py`
- **Confidence:** High

## [PATTERN] #MemoryV2 #Dedup Priority-Max Merge Strategy
- **Kontext:** Deduplizierung bei gleichem `canonical_key`.
- **Problem:** Einfaches Ignorieren verliert wichtige Updates; blindes Überschreiben verliert History.
- **Fix:** Deterministische Merge-Strategie: Priority = MAX(old, new), Tags = UNION(old, new), source_skill = Keep-Original (log collision), snippet = Update only if priority↑, last_accessed = NOW(), Cache-Invalidate.
- **Location:** `backend/services/memory_manager.py:_merge_existing_memory()`
- **Confidence:** High

## [PATTERN] #Windsurf #Cascade #Automation Diamond-OS Skill Integration
- **Kontext:** Automatisierung von Routine-Prozessen (Pre-Check, Audit, Session-Start).
- **Problem:** Manuelles Lesen von Rules, Erstellen von Task-Dateien und Sammeln von Git-Diffs kostet Zeit und ist fehleranfällig (insbesondere das Vergessen von Impact-Analysen).
- **Fix:** Nutzung von Windsurf Cascade Skills in `.windsurf/workflows/`. Aufruf via Slash-Command (z.B. `/session-start`). Nutzung des `// turbo` Markers in den .md-Dateien erlaubt Cascade die automatische, unbestätigte Ausführung von Shell-Commands (wie `git diff` oder Tests).
- **Location:** `.windsurf/workflows/*.md` 
- **Confidence:** High (Opus Verified)

## [PATTERN] #MemoryV2 #Deduplication Jaccard Similarity Duplicate Filter
- **Kontext:** Speicher-Context Budget Selection (Knapsack-Algorithmus).
- **Problem:** Ähnliche Fakten ("Kaffee"-Dubletten) verstopfen den Context.
- **Fix:** Token-basierte Jaccard-Ähnlichkeit: `intersection / union`. Threshold >0.80 = Dublette → Slot überspringen. Normalisierung: lowercase, alphanumerisch, Wörter >2 Zeichen.
- **Location:** `backend/services/memory_budget.py:_calculate_text_similarity()`
- **Confidence:** High
- **Tags:** BUG-MEM-020

## [PATTERN] #MemoryV2 #SearchGuard Recall-Guard for Self-Referential Queries
- **Kontext:** Proaktive Websuche-Skill-Auswahl.
- **Problem:** Self-referentielle Fragen ("Was bin ich allergisch gegen?") lösen unnötig Websuche aus.
- **Fix:** Regex `_SELF_REF_RE` erkennt Muster `(wer|was|wie).*(ich|mein|meine)` → Blockiert Websearch, erzwingt Memory-Only Antwort.
- **Location:** `backend/services/chat_orchestrator.py`
- **Confidence:** High
- **Tags:** BUG-MEM-021

## [PATTERN] #MemoryV2 #Safety Medical-Override for Health-Critical Slots
- **Kontext:** System-Prompt Injection für Gesundheitsdaten.
- **Problem:** Allergien/Gesundheitsdaten werden vom LLM ignoriert.
- **Fix:** Tag-Check (`gesundheit`, `allergie`, `medizin`) + Keyword-Check → Prepended Warning Block im System-Prompt: "!!! CRITICAL MEDICAL WARNING !!!"
- **Location:** `backend/services/chat_orchestrator.py`
- **Confidence:** High
- **Tags:** BUG-MEM-021

## [PATTERN] #MemoryV2 #Context Family-Context Instruction Hardening
- **Kontext:** Direktiven für Familienbeziehungen.
- **Problem:** LLM behauptet "Ich habe keine Informationen" obwohl Familienmitglieder im Context sind.
- **Fix:** Family-Relation-Regex erkennt (Bruder, Schwester, Vater, Mutter, etc.) → Hard-Verbot: "VERBOTEN: 'Ich habe keine Informationen dazu'"
- **Location:** `backend/services/chat_orchestrator.py`
- **Confidence:** High
- **Tags:** BUG-MEM-021

## [PATTERN] #MemoryV2 #Safety GLOBAL-UNLOCK Trigger Threshold
- **Kontext:** Automatisches Laden von Safety-kritischen Memories.
- **Problem:** Gesundheitsdaten (Priority 0.90) erreichen nicht den GLOBAL-UNLOCK Threshold (>=0.8).
- **Fix:** Health Priority auf 0.95 erhöht → Triggert `high_prio_memories = db.query(models.Memory).filter(models.Memory.priority >= 0.8)`
- **Location:** `backend/services/memory_enricher.py`
- **Confidence:** High
- **Tags:** BUG-MEM-022

## [PATTERN] #MemoryV2 #Retrieval Top-K Vector Query Limit Expansion
- **Kontext:** Vektorsuche für Memory-Retrieval.
- **Problem:** Default limit von 10 künstelt die Kandidatenliste vor dem Knapsack-Algorithmus ab.
- **Fix:** Limit von 10 auf 50 erhöht. Knapsack regelt das Budget - Vektorsuche darf nicht vorher filtern!
- **Location:** `backend/services/memory_manager.py:retrieve_diamond_slots()` / `retrieve_diamond_context()` (Token-budgetierter Diamond-Retrieval-Pfad; Vektorsuche + Knapsack im Slots-Flow)
- **Confidence:** High
- **Tags:** BUG-MEM-023

## [PATTERN] #Orchestration #DiamondCleanup Service-Agnostic Dispatcher Pattern (V2 — Full Transformation)
- **Kontext:** ChatOrchestrator mit 100+ Keywords, Regex-Patterns, hartkodierten Prompt-Strings und komplexer Policy-Logik.
- **Problem:** Harte Keyword-Listen, Regex-Patterns und Prompt-Texte im Orchestrator machen ihn unwartbar und verletzen Single-Responsibility-Prinzip. Cross-Cutting Concerns sind über den Code verstreut.
- **Fix:** Vollständige Extraktion in 6 dedizierte Service-Module:
  - `intent_engine.py`: Zentrale Intent-Erkennung (Shopping, Local Business, Ollama, Personal Recall, Meta-Agent, Fact-Telling, Self-Referential, Policy)
  - `identity_manager.py`: Identity-Regex, Realtime-Name-Extraktion, Unknown-Face-Buffer, Chat-Identity-Tracking
  - `vision_service.py`: `force_save_person()` und `start_save_person_background()` für Thread-basierte Personen-Speicherung
  - `intercept_handler.py`: Image-Intent Skill Guardrails + Lokale Bildanfragen-Handler
  - `policy_handler.py`: Policy-Consent-Phase komplett extrahiert
  - `prompt_registry.py`: Zentrale Prompt-Direktiven (Verbosity Control, Fallbacks, System-Prompts)
- **Lesson:** Der Orchestrator ist jetzt ein "reiner Dirigent" — ZERO harte Strings/Regex/Prompts für Logik-Entscheidungen. Alles delegiert an spezialisierte Services.
- **Location:** `backend/services/orchestrator/` (6 Module)
- **Confidence:** High (Diamond Gold)
- **Tags:** ORCH-TRANSFORM-EPIC, ServiceExtraction, CleanArchitecture, SingleSourceOfTruth, ZeroHardcoded

## [PATTERN] #Refactoring #Safety Missing Attribute Guard (Cross-Module)
- **Kontext:** Cross-Module Refactoring mit neuen Service-Imports und entfernten Klassenvariablen.
- **Problem:** Nach Refactoring fehlten Attribute (z.B. `META_TOPIC_INSTRUCTION_MAP`, `UNKNOWN_FACE_BUFFER`) oder hatten falsche Referenzen. Runtime-Fehler erst bei Ausführung sichtbar.
- **Fix:** 
  1. Explizite Re-Exporte aus Services: `from intent_engine import META_TOPIC_INSTRUCTION_MAP`
  2. Singleton-Pattern für Services mit `intent_engine`, `identity_manager` Instanzen
  3. Service-Methoden für alle State-Accesses (statt direkter Dictionary-Zugriffe)
  4. Syntax-Check + Import-Check nach jedem Refactoring-Schritt
- **Lesson:** Bei Cross-Module Refactoring: (1) Single Source of Truth erhalten, (2) Re-Exports explizit dokumentieren, (3) State-Access über Service-Methoden (keine direkten Variablen).
- **Location:** `backend/services/chat_orchestrator.py` (Import-Section)
- **Confidence:** High
- **Tags:** ORCH-DIAMOND-FINAL, RefactoringSafety, CrossModule, ImportGuard

## [PATTERN] #Orchestration #Security Precedence Guard (Capability Kill-Switch)
- **Kontext:** LLM-Heuristiken (z.B. Gemini Grounding) überschreiben Prompt-Verbote und erzwingen Websuchen bei persönlichen Daten.
- **Problem:** LLM-Provider ignorieren Prompt-Guidance und führen hartkodierte Websearch-Calls aus (z.B. `_run_drill_down_list_research` in Gemini Gateway).
- **Fix:** Entferne die `system.websearch` Skill-ID deterministisch aus der Liste der verfügbaren Tools auf Orchestrator-Ebene, bevor der LLM-Call erfolgt (`if _SELF_REF_RE.search(...)`). Zusätzlich: Kill-Switch im Gateway der Drill-Down blockiert wenn websearch nicht in `allowed_skill_ids`.
- **Lesson:** Capability-Removal auf Infrastruktur-Ebene schlägt Prompt-Guidance jedes Mal. Dual-Layer Protection (Orchestrator + Gateway) für Zero-Trust.
- **Location:** `backend/services/chat_orchestrator.py`, `backend/llm_providers/gemini/gateway.py`
- **Confidence:** High
- **Tags:** FIX-035, PrecedenceGuard, DeadCodeElimination, ProviderAgnostic

## [PATTERN] #MemoryV2 #VectorSearch Semantic Query Expansion
- **Kontext:** Vektor-Embeddings (z.B. all-MiniLM) verknüpfen abstrakte Begriffe wie "Familie" nicht stark genug mit konkreten Graden wie "Bruder" oder "Frau".
- **Problem:** Top-K Starvation — "Wer ist mein Bruder?" findet keine relevanten Memories weil Embedding-Distanz zu groß.
- **Fix:** Implementiere eine einfache Query-Expansion vor dem DB-Call. Wenn "familie" im Query vorkommt, hänge "bruder schwester vater mutter frau kind sohn tochter" an den Suchstring an.
- **Lesson:** Kleine terminologische Brücken lösen Top-K Starvation in Vektor-Datenbanken. Semantische Expansion ohne Embedding-Rekalkulation.
- **Location:** `backend/services/memory_manager.py`
- **Confidence:** High
- **Tags:** BUG-MEM-031, QueryExpansion, SemanticBridge

## [PATTERN] #NLP #Extraction Natural Language Fact Sanitization
- **Kontext:** Memory-Fact-Extraktion durch LLM.
- **Problem:** "Predicate Bleed" — Der Extractor schreibt technische JSON-Keys (z.B. `ist_beziehung`) direkt in den natürlichen Fakt-Text.
- **Fix:** Harte Prompt-Direktive im Extractor: Das Feld `fact` darf NUR grammatikalisch korrektes Deutsch enthalten. Technische Prädikate gehören ausschließlich in das Metadaten-Feld `predicate`.
- **Lesson:** Verunreinigte Fakt-Texte zerstören die semantische Suche. Fakt = Natürliche Sprache, Predicate = Technischer Key.
- **Location:** `backend/services/memory_extractor.py`
- **Confidence:** High
- **Tags:** BUG-MEM-033, FactField, ExtractionQuality

## [PATTERN] #Jaccard #Deduplication Token Length Sensitivity
- **Kontext:** Jaccard-Ähnlichkeits-Filter für Memory-Deduplizierung im Knapsack.
- **Problem:** Filter, die Wörter mit ≤2 Zeichen ignorieren, machen nummerierte Listen (z.B. "Punkt 1" vs "Punkt 2") zu identischen Dubletten.
- **Fix:** Nutze unterscheidbare Suffixe mit >2 Zeichen (z.B. "Alpha", "Bravo", "Checkpoint-A", "Checkpoint-B") in Tests oder senke den Normalisierungs-Threshold für Tests.
- **Lesson:** Zu aggressive Token-Filterung führt zu Datenverlust durch False-Positive Deduplizierung. Token-Length-Thresholds müssen kontext-sensitiv sein.
- **Location:** `backend/services/memory_budget.py`, `backend/tests/test_memory_regression.py`
- **Confidence:** High
- **Tags:** BUG-MEM-020, Jaccard, TokenFilter, TestDesign

## [PATTERN] #MemoryV2 #Security Precedence Guard (Security vor Merge)
- **Kontext:** Security Guard in `_merge_existing_memory()` für nicht-editierbare Memories.
- **Problem:** Core-Identities (z.B. Name) wurden trotz `user_editable=False` durch Deduplizierungs-Logik überschrieben.
- **Fix:** Precedence Guard am Anfang der Merge-Funktion: `if not existing.user_editable: return None`. Security-Check vor Merge-Logik.
- **Lesson:** Sicherheitsprüfungen müssen VOR Geschäftslogik erfolgen (Fail-Fast). Nicht-editierbare System-Memories sind immutable.
- **Location:** `backend/services/memory_manager.py:_merge_existing_memory()`
- **Confidence:** High
- **Tags:** BUG-MEM-SEC-001, SecurityGuard, PrecedencePattern, Immutable

## [PATTERN] #Orchestration #NoneSafety Variable-Initialisierung am Methodenanfang
- **Kontext:** `run_tool_loop_result` in `chat_orchestrator.py` wurde außerhalb des Initialisierungsblocks verwendet.
- **Problem:** UnboundLocalError wenn Variable innerhalb verschachtelter Code-Pfade definiert, aber außerhalb verwendet wird.
- **Fix:** Initialisiere ALLE Variablen, die später außerhalb ihrer Definition verwendet werden, am Methodenanfang mit `None`. Nutze None-Check vor Zugriff.
- **Lesson:** Python hat keine Block-Scope-Isolation wie C++. Variablen in `if`-Blöcken sind im gesamten Methoden-Scope sichtbar, aber möglicherweise nicht initialisiert.
- **Location:** `backend/services/chat_orchestrator.py:process_turn()`
- **Confidence:** High
- **Tags:** BUG-ORCH-001, NoneSafety, VariableInitialization, DefensiveProgramming

## [PATTERN] #PhaseDispatch #Orchestration 5-Phasen Dispatcher Architektur
- **Kontext:** Chat-Orchestrator mit komplexem Workflow (Request-Klassifizierung, Early-Exit, Memory-Context, Generation, Finalisierung).
- **Problem:** Monolithische `process_turn()` Methode mit tiefen Indentations und vermischten Zuständigkeiten.
- **Fix:** Strukturierung in 5 dedizierte Phasen mit eigener Workflow-State-Klasse:
  1. **RequestContext** — Zentraler Workflow-State (Request, BackgroundTasks, AuditContext, Identity)
  2. **`_classify_request()`** — Initialisierung, Klassifizierung, Mode-Detection
  3. **`_try_early_exit()`** — Gating-Logik (Identity-Recall, Name-Detection, Policy-Prompts)
  4. **`_build_memory_context()`** — Memory-Retrieval, Fact-Coupon-Extraction, Knapsack-Selection
  5. **`_execute_generation()`** — Prompt-Building, Skill-Directive-Injection, Tool-Loop-Execution
  6. **`_finalize_response()`** — Post-Processing, Fact-Backfill, Cost-Aggregation, Persistierung
- **Vorteile:**
  - **Single Responsibility:** Jede Phase hat einen klaren Vertrag (Input → Output)
  - **Testability:** Phasen können isoliert getestet werden
  - **Observability:** Klare Log-Segmente pro Phase (`[PHASE X]`)
  - **Maintainability:** Änderungen an einer Phase beeinflussen andere nicht
  - **Early-Exit Pattern:** Gating-Logik zentralisiert, kein Deep Nesting
- **Location:** `backend/services/chat_orchestrator.py:ChatOrchestrator`
- **Confidence:** High (Live-Test PASS 2026-04-10)
- **Tags:** PhaseDispatch, OrchestrationV2, Architecture, DiamondGold

## [PATTERN] #MemoryV2 #FactCoupons Deterministische Must-Include Fakten-Injektion
- **Kontext:** Kleine Modelle (GPT-Nano/Flash) ignorieren komplexe semantische Prompts im Kontext (Lost-in-the-Middle-Problem).
- **Problem:** Negative Präferenzen (Allergie, Abneigungen) werden trotz `!!! ABSOLUTE WAHRHEITSPFLICHT !!!` im Prompt nicht erwähnt.
- **Fix:** Generiere deterministische `[MUST-MENTION-NEGATIVE]` / `[HEALTH]` / `[PREFERENCE]` Coupons für kritische Fakten. Injeziere als **letzte System-Message** vor User-Prompt (maximale Aufmerksamkeit). Coupon-Format: `1. [TAG] Fakt-Text` mit expliziter Regel: "Ignorieren = kritischer Systemfehler".
- **Lesson:** Nano-Modelle verstehen eindeutige, nummerierte Befehle besser als abstrakte Prinzipien. Deterministische Struktur (`[TAG] + nummerierte Liste`) überwindet kognitive Schwächen kleiner Modelle.
- **Location:** `backend/services/memory_budget.py:extract_fact_coupons()`, `chat_orchestrator.py` Coupon-Injection
- **Confidence:** High (Opus 4.6 Verified + Live-Test PASS)
- **Tags:** MemoryV2, Security, RecallGuard, NanoModel, DeterministicCoupons, DiamondGold

## [PATTERN] #HardLoopBreaker #Orchestration PDF-Idempotenz im Loop (Gemini Loop Fix)
- **Kontext:** Gemini LLM ignoriert Tool-Erfolge und loopt mit identischen Tool-Calls (z.B. PDF-Erstellung).
- **Problem:** Mehrfache Ausführung desselben Tool-Calls (system.create_pdf) mit identischen Argumenten → Ressourcenverschwendung + UI-Inkonsistenz.
- **Fix:** Dreifacher Schutz im `run_tool_loop`:
  1. **Hard-Loop-Breaker (Pre-Execution)**: `_track_tool_call_fn()` prüft vor Tool-Ausführung auf Duplikate. Bei Duplikat → sofortiger `return` mit finaler Textantwort.
  2. **Aggressive Normalisierung**: `_normalize_tool_args()` entfernt alle nicht-alphanumerischen Zeichen aus Content/Filename für Cache-Key-Vergleich.
  3. **PDF-Success-Tracker (Post-Execution)**: Trackt erfolgreiche PDF-Erstellung in `_pdf_already_succeeded` → Emergency Exit bei erneutem PDF-Request im selben Turn.
- **Lesson:** Tool-Loop-Schutz muss auf Engine-Ebene (execution_engine.py) implementiert werden, nicht im Gateway. Callback-Übergabe via `gateway_kwargs` sicherstellen.
- **Location:** `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/execution_dispatcher.py`
- **Confidence:** High (Live-Test mit Gemini PDF-Gedicht-Prompt validated)
- **Tags:** #HardLoopBreaker, BUG-GEMINI-LOOP, ToolIdempotency, DiamondSeal, PhaseDispatch

## [PATTERN] #MemoryV2 #Security Precedence Guard für Personal Context
- **Kontext:** Personal-Recall-Fragen ("Wer ist in meiner Familie?") wurden durch proaktive Websearch überschrieben.
- **Problem:** Tool-Skills (websearch) hatten Vorrang vor Memory-Recall bei persönlichen Fragen.
- **Fix:** Entferne `system.websearch` aus `relevant_skill_ids` wenn `_SELF_REF_RE` (mein/meine/mir/mich) im Query erkannt wird. Dual-Layer: Orchestrator entfernt Skill + Gemini Gateway Kill-Switch blockiert Drill-Down.
- **Lesson:** Personal Context > Proactive Heuristics. Sicherheitskritische Guards müssen im Orchestrator (früh) UND im Provider-Gateway (spät) implementiert werden (Defense in Depth).
- **Location:** `backend/services/chat_orchestrator.py` (_apply_precedence_guards), `backend/llm_providers/gemini/gateway.py` (_websearch_allowed Kill-Switch)
- **Confidence:** High (Live-Test PASS)
- **Tags:** MemoryV2, Security, PrecedenceGuard, PersonalRecall, DefenseInDepth

## [PATTERN] #TemporalSync #MemoryV2 Episodic Metadata & Zeitstempel
- **Kontext:** User fragt "Wann habe ich dir das gesagt?" — LLM hat keine Zeit-Informationen zu Erinnerungen.
- **Problem:** MemorySlots hatten keine temporalen Metadaten. DB speichert UTC, aber LLM sieht nur Fakt-Text ohne Kontext wann/im welchen Chat.
- **Fix:** 
  1. MemorySlot erweitert um `timestamp` (German Lokalzeit: "Heute um 14:30", "3. März 2026") und `chat_title`
  2. `_utc_to_local()` via C-level `localtime()` für bulletproof Windows/Linux/Docker-Kompatibilität
  3. `format_temporal_stamp()` mit German-Month-Mapping und "Heute/Gestern"-Erkennung
  4. `_format_slot_line()` erzeugt episodic Format: `| GESPEICHERT AM: ... | IM CHAT: '...' | FAKT: ...`
- **Lesson:** Zeitstempel müssen menschenlesbar (nicht ISO8601) und lokalisiert sein. Episodic Context ermöglicht "Wann?"-Fragen.
- **Location:** `backend/services/memory_budget.py:MemorySlot`, `format_temporal_stamp()`, `_format_slot_line()`
- **Confidence:** High
- **Tags:** #TemporalSync, MemoryV2, TemporalRecall, EpisodicMemory, GermanLocalization, DiamondGold, PhaseDispatch

## [PATTERN] #MemoryV2 #OriginAwareness Ghost-Chat Dedup & Personen-Merging
- **Kontext:** Extrahierte Fakten aus "Hintergrund-Extraktion" (Ghost-Chats) verlieren den Origin-Kontext.
- **Problem:** "Chris ist Freund" aus Chat A und "Chris heißt Christoph" aus Chat B wurden als separate Slots behandelt. User-Identität konnte mit Drittpersonen verwechselt werden (Identity-Flip).
- **Fix:**
  1. `_is_relation_slot()` erkennt Beziehungs-Fakten via Tags oder Text-Muster ("freund", "bruder", "des nutzers")
  2. `_extract_proper_names()` zieht Namen aus Fakten für Same-Person-Erkennung
  3. Origin-aware Dedup: Bei Near-Duplicate wird älterer Zeitstempel (lower memory_id) bevorzugt + realer Chat-Titel über Ghost-Titel
  4. Identity-Anchor: Visueller `╔═ DU SPRICHST MIT: ROLF ═╗` Block am Prompt-Anfang verhindert Identity-Flip
- **Lesson:** Deduplication muss semantisch (wer) + temporal (wann) + herkunftsbasiert (woher) sein. Die älteste Erwähnung einer Person ist der Ursprung.
- **Location:** `backend/services/memory_budget.py:_is_relation_slot()`, `_extract_proper_names()`, `chat_orchestrator.py:IDENTITY-ANCHOR`
- **Confidence:** High (Live-Test: Rolf=Nutzer, Chris=Freund — kein Flip)
- **Tags:** MemoryV2, OriginAwareness, GhostChat, IdentityFlip, PersonDedup, DiamondGold

## [PATTERN] #MemoryV2 #SystemClock LLM Zeit-Bewusstsein
- **Kontext:** User fragt "Wie spät ist es?" oder referenziert aktuelles Datum im Vergleich zu Memory-Zeitstempeln.
- **Problem:** LLM hat kein Bewusstsein von "jetzt" — kann Zeit-Fragen nicht beantworten oder Zeitstempel relativ zu "heute" interpretieren.
- **Fix:** System Clock Injection als erste System-Message: `AKTUELLES DATUM/UHRZEIT: Mittwoch, 09.04.2026, 21:15 Uhr` — dynamisch generiert via `datetime.now()` mit German-Weekday-Mapping.
- **Lesson:** LLMs sind zeitlos. Für Zeit-Fragen und relative Zeitinterpretationen muss aktuelle Zeit explizit im Kontext stehen.
- **Location:** `backend/services/chat_orchestrator.py` — System Clock Block vor IDENTITY-ANCHOR
- **Confidence:** High
- **Tags:** MemoryV2, SystemClock, TemporalAwareness, DiamondGold

## [PATTERN] #MemoryV2 #RelevanceGuard Context-Aware Fact-Coupons
- **Kontext:** Fact-Coupons (deterministische Must-Include Fakten) wurden bei jeder Query injiziert — auch bei irrelevanten Fragen (z.B. Allergie-Info bei "Wie spät ist es?").
- **Problem:** GPT-Nano erwähnte kritische Fakten in unpassenden Kontexten (Over-Sharing) oder verhielt sich unnatürlich.
- **Fix:**
  1. `_health_risk_triggers` — Keywords die eine Gesundheits-Coupon rechtfertigen (essen, trinken, kochen, allergi, nuss, milch...)
  2. `_is_health_relevant` — Query-Check vor Coupon-Generierung
  3. Gesundheits-Fakten werden nur bei risiko-relevanten Queries zu Coupons — sonst bleiben sie im normalen Kontext
  4. Prompt-Update: "!!! FACT COUPONS — RELEVANZ-PFLICHT !!!" + 3 explizite Regeln (NICHT LEUGNEN, RELEVANZ-FILTER, Sicherheit > Kürze)
- **Lesson:** Sicherheit (Never Deny) und Diskretion (Context-Relevance) sind kein Widerspruch. Guards können stufenweise sein: Coupon nur wenn nötig, aber niemals leugnen.
- **Location:** `backend/services/memory_budget.py:extract_fact_coupons()`, `_format_coupons_block()`
- **Confidence:** High (GPT-Nano: Sicher UND Diskret)
- **Tags:** MemoryV2, RelevanceGuard, FactCoupons, Safety, Discretion, DiamondGold, Elite

## [PATTERN] #Architecture #Task020 Memory Core Split — Package-Facade + Einzeiler-Shim
- **Kontext:** EPIC **Task 020** — „God Object“ `memory_manager.py` in fachliche Pakete (`crud_service`, `retrieval_service`) zerlegen, ohne hunderte Importe im Repo zu brechen.
- **Problem:** Direktes Verschieben aller Symbole führt zu **Import-Zusammenbruch**; Tests, die `unittest.mock.patch` auf alte Pfade setzen, mocken oft **nicht** die zur Laufzeit genutzte Implementierung.
- **Lösung (Diamond-Refactor):**
  1. **`backend/services/memory/__init__.py`** als **Facade**: exportiert die öffentliche API (`__all__`, klare Re-Exports).
  2. **Legacy-Modul** (`memory_manager.py`) als **Einzeiler-Shim**: z. B. `from backend.services.memory import *` bzw. gezielte Re-Exports — ruft weiterhin denselben Code wie das Paket auf, alte `from … import memory_manager`-Pfade bleiben gültig.
  3. **Tests:** `patch`-Ziele **zwingend** auf den **kanonischen Namespace** umstellen (z. B. `backend.services.memory.retrieval_service.vector_service`), wo das Symbol **tatsächlich gebunden** ist — sonst läuft der Test gegen das echte Modul und der Mock greift nicht.
- **Lesson:** Shim + Facade entkoppeln Migration von Big-Bang-Import-Fixes; Test-Patches sind Teil der Migration, nicht „optional nachträglich“.
- **Location:** `backend/services/memory/`, `backend/services/memory_manager.py` (Shim), betroffene `backend/tests/*`
- **Confidence:** High (Task 020, Opus/Cursor-Pfad)
- **Tags:** Task020, EPIC-MEMORY-CORE-REFACTOR, ShimPattern, Facade, unittest.mock, Namespace

## [PATTERN] #FullStack #Task021 Smart Chat Naming — Platzhalter, Races, Background-Guards
- **Kontext:** EPIC **Task 021** — automatische Chat-Titel nach genug Kontext; UI soll ohne F5 aktualisieren; Backend soll nicht durch voreilige Client-`PUT`s blockiert werden.
- **Problem A (Async UI / Race):** Das Frontend neigt dazu, bei „Neuer Chat“ **sofort** einen **`PUT /api/chats/{id}/title`** mit Erstsatz oder Kurzlabel zu senden. Das setzt oft **`auto_generated=false`** und verhindert zuverlässig das spätere Smart-Naming (Backend sieht einen „manuellen“ Titel).
- **Lösung A (Placeholder-Aware):** Backend-Trigger und Titel-Logik **Platzhalter-tolerant**: bekannte Defaults (`PLACEHOLDER_TITLES`, erweiterte „replaceable“-Heuristik in `response_finalizer._title_looks_replaceable`) erlauben den **ersten** KI-Naming-Lauf auch wenn das Flag nicht mehr „frisch“ ist; manuelle Umbenennungen bleiben über echte Kurztitel geschützt. **Frontend:** voreilige Titel-`PUT`s entfernen; stattdessen nach Stream **`GET /api/chats/{id}`** (Polling, gestaffelt: `scheduleSmartTitleRefresh`) + `patchChatTitleInUI`.
- **Problem B (Doppel-Chats):** `loadChats()` bei **leerer** Liste rief **`createNewChat()`** ohne `await` auf; kombiniert mit **`createNewChat` → `loadChats()`** und doppeltem Bootstrap (**`DOMContentLoaded`** + **`app.js`** nach Login) entstanden **zwei POST /api/chats** pro Aktion.
- **Lösung B:** `loadChats(..., { suppressAutoCreate: true })` nach manuellem `createNewChat`; Mutex / `await` beim Auto-Create; **nur ein** initialer Listen-Lade-Pfad; Button-Listener idempotent (`data-janus-bound`).
- **Problem C (Naming-Job Kosten / GPT-Leertext):** Hintergrund-Job soll nicht bei **jedem** Turn LLM kosten; Speed-Modell **`gpt-5.4-nano`** liefert für Mini-Titel-Prompts oft **keinen** `content` → Titel bleibt „Neuer Chat“.
- **Lösung C (Background Job Integrity):** **`last_topic_hash`** als **Einmal-Guard** nach erfolgreichem Naming (kein erneutes Feuern pro Request). Für OpenAI-Titel explizit **`gpt-4o-mini`** statt Speed-Tier; bei **keinem** brauchbaren Roh-Titel: **kein** Commit und **`last_topic_hash`** nicht setzen (sonst blockiert der Guard künftige Versuche fälschlich).
- **Ergänzung (Stream-Pfad):** Titel-Trigger sitzt in **`finalize_response`** nach **`persist_assistant_message`**; im Stream nutzt **`finalize_response_async`** eine **frische DB-Session** — konsistent mit Turbo-Flow (Commit/Expunge vor Stream).
- **Location:** `frontend/js/chat.js`, `frontend/js/chat-manager.js`; `backend/services/orchestrator/response_finalizer.py`, `title_generator.py`, `backend/data/crud.py` (`update_chat_title`, `auto_generated`)
- **Confidence:** High (Live-Test Gemini + GPT, Task 021 DONE)
- **Tags:** Task021, SmartChatNaming, RaceCondition, Placeholder, last_topic_hash, SSE, Polling, loadChats, gpt-4o-mini

## [PATTERN] #Frontend #StateManagement Vanilla EventBus vs. Framework
- **Kontext:** Dual-Window-Chat — mehrere UI-Zustände (aktives Fenster, Fokus, später Routing pro Pane) ohne React/Vue-Store.
- **Problem:** Volle State-Management-Frameworks wären Overhead für eine bestehende Vanilla-Codebasis.
- **Lösung:** Ein **einfacher EventTarget-Bus** reicht: zentraler Modul-Store (`getWindowState`, `subscribeWindowState`) plus **`window.dispatchEvent(new CustomEvent("janus:window-state", …))`** (oder ein kleines `new EventTarget()` als eigener Bus) für lose Kopplung. **CustomEvent + Listener** (oder Subscription-Callback) decken komplexe UI-Zustände ab und sparen Overhead gegenüber einem Framework-Store.
- **Location:** `frontend/js/window-state.js`
- **Confidence:** High (Task 022)
- **Tags:** Task022, DualWindow, VanillaJS, CustomEvent, StateStore

## [PATTERN] #UX #Layout Layout Context Preservation (Dual-Window)
- **Kontext:** Zwei Chat-Fenster nebeneinander — naheliegend: **50/50-Flex** oder Full-Width pro Pane.
- **Problem:** Volle Breite pro Fenster **zerstört die vertraute UX** des bisherigen **kompakten** Einzelfensters (~600×700px); Nutzer empfinden das Layout als „fremd“ oder überladen.
- **Lösung:** **Ursprüngliche Fenster-Dimensionen beibehalten** (CSS-Variablen, feste Startgröße, rechts freier Raum); linkbündig an die Sidebar; optional schwebend mit Drag/Resize statt starrem Vollflächen-Split. **Kompaktheit > Bildschirm ausfüllen**, solange kein explizites User-Ziel „maximale Fläche“ existiert.
- **Location:** `frontend/css/style.css` (`--dual-chat-host-width`, `--dual-chat-host-height`), `#chat-view #chat-window-A|B`
- **Confidence:** High (Task 022)
- **Tags:** Task022, DualWindow, Layout, UX, CompactChrome

## [PATTERN] #UX #Focus Focus Feedback Triade (Multi-Pane)
- **Kontext:** Zwei gleichwertige Fenster — der Nutzer muss **sofort** wissen, wohin Eingaben und Aufmerksamkeit gehen.
- **Problem:** **Farbe allein** (z. B. nur Akzent-Border) reicht nicht; bei Überlappung oder ähnlichen Flächen bleibt der aktive Bereich schwer erkennbar.
- **Lösung:** **Triade kombinieren:** (1) **deutlicher Rahmen** (z. B. 3px Außenlinie), (2) **innerer Glow** (`inset box-shadow` für „Licht im aktiven Fenster“), (3) **Dimmen inaktiver Bereiche** (z. B. **`opacity: 0.65`** auf dem gesamten inaktiven Fenster). Optional vierte Stütze: **Header-Anker** (aufgehellter Header + farbige Unterkante). Kurz: Rand + Innenglanz + Dimmen = intuitive Fokusführung.
- **Location:** `frontend/css/style.css` (`#chat-view #chat-window-A|B`, `.window-active`, Header-Selektoren)
- **Confidence:** High (Task 022)
- **Tags:** Task022, DualWindow, Focus, Accessibility, VisualHierarchy

## [PATTERN] #Architecture #Routing Contextual Routing Strategy — Global Standard vs. Local Override
- **Kontext:** Dual-Window-Chat mit **einer** Sidebar (`#provider-select` / `#model-select`) und **zwei** unabhängigen Panes (A/B).
- **Problem:** Ohne klare Hierarchie wäre unklar, ob die Sidebar oder der Fenster-Header „gewinnt“, wenn beide sichtbar sind.
- **Lösung:** **`effectiveProviderModelForWindow(windowId)`** in `chat.js`: (1) **Globaler Standard** — Werte aus der Sidebar, solange das Fenster **keinen** Override setzt (`provider`/`modelId` in `window-state` = `null`). (2) **Local Override** — sobald der Nutzer im **Fenster-Header** Provider/Modell wählt (oder explizit auf „Wie Sidebar“ zurückstellt), gelten die **persistierten** Fenster-Felder für Requests (Senden, Bild/PDF, TTS-Hints). Eine Funktion kapselt die Auflösung; kein doppelter Katalog-Pfad.
- **Lesson:** **Eine** Wahrheitsquelle für den Katalog (Sidebar + `fillModelOptionsIntoSelect`); **zwei** Ebenen der **Auswahl** — global vs. pro Fenster — mit expliziter Override-Semantik statt implizitem „letzter Klick gewinnt“.
- **Location:** `frontend/js/window-state.js` (`setWindowProvider`, `setWindowModel`), `frontend/js/chat.js` (`effectiveProviderModelForWindow`), `frontend/js/app.js` (`syncChatWindowHeaderLlm`, `fillModelOptionsIntoSelect`)
- **Confidence:** High (Task 024, verifiziert)
- **Tags:** Task024, DualWindow, LLM, Routing, Override, Sidebar

## [PATTERN] #UX #Layout Zwei-Zeilen-Header — vertikaler Stack gegen horizontales „Crushing“
- **Kontext:** Zwei Chat-Fenster nebeneinander bei **~600px** effektiver Fensterbreite pro Pane (Task 022 Layout Preservation).
- **Problem:** **Titel + zwei Dropdowns + Reset/Drag** in **einer** horizontalen Zeile führt zu **Layout-Crushing**: Schrift bricht hässlich, `<select>` schrumpfen auf Mindestbreite, Lesbarkeit leidet.
- **Lösung:** **Zwei-Zeilen-Header:** Zeile 1 nur **Chrome** (Reset, Drag, Titel); Zeile 2 dediziertes **Grid** für Provider- und Modell-`<select>` (`0.9fr` / `1.1fr`). Vertikaler Stack gibt beiden Zeilen volle Zeilenbreite — stabilere UX bei Dual-Window ohne breitere Viewport-Breite.
- **Lesson:** Bei **multi-pane kompakter Breite** zuerst **Zeilen aufteilen**, bevor horizontale Flex-Kämpfe zwischen Titel und Controls entstehen.
- **Location:** `frontend/index.html` (`.chat-window-header-row` / `.chat-window-header-controls`), `frontend/css/style.css`
- **Confidence:** High (Task 024, verifiziert)
- **Tags:** Task024, DualWindow, Header, Responsive, CompactChrome

## [PATTERN] #UX #VisualHierarchy Visual Hierarchy over Clutter
- **Kontext:** Task 025 — Navigation Sync / **Clean List Policy** für die Sidebar-Chatliste bei zwei Fenstern.
- **Problem:** Permanente **A/B-Badges** oder farbige Flächen auf **jeder** Zeile erzeugen „Bonbon-Look“: hohe visuelle Last, schwer zu scannen, wichtige Information (Titel) tritt zurück.
- **Lösung:** **Status-only** sichtbar: schmale **Linien-Marker** links nur, wenn ein Chat **wirklich** in A/B liegt; **Zuweisung** (in A/B öffnen) als **Hover-/Focus-within-Actions** (`chat-item-assign`), halbtransparent, ohne Dauerpräsenz.
- **Lesson:** **Hierarchie vor Lärm** — Interaktion, die selten gebraucht wird, nicht dauerhaft rendern; stattdessen ruhige Basis + kontextuelle Aktionen.
- **Location:** `frontend/js/chat-manager.js`, `frontend/css/style.css` (`#chat-list .chat-item`, `.chat-item-assign`)
- **Confidence:** High (Task 025, verifiziert)
- **Tags:** Task025, Sidebar, DualWindow, CleanList, HoverActions

## [PATTERN] #UX #Consistency The Color Anchor (Multi-Window)
- **Kontext:** Task 022–025 — Zwei Fenster, eine Sidebar, viele gleichartige Flächen.
- **Problem:** Ohne **wiedererkennbare Verknüpfung** zwischen Sidebar und Arbeitsfläche muss der Nutzer **raten**, welcher Chip/Titel zu welchem Fenster gehört.
- **Lösung:** **Ein Anker:** dieselben CSS-Variablen **`--color-pane-a`** (Lila) und **`--color-pane-b`** (Cyan) für **Active-Chip**, **Listen-Marker**, **Header-Streifen** und **Fokus-Glow** des jeweiligen Fensters. Ein Blick von der Sidebar zum Fenster bestätigt die Zuordnung **farbig 1:1**.
- **Lesson:** **Farbe als semantisches Kabel** zwischen entfernten UI-Regionen — stärker als Text-Labels allein, besonders bei kompaktem Layout.
- **Location:** `frontend/src/styles.css` (`:root`), `frontend/css/style.css` (Chips, Header, `#chat-view #chat-window-*`)
- **Confidence:** High (Task 025, verifiziert)
- **Tags:** Task025, DualWindow, ColorSystem, Consistency, Sidebar

## [PATTERN] #Architecture #Persistence Warm Start Persistence Strategy
- **Kontext:** Epic **Window State Persistence** — Neustart soll **Chats** und **Sichtbarkeit von B** wiederherstellen, nicht aber zufällige Fensterpositionen.
- **Problem:** Alles in einem JSON zu speichern vermischt **logischen Arbeitszustand** (welcher Chat wo, ist B offen) mit **physischem Chrome** (Pixel-Position nach Drag) — fehleranfällig, plattformabhängig, schwer zu migrieren.
- **Lösung:** **Trennung:** (1) **`localStorage`** (`janus_window_workspace_v1`) nur **logisch** — `chatA`/`chatB`, `activeWindowId`, `isOpenB`; bei jedem `emit()` aus `window-state.js`. (2) **Layout** bewusst **nicht** persistieren; nach `loadChats()` **`resetChatWindowLayout("A"|"B")`** für Standard-Andockung (`--dual-chat-host-*`). DOM der Fenster bleibt erhalten (**Content persistent**), nur Anzeige/State getrennt.
- **Lesson:** **Warm start** = reproduzierbare **Semantik** + vorhersagbare **Geometrie**; physisches Layout separat oder gar nicht speichern, wenn das Produkt eine **Default-Dock**-Erwartung hat.
- **Location:** `frontend/js/window-state.js`, `frontend/js/app.js`, `frontend/js/chat-manager.js` (`loadChats` Restore-Pfad)
- **Confidence:** High (verifiziert)
- **Tags:** Task025, Persistence, localStorage, Layout, DualWindow

## [PATTERN] #Frontend #Events Hierarchical Event Handling
- **Kontext:** Task 026 — **`.chat-item-actions`** (`btn-assign-a` / `btn-assign-b`) innerhalb einer **`.chat-item`**, deren **`.chat-title`** separat **`loadChat(..., getActiveWindowId())`** auslöst.
- **Problem:** Ein Klick auf A/B würde **bubbleln** und ggf. die **Titel-Logik** oder Eltern-Handler mit auslösen — doppeltes Laden oder falsches Ziel-Fenster.
- **Lösung:** Auf den Zuweisungs-Buttons **`e.stopPropagation()`** — das Ereignis steigt **nicht** zur Titel-Zeile / zum Listeneintrag auf; die **Hover-Action** bleibt eine **eigene Schicht** neben der Haupt-Klick-Semantik (Titel = aktives Fenster, Buttons = explizites A/B).
- **Lesson:** Bei **überlappenden** Interaktionsflächen im selben Composite-Widget Schichten per **Propagation-Stop** trennen, statt globale „nur ein Handler“-Sonderfälle.
- **Location:** `frontend/js/chat-manager.js` (`renderChatList`, Listener auf `.btn-assign-a` / `.btn-assign-b`)
- **Confidence:** High (Task 026, verifiziert)
- **Tags:** Task026, DOM, stopPropagation, Sidebar, DualWindow

## [PATTERN] #UX #Animation Visual Confirmation via Animation
- **Kontext:** Task 026 — **`loadChat`** ist **asynchron** (Fetch + DOM); der Nutzer braucht ein **sofortiges** Signal, dass „in **diesem** Fenster“ gearbeitet wird.
- **Problem:** Reines await ohne Feedback fühlt sich nach **Hintergrundaktion** an; Fokus allein (`setActiveWindow`) ist subtil.
- **Lösung:** Nach erfolgreichem Laden **`flashWindowAssignFeedback(windowId)`** — temporäre Klasse **`janus-assign-feedback--a|b`** auf **`#chat-window-A|B`**, CSS **`@keyframes janus-assign-pulse-a`** / **`janus-assign-pulse-b`** verstärken kurz den **bestehenden** Pane-**`box-shadow`** (Puls, ~0,7s). So ist der **Erfolg** sichtbar, ohne Toast-Overhead.
- **Lesson:** **Kurze, lokale Keyframe-Animation** auf dem **Zielobjekt** der Aktion verkoppelt async Arbeit mit **räumlicher Bestätigung** — besonders bei Multi-Window.
- **Location:** `frontend/js/chat-manager.js` (`flashWindowAssignFeedback`), `frontend/css/style.css` (`@keyframes janus-assign-pulse-a|b`, `.janus-assign-feedback--a|b`)
- **Confidence:** High (Task 026, verifiziert)
- **Tags:** Task026, CSS, Keyframes, Feedback, DualWindow

## [PATTERN] #UX #CSS Hover States vs. Visibility
- **Kontext:** Task 026 — **`.chat-item-actions`** soll standardmäßig **unsichtbar**, bei **Hover/Focus** sichtbar sein.
- **Problem:** **`display: none`** nimmt das Element aus dem **Layout-Fluss** und aus der **Tab-Reihenfolge**; zudem kann **`display` togglen** zu **Layout-Sprüngen** führen, wenn Nachbarn neu fließen.
- **Lösung:** **`opacity: 0`** + **`visibility: hidden`** + **`pointer-events: none`** im Ruhezustand; bei **`.chat-item:hover`** / **`:focus-within`** zurück auf sichtbar/interaktiv. Der Flex-Slot für die Action-Gruppe **bleibt reservierbar** (Box bleibt im Flex-Row-Modell konsistent), **`:focus-within`** funktioniert mit sichtbar gemachten Kindern — besser als hartes **`display: none`** auf den Buttons.
- **Lesson:** **`visibility` + `opacity`** statt **`display: none`**, wenn **Layout-Stabilität** und **Tastatur/Fokus** mit **Hover-Reveal** kombiniert werden sollen.
- **Location:** `frontend/css/style.css` (`.chat-item-actions`, `#chat-list .chat-item:hover` / `:focus-within`)
- **Confidence:** High (Task 026, verifiziert)
- **Tags:** Task026, CSS, visibility, opacity, Accessibility

## [PATTERN] #Backend #SQLite #P0 SQLite Schema Drift Protection (Emergency Fix)

- **Kontext:** Task 027 — ORM und Pydantic erwarten **`chats.category`**, die **physikalische** SQLite-Datei unter `%APPDATA%/Janus Projekt/janus.db` hatte die Spalte nach einem **Alembic/Drift-Szenario** nicht → **`GET /api/chats`** endete mit **500** (SQLAlchemy kann Spalte nicht laden); der Browser meldet oft zusätzlich **CORS**, weil die Fehlerantwort ohne brauchbare CORS-Header wirkt.
- **Problem:** Zwei Welten: **Code + Alembic-Revision** vs. **lange genutzte AppData-DB** (Migration nie durchlaufen, oder `alembic upgrade` an älterem Kopf gescheitert). Die alte Hilfsfunktion **`_ensure_sqlite_schema_migrations`** hatte zudem einen **Early-Return**, sobald **`users.suggestion_mode`** schon existierte — dann wurden **keine weiteren** `ALTER TABLE`-Schritte mehr ausgeführt, u. a. **`chats.category`** blieb aus.
- **Lösung:** (1) **Refactor** der Funktion: **getrennte Blöcke** pro Tabelle/Spalte — zuerst `users.suggestion_mode` falls nötig, danach **`chats.category`** per `inspect` + `ALTER TABLE chats ADD COLUMN category VARCHAR NOT NULL DEFAULT 'general'` nur wenn die Spalte fehlt. (2) **Einmaliger P0-Fix** auf der betroffenen DB per SQL/Script, bis alle Clients neu starten. (3) Optional weiterhin **Alembic** für saubere Revision-Historie auf frischen Deployments.
- **Lesson:** Bei **SQLite + Desktop-Pfad** immer **defensive Startup-Migrationen** für neue Spalten einplanen; **kein** „ein Flag, dann return“ über mehrere unabhängige Schema-Änderungen hinweg — sonst bleibt Drift unsichtbar bis Production-SELECT.
- **Location:** `backend/data/database.py` (`_ensure_sqlite_schema_migrations`, Aufruf aus `init_db()`)
- **Confidence:** High (Task 027 P0, verifiziert)
- **Tags:** Task027, SQLite, Drift, Alembic, P0, FastAPI

## [LESSON] #UX #Architecture The Power of the Layer Model (Janus AI OS — UX closure 2026-04-13)

- **Kontext:** Nach Abschluss der Epic-Linie **Task 021–028** (Dual-Window, Binding, Navigation, Actions, Grouping, Dock) war klar, dass die **Usability skaliert**, weil drei Schichten strikt getrennt bleiben — statt alles in „eine große Chat-Oberfläche“ zu pressen.
- **Die drei Schichten:**
  1. **Chat (Denken)** — Composer, Stream, Verlauf: primärer kognitiver Loop; hier passiert Modellierung und Dialog.
  2. **Fenster (Kontext)** — Dual-Pane A/B, Chat-Zuordnung, **pro-Fenster** Provider/Modell (`window-state`): *welcher* Verlauf und *welches* LLM gerade gilt.
  3. **Dock (Werkzeuge)** — Taskleiste unten: Minimieren/Wiederherstellen für **parallele** Werkzeuge (Wissensdatenbank, Image Studio, Bildgalerie) **ohne** den Denk-Kontext der Chat-Fenster zu verdrängen.
- **Lesson:** Wenn **Denken**, **Kontext** und **Werkzeuge** jeweils eine eigene **mentale Adresse** im UI haben, können Nutzer parallel arbeiten (Chat offen, Panel minimiert in der Leiste) — **Skalierung durch Entkopplung**, nicht durch mehr Widgets auf derselben Fläche.
- **Location:** `frontend/js/window-state.js`, `frontend/js/dock.js`, `frontend/js/chat.js`, `frontend/css/style.css`
- **Confidence:** High (Epic COMPLETE 2026-04-13)
- **Tags:** JanusAIOS, Task021-028, LayerModel, DualWindow, Dock, UX

## [LESSON] #UX #Design Iconography as Guidance (Janus AI OS — UX closure 2026-04-13)

- **Kontext:** Sidebar und Dock nutzen **wiedererkennbare Icons** mit **farblicher Semantik** — nicht nur Dekoration, sondern **Orientierung** bei vielen gleichartigen Einträgen.
- **Problem:** Ohne System wirken „noch ein Icon“ und „noch ein Panel“ gleich wichtig; **kognitive Last** steigt (Scan-Zeit, Fehlklicks).
- **Lösung — Farbkodierung als Kurzschluss:**
  - **Aktion / Erzeugung** (z. B. **Image Studio**, warmes **Gold/Amber**) signalisiert: „Hier startest du einen aktiven Erzeugungsflow.“
  - **Konsum / Bestand** (z. B. **Bildgalerie**, **neutrales Grau**) signalisiert: „Hier siehst du, was schon da ist.“
  - **Wissens-/Referenz-Modus** (z. B. **Wissensdatenbank**, **Violett**) signalisiert: Lesen, Dokumente, RAG — nicht dasselbe wie Chat oder Studio.
  - **Pane-Zuordnung** bleibt über **`--color-pane-a` / `--color-pane-b`** (Lila vs. Cyan) mit Sidebar und Fenster-Chrome **1:1** verkoppelt (siehe Pattern „The Color Anchor“).
- **Lesson:** **Icon + Farbe = eine Zeile Dokumentation im Kopf**; Nutzer sortieren Modus schneller als bei rein textuellen oder einfarbigen Listen.
- **Location:** `frontend/css/style.css` (Sidebar-Icons, `.dock-item--*`), `frontend/index.html`
- **Confidence:** High (Epic COMPLETE 2026-04-13)
- **Tags:** JanusAIOS, Iconography, ColorSemantics, ActionVsConsumption, Dock, Sidebar

## [PATTERN] #Frontend #StateManagement Dock Restore vs. Toggle Intent (Session 2026-04-13)

- **Kontext:** **Wissensdatenbank** und **Bildgalerie** am Dock — Klick auf das **minimierte** Taskleisten-Icon soll **immer wiederherstellen**, während die **Sidebar** ohne Argumente oft **Toggle** (offen → minimieren) bedeutet.
- **Problem:** Eine gemeinsame Bridge (`openJanusKnowledge()` ohne Args) wurde als **„Toggle-Intent“** behandelt: wenn der Zustand kurz als **sichtbar** galt, konnte derselbe Code-Pfad **sofort wieder minimieren** — es wirkte wie „Klick öffnet nicht“. Zusätzlich: **`window.openJanusKnowledge` nur setzen, wenn noch keine Function existiert** ließ einen **fremden Stub** dauerhaft gewinnen.
- **Lösung:**
  1. **Explizites Kanal-Signal:** `CustomEvent("open-knowledge-center", { detail: { fromTaskbarDock: true } })` vom Dock-Button; `openBridge(documentId, { fromTaskbarDock })` **überspringt** den Toggle-Zweig und führt immer **`openKnowledgeCenter`** aus (Position + Dokumente).
  2. **`window.openJanusKnowledge` immer** auf die Legacy-Bridge setzen (kein „nur wenn frei“), damit kein alter Platzhalter stehen bleibt.
  3. **Fallback:** Nach dem Event `dockOpen("knowledge-center")`, falls State noch **minimiert/geschlossen** (z. B. Listener fehlte).
  4. **Galerie:** eigenes Dock-Modul `gallery` in `window-state.js`; `subscribeWindowState` steuert Sichtbarkeit; **`applyDockUi`** darf bei fehlenden Chat-A/B-Buttons **nicht** vorzeitig `return`en, sonst bleiben Dock-Module-Buttons stehen.
- **Location:** `frontend/js/dock.js`, `frontend/js/knowledge-center.js`, `frontend/js/gallery.js`, `frontend/js/window-state.js`
- **Confidence:** High (verifiziert in Session)
- **Tags:** Task028, Dock, CustomEvent, ToggleVsRestore, window-state, JanusAIOS

## [PATTERN] #Pydantic #SchemaStrictness "Structural Validation"
- **Kontext:** Task 034 Schema Lockdown — Video-Suchergebnisse müssen konsistente Datenstruktur haben.
- **Problem:** Fehlende Pflichtfelder in Tool-Resultaten führen zu stillem Datenverlust oder Pydantic-Validierungsfehlern.
- **Lösung:** Pflichtfelder `query` und `retrieved_at` (ISO-String) im data-Dictionary des Video-Suchergebnisses. Strukturelle Validierung verhindert, dass unvollständige Daten weitergegeben werden.
- **Ergebnis:** Keine stille Validierungsfehler mehr; saubere Pydantic-Validierung im Backend-Log; stabile `modal_request` Daten für das Frontend.
- **Location:** `backend/tools/video_tools.py` (data-Dictionary in feed_authority_result und standard result)
- **Confidence:** High (Task 034)
- **Tags:** Pydantic, SchemaStrictness, StructuralValidation, Task034

## [PATTERN] #Heuristics #Precision "Geo-Channel Separation"
- **Kontext:** Task 035 Search Precision — Städtenamen wie Rom, Paris dürfen nicht als YouTube-Handles missverstanden werden.
- **Problem:** Channel-Resolution interpretiert geografische Begriffe fälschlich als YouTube-Channel-Namen (z.B. "Geschichte von Rom" → Suche nach @rom statt Stadt-Dokumentation).
- **Lösung:** `GEO_REJECTION_LIST` mit Städtenamen (rom, paris, berlin, wien, tokio, etc.); `_is_geo_rejected_hint()` Guard prüft extrahierte Hints gegen Liste; bei Treffer wird Channel-Lock verhindert und Global Search erzwungen.
- **Ergebnis:** "Geschichte von Rom" liefert wieder Stadt-Dokumentation statt Creator-Handle-Videos; höhere Relevanz bei geografisch-allgemeinen Anfragen.
- **Location:** `backend/tools/video_tools.py` (GEO_REJECTION_LIST, _is_geo_rejected_hint)
- **Confidence:** High (Task 035)
- **Tags:** Heuristics, Precision, GeoChannelSeparation, VideoSearch, Task035

## [PATTERN] #Security #Coherence "Self-Healing Identity"
- **Kontext:** Task 036 Auth-Coherence — Provider-Wechsel muss automatisch den korrekten API-Key nachladen.
- **Problem:** Nach PROVIDER-COHERENCE Korrektur (z.B. openai → gemini) bleibt der alte API-Key erhalten, was zu 400er Auth-Fehlern führt.
- **Lösung:** Automatischer API-Key-Refresh nach Provider-Korrektur via `keyring.get_password('Janus-Projekt', detected_provider)`; Ollama Placeholder-Key; [AUTH-COHERENCE] Logging.
- **Ergebnis:** Auth & Provider Coherence sind vollständig self-healing; keine 400er Auth-Fehler mehr bei Provider-Drift.
- **Location:** `backend/services/chat_orchestrator.py` (_execute_generation, lines 1541-1559)
- **Confidence:** High (Task 036)
- **Tags:** Security, Coherence, SelfHealingIdentity, AuthRefresh, Task036

## [PATTERN] #Orchestration #OpenAI "The Declarative Tool-Force Guard"
- **Kontext:** Task 042 Forced Tool-Call — Wenn ein Tool-Call erzwungen wird (tool_choice), muss das Backend sicherstellen, dass die Tool-Definition in der tools-Liste enthalten ist.
- **Problem:** Fehlt die Tool-Definition (z.B. durch Skill-Filterung), gibt OpenAI einen 400er API-Fehler, selbst wenn tool_choice korrekt gesetzt ist.
- **Lösung:** Re-Injection Guard prüft, ob forced_tool_name in params['tools'] vorhanden ist; wenn nicht, wird die Tool-Definition via skill_router.get_tool_definition() nachgeladen und injiziert; Logging [OPENAI_SHIM] Re-injecting missing forced tool definition.
- **Ergebnis:** 400er API-Fehler verschwinden; PDF-Audit-Workflow funktioniert wie geplant: Upload → Forced Tool Call → Korrekte Inhaltsanalyse → Zusammenfassung.
- **Location:** `backend/llm_providers/openai/service.py` (iter_openai_chat_completion_stream_events, lines 113-138)
- **Confidence:** High (Task 042, Task 044)
- **Tags:** Orchestration, OpenAI, ToolForceGuard, ReInjection, Task042, Task044

## [PATTERN] #API #Interoperability "Naming-Shim Strategy"
- **Kontext:** Task 043 OpenAI Naming Shim — Interne saubere Architekturen (domain.action) müssen gegenüber Provider-APIs mit strikten Regex-Regeln normalisiert werden.
- **Problem:** OpenAI akzeptiert keine Punkte in Tool-Namen (^[a-zA-Z0-9_-]+$ Pattern), was zu BadRequestError 400 führt.
- **Lösung:** Naming-Shim vor API-Aufruf normalisiert Tool-Namen (domain.action → domain_action) in Tool-Liste und tool_choice; Logging [OPENAI_SHIM] Normalizing tool name from 'domain.action' to 'domain_action'.
- **Ergebnis:** OpenAI-API akzeptiert Tool-Namen ohne BadRequestError; interne Architektur bleibt sauber (domain.action) während Provider-API-Kompatibilität gewährleistet wird.
- **Location:** `backend/llm_providers/openai/service.py` (iter_openai_chat_completion_stream_events, lines 93-111)
- **Confidence:** High (Task 043)
- **Tags:** API, Interoperability, NamingShim, OpenAI, Normalization, Task043

## [PATTERN] #UX #Filesystem "The Flattened Result Strategy"
- **Kontext:** Task 039 PDF Storage Path — Arbeitsergebnisse (Generierte PDFs) gehören in den Workspace-Root, während Referenzmaterial (Uploads) in Unterordner gekapselt werden sollte.
- **Problem:** Alle PDFs im selben Ordner führen zu Unübersichtlichkeit; generierte Dokumente (wertvollste Ergebnisse) sind schwer auffindbar unter vielen Uploads.
- **Lösung:** Generierte PDFs in ~/Documents/JanusPDFs (Workspace-Root), Uploads in ~/Documents/JanusPDFs/Uploads (Unterordner); os.makedirs mit parents=True, exist_ok=True.
- **Ergebnis:** Maximale Auffindbarkeit der wertvollsten Dateien; klare Trennung zwischen Arbeitsergebnissen und Referenzmaterial; bessere UX bei Dateiverwaltung.
- **Location:** `backend/tools/pdf_generator.py` (get_secure_absolute_path, line 1323), `backend/api/routers/rag.py` (upload-document, line 99)
- **Confidence:** High (Task 039, Task 040)
- **Tags:** UX, Filesystem, WorkspaceStrategy, PDFStorage, Task039, Task040

## [PATTERN] #Orchestration #Resilience "Pre-filled Tool Injection"
- **Kontext:** BUG-ORCH-002 — Audit-Workflow mit forced_tool_args muss deterministisch den Tool-Call ausführen, ohne auf das LLM zu warten.
- **Problem:** Die ursprüngliche Implementierung injizierte eine `fake_assistant_message` mit `tool_calls` in `gateway_kwargs["messages"]`, was OpenAI als Verstoß gegen den Chat Completions Vertrag (assistant tool_calls ohne matching tool-role replies) abgelehnt hat → 400 BadRequest.
- **Lösung:** **Initial-Loop-State Pattern**: Bei Iteration 0 mit vorhandenen `forced_tool_args` wird der LLM-Call übersprungen und stattdessen ein synthetisches Tool-Call-Response generiert, das direkt in die Tool-Ausführung übergeht. Tool-Namen werden für OpenAI normalisiert (Punkt → Unterstrich).
- **Ergebnis:** Keine 400er Fehler mehr; deterministische Tool-Ausführung für Audit-Workflows; saubere Message-History bei OpenAI.
- **Location:** `backend/services/orchestrator/execution_engine.py` (run_tool_loop lines 1038-1109, run_tool_loop_stream lines 1937-2056)
- **Confidence:** High (BUG-ORCH-002)
- **Tags:** Orchestration, Resilience, ToolInjection, AuditWorkflow, OpenAI, BUG-ORCH-002

## [PATTERN] #Pydantic #Safety "Alias-Safe ExecutionResponse"
- **Kontext:** BUG-ORCH-002 — ExecutionResponse Schema mit Aliases für abwärtskompatible Felder.
- **Problem:** Pydantic v2 Aliases (z.B. `alias="usage"` für `token_usage`) können bei direktem `.get()` Zugriff fehlschlagen, wenn der Key nicht dem Alias entspricht.
- **Lösung:** Gehärteter Zugriff mit `getattr()` statt `.get()` und expliziter Alias-Auflösung. Fallback-Ketten für optionale Felder: `getattr(obj, 'field', None) or obj.model_dump().get('field')`.
- **Ergebnis:** Stabile Feld-Zugriffe trotz Pydantic Aliases; keine KeyError bei Schema-Evolution.
- **Location:** `backend/services/orchestrator/schemas.py` (ExecutionResponse)
- **Confidence:** High (BUG-ORCH-002)
- **Tags:** Pydantic, Safety, AliasHandling, ExecutionResponse, SchemaEvolution, BUG-ORCH-002

