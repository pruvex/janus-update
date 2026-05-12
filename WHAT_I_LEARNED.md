# KNOWLEDGE BASE: WHAT I LEARNED
**Zweck:** Langzeitgedächtnis für AI Studio, Cursor und Windsurf.
**Regel:** Jeder gelöste Bug darf nur EINMAL gelöst werden.

## [PATTERN] #TemplateLiteralInComments "Template literals in comments can be evaluated by JavaScript parsers causing reference errors"
- **Kontext:** BACKLOG-025 Frontend Rendering Failure. JavaScript-Fehler "win is not defined" blockierte das Rendering von Assistant-Nachrichten nach SSE-Stream-Initiierung. Der Fehler trat in `frontend/js/chat.js` auf.
- **Problem:** Template literals in Kommentaren (z.B. `${win}`) werden von einigen JavaScript-Parsern/Build-Tools evaluiert, obwohl sie in Kommentaren stehen. Wenn die referenzierte Variable nicht im Scope existiert, wird ein ReferenceError geworfen ("win is not defined"), der den Code-Block invalidiert.
- **Lösung:** Template literals in Kommentaren zu literalen Strings ändern (z.B. `${win}` → `{windowId}`). Keine Template-Literal-Syntax in Kommentaren verwenden, es sei denn sie sind explizit als Platzhalter für Dokumentationszwecke gedacht und werden nicht evaluiert.
- **Härtung:** Code-Review-Check: Prüfe ob `${...}` in Kommentaren verwendet wird. Linting-Regel: ESLint-Regel für template-literal-in-comments implementieren. Build-Process: Prüfe ob Parser Kommentare evaluiert und deaktiviere dies wenn möglich.
- **Tripwire:** "is not defined" Fehler in Kommentaren mit Template-Literal-Syntax. Build schlägt fehl mit ReferenceError obwohl Code syntaktisch korrekt ist.
- **Location:** `frontend/js/chat.js` (line 747), implementiert 2026-05-12.
- **Epic:** BACKLOG-025 — Frontend Rendering Failure
- **Confidence:** High
- **Tags:** TemplateLiteral, Comments, JavaScriptParser, ReferenceError, BACKLOG025

## [PATTERN] #DynamicFallbackErrorDetails "Dynamic fallback with specific error details instead of generic messages"
- **Kontext:** BACKLOG-006 Generische Fehlermeldung statt spezifischer Fehlerdetails. Wenn ein Tool-Aufruf fehlschlägt, zeigten alle Provider (GPT, Gemini) eine generische Fallback-Nachricht "Ich konnte diesmal keine stabile Antwort erzeugen..." statt spezifischen Fehlerdetails.
- **Problem:** Statischer `fallback_summary` in execution_dispatcher.py ohne Fehlerdetails. Exception-Handler in execution_engine.py verwenden denselben statischen Fallback ohne Kontext. User erhält keine hilfreichen Informationen über den tatsächlichen Fehler (Tool-Name, Fehlercode, Fehlermeldung, Provider, Model).
- **Lösung:** Dynamische Fallback-Zusammenfassung implementieren: (1) `_build_dynamic_fallback_summary()` Helper-Funktion erstellen, die Tool-Name, Fehlercode, Fehlermeldung, Provider und Model in eine spezifische Fehlermeldung formatiert. (2) Tool-Fehler-Tracking mit `_last_tool_error` Variable in `run_tool_loop()` und `run_tool_loop_stream()`. (3) Error-Details aus Tool-Ergebnissen extrahieren (error_code, error_message). (4) Alle Fallback-Verwendungen mit dynamischem Fallback aktualisieren (Exception, Stream-Crash, leere Tool-Round, leeres Text-Ergebnis). (5) Backend-Logs behalten vollständige Exception-Details mit `exc_info=True`.
- **Härtung:** Audit muss prüfen, ob alle Fallback-Verwendungen dynamischen Fallback verwenden, wenn `_last_tool_error` verfügbar ist. Tripwire: Generische Fallback-Nachricht trotz verfügbarer Error-Details.
- **Location:** `backend/services/orchestrator/execution_engine.py`, `backend/services/orchestrator/execution_dispatcher.py`.
- **Epic:** BACKLOG-006 — Dynamic Error Messages — 2026-05-11.
- **Confidence:** High
- **Tags:** DynamicFallback, ErrorHandling, ToolErrors, FallbackSummary, BACKLOG006

## [PATTERN] #DefaultValueConsistency "Spec and task default values must match implementation"
- **Kontext:** TASK-001 Dark Mode Toggle. Final audit found default=True in code but spec/task required default=False (Light Mode as standard).
- **Problem:** Database model and Pydantic schema default values must exactly match spec requirements. Mismatch causes user-facing behavior to diverge from documented behavior.
- **Lösung:** When implementing boolean preference fields, verify default value in three places: (1) SQLAlchemy Column default, (2) Pydantic Field default, (3) Spec/task documentation. For "Light Mode as standard" requirement, use default=False.
- **Härtung:** Audit must check all three locations for consistency. Tripwire: Spec says "X as standard" but code has default=True for X.
- **Location:** `backend/data/models.py`, `backend/data/schemas.py`, spec documentation.
- **Epic:** TASK-001 Dark Mode Toggle — 2026-05-10.
- **Confidence:** High
- **Tags:** DefaultValueConsistency, SpecCompliance, DatabaseDefaults, PydanticDefaults, TASK001

## [PATTERN] #RealModuleE2E "E2E tests must import real UI modules — never duplicate production UI logic inside tests"
- **Kontext:** TASK-068 Auto Update System. `/2_final-audit` found that the first Playwright E2E test for the update UI duplicated renderer logic inline instead of exercising the real `frontend/js/update-ui.js` implementation. This created a false-positive risk for the Electron auto-update UI.
- **Problem:** If an E2E test reimplements UI behavior inside `page.addInitScript()` or a test-local helper, the test validates the duplicate, not production code. Production imports, exports, DOM wiring, lifecycle order, and IPC bindings can be broken while tests still pass.
- **Lösung:** UI E2E tests must load or import the real production module and mock only external boundaries such as Electron IPC. For update UI tests, use real `update-ui.js`, expose a controlled `window.electron` mock, wait for listener registration/state propagation, and verify rendered DOM plus IPC calls.
- **Härtung:** Audit Playwright specs for inline copies of production UI logic. Syntax-check imported modules (`node -c frontend/js/update-ui.js`, `node -c frontend/js/app.js`) and run the real E2E spec (`npx playwright test tests/e2e/auto-update.spec.js`). Keep Playwright `testMatch` aligned to the canonical `.spec.js` file and remove temporary duplicate `.spec.cjs` patterns.
- **Tripwire:** Tests pass while the app fails to import a module, UI selectors do not exist in production, or production button clicks do not call IPC. Another tripwire is a large `page.addInitScript()` block that recreates rendering functions instead of importing the real module.
- **Location:** `frontend/js/update-ui.js`, `frontend/js/app.js`, `tests/e2e/auto-update.spec.js`, `playwright.config.js`, implementiert 2026-05-04.
- **Epic:** TASK-068 — Auto Update System
- **Confidence:** High
- **Tags:** RealModuleE2E, MockOverMock, FalsePositiveTests, Playwright, ElectronIPC, AutoUpdate, TASK068

## [PATTERN] #BrowserE2EInternalApiKey "Vite + Playwright gegen echtes Backend: X-Janus-Internal-Key nachziehen"
- **Kontext:** TASK-069 Capability Overview E2E. FastAPI schützt `/api/*` mit `api_key_auth` (`X-Janus-Internal-Key`). Im Electron-App-Pack injiziert `frontend/js/app.js` den Schlüssel über `window.electron.getApiKey()` in jeden Backend-`fetch`. Im reinen Vite-Browser (Playwright gegen `localhost:5173`) gibt es keinen Electron-Bridge → **kein** Header auf `/api/chats` und `/api/chat/stream`.
- **Problem:** JWT allein genügt nicht; `/api/users/me` schlägt ebenfalls fehl ohne Internal Key (Router-Dependency). Symptom: leeres Chat-UI, Textarea wird nicht geleert (`ensureChatForWindow` scheitert still), keine `.message.assistant`.
- **Lösung:** In Playwright vor `page.goto` eine Route registrieren (`http://127.0.0.1:8001/api/**` und `http://localhost:8001/api/**`), die denselben Key wie das Backend aus `%APPDATA%\Janus Projekt\config.json` (`api_key`) als Header durchreicht. Zusätzlich echten Produktpfad nutzen: `await import('/js/chat.js').sendMessage('A')` statt frágilen Button-Klicks (Taskleiste `#dock-bar` fängt Pointer ab).
- **Härtung:** Vor „Neuer Chat“ Region „Chat-Fenster A“ fokussieren (`getActiveWindowId`); auf erfolgreiches `POST /api/chats` warten; bei gemeinsamer SQLite-E2E-DB `test.describe.configure({ mode: 'serial' })` gegen parallele Worker.
- **Tripwire:** E2E „hängt“ in `sendMessage` oder findet keine Assistant-Message trotz gültigem JWT.
- **Location:** `tests/e2e/capability-overview.spec.js`, `frontend/js/app.js` (fetch-Wrapper), `backend/dependencies.py`, `backend/main.py`, implementiert 2026-05-04.
- **Epic:** TASK-069 — Capability Overview Response
- **Confidence:** High
- **Tags:** Playwright, FastAPI, api_key_auth, Vite, RealModuleE2E, TASK069, DockBar

## [PATTERN] #ContextualEntityResolution "Contextual Entity Resolver — Fuzzy + Temporal Disambiguation against calendar_snapshot before forced find_and_update_event"
- **Kontext:** TASK-065 Contextual Entity Resolver. Ziel: Vermeidung von falschen Mutationen durch unscharfe Titel-Matches. Das System muss vor dem Aufruf von `calendar.find_and_update_event` prüfen, ob der Nutzer-Text eindeutig auf einen bestehenden Kalender-Eintrag verweist.
- **Problem:** Ohne Entity Resolution könnte "Aldi" auf den falschen Aldi-Termin treffen (z.B. Aldi Nord statt Aldi Süd). Das Modell könnte versehentlich den falschen Termin mutieren. Fuzzy-Suche allein reicht nicht aus bei identischen Titeln an unterschiedlichen Daten.
- **Lösung:** **Contextual Entity Resolver mit Dispatcher Hints:**
  1. **Resolver Input:** `query` (Nutzer-Text), `snapshot` (calendar_snapshot aus Memory), `operation_type` ("MUTATION").
  2. **Resolution Strategy:** Rapidfuzz-Kaskade (token_set_ratio → partial_ratio → WRatio) + Temporal-Pre-Pass bei identischen Titeln (nächstes Datum gewinnt).
  3. **Dispatcher Hints:** `PROCEED` (resolved, pre-filled event_id), `FALLBACK_TO_LIST` (ambiguous/weak, force list_events), `CLARIFY_USER` (not_found, no tool call).
  4. **Guided Assistant Mode:** Bei PROCEED wird `event_id` und `title` in action_guidance injiziert. Das Modell muss zwingend diese Werte verwenden (KEINE Erfindung, KEINE Änderung).
  5. **Execution Dispatcher Integration:** Resolver wird in execution_dispatcher.py aufgerufen wenn `is_calendar_mutation` und `mutation_target` vorhanden sind. Result steuert `forced_tool` und `action_guidance`.
  6. **Fallback to API:** Wenn `event_id` vom Resolver geliefert wird, nutzt `find_and_update_event` direkten API-GET (Google Calendar API) statt Fuzzy-Suche (Performance + Genauigkeit).
- **Härtung:** Temporal-Pre-Pass löst Konflikte bei identischen Titeln deterministisch. Dispatcher Hints garantieren korrektes Tool-Choice. Guided Assistant Mode verhindert ID-Erfindung durch LLM.
- **Tripwire:** Wenn falscher Termin mutiert wird → Resolver nicht aufgerufen oder temporal logic fehlt. Wenn LLM eigene event_id erfindet → Guided Assistant Guidance fehlt oder wird ignoriert.
- **Location:** `backend/services/orchestrator/entity_resolver.py` (ContextualEntityResolver), `backend/services/orchestrator/execution_dispatcher.py` (Resolver integration), `backend/tools/calendar_tools.py` (event_id fast path), implementiert 2026-05-02.
- **Epic:** TASK-065 — Contextual Entity Resolver
- **Confidence:** High (Temporal-Pre-Pass deterministisch, Dispatcher Hints klare Steuerung, Guided Assistant Mode verhindert Halluzination).
- **Tags:** ContextualEntityResolution, EntityResolver, CalendarSnapshot, FuzzySearch, TemporalDisambiguation, DispatcherHints, GuidedAssistant, TASK065

## [PATTERN] #GuidedAssistantMutation "Guided Assistant Mode for Calendar Mutations — Pre-filled event_id + Title in action_guidance, LLM forced to use exact values"
- **Kontext:** TASK-065 Contextual Entity Resolver + TASK-067 Guided Assistant Mode. Ziel: Verhinderung von ID-Erfindung und falschen Mutationen durch das LLM. Das Modell muss die vom Entity Resolver aufgelösten Werte zwingend verwenden.
- **Problem:** Ohne Guided Assistant könnte das LLM eine eigene `event_id` erfinden oder den falschen Titel verwenden, was zu falschen Mutationen führt. Das Modell könnte auch versuchen, `calendar.list_events` aufzurufen statt direkt zu mutieren.
- **Lösung:** **Guided Assistant Mode mit Strict Constraints:**
  1. **Resolver Result Injection:** Wenn Resolver `PROCEED` zurückgibt, werden `event_id` und `original_title` in `action_guidance` injiziert.
  2. **Strict Instruction Block:** Guidance enthält klare Anweisung: "DEINE PFLICHT: 1. Rufe calendar.find_and_update_event auf. 2. Setze ZWINGEND event_title_query = X und event_id = Y — KEINE andere ID, KEIN anderer Titel."
  3. **Mutation Hammer:** `calendar_mutation_hammer` Directive wird angehängt mit zusätzlichen Sicherheitsregeln (VERBOTEN: event_id ignorieren, erfinden, ändern).
  4. **Schema Hint:** `event_title_query` Parameter-Name ist zwingend (NICHT 'query', 'title', 'event_name'). Schema-Description in schemas.py klärt dies.
  5. **Tool-Choice Enforcement:** `forced_tool = calendar.find_and_update_event` wird gesetzt, LLM hat keine Wahl.
  6. **Payload Freedom:** LLM darf die Mutations-Payload frei ausfüllen (new_description, new_start_time, etc.), aber `event_title_query` und `event_id` sind fix.
- **Härtung:** Strict Instruction Block mit klaren VERBOTEN-Regeln. Mutation Hammer als finaler Sicherheits-Check. Schema Hint verhindert Parameter-Namen-Konflikte.
- **Tripwire:** Wenn LLM eigene event_id verwendet → Guidance nicht injiziert oder wird ignoriert. Wenn LLM list_events aufruft → forced_tool nicht korrekt gesetzt. Wenn Parameter-Name falsch → Schema Hint fehlt.
- **Location:** `backend/services/orchestrator/execution_dispatcher.py` (Guided Assistant injection), `backend/services/orchestrator/prompt_registry.py` (calendar_mutation_hammer), `backend/data/schemas.py` (event_title_query hint), implementiert 2026-05-02.
- **Epic:** TASK-065 + TASK-067 — Contextual Entity Resolver + Guided Assistant Mode
- **Confidence:** High (Strict Constraints, Mutation Hammer, forced_tool enforcement).
- **Tags:** GuidedAssistantMutation, GuidedAssistant, StrictConstraints, MutationHammer, SchemaHint, ToolChoiceEnforcement, TASK065, TASK067

## [PATTERN] #DeicticFallback "Deictic Context Fallback — Pronoun Detection via full_user_text + orchestrator_context.history for Calendar Mutation Autonomy"
- **Kontext:** TASK-065 Contextual Entity Resolver Extension. Ziel: Vermeidung von "Vermerkt"-Antworten ohne Aktion bei deiktischen Bezügen ("ihn absagen", "da Handtuch nicht vergessen"). Das System muss implizite Referenzen auf kurzzeitig besprochene Kalender-Ereignisse auflösen können.
- **Problem:** Ohne Deictic-Fallback könnte "ihn absagen" als NOT_FOUND klassifiziert werden, wenn "ihn" keinem Ereignistitel entspricht. Das LLM würde nur "Vermerkt" antworten statt die Mutation auszuführen. Pronomen werden oft von _extract_mutation_target entfernt oder sind zu kurz für Fuzzy-Match.
- **Lösung:** **Deictic Context Fallback mit Multi-Source Detection:**
  1. **full_user_text Parameter:** `resolve()` erhält `full_user_text` (komplette User-Nachricht) zusätzlich zu `query` (extrahiertes mutation_target). Deiktische Marker ("ihn", "den", "da", "dort", "mitzubringen") werden im vollen Text gesucht, nicht nur im extrahierten Target.
  2. **orchestrator_context.history:** Statt `wf.messages` wird `wf.orchestrator_context.history[-4:]` verwendet für saubere Chat-Historie ohne System-Prompt-Injection.
  3. **_DEICTIC_RE Regex:** Pattern erkennt deiktische/anaphorische Ausdrücke: "ihn", "den", "da", "dort", "dazu", "dafür", "dort(hin)", "den termin", "mitzubringen", "mitnehmen".
  4. **Fallback Conditions:** Aktiviert wenn (a) MUTATION operation, (b) NOT_FOUND oder WEAK_MATCH status, (c) is_calendar_mutation=True, (d) recent_messages vorhanden, (e) deiktischer Marker im full_user_text ODER query ist sehr kurz (≤ 2 tokens).
  5. **Single-Event-Check:** Prüft ob genau ein Kalender-Ereignis in den letzten 2 Turns erwähnt wurde. Falls ja, wird dieses Ereignis als RESOLVED mit dispatcher_hint="PROCEED" zurückgegeben.
  6. **Short-Query Guard Bypass:** Wenn `_full_text_has_deictic=True` ist, wird der Short-Query-Guard (query_too_short) umgangen, da deiktische Bezüge gültige Intentionen signalisieren.
  7. **Honest Scoring:** Context-Fallback setzt score_final=75.0 (statt 100.0) um zu reflektieren, dass es sich um Kontext-Inferenz statt Fuzzy-Match handelt.
- **Härtung:** Multi-Source-Detection (full_user_text + orchestrator_context.history) garantiert robuste Deiktik-Erkennung. Single-Event-Check verhindert Ambiguität. Honest Scoring verhindert Überbewertung.
- **Tripwire:** Wenn "ihn absagen" als NOT_FOUND klassifiziert → Deictic-Fallback nicht aktiv oder History leer. Wenn falsches Ereignis gewählt → Single-Event-Check fehlt. Wenn Orchestrator-History mit System-Prompt verunreinigt → wf.orchestrator_context.history nicht verwendet.
- **Location:** `backend/services/orchestrator/entity_resolver.py` (_DEICTIC_RE, _has_deictic_reference, resolve with full_user_text, context fallback logic), `backend/services/orchestrator/execution_dispatcher.py` (orchestrator_context.history source), implementiert 2026-05-03.
- **Epic:** TASK-065 — Contextual Entity Resolver Extension
- **Confidence:** High (Deiktik-Regex deckt gängige Pronomen ab, Single-Event-Check deterministisch, Honest Scoring transparent).
- **Tags:** DeicticFallback, PronounDetection, ContextInference, CalendarMutationAutonomy, OrchestratorContext, TASK065

## [PATTERN] #GuidedModeSchema "Optional event_title_query for Direct ID-Patching in Guided Mode — No Artificial Search Strings Required"
- **Kontext:** TASK-067 Guided Assistant Mode Extension. Ziel: Erlauben von Modellen, direkt per ID zu patchen wenn Guided Mode aktiv ist, ohne künstlich Suchstrings erfinden zu müssen.
- **Problem:** Ohne optionales event_title_query müsste das LLM immer einen Suchstring (event_title_query) angeben, selbst wenn es bereits die event_id vom Entity Resolver hat. Das führt zu unnötigen Erfindungen oder redundanten Fuzzy-Suchen.
- **Lösung:** **Optional event_title_query mit ID-Priority:**
  1. **Schema Change:** `FindAndUpdateCalendarEventArgs` in `schemas.py`: `event_title_query` von `str` zu `Optional[str] = None`. Description ergänzt: "Optional wenn event_id angegeben wird."
  2. **Function Signature:** `find_and_update_calendar_event()` in `calendar_tools.py`: `event_title_query` Parameter zu `Optional[str] = None`.
  3. **ValueError Guard:** Zu Beginn der Funktion: Wenn `not event_id and not event_title_query`, raise `ValueError("Entweder event_id oder event_title_query muss angegeben werden.")`.
  4. **Fast Path Preservation:** Wenn `event_id` vorhanden ist, wird der Fuzzy-Suche-Pfad komplett übersprungen (API-GET direkt). Keine Notwendigkeit für event_title_query.
  5. **Guided Mode Integration:** Wenn Entity Resolver `PROCEED` zurückgibt, wird nur `event_id` in action_guidance injiziert. LLM kann direkt patchen ohne event_title_query.
  6. **Backward Compatibility:** Fuzzy-Suche funktioniert weiterhin wenn event_title_query angegeben wird. Kein Breaking Change für bestehende Code-Pfade.
- **Härtung:** ValueError Guard verhindert leere Calls. Fast Path bleibt erhalten. Backward Compatibility garantiert.
- **Tripwire:** Wenn LLM trotzdem event_title_query erfindet → Guidance nicht korrekt oder LLM ignoriert Optional-Flag. Wenn ValueError ausgelöst → Beide Parameter fehlen. Wenn Fuzzy-Suche trotz ID ausgeführt → Fast Path Logik beschädigt.
- **Location:** `backend/data/schemas.py` (FindAndUpdateCalendarEventArgs), `backend/tools/calendar_tools.py` (find_and_update_calendar_event), implementiert 2026-05-03.
- **Epic:** TASK-067 — Guided Assistant Mode Extension
- **Confidence:** High (ValueError Guard klar, Fast Path erhalten, Backward Compatible).
- **Tags:** GuidedModeSchema, OptionalParameters, IDPatching, DirectMutation, SchemaExtension, TASK067

## [PATTERN] #IntentEngineGuard "BUG-SYS-019 Guard — Calendar Mutation Beats Fact-Telling Pattern to Prevent Tool Override"
- **Kontext:** C7 (Code-Fix Pipeline) — Intent Engine Overlap Fix. Ziel: Verhindern dass BUG-SYS-019 fact-telling pattern ("mein/meine") calendar mutation intent zu personal_recall override und calendar.find_and_update_event aus der Skill-Liste entfernt.
- **Problem:** BUG-SYS-019 erkennt persönliche Fakten ("mein Hund heißt...") und setzt is_fact_telling=True. Dies kann calendar mutation intent ("ergänze meinen Termin") überschreiben, weil fact-telling Vorrang hat. Das LLM erhält dann keine calendar Tools, obwohl eine Mutation angefordert wurde.
- **Lösung:** **Calendar Mutation Priority Guard:**
  1. **Fact-Telling Detection:** `is_fact_telling_pattern()` in `intent_engine.py` prüft Regex-Patterns wie `(mein|meine)\s+`, `(ich habe)\s+`, etc.
  2. **Guard Logic:** In `detect_all_intents()` wird `_is_fact_telling = self.is_fact_telling_pattern(user_text)` berechnet.
  3. **Override Check:** Wenn `_is_mutation` (is_calendar_mutation) AND `_is_fact_telling` beide True sind, wird `_is_fact_telling = False` gesetzt.
  4. **Logging:** Bei Override wird geloggt: "[INTENT-ENGINE] Calendar mutation detected — overriding fact-telling pattern (BUG-SYS-019 guard: mutation beats personal_recall)".
  5. **Result Injection:** `IntentDetectionResult.is_fact_telling` wird mit dem korrigierten `_is_fact_telling` Wert belegt.
  6. **Tool Loading:** Da is_fact_telling=False, werden calendar Tools (inkl. find_and_update_event) korrekt geladen, selbst wenn "mein/meine" im User-Text steht.
- **Härtung:** Guard ist deterministisch basierend auf boolean flags. Logging macht Override transparent. Calendar mutation hat absolute Priorität über fact-telling.
- **Tripwire:** Wenn "ergänze meinen Termin" keine calendar Tools lädt → Guard nicht implementiert oder is_calendar_mutation nicht erkannt. Wenn fact-telling trotz calendar mutation aktiv → Guard Logik fehlt oder Reihenfolge falsch.
- **Location:** `backend/services/orchestrator/intent_engine.py` (detect_all_intents guard), implementiert 2026-05-03.
- **Epic:** C7 — Intent Engine Overlap Fix
- **Confidence:** High (Deterministische boolean Logik, klare Priorisierung, Logging vorhanden).
- **Tags:** IntentEngineGuard, BUGSYS019, CalendarMutationPriority, FactTellingOverride, IntentPrecedence, C7

## [PATTERN] #IntentEngineV2 "Wortgrenzen-Cache + Single Dispatch Contract — Vermeidung von Substring-Kollisionen und hierarchische Intent-Auflösung"
- **Kontext:** Intent Engine V2 Härtung nach 8/10 Architektur-Audit. Ziel: Vermeidung von False-Positives durch Substring-Matching (z.B. "uhr" in "kaufen" vs "14 uhr") und Konsolidierung von Intent-Checks auf einen einzigen Dispatch pro Request.
- **Problem:** (1) Substring-Kollisionen: `in`-Operator matched "uhr" in "kaufen" als Produkt-Signal obwohl es Uhrzeit ist. (2) Redundante Checks: Orchestrator rief mehrfach `detect_*_intent()` auf (shopping, calendar, local_business, etc.) → ineffizient und inkonsistent. (3) Shopping vs. Calendar Konflikt: "um 14 uhr einkaufen beim netto" wurde als Shopping-Intent klassifiziert, Kalender-Tools entfernt.
- **Lösung:** **_WORD_BOUNDARY_CACHE + Single Dispatch Contract:**
  1. **_WORD_BOUNDARY_CACHE:** Regex-Pattern `(?<!\w){phrase}(?!\w)` mit Cache (`_WORD_BOUNDARY_CACHE: Dict[str, re.Pattern]`) für wortgrenzentreues Matching. `_contains_phrase(text_norm, phrase)` cached Pattern pro Phrase.
  2. **Single Dispatch Contract:** Orchestrator ruft nur noch `intent_engine.detect_all_intents(user_text)` einmal pro Request. Ergebnis ist `IntentDetectionResult` mit allen Intent-Flags (`is_shopping_intent`, `is_calendar_intent`, etc.).
  3. **Shopping vs. Calendar Hierarchie:** `detect_all_intents()` löst Konflikte hierarchisch: Wenn beide Intents aktiv, gewinnt Calendar wenn `_has_calendar_command_signal()` → Shopping wird vetoed (`vetoed["shopping"] = "calendar_command"`). Umgekehrt gewinnt Shopping wenn starkes Commerce-Signal ohne Calendar-Kommando.
  4. **Signal-Methoden:** `_has_strong_shopping_signal()` (price + action/vendor/product), `_has_calendar_command_signal()` (command/object + date/time), `_has_uhr_product_signal()` (uhr als Produkt, nicht Uhrzeit via Prefix-Check auf Zahlen).
  5. **Global Veto Whitelist:** `apply_global_veto()` wirkt nur noch auf `veto_eligible_intents` (storybook, meta_agent, summary, image, complex_document), nicht mehr global für jeden Caller.
  6. **IntentDetectionResult Erweiterung:** `primary_intent` (Precedence-Chain), `vetoed_intents` (Veto-Tracking), `summary_global_veto`, `meta_agent_global_veto`, `named_channel_video`.
- **Härtung:** Regex mit Lookbehind/Lookahead garantiert Wortgrenzen. Pattern-Cache vermeidet redundante Kompilierung. Single Dispatch garantiert Konsistenz. Veto-Tracking macht Entscheidungen transparent.
- **Future Work für Diamond Standard (10/10):** Umstellung aller verbleibenden Intents (Image, Recall) auf Boundary-Cache und vollständige Eliminierung von Einzel-Checks wie Storybook. Ziel: Alle Intent-Detektion nutzen `_contains_phrase()` und `_WORD_BOUNDARY_CACHE` für konsistente Wortgrenzen-Erkennung.
- **Tripwire:** Wenn "uhr" in "14 uhr" als Produkt erkannt → `_has_uhr_product_signal()` Prefix-Check fehlt. Wenn Calendar vs. Shopping nicht aufgelöst → Hierarchie-Logik in `detect_all_intents()` fehlt. Wenn Orchestrator noch Einzel-Checks → Single Dispatch nicht implementiert.
- **Location:** `backend/services/orchestrator/intent_engine.py` (_WORD_BOUNDARY_CACHE, _contains_phrase, detect_shopping_intent, detect_calendar_intent, detect_all_intents, apply_global_veto), `backend/services/chat_orchestrator.py` (Single Dispatch via intent_detection_result), `backend/services/orchestrator/execution_dispatcher.py` (summary_global_veto via IntentDetectionResult), implementiert 2026-05-02.
- **Epic:** Intent Engine V2 Härtung (Calendar Routing Fix + Architektur-Refactor)
- **Confidence:** High (Wortgrenzen-Cache verhindert Substring-Kollisionen, Single Dispatch konsolidiert Checks, Hierarchie löst Shopping/Calendar-Konflikte deterministisch).
- **Tags:** IntentEngineV2, WordBoundaryCache, SingleDispatch, ShoppingCalendarHierarchy, IntentDetectionResult, VetoTracking, GlobalVetoWhitelist

## [PATTERN] #PureTextSummaryMode "Skill-Stripping bei Zusammenfassungs-Intents zur Qualitätssteigerung — relevant_skill_ids cleared, tools disabled, proactive guidance suppressed"
- **Kontext:** TASK-057 Context Awareness System erforderte einen Pure-Text Summary Mode, der alle Skills und Tools deaktiviert, wenn der Nutzer eine Zusammenfassung anfordert. Ohne diesen Modus könnten Skills unerwünscht in den Zusammenfassungs-Prozess eingreifen.
- **Problem:** Wenn ein Nutzer "fasse zusammen" oder "erstelle eine Zusammenfassung" eingibt, könnten proactive Skills oder forced tools den rein textuellen Zusammenfassungs-Prozess stören. Der Intent ist klar: reine Textverarbeitung ohne Skill-Intervention.
- **Lösung:** **Global Veto System für Summary Intents:**
  1. **Intent Engine:** `apply_global_veto()` in `intent_engine.py` erkennt Zusammenfassungs-Keywords ("fass zusammen", "zusammenfassen", "summarize", etc.) und gibt `vetoed=True` mit `veto_reason="summary"` zurück.
  2. **Execution Dispatcher:** Bei `vetoed` werden `wf.relevant_skill_ids = []`, `wf.force_tool_name = None`, `wf.proactive_guidance = ""`, `wf.has_tool_trigger = False` gesetzt.
  3. **Gateway Kwargs:** `tool_choice = "none"` erzwingt reine Textverarbeitung ohne Tool-Calls.
  4. **Meta-Agent:** `chat_orchestrator.py` prüft Veto vor Meta-Agent-Run und blockiert Meta-Agent bei Summary-Veto.
- **Härtung:** Veto-Logik ist deterministisch basierend auf Keyword-Matching. Keine probabilistische Klassifikation. Skills können bei Bedarf explizit erlaubt werden, wenn der Veto nicht auslösen soll.
- **Tripwire:** Wenn Tools bei Zusammenfassungs-Anfragen aktiv werden → Veto-Logik nicht implementiert oder Keywords fehlen. Erkennbar im Log: `[SKILL-TRIGGER]` trotz Summary-Request.
- **Location:** `backend/services/orchestrator/intent_engine.py` (apply_global_veto), `backend/services/orchestrator/execution_dispatcher.py` (Pure-Text gating), `backend/services/chat_orchestrator.py` (Meta-Agent Veto-Check), implementiert 2026-05-01.
- **Epic:** TASK-057 — Context Awareness System (Pure-Text Summary Mode)
- **Confidence:** High (Deterministische Keyword-Erkennung, klare Gating-Logik, keine Skill-Intervention bei Summary-Intents).
- **Tags:** PureTextSummaryMode, IntentEngine, GlobalVeto, SkillStripping, ToolDisabling, ContextAwareness, TASK057

---

## [PATTERN] #SelfHealingAuth "Stiller Re-Login bei 401-Fehlern zur Aufrechterhaltung der Persistenz — Token-Refresh + Retry ohne User-Feedback"
- **Kontext:** Frontend-401-Fehler beim Modellwechsel durch 30-Minuten Token-TTL. Nutzer mussten manuell neu einloggen oder sahen Fehlermeldungen. Das Ziel: Transparente Token-Erneuerung ohne Nutzer-Unterbrechung.
- **Problem:** 30-Minuten Token-TTL führt zu 401-Fehlern bei längeren Sessions. `updateLastUsedModelInBackend()` schlägt fehl, `last_used_provider` wird nicht persistiert, Modellwechsel ist unvollständig.
- **Lösung:** **Auth Self-Healing mit Silent Login:**
  1. **Token TTL Extension:** `backend/dependencies.py` — `ACCESS_TOKEN_EXPIRE_MINUTES` von 30 auf 1440 (24h) erhöht.
  2. **Frontend Retry-Mechanismus:** `frontend/js/app.js` — Bei `response.status === 401` wird `attemptSilentLogin()` aufgerufen.
  3. **Silent Login:** Nutzt `/api/auth/token` mit bestehenden Credentials für neuen Token.
  4. **Retry:** Nach erfolgreichem Refresh wird der ursprüngliche Request mit neuem Token wiederholt.
  5. **No User Feedback:** Bei erfolgreichem Retry sieht der Nutzer keine Fehlermeldung. Nur bei fehlgeschlagenem Refresh wird Error geloggt.
- **Härtung:** Token-TTL auf 24h reduziert Häufigkeit von 401-Fehlern. Retry-Mechanismus fängt verbleibende Fälle ab. `attemptSilentLogin()` ist idempotent und sicher.
- **Tripwire:** Wenn 401-Fehler sichtbar werden → Silent Login nicht implementiert oder Refresh fehlgeschlagen. Erkennbar im Log: `[AUTH] 401 error without retry` oder ähnliche Warnungen.
- **Location:** `backend/dependencies.py` (ACCESS_TOKEN_EXPIRE_MINUTES), `frontend/js/app.js` (updateLastUsedModelInBackend retry logic), implementiert 2026-05-01.
- **Epic:** TASK-057 — Context Awareness System (Auth Self-Healing)
- **Confidence:** High (Token-TTL erhöht, Retry-Mechanismus implementiert, Silent Login funktioniert).
- **Tags:** SelfHealingAuth, SilentLogin, TokenRefresh, RetryMechanism, 401Handling, ContextAwareness, TASK057

---

## [PATTERN] #BackgroundCostCommit "Zwang zum db.commit() in asynchronen oder verzweigten Engine-Pfaden zur zuverlässigen Cost-Persistenz"
- **Kontext:** Cost-Entries wurden in `execution_engine.py` erstellt, aber nicht persistiert, weil `db.commit()` fehlte. Asynchrone Pfade (Non-Stream und Stream) hatten unterschiedliche DB-Handling-Logik.
- **Problem:** `create_cost_entry()` wurde aufgerufen, aber ohne `db.commit()` wurden die Einträge nicht in die SQLite-Datenbank geschrieben. Bei Neustart des Servers waren alle Cost-Entries verloren.
- **Lösung:** **Explizite db.commit() nach Cost-Eintrag:**
  1. **Non-Stream Pfad:** `execution_engine.py` — Nach `create_cost_entry()` explizites `db.commit()`.
  2. **Stream Pfad:** `execution_engine.py` — Nach `create_cost_entry()` im Stream-Handler ebenfalls `db.commit()`.
  3. **Konsistenz:** Beide Pfade (iterative und streaming) haben identische Commit-Logik.
- **Härtung:** Explizites Commit garantiert Persistenz auch bei späteren Fehlern im Request-Cycle. DB-Session bleibt offen für weitere Operationen.
- **Tripwire:** Wenn Cost-Entries nach Neustart fehlen → `db.commit()` fehlt. Erkennbar in DB: `costs` Tabelle leer obwohl Requests verarbeitet wurden.
- **Location:** `backend/services/orchestrator/execution_engine.py` (run_agent_factory Non-Stream + Stream Pfade), implementiert 2026-05-01.
- **Epic:** TASK-057 — Context Awareness System (FinOps Cost Commit Fix)
- **Confidence:** High (Expliziter Commit implementiert, Cost-Entries werden persistiert).
- **Tags:** BackgroundCostCommit, DBCommit, CostPersistence, AsyncPath, StreamPath, FinOps, TASK057

---

## [LESSON] #PromptCachingClockLine "System-Prompt Clock-Line invalidiert Cache jede Minute — Sub-Segment-Zerlegung statt monolithischem Hash"
- **Kontext:** TASK-056 Prompt Caching Blueprint analysierte den realen System-Prompt-Aufbau in `execution_dispatcher.py`. Der Plan nahm an, der System-Prompt sei stabil/cachebar. Die Realität: `wf._clock_line` wird mit `datetime.now()` gebaut und jede Minute aktualisiert, dann am Prefix prepended.
- **Problem:** OpenAI's automatisches Prefix-Caching funktioniert nur bei stabilem Prefix. Die Clock-Line am Anfang invalidiert den gesamten System-Prompt-Hash 1440 Mal pro Tag, selbst wenn alle anderen Teile stabil wären. Ein monolithischer Hash über den fertigen `wf.final_system_prompt` ist wirkungslos.
- **Lösung:** **Sub-Segment-Zerlegung des System-Prompts:** Der Segmenter muss die einzelnen `wf.*`-Felder (clock_line, identity_anchor, identity_directive, base_prompt, ui_guidance, research_guidance, tool_protocol, small_talk_guard, capability_guidance, suggestion_suffix, skill_directives, coupons) **vor** der Konkatenation analysieren. Dynamische Segmente (clock_line, suggestion_suffix, capability_guidance, coupons) werden als nicht-cachebar klassifiziert. Stabile Segmente werden separat gecached. Integrationspunkt muss **vor** Zeile 314 (`wf.messages = [...]`) liegen.
- **Härtung:** Clock-Line ans Ende verschieben oder als separates System-Message senden, um OpenAI Prefix-Stability zu maximieren. Cache-Key enthält `segment_type` zur Unterscheidung. Feature-Flag für Segmenter, aber Telemetrie läuft auch bei `disabled` (cache_bypassed=N).
- **Tripwire:** Wenn Cache-Hit-Rate < 10% trotz stabilem System-Prompt → Clock-Line oder andere dynamische Injections nicht als Sub-Segmente behandelt. Erkennbar im Log: Clock-Line ändert sich jede Minute, aber Cache-Key bleibt gleich.
- **Location:** `backend/services/orchestrator/execution_dispatcher.py` (Zeilen 279-280, 296-307, 218-236, 316-319), dokumentiert 2026-04-29 in TASK-056 Cascade Review.
- **Confidence:** High (Code-Analyse bestätigt Clock-Line-Killer, Sub-Segment-Zerlegung ist Lösung).
- **Tags:** PromptCaching, ClockLine, SystemPrompt, SubSegment, OpenAICache, TASK056

---

## [PATTERN] #SavingsVisualizer "Monetäre Ersparnis-Visualisierung — tokens_saved + cost_saved in DB, UI berechnet Effizienz-Quote"
- **Kontext:** Einführung von Prompt Caching zur Kostenreduktion. Token-Einsparungen sind für Nutzer abstrakt. Ersparnis muss monetär und prozentual greifbar sein.
- **Problem:** Ohne monetäre Darstellung bleibt der Wert von Prompt Caching für Nutzer unsichtbar. Reine Token-Zahlen sind schwer zu interpretieren. Keine direkte Sichtbarkeit des finanziellen Mehrwerts von Janus-Optimierungen.
- **Lösung:** **Speicherung von `tokens_saved` und `cost_saved` in der `costs` Tabelle:**
  1. **DB-Schema:** `backend/data/models.py` — `tokens_saved` (INT, default=0), `cost_saved` (FLOAT, default=0.0) Spalten.
  2. **Auto-Migration:** `backend/data/database.py` — `_ensure_sqlite_schema_migrations()` führt `ALTER TABLE` für beide Spalten aus.
  3. **Berechnung:** `backend/services/cost_service.py` — `_calculate_cost_saved()` multipliziert `tokens_saved` mit `input_cost_per_token * USD_TO_EUR_CONVERSION_RATE` aus Model-Catalog.
  4. **Übergabe:** `backend/services/orchestrator/execution_engine.py` — `estimated_tokens_saved` aus `prompt_cache_decision` an `create_cost_entry()` übergeben (Non-Stream + Stream).
  5. **Aggregation:** `backend/data/crud.py` — `get_monthly_cost_summary_by_model()` aggregiert `total_tokens_saved` und `total_cost_saved` pro Modell.
  6. **UI-Visualisierung:** `frontend/js/cost-visualizer.js` — Deep-Dive-Modal zeigt pro Modell: `(Janus Caching: -X.XXXX € | Y% gespart)`. Footer zeigt Gesamtersparnis. Toggle-Button wechselt zwischen Modell- und Kosten-Sortierung.
  7. **Effizienz-Quote:** `efficiencyPct = (cost_saved / (total_cost + cost_saved)) * 100` — korrekte Definition als Anteil an den Gesamtprompt-Kosten.
- **Härtung:** Auto-Migration garantiert, dass neue Spalten in existierenden Datenbanken hinzugefügt werden. Historische Einträge erhalten automatisch `0` / `0.0`. UI zeigt Ersparnis nur wenn `cost_saved > 0`.
- **Tripwire:** Wenn Ersparnis im Modal nicht angezeigt wird → `total_cost_saved` nicht in API-Response enthalten. Erkennbar im Network-Tab: `/api/costs/summary-by-model` Response prüfen. Wenn Ersparnis immer 0.00€ → `tokens_saved` wird nicht an `create_cost_entry()` übergeben oder Berechnung fehlerhaft.
- **Location:** `backend/data/models.py` (Spalten), `backend/data/database.py` (Migration), `backend/services/cost_service.py` (Berechnung), `backend/services/orchestrator/execution_engine.py` (Übergabe), `backend/data/crud.py` (Aggregation), `frontend/js/cost-visualizer.js` (Visualisierung), implementiert 2026-04-29.
- **Epic:** TASK-056 — Prompt Caching System (Phase 4: Savings Engine)
- **Confidence:** High (DB-Migration funktioniert, API liefert Daten, UI zeigt Ersparnis korrekt).
- **Tags:** SavingsVisualizer, CostTracking, PromptCaching, UI, Database, TASK056

---

## [PATTERN] #UIDeduplication "UI Deduplication — Parallele Rendering-Flags und DOM-Clearing mit Delay"
- **Kontext:** UI Model Management in Janus zeigte doppelte Buttons und Modelle in den Einstellungen, besonders bei schnellen User-Interaktionen oder parallelen Render-Aufrufen.
- **Problem:** Doppelte Event-Listener, parallele `renderSettingsView()` Aufrufe, und Race Conditions beim DOM-Manipulation führten zu duplizierten UI-Elementen. Einfaches `innerHTML = ""` war nicht ausreichend.
- **Lösung:**
  1. **Rendering Flags:** `isSettingsViewRendering` und `isModelViewLoading` Flags verhindern parallele Ausführung.
  2. **DOM-Clearing mit Delay:** `innerHTML = ""`, dann `await new Promise(resolve => setTimeout(resolve, 0))`, dann nochmal `innerHTML = ""` für sicheres Entschlacken.
  3. **Set-Deduplication:** `renderedModelIds` Set verhindert doppelte Modelle in der Liste.
  4. **Spezifischer Event Listener:** `e.target.closest("button.model-manage-btn")` statt generischem `tagName === "BUTTON"`.
  5. **Button-Disabling:** Button wird während des Ladens deaktiviert und zeigt "Lade...".
- **Härtung:** Flags garantieren Single-Execution. DOM-Delay gibt Browser Zeit für Reflow. Set garantiert eindeutige IDs.
- **Tripwire:** Wenn Buttons/Modelle doppelt erscheinen → parallele Rendering-Flags fehlen. Wenn Event Listener auf falsche Elemente triggert → `closest()` Selector zu generisch.
- **Location:** `frontend/js/settings.js` (renderSettingsView, renderModelManagementView, Event Listener), gefixt 2026-04-28.
- **Confidence:** High (Keine doppelten Elemente mehr bei schnellen Klicks).
- **Tags:** UIDeduplication, RaceCondition, DOM, Rendering, JavaScript

---

## [PATTERN] #StatisticalRoutingBaseline "Statistical Routing Baseline — 10 Durchläufe zur Eliminierung stochastischen Rauschens bei Modell-Vergleichen"
- **Kontext:** D20 Routing Calibration implementiert eine systematische Modell-Kalibrierung über Matrix-Tests (Skills × Models × Runs). Ein einzelner Test-Lauf kann durch stochastisches Rauschen (Temperatur, Sampling, Netzwerk-Latenz) verfälscht sein. Entscheidungen über Modell-Zuweisungen basieren auf statistischer Signifikanz, nicht auf Einzelfällen.
- **Problem:** Ohne statistische Baseline führen Einzelfälle zu falschen Schlussfolgerungen. Ein Modell kann einmal gut abschneiden (Glück) und einmal schlecht (Pech). Entscheidungen basierend auf Einzelfällen sind nicht reproduzierbar und führen zu Instabilität im Routing.
- **Lösung:** **Statistische Baseline durch 10 Durchläufe:**
  1. Matrix-Test-Infrastruktur: POST-Endpoint `/api/system/run-batch-tests` mit `runs_per_model` Parameter.
  2. Outer Loop (Models) × Inner Loop (Runs_per_model) für statistische Signifikanz.
  3. Rate-Limiting: `asyncio.sleep(0.5)` zwischen Calls (429-Schutz bei Bulk-Tests).
  4. Trace-ID-Tracking: `uuid.uuid4()` pro Test (400 unique IDs für 10 Skills × 4 Models × 10 Runs).
  5. Model-Override: Lambda mit Keyword-Argumenten (provider, model, **kwargs) für korrekte Durchreichung.
  6. Aggregation: Pass-Rate, Latenz-Mittelwert, Escalation-Rate über alle Runs aggregieren.
- **Härtung:** Rate-Limiting garantiert API-Stabilität. Trace-ID-Tracking ermöglicht post-hoc Analyse. Model-Override via Lambda sicherstellt, dass das angegebene Modell tatsächlich verwendet wird (nicht das Default aus model_routing.json).
- **Tripwire:** Wenn Modell-Zuweisungen basierend auf Einzelfällen getroffen werden → keine statistische Baseline. Erkennbar: `runs_per_model=1` in Matrix-Test-Config. Wenn 429-Fehler bei Bulk-Tests → Rate-Limiting fehlt. Wenn Trace-IDs nicht unique → UUID-Generierung defekt.
- **Location:** `backend/api/routers/system.py` (RoutingCalibrationRequest, Matrix-Run-Logic, Rate-Limiting, Trace-ID, Lambda-Fix), `backend/services/testing/test_runner.py` (trace_id Parameter), implementiert 2026-04-27.
- **Epic:** D20 — Routing Calibration
- **Confidence:** High (Statistische Signifikanz durch 10 Runs, Rate-Limiting aktiv, Trace-ID-Tracking implementiert).
- **Tags:** StatisticalRoutingBaseline, ModelRouting, Calibration, MatrixTest, RateLimiting, TraceID, D20

---

## [LESSON] #AsyncLifecycleSafety "Async Lifecycle Safety — DB-Closing in Background-Tasks muss nach Abschluss aller Closure-Ausführungen erfolgen"
- **Kontext:** D18 WIRING-FIX entdeckte, dass `db.close()` in einem inneren `finally` Block lief, BEVOR die Closure, die die DB-Session captured hatte, ihre Ausführung beendet hatte. Die `real_tool_call_fn` Closure in `system.py` captured die DB-Session, aber `db.close()` wurde im `finally` Block aufgerufen, der NACH dem Closure-Aufruf aber VOR dem Abschluss aller asynchronen Operationen innerhalb der Closure ausgeführt wurde.
- **Problem:** DB-Sessions in Background-Tasks haben eine längere Lebensdauer als der synchrone Code-Abschnitt. Wenn `db.close()` zu früh aufgerufen wird, haben nachfolgende asynchrone Operationen (z.B. LLM-Calls via `llm_gateway.call_llm`) eine tote DB-Session. Dies führt zu `InterfaceError: Connection already closed` oder ähnlichen Fehlern bei Tool-Ausführung.
- **Lösung:** **DB-Closing nach Abschluss aller Closure-Ausführungen:**
  1. Verschiebe `db.close()` vom inneren `finally` Block zu einem äußeren `try/finally`, das den gesamten Background-Task umschließt.
  2. Stelle sicher, dass die Closure, die die DB-Session captured, ihre Ausführung vollständig beendet hat, bevor `db.close()` aufgerufen wird.
  3. Bei Matrix-Runs (D20): DB-Session bleibt für alle Model- und Run-Iterationen aktiv, wird erst nach Abschluss aller Tests geschlossen.
- **Härtung:** Forensische Logging-Statements vor und nach kritischen DB-Operationen. DB-Session-Status-Check vor Tool-Ausführung (optional, für Debugging).
- **Tripwire:** Wenn Tool-Ausführung mit `InterfaceError: Connection already closed` fehlschlägt → DB-Closing zu früh. Erkennbar im Log: `[DB-CLOSED]` Eintrag vor `[TOOL-EXECUTION]` Eintrag.
- **Location:** `backend/api/routers/system.py` (db.close scope in run_batch_background), gefixt 2026-04-27 (D18 WIRING-FIX), bestätigt 2026-04-27 (D20).
- **Confidence:** High (DB-Session bleibt für gesamte Batch-Dauer aktiv, keine Connection-Closed-Fehler mehr).
- **Tags:** AsyncLifecycleSafety, DBClosing, BackgroundTasks, Closure, Lifecycle, D18, D20

---

## [PATTERN] #DeterministicSkillTesting #QualitySystem "Deterministic Quality System — Entkopplung von Test-Generierung und -Ausführung, strikte Ablehnung von KI in der Validierung"
- **Kontext:** D16 Skill Stability System implementiert ein deterministisches Qualitätssystem für Janus-Skills, weg von "probabilistischer Hoffnung" hin zu "gemessener Stabilität". Das System besteht aus Test Generator (Blueprint-Generierung), Validation Engine (deterministische Regeln), Model Router (Skill-zu-Modell Mappings), Escalation Engine (Primary → Fallback → Escalation) und Test Runner (Ausführung mit D10 Telemetrie).
- **Problem:** Ohne deterministisches Testsystem basiert Skill-Stabilität auf probabilistischen Annahmen. KI-basierte Validierung führt zu inkonsistenten Ergebnissen und schwer reproduzierbaren Fehlern. Fehlende Eskalations-Logik führt zu Single-Point-of-Failure bei Modellproblemen.
- **Lösung:**
  1. **Test Generator:** Rule-basierte Blueprint-Generierung (happy_path, edge_case, failure_case) ohne KI-Beteiligung. JSON-Blueprints werden in `config/skill_tests/` persistiert.
  2. **Validation Engine:** Deterministische Validatoren (contains, not_contains, regex, not_crash). STRICTLY FORBIDDEN: KI-basierte Validierung. None/Empty-Guards für robuste Fehlerbehandlung.
  3. **Model Router:** Skill-zu-Modell Mappings aus `model_routing.json` mit Fallback auf Global Defaults. Tiers: Primary, Fallback, Escalation.
  4. **Escalation Engine:** Automatische Eskalation bei Fehlern (Primary → Fallback → Escalation). Circuit Breaker bei vollständiger Eskalations-Erschöpfung. Kosten-Tracking pro Tier.
  5. **Test Runner:** Async-Ausführung mit D10 Integration (`log_event()`). AI Studio kompatible Health Reports (health_score, status, avg_latency_ms).
  6. **API Endpoint:** `GET /api/system/run-skill-tests/{skill_id}` für manuelle Triggerung aus AI Studio.
- **Härtung:** Async-Integrity Pattern (konsistentes Awaiten in Eskalationskette). None-Guards für alle Validierungsmethoden. Type-Guards für Result-Validierung.
- **Tripwire:** Wenn Tests inkonsistente Ergebnisse liefern → KI-basierte Validierung aktiv. Wenn latency_ms = 0.0 → Async-Await fehlt. Wenn Circuit Breaker nicht triggert → Eskalations-Logik defekt.
- **Location:** `backend/services/testing/test_generator.py`, `backend/services/testing/validation.py`, `backend/services/routing/model_router.py`, `backend/services/routing/escalation.py`, `backend/services/testing/test_runner.py`, `backend/api/routers/system.py`, implementiert 2026-04-26.
- **Epic:** D16 — Deterministic Quality System
- **Confidence:** High (Deterministische Regeln, strikte KI-Ablehnung in Validierung, konsistente Async-Handling).
- **Tags:** DeterministicSkillTesting, QualitySystem, Validation, Escalation, ModelRouting, D10Integration, AsyncIntegrity

---

## [LESSON] #AsyncIntegrity #Escalation "Coroutine-Vampir bei Tool-Calls — Konsistentes Awaiten in der Eskalationskette für korrekte Latenz-Messung"
- **Kontext:** Die EscalationEngine führte tool_call_fn auf, aber ohne await wenn das Ergebnis eine Coroutine war. Dies führte zu latency_ms = 0.0 und korrupten Zeitmessungen. Der Mock-Tool-Call im API Router war async, aber der Aufruf wurde nicht konsistent awaited.
- **Problem:** Wenn tool_call_fn eine Coroutine zurückgibt (async function), aber nicht awaited wird, wird das Coroutine-Objekt selbst als Ergebnis behandelt. Dies führt zu: (1) Falsche latency_ms (0.0 statt echter Ausführungszeit), (2) AttributeError bei Zugriff auf Coroutine-Attribute, (3) Unvorhersehbares Verhalten bei Validierung.
- **Lösung:** **Konsistentes Async-Handling in der Eskalationskette:**
  1. `execute_with_escalation()` zu async machen.
  2. `_execute_at_tier()` zu async machen.
  3. `asyncio.iscoroutine(result)` Check nach tool_call_fn.
  4. Wenn Coroutine: `result = await result`.
  5. Alle Aufrufe in der Kette mit await versehen.
- **Härtung:** Async-Check mit `asyncio.iscoroutine()` für maximale Robustheit. Convenience-Funktionen ebenfalls async machen.
- **Tripwire:** Wenn latency_ms = 0.0 in Test-Reports → Async-Await fehlt in Escalation Engine. Wenn AttributeError bei Result-Attributen → Coroutine nicht awaited.
- **Location:** `backend/services/routing/escalation.py` (execute_with_escalation, _execute_at_tier), `backend/services/testing/test_runner.py` (escalation call), gefixt 2026-04-26.
- **Confidence:** High (Latency-Messung zeigt jetzt echte Werte, keine AttributeErrors mehr).
- **Tags:** AsyncIntegrity, Escalation, Coroutine, Latency, Await, ToolCall

---

## [PATTERN] #DeterministicProblemClassification #DecisionLoop "Escalation-Tier-Signal als Root-Cause-Indikator — Nutzung von final_tier, attempts_count und latency_ms zur automatischen Kategorisierung von Skill-Defekten ohne KI-Interpretation"
- **Kontext:** D17 Skill Health Matrix & Decision Interface baut auf D16 (Skill Stability System) und D13 (Optimization Engine) auf. Nach dem Testlauf liefert die Eskalationskette strukturierte Daten (final_tier, attempts_count, status, latency_ms), die als deterministisches Signal für die Root-Cause-Analyse dienen. Die Herausforderung: Aus diesen Daten die richtige Maßnahme ableiten, ohne auf KI-Interpretation zurückzugreifen.
- **Problem:** Generische "pass/fail" Metriken geben keinen Aufschluss über die Art des Fehlers. Ein Skill, der auf Primary scheitert aber auf Fallback läuft, hat ein anderes Problem als ein Skill, der auf allen Tiers scheitert. Ohne Klassifikation bleibt die Maßnahme unklar.
- **Lösung (4 Kategorien, strikt deterministisch):**
  1. **MODEL_WEAKNESS:** `status == "passed"` AND `final_tier NOT IN ("primary", "")` → Primary-Modell ist zu schwach, aber stärkere Modelle bestehen. Maßnahme: Fallback zu Primary promoten (manuell in model_routing.json).
  2. **PROMPT_ISSUE:** `status IN ("failed", "error")` AND `attempts_count >= 2` → Skill scheitert über ALLE Tiers. Der Befehl ist unklar oder das Tool-Schema fehlerhaft. Maßnahme: Prompt/Schema Review.
  3. **VALIDATION_FAIL:** `status == "failed"` AND `attempts_count <= 1` → Primary führt aus, Ergebnis kommt zurück, aber ValidationEngine (Regex/Contains) schlägt Alarm. Modell halluziniert das Output-Format. Maßnahme: Prompt verschärfen oder Validierung lockern.
  4. **TIMEOUT:** `status == "passed"` AND `latency_ms > 3000ms` → Test besteht, aber Latenz über Schwellenwert. Maßnahme: Schnelleres Modell oder Response-Caching.
- **Confidence Score:** Frequency-basiert (`category_count / total_runs`). Keine probabilistische Schätzung, rein auf Frequenzdaten.
- **Integration:** `ProblemClassifier` in `optimization_engine.py` aggregiert D10 `skill_test` Events pro Skill. `generate_decision_report()` emittiert pro degraded Skill: Health-Metriken-Tabelle, Problem-Klassifikation-Tabelle (Dominant Category, Confidence, Breakdown), `[PROVISIONAL]` Root-Cause-Empfehlung. Summary enthält Category Distribution.
- **Härtung:** D10 Payload um `final_tier` und `attempts_count` erweitert (`_log_to_d10`). Alle Recommendations tragen `[PROVISIONAL]` Prefix (D15 Compliance). `model_routing.json` wird NICHT vom Code geändert (Zero Mutability Guardrail).
- **Tripwire:** Wenn `final_tier` fehlt in D10 Payload → `_log_to_d10` nicht aktualisiert. Wenn alle Skills "HEALTHY" aber pass_rate < 0.9 → Klassifikationslogik defekt. Wenn Recommendations ohne `[PROVISIONAL]` → D15 Compliance verletzt.
- **Location:** `backend/services/logging/optimization_engine.py` (ProblemClassifier, classify_test_event, _build_recommendation), `backend/services/testing/test_runner.py` (_log_to_d10 payload), `backend/api/routers/system.py` (GET /api/system/decision-report), implementiert 2026-04-26.
- **Epic:** D17 — Skill Health Matrix & Decision Interface
- **Confidence:** High (Deterministisch, 4 klar abgegrenzte Kategorien, frequency-basierter Confidence Score, keine KI-Interpretation).
- **Tags:** DeterministicProblemClassification, DecisionLoop, EscalationSignal, HealthMatrix, D13Integration, D16Integration

---

## [PATTERN] #Logging #Hardening "Resilient Telemetry Pattern — Kombination aus contextvars für Traceability, UPSERT für Idempotenz und Drop-Oldest für Speichersicherheit"
- **Kontext:** Logging Pipeline Phase 1 (reines Sammeln) wurde auf Phase 2 (analytische Härtung) gehoben. Die Infrastruktur fehlte Resilienz-Mechanismen: keine Trace-ID Context-Propagation, keine Queue Overflow-Strategie, keine System-Health-Monitoring, keine strikte Payload-Validierung. Bei hohem Throughput konnte die Queue volllaufen und Events verloren gehen. Doppelte Uploads bei Retries führten zu Duplikaten in Supabase.
- **Problem:** Ohne Trace-ID war Request-Tracking unmöglich (keine End-to-End Tracing). Ohne Overflow-Strategie würde die Queue blockieren bei volllauf (5000 Events). Ohne UPSERT-Idempotenz führten Retries zu Duplikaten in Supabase. Ohne Schema-Validierung konnten ungültige Payloads die Queue verunreinigen.
- **Lösung (Phase 2 Hardening):**
  1. **Schema-Erweiterung:** `LogEventBase` um `trace_id` (UUID/String) erweitert. `LogEventPayload` als striktes Pydantic-Modell mit `input_hash`, `output_summary`, `error_code`.
  2. **Trace-ID Context-Propagation:** `contextvar.ContextVar('_trace_id')` mit `set_trace_id()`, `get_trace_id()`, `generate_trace_id()`. Auto-Population in `log_event()` wenn nicht gesetzt.
  3. **Validierungsschicht:** Schema-Validierung vor `queue.put()` mit Warn-Logging bei Verletzung.
  4. **Queue Overflow Strategy:** Drop-Oldest bei voller Queue (maxsize=5000) via `get_nowait()`.
  5. **UPSERT Idempotenz:** UUID-Generierung in `log_event()`, Batch-Uploader nutzt `upsert()` mit `on_conflict="id"`.
  6. **Metrics Tracking:** `successful_uploads`, `failed_uploads`, `total_retries` als Counter.
  7. **system_health Event:** Periodisches Logging alle 50 Batches mit Queue-Größe und Erfolgsrate.
  8. **Integration:** `routing_decision` im Orchestrator, `fallback_trigger` in ExecutionEngine.
  9. **Auto-Migration-Guard:** `ensure_logging_schema()` prüft via `information_schema.columns` ob `trace_id` Spalte existiert, führt `ALTER TABLE + CREATE INDEX` bei Bedarf aus. Wird bei jedem Serverstart via `start_worker()` aufgerufen.
  10. **Local DLQ Fallback:** `_write_to_dlq()` schreibt fehlgeschlagene Batches nach 5 Retries in `backend/logs/failed_batches.jsonl` statt Events ewig in Queue zu halten. JSONL-Format mit Error-Context für manuelle Recovery.
- **Architektur:** Async RAM-Queue (asyncio.Queue) → Batch Worker (Background Task) → UPSERT zu Supabase. Graceful Shutdown via `flush_log_queue()`.
- **Härtung:** Validierungsschicht verwirft Events mit ungültigem Payload. Overflow-Strategie garantiert, dass neue Events immer in die Queue passen. UPSERT garantiert Idempotenz bei Retries. Metrics und system_health ermöglichen proaktives Monitoring.
- **Tripwire:** Wenn Logs keine Trace-IDs haben → contextvar nicht gesetzt. Erkennbar: `trace_id=None` in Supabase. Wenn Queue voll und Events blockieren → Overflow-Strategie nicht aktiv. Erkennbar: `asyncio.QueueFull` Exception. Wenn Duplikate in Supabase → UPSERT nicht korrekt konfiguriert. Erkennbar: gleiche Event-IDs mehrfach in logs_raw Tabelle.
- **Location:** `backend/services/logging/logger_core.py` (contextvar, Overflow, Metrics, system_health, Validierung), `backend/data/schemas_logging.py` (trace_id, LogEventPayload), `backend/services/chat_orchestrator.py` (set_trace_id, routing_decision), `backend/services/orchestrator/execution_engine.py` (fallback_trigger), implementiert 2026-04-25.
- **Epic:** D10-HARDENING — Phase 2 der Logging Pipeline (Phase 1: D10 Logging Pipeline Phase 1)
- **Confidence:** High (Kombination aus contextvars, Drop-Oldest und UPSERT bietet maximale Resilienz für Logging-Pipeline).
- **Tags:** Logging, Hardening, ResilientTelemetry, ContextVar, Traceability, UPSERT, Idempotency, DropOldest, OverflowProtection, Metrics, SystemHealth, SchemaValidation, Phase2

---

## [LESSON] #Logging #Context "Metadata Injection Pattern — ToolExecutor benötigt explizite Provider/Model-Daten im additional_context für akkurate Telemetrie"
- **Kontext:** Diamond-Skills wie `system.weather` bypassen den `ToolExecutor` und werden direkt ausgeführt. Das Logging extrahiert `provider` und `model` aus `additional_context`, aber diese Werte wurden nicht an allen ToolExecutor-Instanziierungen übergeben. Resultat: Logs zeigten "unknown" für provider/model.
- **Problem:** Inkonsistente Context-Propagation bei ToolExecutor-Instanziierungen. `tool_executor.py` extrahiert `provider` und `model` aus `self.additional_context`, aber nicht alle Instanziierungs-Orte übergaben diese Werte. Dies führte zu "MISSING_PROVIDER"/"MISSING_MODEL" Fallbacks im Logging.
- **Lösung:** **Konsistente Metadata-Injection:** `provider` und `model` zu `additional_context` hinzugefügt bei ALLEN ToolExecutor-Instanziierungen:
  - `chat_orchestrator.py` (Zeile 1905-1917, 747-759)
  - `agent_runtime.py` (Zeile 60-73, 97-112, 127-140)
  - `execution_dispatcher.py` (bereits korrekt)
  - `policy_handler.py` (bereits korrekt)
  - `meta_agent_pipeline.py` (bereits korrekt)
- **Härtung:** ChatRequest-Attribut-Fix: `req.chosen_model` → `req.model` (ChatRequest-Schema hat `model`, nicht `chosen_model`). Forensische Logs aus allen Dateien entfernt (Debug-Code Cleanup).
- **Tripwire:** Wenn Logs "unknown" für provider/model zeigen → ToolExecutor-Instanziierung ohne additional_context-Propagation. Erkennbar im Log: `!!! LOGGING-DEBUG !!! Raw Context Keys: ['chat_id']` (provider/model fehlen).
- **Location:** `backend/services/chat_orchestrator.py`, `backend/services/agent_runtime.py`, `backend/services/tool_executor.py`, gefixt 2026-04-25.
- **Confidence:** High (Test bestätigt: Context enthält `{'chat_id': 999999, 'provider': 'openai', 'model': 'gpt-4o-mini'}`).
- **Tags:** Logging, Context, MetadataInjection, ToolExecutor, Provider, Model, DiamondSkills, Telemetry

---

## [LESSON] #LoopBreaker #SelfCorrection "Error-Retry-Exception — Duplicate Calls sind erlaubt, wenn das vorherige Tool-Ergebnis einen Fehler zurückgab"
- **Kontext:** HARD-LOOP-BREAKER blockierte alle Duplicate Calls strikt, auch wenn das vorherige Tool-Ergebnis einen Fehler (z.B. INVALID_ARGUMENTS) zurückgab. Dies verhinderte Self-Correction durch das Modell — bei fehlerhaften Argumenten konnte das Modell nicht erneut versuchen mit korrigierten Argumenten. Resultat: Modelle halluzinierten Antworten statt Tool-Errors zu korrigieren.
- **Problem:** Striktes Duplicate-Blocking ohne Kontext-Berücksichtigung führt zu unnötigen Fehlern bei Self-Correction-Szenarien. Wenn ein Tool einen Fehler aufgrund ungültiger Argumente zurückgibt, sollte das Modell die Möglichkeit haben, den Tool-Call mit korrigierten Argumenten zu wiederholen, ohne vom Loop-Breaker blockiert zu werden.
- **Lösung:** **Tool-Status-Tracking:** Speichere den Status jedes Tool-Ergebnisses in `wf.kpi_tool_status: dict[str, str]` (cache_key -> status). **Self-Correction-Exception:** Erweitere `_track_tool_call_fn` um zu prüfen, ob der vorherige Status "error" enthält. Wenn ja, erlaube einen Retry für Self-Correction. **Status-Speicherung:** Nach Tool-Ausführung speichere den Status, wenn "error" oder "invalid" enthalten ist (sowohl im non-stream als auch im stream Pfad).
- **Härtung:** Die Self-Correction-Exception ist auf Error-Status beschränkt (nicht auf Success). Ein Retry ist nur einmal erlaubt (Status wird auf "retry_attempt" gesetzt). Die Sicherheitsmechanismen bleiben für echte Loops aktiv.
- **Tripwire:** Wenn ein Modell bei einem Tool-Error halluziniert statt Self-Correction zu versuchen → Self-Correction-Exception fehlt oder ist zu restriktiv. Erkennbar im Log: `[HARD-LOOP-BREAKER] BLOCKED duplicate tool call` trotz vorherigem Fehler.
- **Location:** `backend/services/orchestrator/execution_dispatcher.py` (wf.kpi_tool_status + Self-Correction-Exception), `backend/services/orchestrator/execution_engine.py` (Tool-Status-Tracking non-stream + stream), gefixt 2026-04-24.
- **Confidence:** High (Error-Retry-Exception ermöglicht Self-Correction ohne Deaktivierung der Sicherheitsmechanismen).
- **Tags:** LoopBreaker, SelfCorrection, ErrorRetry, ToolStatus, INVALID_ARGUMENTS, ModelSelfCorrection

---

## [LESSON] #Gemini #API #ThoughtSignature "Gemini 3 requires thought_signature for functionCall parts — must preserve original parts from API response instead of reconstructing them"
- **Kontext:** Gemini 3 Modelle erfordern `thought_signature` für `functionCall` Parts. Der aktuelle Code in `backend/llm_providers/gemini/service.py` erstellt neue `function_call` Parts ohne diese Signatur (Zeilen 540-545). API-Antwort: `InvalidArgument: 400 Function call is missing a thought_signature.`
- **Problem:** Der Code extrahiert Tool-Calls aus der Gemini-Antwort und konstruiert neue `protos.Part(function_call=...)` Objekte ohne die `thought_signature` aus dem ursprünglichen Part zu übernehmen. Gemini 3 validiert strikt, dass der erste `functionCall` part in jedem Schritt des aktuellen Turns eine `thought_signature` enthält.
- **Lösung:** Die `thought_signature` muss aus der ursprünglichen Gemini-Antwort extrahiert werden, wenn Tool-Calls verarbeitet werden. Parts sollten nicht neu erstellt, sondern direkt aus der API-Antwort übernommen werden. **Fix-Empfehlung:** Original Parts direkt in `_gemini_raw_model_parts` speichern und später wiederverwenden, anstatt neue Parts zu erstellen.
- **Dokumentation:** Gemini API Docs: https://ai.google.dev/gemini-api/docs/thought-signatures — "The first functionCall part in each step of the current turn must include its thought_signature. If you omit a thought_signature for the first functionCall part in any step of the current turn, the request will fail with a 400 error."
- **Status:** Pending Investigation — Forensische Dokumentation in `documentation/forensics/GEMINI_THOUGHT_FAIL_MATRIX.md` erstellt. Test-Matrix für systematische Fehleranalyse vorbereitet. Opus-Eskalation empfohlen für tiefgreifende Änderungen an Gemini-Service-Logik.
- **Location:** `backend/llm_providers/gemini/service.py` (Zeilen 540-545: function_call Parts ohne thought_signature), dokumentiert 2026-04-24.
- **Confidence:** High (API-Dokumentation bestätigt Anforderung, Fehlermeldung eindeutig).
- **Tags:** Gemini, API, ThoughtSignature, FunctionCall, LLM, Provider, 400Error

---

## [PATTERN] #GoogleCalendarSyncReliability "PATCH-with-Verify-and-Fallback — Selbstreparierender Google-Kalender-Sync mit Pagination, conferenceDataVersion und Output-Only-Key-Filterung"
- **Kontext:** Google Calendar API hat spezifische Eigenheiten, die zu Datenverlust oder unsichtbaren Sync-Fehlern führen können: (1) maxResults=25 paginiert nur 25 Events, (2) PUT events.update kann Output-Only-Felder zurückspielen und Metadaten-Änderungen "schlucken", (3) conferenceDataVersion=0 führt bei Meet-Terminen zu unzuverlässigen Konferenz-Metadaten, (4) organizer.self=false kann auf eingeladene Konten hinweisen. Ohne diese Kenntnisse erscheint Sync als "funktionierend" obwohl Änderungen nicht in der Google Web-UI sichtbar werden.
- **Problem:** (1) Bei >25 Terminen pro Zeitraum werden Termine abgeschnitten → Janus sieht nicht alle Events. (2) PATCH/UPDATE ohne Verifikation kann "leere" Änderungen sein → UI zeigt gespeichert, Google hat nichts geändert. (3) Fehlende conferenceDataVersion führt zu Meet-Link-Verlust bei Updates. (4) Output-Only-Felder (kind, etag, htmlLink, created, updated, hangoutLink, creator) bei PUT zurückgespielt können API-Defaults überschreiben und Updates invalidieren.
- **Lösung:** **PATCH-with-Verify-and-Fallback + Pagination:**
  1. **Pagination-Loop:** `get_calendar_events` nutzt `pageToken` und `maxResults=250` statt statischem `maxResults=25`. Loop sammelt alle Seiten bis `nextPageToken` fehlt.
  2. **Output-Only-Key-Filter:** `_GOOGLE_CAL_EVENT_OUTPUT_ONLY_KEYS` (frozenset mit kind, etag, htmlLink, created, updated, hangoutLink, creator) wird vor PUT aus dem Body entfernt. `_body_for_calendar_events_put()` filtert diese Schlüssel.
  3. **conferenceDataVersion-Logik:** `_conference_data_version_for_put()` prüft auf `conferenceData` oder `hangoutLink` und setzt `conferenceDataVersion=1` für Meet-Termine. Fallback auf 0 bei 400-Fehlern.
  4. **PATCH-first für Metadaten:** Bei reinen Metadaten-Updates (Ort/Beschreibung/Teilnehmer ohne Start/Ende) wird zuerst `events.patch` mit minimalem Body verwendet. Nur gesetzte Felder werden gesendet.
  5. **PATCH-Verifikation:** Nach PATCH wird GET ausgeführt und Felder verglichen (`_cal_text_normalized` für CRLF-Normalisierung). Bei Mismatch (mismatch_loc, mismatch_desc, mismatch_summary) wird Fallback `events.update` mit gemergem Body ausgeführt.
  6. **Fallback-Update:** Bei PATCH-Verifikations-Fehlern wird `events.update` mit `_body_for_calendar_events_put()` und korrekter `conferenceDataVersion` aufgerufen. Retry mit cdv=0 bei 400-Fehlern.
  7. **Forensische Logging-Signale:** `organizer.self=false` wird als Info geloggt (unterschiedliches eingeladenes Konto). `verify-mismatch` (Ort/Beschreibung/Summary) wird als Warning geloggt mit event_id, eventType und Diff-Details.
- **Härtung:** Pagination garantiert vollständige Event-Liste. Output-Only-Filterung verhindert "Rückspiel-Effekte". conferenceDataVersion schützt Meet-Metadaten. PATCH-Verifikation garantiert, dass Änderungen wirklich in Google ankommen. Fallback-Update deckt PATCH-Fälle ab, wo Google "leer" wirkt.
- **Tripwire:** Wenn >25 Terminen im Zeitraum fehlen → Pagination nicht aktiv. Wenn Metadaten-Updates in Web-UI nicht sichtbar → PATCH-Verifikation fehlt oder Output-Only-Keys nicht gefiltert. Wenn Meet-Links nach Updates verschwinden → conferenceDataVersion nicht gesetzt. Wenn Logs keine organizer.self/verify-mismatch zeigen → Forensische Logging-Signale nicht aktiv.
- **Location:** `backend/tools/calendar_tools.py` (Pagination-Loop, Output-Only-Filter, conferenceDataVersion, PATCH-Verifikation, Fallback-Update, Forensische Logs), implementiert 2026-05-01.
- **Epic:** TASK-058 — Calendar UX Refinement (Google Sync Hardening)
- **Confidence:** High (Pagination garantiert Vollständigkeit, PATCH-Verifikation mit Fallback deckt API-Eigenheiten ab, forensische Logs für Debugging).
- **Tags:** GoogleCalendarSyncReliability, Pagination, ConferenceDataVersion, OutputOnlyKeys, PATCHVerifyFallback, ForensicLogging, TASK058

---

## [LESSON] #RAG #WindowsPaths "The Slash-Trap — Normalisiere Pfade immer auf Forwardslashes vor Vektor-Filtern"
- **Kontext:** RAG V2 Vektorsuche (ChromaDB) speichert Metadaten-Pfade mit Backslashes (`C:\Users\...\aegypten.pdf`). Der Filename-Filter im `hybrid_retriever.py` verglich User-Input (`aegypten`) direkt mit diesen DB-Pfaden. Auf Windows führte der Slash-Mismatch dazu, dass die Vektorsuche 0 Treffer lieferte obwohl die Datei physisch im Index existierte. Das System fiel dann auf globale Suche zurück → Halluzinationen (z.B. "aegypten.pdf enthält Skandinavien-Analyse").
- **Problem:** Path-String-Vergleich ohne Normalisierung ist auf Windows nicht deterministisch. `C:\foo\bar.pdf` vs `C:/foo/bar.pdf` vs `C:\FOO\BAR.PDF` sind für String-Endswith-Vergleiche unterschiedliche Werte, obwohl sie dieselbe Datei referenzieren. ChromaDB-Metadaten speichern Pfade wie sie beim Ingest eingehen (meist mit Backslashes), während User-Input variieren kann (Forward-Slashes, Lower/Upper-Case, mit/ohne Extension).
- **Lösung:** **Pfad-Normalisierung-Funktion** (`_normalize_path(p: str) -> str`) die Backslashes zu Forwardslashes wandelt und lowercased. Diese Funktion wird auf ALLE Pfad-Vergleiche angewendet:
  ```python
  @staticmethod
  def _normalize_path(p: str) -> str:
      return p.replace("\\", "/").lower() if p else p
  ```
  Angewendet in:
  - `hybrid_retriever.py`: Filename-Filter und IndexStore-Lookup
  - `tool_executor.py`: `_v2_fulltext_fallback` Stem-Matching
  - `index_store.py`: `get_chunks_by_file` ChromaDB-Query
- **Härtung (Lockdown):** Wenn `filename`-Parameter übergeben wird, wird die globale Vektorsuche komplett übersprungen. Nur noch IndexStore-Lookup + Rescue-Path (direkter SQL-Zugriff auf Chunks). Wenn das 0 Ergebnisse liefert → leer zurückgeben, NIE globale Suche als Fallback.
- **Tripwire:** Wenn RAG-Filename-Suche auf Windows "nichts findet" obwohl die Datei im Index existiert → Slash-Trap. Erkennbar im Log: `[FILENAME-FILTER] Retrieval miss for '{filename}'` obwohl die Datei physisch vorhanden ist.
- **Location:** `backend/services/rag/hybrid_retriever.py` (normalize + lockdown), `backend/services/tool_executor.py` (normalize), `backend/services/rag/index_store.py` (normalize), gefixt 2026-04-22.
- **Confidence:** High (Test mit 5 Varianten: `aegypten`, `aegypten.pdf`, `AEGYPTEN.PDF`, `Aegypten.Pdf`, voller Pfad — alle 5 treffen korrekt).
- **Tags:** RAG, WindowsPaths, SlashTrap, Normalization, ChromaDB, PathComparison, HybridRetriever

## [LESSON] #HardwareTruth #RAG "Hardware-Truth over Index-Faith — Physischer Scan vor Tool-Ausführung"
- **Kontext:** RAG V2 Dubletten-Erkennung basierte auf IndexStore-Lookup (`get_all_paths_for_filename`). Nach Memory-Purge war das zweite Duplikat (Documents\JanusPDFs\aegypten.pdf) nicht mehr indiziert, aber physisch vorhanden. Tool-Executor vertraute blind auf Index und injizierte keinen Warn-Header → KI wählte Datei stillschweigend aus ("Silent Selection") ohne User-Transparenz.
- **Problem:** Blindes Vertrauen auf Datenbank-Index führt zu "Silent File Mismatch" Halluzinationen. Der Index kann veraltet sein (durch Purges, Re-Indexing, oder inkrementelle Updates). Wenn eine Datei physisch existiert aber nicht im Index, "sieht" das Tool sie nicht und wählt eine andere Datei stillschweigend aus. Der User erhält keine Warnung über die Redundanz.
- **Lösung:** **Physischer Dubletten-Scan** vor Tool-Ausführung. Wissens-Tools (knowledge.query, knowledge.read_full_text) müssen vor der eigentlichen Ausführung einen schnellen physischen Scan über die Workspaces machen (via `filesystem_manager.find_files` oder glob). Wenn `count > 1`, wird ein Warn-Header injiziert:
  ```python
  # Physical duplicate detection in tool_executor.py
  from backend.services.filesystem_manager import find_files
  stem_pattern = f"{needle_stem}.*"
  fs_result = find_files(pattern=stem_pattern, max_results=100, search_all_drives=False)
  if len(filtered_physical) > 1:
      # Inject warning header
      warning_block = f"!!! SYSTEM-WARNHINWEIS: MEHRERE DATEIEN GEFUNDEN !!!\nDateiname: {filename}\nGefundene Pfade:\n{paths}\nAktuelle Auswahl: {chosen.path}"
  ```
  P0-Direktive in Skill-JSONs zwingt LLM zur Transparenz: "Hinweis: Ich habe [Anzahl] Versionen von [Datei] gefunden. Ich verwende hier die Datei aus [Pfad]. Die anderen Fundorte sind: [Liste]."
- **Härtung:** Warn-Header ist P0-Priorität (vor jedem anderen Content). LLM muss mit dem Hinweis beginnen, sonst gilt die Antwort als "schwerer Systemfehler". Der Header ist im Tool-Output physisch injiziert, nicht nur im LLM-System-Prompt.
- **Tripwire:** Wenn User nach einer Datei fragt und das Tool eine Datei liefert, aber es gibt physisch weitere Kopien mit demselben Namen im Workspace → Hardware-Truth-Verletzung. Erkennbar im Log: Fehlender `[DUPLICATE-DETECTION]` Eintrag trotz physischer Dubletten.
- **Location:** `backend/services/tool_executor.py` (physical duplicate detection), `backend/skills/knowledge/query.json` (P0 directives), `backend/skills/knowledge/read_full_text.json` (P0 directives), gefixt 2026-04-22.
- **Confidence:** High (Physischer Scan findet alle Dateien unabhängig vom Index-Stand).
- **Tags:** RAG, HardwareTruth, IndexFaith, DuplicateDetection, Filesystem, Transparency, P0Directives

## [LESSON] #Orchestration #ToolManager "The Store-Key Ambiguity — Registriere Tools immer unter ihrer globalen Skill-ID, nicht unter dem lokalen Funktionsnamen"
- **Kontext:** `ToolManager.register_tool()` speicherte Tools unter `func.__name__` (z.B. `query_knowledge_base`, `read_file`, `list_directory`), während `get_tool()` versuchte, unter der Skill-ID (z.B. `knowledge.query`, `filesystem.read_file`) zu suchen. Legacy-Routing-Logik existierte, aber der Store-Key war asymmetrisch — ein Reverse-Lookup auf einen nicht existierenden Key.
- **Problem:** `get_tool("knowledge.query")` lieferte immer `None`, weil das Tool unter `"query_knowledge_base"` gespeichert war. Das Forward-Mapping (legacy → skill) existierte im Code, aber der Store war unter dem Legacy-Namen, nicht der Skill-ID. Ergebnis: Zwei parallele Namensräume ohne funktionierende Verbindung.
- **Lösung:** `register_tool()` persistiert jetzt primär unter `skill_id = self.get_skill_id(tool_name)` und legt bei Divergenz einen Alias unter dem Legacy-Namen an:
  ```python
  skill_id = self.get_skill_id(tool_name)
  self.tools[skill_id] = tool  # Registrierung unter Skill-ID (z.B. knowledge.query)
  if tool_name != skill_id:
      self.tools[tool_name] = tool  # Alias unter Legacy-Name (z.B. query_knowledge_base)
  ```
- **Tripwire:** Wenn `get_tool(skill_id)` für ein existierendes Skill-ID `None` zurückgibt, obwohl das Tool registriert ist → Store-Key-Mismatch zwischen `register_tool()` und `get_tool()`.
- **Location:** `backend/services/tool_manager.py::register_tool` (Zeilen 326-329), gefixt 2026-04-22.
- **Confidence:** High (Audit + Code-Review bestätigt Asymmetrie).
- **Tags:** Orchestration, ToolManager, SkillID, LegacyRouting, StoreKey, Asymmetry

---

## [PATTERN] #StranglerArchive "Strangler Archive Pattern — Nachrichten bei Kompression in Archiv-Tabelle schieben statt löschen; Injektion eines Summary-Proxys für Kontext-Erhalt"
- **Kontext:** TASK-057 Context Awareness System implementierte Token-over-Count und Emergency Overflow Selection. Bei Kompression von Nachrichten (z.B. wenn Token-Limit erreicht wird) wurden alte Nachrichten gelöscht, was zu Kontextverlust führte. Das Strangler Pattern bietet eine Alternative: Komprimierte Nachrichten werden in eine Archiv-Tabelle verschoben und ein Summary-Proxy injiziert, um Kontext zu erhalten.
- **Problem:** Löschen von Nachrichten bei Kompression führt zu unwiederbringlichem Kontextverlust. Historische Informationen gehen verloren, was die Qualität von nachfolgenden Antworten beeinträchtigt. Keine Möglichkeit, archivierte Nachrichten wiederherzustellen.
- **Lösung:**
  1. **Archiv-Tabelle:** Neue Tabelle `messages_archive` mit Spalten für Original-Nachricht, Kompressions-Metadaten und Summary-Proxy.
  2. **Kompressions-Logik:** Wenn Token-Limit erreicht wird, werden älteste Nachrichten in `messages_archive` verschoben statt gelöscht.
  3. **Summary-Proxy:** Für jede archivierte Nachricht wird ein kurzes Summary generiert und als Proxy-Nachricht injiziert.
  4. **Wiederherstellung:** API-Endpoint ermöglicht Wiederherstellung archivierter Nachrichten bei Bedarf.
- **Härtung:** Summary-Proxy garantiert, dass wesentliche Informationen erhalten bleiben. Archiv-Tabelle ermöglicht Audit-Trail und Wiederherstellung.
- **Tripwire:** Wenn Kontext nach Kompression verloren geht → Summary-Proxy nicht injiziert. Erkennbar: Antworten beziehen sich nicht mehr auf archivierte Informationen.
- **Location:** TASK-057 Context Awareness System (Token-over-Count, Emergency Overflow), implementiert 2026-04-30.
- **Confidence:** High (Archiv-Muster bewährt sich in großen Systemen für Kontext-Erhalt).
- **Tags:** StranglerArchive, Compression, ContextRetention, ArchiveTable, SummaryProxy, TASK057

---

## [PATTERN] #SelfHealingGateway "Self-Healing Gateway Pattern — Agnostischer Retry-Loop bei Auth-Fehlern (expired keys) inkl. automatischem Refresh aus dem Keyring"
- **Kontext:** TASK-057 Context Awareness System implementierte Gemini Key Self-Healing bei expired keys. API-Calls können mit 401/expired Fehlern fehlschlagen, wenn API-Keys ablaufen. Der Retry-Loop muss provider-agnostisch sein und automatisch Keys aus dem Keyring refreshen.
- **Problem:** 401/expired Fehler führen zu Abbruch ohne Wiederholung. Manuelle Key-Updates sind zeitaufwendig. Provider-spezifische Retry-Logik führt zu Code-Duplikation. Keine automatische Wiederherstellung bei temporären Auth-Fehlern.
- **Lösung:**
  1. **Retry-Loop:** Wrapper-Funktion um API-Calls mit Retry-Logik bei 401/expired Fehlern.
  2. **Keyring-Refresh:** Bei 401 wird automatisch ein neuer Key aus dem Keyring geladen (via `keyring.get_password()`).
  3. **Provider-Agnostisch:** Retry-Logik funktioniert für alle Provider (OpenAI, Gemini, Ollama).
  4. **Max-Retries:** Begrenzung auf 3 Retries um Endlos-Loops zu vermeiden.
  5. **Logging:** Detailliertes Logging für jeden Retry-Versuch mit Fehler-Context.
- **Härtung:** Retry-Loop garantiert Robustheit bei temporären Auth-Fehlern. Keyring-Refresh ist sicher (verschlüsselte Speicherung). Max-Retries verhindert Endlos-Loops.
- **Tripwire:** Wenn API-Calls bei 401 abbrechen ohne Retry → Retry-Loop nicht aktiv. Erkennbar im Log: Fehlender `[RETRY]` Eintrag bei 401-Fehler.
- **Location:** `frontend/js/context-awareness.js` (Gemini Self-Healing Retry-Loop), implementiert 2026-04-30.
- **Confidence:** High (Retry-Loop funktioniert provider-agnostisch, Keyring-Refresh sicher).
- **Tags:** SelfHealingGateway, RetryLoop, AuthError, Keyring, ProviderAgnostic, TASK057

---

## [PATTERN] #IntentNegativeGuard "Intent Negative Guard Pattern — Nutzung von Ausschlusskriterien (Negative Keywords) in der IntentEngine, um Falsch-Positive bei komplexen Workflows (Storybook) zu verhindern"
- **Kontext:** TASK-057 Context Awareness System implementierte Storybook Intent Härtung. Eine allgemeine Aufforderung zur Zusammenfassung eines langen Textes wurde vom `intent_engine` fälschlicherweise als "Storybook-Intent" klassifiziert, was den falschen Workflow auslöste (Bilderstellung statt Text-Zusammenfassung).
- **Problem:** Positive Keywords allein führen zu Falsch-Positiven bei komplexen Workflows. Zusammenfassungs-Anfragen mit "fass zusammen" triggerten Storybook-Workflow, obwohl sie kreative Aufforderungen erfordern. Keine Möglichkeit, bestimmte Intents explizit auszuschließen.
- **Lösung:**
  1. **Negative Keywords:** `STORYBOOK_NEGATIVE_KEYWORDS` (fass zusammen, zusammenfassen, analysiere, gib mir eine übersicht) definieren Ausschlusskriterien.
  2. **Positive Keywords:** `STORYBOOK_POSITIVE_KEYWORDS` (erzähle eine geschichte, kinderbuch, illustriere, mit den charakteren) definieren explizite Trigger.
  3. **Detect-Methode:** `detect_storybook_intent()` prüft zuerst Negative-Keywords (Ausschluss), dann Positive-Keywords (Einschluss).
  4. **Logik:** Intent nur wenn Positive-Keywords vorhanden UND Negative-Keywords NICHT vorhanden.
  5. **Frontend-Integration:** `chat_orchestrator.py` verwendet `intent_engine.detect_storybook_intent()` statt inline-Check.
- **Härtung:** Negative-Keywords verhindern Falsch-Positive bei Analyse/Zusammenfassungs-Anfragen. Positive-Keywords schärfen Trigger auf kreative Aufforderungen.
- **Tripwire:** Wenn Zusammenfassungs-Anfrage Storybook-Workflow auslöst → Negative-Keywords fehlen oder sind zu restriktiv. Erkennbar im Log: `[CU-2] Storybook intent blocked by negative keyword` fehlt.
- **Location:** `backend/services/orchestrator/intent_engine.py` (STORYBOOK_POSITIVE_KEYWORDS, STORYBOOK_NEGATIVE_KEYWORDS, detect_storybook_intent), `backend/services/chat_orchestrator.py` (intent_engine Aufruf), implementiert 2026-04-30.
- **Confidence:** High (Negative-Keywords verhindern Falsch-Positive, Positive-Keywords schärfen Trigger).
- **Tags:** IntentNegativeGuard, StorybookIntent, FalsePositive, NegativeKeywords, IntentEngine, TASK057

---

## [LESSON] #Pydantic #SchemaDrift "The Parameter Trinity — Manifest (JSON), Schema (Pydantic) und Decorator (Python) müssen denselben Parameter-Namen verwenden"
- **Kontext:** Filesystem-Skills hatten einen Drei-Ebenen-Drift: Skill-JSON (`read_file.json`) definierte `"file_path"`, Pydantic-Schema (`ReadFileArgs`) deklarierte `path: str`, und Python-Decorator (`@requires_path_auth`) erwartete `path_arg="file_path"`. Das JSON-`input_schema` wurde vom System komplett ignoriert.
- **Problem:** Pydantic-Validation akzeptierte `{"path": "..."}`, aber der Decorator las `kwargs["file_path"]` → KeyError/Auth-Fehler trotz erfolgreicher Schema-Validierung. Die gecachte Modell-Instanz (`ToolDefinition.args_schema`) war der "Zombie", der das LLM mit falschem Schema fütterte. Skill-JSON-Schemas waren toter Code (nie gelesen).
- **Lösung:** Pydantic-Schemas an Skill-JSON und Decorator angleichen: `ReadFileArgs.path` → `file_path`, `DeleteFileArgs.path` → `file_path`, `CreateFileArgs.path` → `file_path`. Einheitlicher Parameter-Name `file_path` auf allen drei Ebenen.
- **Tripwire:** Wenn Tool-Validation erfolgreich ist, aber die Ausführung mit `KeyError` auf einem Parameter bricht, der im Schema anders heißt → Parameter-Trinity-Violation.
- **Location:** `backend/data/schemas.py` (Zeilen 620, 646, 650), gefixt 2026-04-22.
- **Confidence:** High (Cross-Reference JSON ↔ Pydantic ↔ Decorator bestätigt Inkonsistenz).
- **Tags:** Pydantic, SchemaDrift, ParameterTrinity, file_path, SkillJSON, Decorator

## [LESSON] #DeadCode #Prompting #PromptRegistry "Registry-Direktiven müssen nicht nur definiert, sondern auch injiziert werden — sonst sind sie wirkungslos"
- **Kontext:** User verschärfte `prompt_registry.py::search_command_priority` + ergänzte `file_system_guard` mit Dubletten-Hinweis über 3 Sessions hinweg. Trotzdem berichteten faule Modelle (Nano/Mini) weiter Datei-Pfade aus Memory ohne Tool-Call. Log-Analyse des echten OpenAI-Request zeigte: Der System-Prompt enthielt WEDER `search_command_priority` NOCH `file_system_guard`.
- **Problem:** Beide Direktiven waren in `_DIRECTIVES` als Einträge definiert, aber nirgends per `prompt_registry.get_directive(...)` aufgerufen und an den System-Prompt angehängt. Der reale Prompt-Build in `execution_dispatcher.py:190` ruft `apply_verbosity_control(wf.system_prompt_for_llm)` — welches bisher nur `verbosity_control` + `no_meta_talk` anhängte. Ergebnis: Dead Code. Die schärfsten Formulierungen ("schwerer Systemfehler", "ABSOLUTE Priorität") erreichten den LLM nie.
- **Lösung:** `apply_verbosity_control()` erweitert — Schleife iteriert über 4 Direktiven statt 2. Damit werden `file_system_guard` + `search_command_priority` bei jedem DEFAULT-Dialog-Turn angehängt. Dedup-Check (`if rule not in base_text`) garantiert Idempotenz bei wiederholten Aufrufen.
- **Tripwire:** Wenn ein neu hinzugefügter `prompt_registry`-Eintrag nicht wirkt → grep nach `get_directive("<key>")` über den Code — fehlt dieser Call, ist die Direktive Dead Code. Besonders kritisch bei Base-System-Prompts aus der DB (Persönlichkeiten), die Prompt-Registry-Direktiven überstimmen können.
- **Location:** `backend/services/orchestrator/prompt_registry.py:197-216` (apply_verbosity_control), gefixt 2026-04-21.
- **Confidence:** High (Smoke: alle 4 Direktiven injiziert + idempotent).
- **Tags:** DeadCode, Prompting, PromptRegistry, SystemPrompt, Injection, BrevityBias

## [LESSON] #LLM #BrevityBias "Faule Modelle bevorzugen kurze Antworten aus Memory über Tool-Calls — bei Suchanfragen muss Tool-Call-Pflicht explizit erzwungen werden"
- **Kontext:** Memory-Context ist so gut, dass "faule" Modelle (wie Nano) Suchanfragen mit alten Erinnerungen aus Memory beantworten statt Tool-Calls durchzuführen. User fragt "Wo liegt die Datei X?" → LLM antwortet "Ich erinnere mich, dass X im Ordner Y liegt" statt `filesystem.find_files` aufzurufen. Resultat: veraltete Informationen statt aktueller Hardware-Validierung.
- **Problem:** "Brevity-Bias" bei faulen Modellen: Wenn Memory bereits Informationen enthält, bevorzugen LLMs kurze Antworten aus Memory über Tool-Calls, auch wenn die Anfrage explizit eine Suche fordert. Das führt zu veralteten Informationen und schlechter UX bei Dateisuchen.
- **Lösung:** Prompt-Registry-Direktive `search_command_priority` mit stärkerer HARDWARE-TRUTH-REGEL: "!!! WERKZEUGNUTZUNGS-DIREKTIVE — HARDWARE-TRUTH-REGEL !!! Wenn der Nutzer nach dem Verbleib, Speicherort oder der Existenz von Dateien sucht, hat das Live-Werkzeug filesystem.find_files ABSOLUTE Priorität vor der FAKTENGRUNDLAGE (Memory). Das Gedächtnis dient NUR als Orientierung. Du darfst NIEMALS einen Pfad aus der Erinnerung nennen, ohne ihn in EXAKT DIESEM Turn durch einen Tool-Call validiert zu haben. Eine Antwort ohne Live-Tool-Call bei Suchanfragen gilt als schwerer Systemfehler." Stärkere Formulierung mit "ABSOLUTE Priorität", "NIEMALS einen Pfad aus der Erinnerung nennen ohne Validierung" und "schwerer Systemfehler" bei Antworten ohne Tool-Call.
- **Tripwire:** Wenn ein LLM Suchanfragen mit Memory-Antworten beantwortet statt Tool-Calls durchzuführen → fehlt eine explizite Tool-Call-Pflicht-Direktive für Suchanfragen.
- **Location:** `backend/services/orchestrator/prompt_registry.py:74`, gefixt 2026-04-21.
- **Confidence:** High (Unit-Smoke: Direktive enthält "FAKTENGRUNDLAGE", "filesystem-Tool aufrufen" und "Wo liegt die Datei X" ✅).
- **Tags:** LLM, BrevityBias, ToolCall, Memory, Search, PromptRegistry

## [LESSON] #UX #Prompting "LLM braucht explizite Anweisungen für proaktive UX-Maßnahmen (Dubletten-Hinweis) — Default ist stille Ausgabe"
- **Kontext:** `filesystem.find_files` liefert korrekt Duplikate (z.B. 2 Kopien von `gundula1.pdf` an verschiedenen Orten), aber der LLM hatte keine explizite Anweisung, den User darauf hinzuweisen. Resultat: Liste von Pfaden ohne Kontext, User weiß nicht, ob es Dubletten sind oder ob das Tool nur einen Treffer gefunden hat.
- **Problem:** LLMs sind standardmäßig "stille Ausgeber" — sie geben das Tool-Result aus, ohne proaktive UX-Verbesserungen einzubauen, es sei denn, es ist explizit angeordnet. Für Dateisuchen ist das kritisch: Dubletten sind ein häufiges UX-Problem, und der User möchte wissen, ob es mehrere Kopien gibt.
- **Lösung:** Prompt-Registry-Direktive `file_system_guard` erweitern: "WICHTIG: Wenn ein Such-Tool (z.B. filesystem.find_files) mehrere Dateien mit identischem Namen an verschiedenen Orten findet, MUSST du den Nutzer explizit auf diese Dubletten hinweisen (z.B. 'Ich habe die Datei an 2 Stellen gefunden: ...')."
- **Tripwire:** Wenn ein Tool-Output eine Liste von ähnlichen Einträgen liefert (Dateien, Produkte, Personen), aber der LLM diese nicht gruppiert oder auf Duplikate hinweist → fehlt eine Prompt-Direktive.
- **Location:** `backend/services/orchestrator/prompt_registry.py:42`, gefixt 2026-04-21.
- **Confidence:** High (Unit-Smoke: Direktive enthält "Dubletten" und "find_files" ✅).
- **Tags:** UX, Prompting, Dubletten, LLM, Proaktivität, PromptRegistry

## [LESSON] #Performance #FactExtraction "Tool-Output-Größe beeinflusst downstream-Fakten-Extraktion massiv — max_results Default an downstream-Overhead anpassen"
- **Kontext:** `filesystem.find_files(max_results=100)` lieferte bis zu 100 Dateipfade als Tool-Output. Die Fakten-Extraktion (`extract_and_save_fact_from_interaction`) verarbeitet die Assistant-Message (die die Dateiliste enthält) und Nano extrahiert jeden Pfad als separate "Langzeit-Fakt". Bei 87 Pfaden → 87 Fakten → DB-Overhead für Sekunden, System-Lag.
- **Problem:** `max_results`-Default wurde nur nach Such-Qualität (Vollständigkeit) gewählt, nicht nach downstream-Kosten (Fakten-Extraktion). 100 Pfade sind für die meisten Use-Cases überdimensioniert und führen zu massivem Overhead.
- **Lösung:** `max_results` Default von 100 auf 20 gesenkt. 20 Treffer sind für die meisten Use-Cases ausreichend; bei Bedarf kann der User `search_all_drives=true` oder explizites `max_results` nutzen. Docstring aktualisiert mit Begründung ("begrenzt Fakten-Extraktion-Overhead nach Dateisuchen").
- **Härtung (empfohlen, nicht implementiert):** Fakten-Extraktion härten, um Pfade als "Langzeit-Fakten" zu ignorieren oder zu deduplizieren. Aktuell ist die Limit-Senkung der pragmatische Fix.
- **Tripwire:** Wenn ein Tool-Output eine große Liste von Items liefert (Dateien, Produkte, Personen) und das System nach der Antwort für Sekunden "friert" → Fakten-Extraktion extrahiert jedes Item als separate Fact.
- **Location:** `backend/services/filesystem_manager.py:318` (max_results Default 100 → 20), gefixt 2026-04-21.
- **Confidence:** High (Unit-Smoke: `max_results default == 20` ✅).
- **Tags:** Performance, FactExtraction, Limit, ToolOutput, Downstream, Nano

## [LESSON] #Numpy #Embeddings #Robustness "np.array/np.stack auf heterogenen Embedding-Listen bricht mit 'inhomogeneous shape' — sanitize vor stack, Alignment via Padding erhalten"
- **Kontext:** `backend/services/vector_service.py::calculate_similarity_with_precomputed` baute das Corpus-Array via `np.array(candidate_embeddings, dtype=np.float32)` aus einer `List[List[float]]`. Im Memory-Retrieval sind die Einträge aber *heterogen*: manche Slots haben kein gecachtes Embedding (→ `None`), andere stammen aus älteren Modell-Versionen mit abweichender Dimension (z.B. 512 statt 384), vereinzelt NaN aus defekten Encodings.
- **Problem:** `np.array(mixed_list, dtype=float32)` scheitert **deterministisch** bei jeder inhomogenen Stelle mit `ValueError: setting an array element with a sequence. The requested array has an inhomogeneous shape after 1 dimensions. The detected shape was (N,) + inhomogeneous part.` Der gesamte Similarity-Batch wirft eine Exception und der Caller kriegt `[0.0] * len(candidates)` zurück — obwohl 26/27 Embeddings valide gewesen wären. Der Bug ist still, weil er im `except Exception` abgefangen und nur geloggt wird; Retrieval-Qualität kollabiert lautlos.
- **Lösung:** Helper `_safe_stack_embeddings(candidates, expected_dim)` filtert *vor* `np.stack`:
  ```python
  valid_pairs = []
  for i, emb in enumerate(candidates):
      if emb is None or not isinstance(emb, (list, tuple, np.ndarray)): continue
      try: arr = np.asarray(emb, dtype=np.float32)
      except (ValueError, TypeError): continue
      if arr.ndim != 1 or arr.size == 0 or not np.all(np.isfinite(arr)): continue
      valid_pairs.append((i, arr))
  ref_dim = expected_dim or valid_pairs[0][1].size
  consistent = [(i, a) for i, a in valid_pairs if a.size == ref_dim]
  return [i for i,_ in consistent], np.stack([a for _,a in consistent]), dropped_count
  ```
  **Kritisch: Alignment-Preservation.** Die Consumer-APIs geben `[0.0] * len(original)` zurück und schreiben Scores per `valid_indices[local]→original_idx` — damit bleibt der Caller (Knapsack-Selector o.ä.) index-kompatibel.
- **Tripwire:** Im Log `Error in precomputed similarity calculation` oder `Error in batch similarity calculation` mit `inhomogeneous part` → **exakt dieser Bug**. Außerdem: Retrieval liefert plötzlich nur noch 0-Scores obwohl Chat aktiv ist.
- **Location:** `backend/services/vector_service.py::_safe_stack_embeddings` (neu), `calculate_similarity_batch`, `calculate_similarity_with_precomputed`, gefixt 2026-04-21.
- **Confidence:** High (Unit-Smoke mit `[valid, None, wrong_dim, nan, valid, 'not_list']` → 4 gefiltert, 2 korrekt gescored, Output-Länge 6 erhalten).
- **Tags:** Numpy, Embeddings, Similarity, Memory, Retrieval, Robustness, Shape, Alignment

## [LESSON] #Pydantic #SchemaDrift "Literals in Pydantic-Schemas driften stillschweigend von realen Config-Werten — baue CI-Drift-Check gegen alle Manifests"
- **Kontext:** `backend/data/schemas.py::SkillMetadata.sandbox_level` definierte `Literal["unrestricted", "workspace_only", "read_only_fs"]`. Die **11 filesystem-Skill-Manifests** (`read_file.json`, `move_file.json`, …) nutzten aber seit Längerem konsistent den Wert `"full"`.
- **Problem:** Der Mismatch warf beim Skill-Loading **keinen Fehler** — offenbar wird `SkillMetadata` im Loader mit tolerantem Pfad (`extra=allow` oder `model_validate` ohne `strict=True`) gebaut, oder `sandbox_level` wird überhaupt nie gegen das Schema validiert beim Load. Die Divergenz existiert damit still, aber jede zukünftige Strict-Validierung (z.B. wenn jemand `ConfigDict(strict=True)` hinzufügt) würde 11 Skills auf einmal brechen.
- **Lösung:** Literal-Liste um tatsächlich genutzten Wert erweitern: `Literal["unrestricted", "workspace_only", "read_only_fs", "full"]`. Die korrekte Richtung war NICHT, 11 Manifests umzubiegen — `"full"` ist semantisch distinkt (volle FS-Rechte innerhalb der Path-Sentinel-Workspace-Grenze, anders als `"workspace_only"` oder `"read_only_fs"`) und die Konvention war gewollt.
- **Härtung (empfohlen, nicht implementiert):** CI-Check, der alle Manifests in `backend/skills/**/*.json` gegen `SkillMetadata` strikt validiert, würde zukünftige Drift sofort sichtbar machen.
- **Tripwire:** Wenn ein Schema-Feld einen Literal-Typ hat und eine Config-Datei einen davon abweichenden Wert, aber kein Fehler geworfen wird — das ist der Drift. Erkennbar nur durch manuelles Cross-Ref oder CI-Validator.
- **Location:** `backend/data/schemas.py:195` (Literal erweitert), gefixt 2026-04-21.
- **Confidence:** Medium-High (Unit-Smoke: alle 4 Literals akzeptiert, `"hacky"` abgelehnt — aber ohne CI-Validator bleibt Drift-Risiko).
- **Tags:** Pydantic, Literal, Schema, Config, Drift, Validation, CI

## [PATTERN] #Orchestration #IntentOverride "Pre-Resolution Logic-Escalation für Planungs-Tasks"
- **Kontext:** Komplexe Planungs-Tasks (z.B. Sortieren von PDFs nach Themeninhalt) erfordern höhere Reasoning-Kapazität als Standard-Modelle bieten. Das System soll solche Intents automatisch erkennen und vor der Tool-Ausführung auf ein Logic-Tier-Modell eskalieren, ohne dass der LLM explizit nach einem Upgrade fragen muss.
- **Problem:** Ohne Intent-Eskalation versuchen "faule" Modelle (Nano/Mini) komplexe Sortieraufgaben mit glob-Pattern statt semantischer Analyse. Resultat: Ungenaue Sortierung nach Dateinamen statt Inhalt, fehlerhafte Bulk-Operationen.
- **Pattern:** **Pre-Resolution Intent-Detection + MOA-Hierarchie-Upgrade.** In `_apply_pre_resolution_guards()` (vor Tool-Loop) wird die letzte User-Nachricht auf Sortier-Intents geprüft (`sortiere` + `pdf/dateien`). Wenn erkannt, wird via `MOA_MODEL_HIERARCHY` das Logic-Tier-Modell für den aktuellen Provider ermittelt und `wf.chosen_model` überschrieben. Das Upgrade gilt nur für den aktuellen Turn.
  ```python
  if 'sortiere' in query and ('pdf' in query or 'dateien' in query):
      provider_key = str(current_provider or "").strip().lower()
      provider_tiers = MOA_MODEL_HIERARCHY.get(provider_key)
      logic_model = provider_tiers.get('logic') if provider_tiers else None
      if logic_model and wf.chosen_model != logic_model:
          wf.chosen_model = logic_model
  ```
- **Warum Pre-Resolution:** Das Modell-Upgrade muss VOR dem Prompt-Build passieren, damit der LLM mit dem Logic-Tier-Modell den Plan erstellt und die Tool-Aufrufe generiert. Nachträgliches Upgrade wäre zu spät.
- **Trigger-Kriterien für Intent-Override:** (1) Klare Intent-Keywords (`sortiere`, `ordnen`, `thematisch`). (2) Subjekt-Keywords (`pdfs`, `dateien`). (3) Provider-agnostische Hierarchie via MOA_MODEL_HIERARCHY (OpenAI: gpt-5.4, Gemini: gemini-3-pro-preview).
- **Location:** `backend/services/orchestrator/execution_dispatcher.py` (_apply_pre_resolution_guards), `backend/llm_providers/shared/moa.py` (MOA_MODEL_HIERARCHY), implementiert 2026-04-24.
- **Confidence:** High (Intent-Erkennung ist deterministisch, MOA-Hierarchie ist zentral definiert und provider-agnostisch).
- **Tags:** Orchestration, IntentOverride, LogicEscalation, MOA, PreResolution, Planning, Sorting

---

## [PATTERN] #Planning #FehlbefundZurueckweisung "Externe Fix-Pläne immer gegen Code verifizieren, bevor implementiert wird"
- **Kontext:** Der User übergab einen 3-Punkte-Fix-Plan aus AI Studio. Punkt #2 lautete: "Repariere den OllamaCompiler Import in `backend/services/prompting/factory.py`."
- **Problem:** Blindes Abarbeiten hätte hier einen Phantom-Fix produziert — `factory.py:3` importiert sauber aus `backend/llm_providers/ollama/compiler.py`, die Klasse `OllamaCompiler(BasePromptCompiler)` existiert, hat eine funktionierende `compile()`-Methode. Der Live-Log zeigte keinen Import-Fehler; Ollama-Polling lief erfolgreich. Kein Beweis für einen Bug.
- **Pattern:** **Vor Implementation Scope-Review.** Jeder Plan-Punkt wird gegen drei Quellen abgeglichen: (1) Code (existiert die vermutete Fehlstelle?), (2) Log (gibt es Runtime-Evidenz?), (3) Stacktrace/Reproduktion (ist der Bug reproduzierbar?). Nur bei Treffer in mindestens einer Quelle implementieren.
- **Kommunikation mit User:** Fehlbefund *nicht* stillschweigend skippen, sondern explizit zurückmelden mit Beweis (Code-Zitat, Log-Quote) und User entscheiden lassen — eventuell sieht er etwas, das in meinem Scan fehlte.
- **Counter-Pattern:** AI-Studio-Pläne blind als Ground-Truth behandeln. Das produziert Schein-Commits, die echten Bugs Aufmerksamkeit wegnehmen und die Test-Suite mit Non-Fixes aufblähen.
- **Tripwire:** Wenn ein Fix-Plan sehr spezifisch klingt ("Repariere X in Datei Y"), aber du beim Öffnen der Datei keinen Bug siehst und im Log keine Spur findest — **nicht fixen**. Stattdessen zurückmelden.
- **Location:** Session 2026-04-21 Core-Repair-Arc (OllamaCompiler-Plan-Punkt zurückgewiesen).
- **Confidence:** High (Backend läuft produktiv, Ollama-Integration aktiv, keine Import-Error-Logs).
- **Tags:** Planning, Review, AIStudio, FalsePositive, VerifyBeforeFix, Communication

## [LESSON] #Python #Pathlib #Robustness "Path.rglob bricht bei FileNotFoundError komplett ab — nutze os.walk mit onerror für robuste rekursive Suche"
- **Kontext:** Für `filesystem.find_files` (rekursive Dateisuche) wurde zunächst `Path(root).rglob(pattern)` genutzt. Auf Windows-Systemen mit defekten/falsch benannten Desktop-Ordnern (z.B. `C:\Users\pruve\Desktop\kikitest.` — Trailing-Dot ist auf NTFS lesbar, aber über manche API-Pfade nicht auflösbar) wirft `rglob` intern `FileNotFoundError: [WinError 3]` und **bricht die gesamte Iteration ab** statt nur den betroffenen Pfad zu überspringen. Ergebnis: Suche liefert 0 Treffer obwohl Datei vorhanden ist.
- **Lösung:** `os.walk(root, onerror=_walk_onerror)` mit einem `onerror`-Callback, der Per-Pfad-Fehler auf DEBUG loggt und die Iteration weiterführt. Kombiniert mit `fnmatch.filter(filenames, pattern)` ersetzt das `rglob` vollständig, ist robuster UND erlaubt zusätzlich die In-Place-Mutation von `dirnames[:]` für Noise-Ordner-Skips (`Windows`, `node_modules`, etc.).
  ```python
  def _walk_onerror(err: OSError) -> None:
      logger.debug("find_files: Überspringe unerreichbaren Pfad (%s)", err)

  for dirpath, dirnames, filenames in os.walk(str(root), onerror=_walk_onerror):
      if apply_exclude:
          dirnames[:] = [d for d in dirnames if d.lower() not in EXCLUDE_DIRS]
      for fname in fnmatch.filter(filenames, effective_pattern):
          matches.append(os.path.join(dirpath, fname))
  ```
- **Tripwire:** Wenn eine rekursive Path-Suche auf Windows unerwartet 0 Treffer liefert, obwohl die Datei existiert, und im Log `WinError 3` oder `FileNotFoundError` auftaucht — das ist der Bug.
- **Location:** `backend/services/filesystem_manager.py::find_files` (Z. 370ff), gefixt 2026-04-21
- **Confidence:** High (Live-verifiziert: Auto-Escalation über 3 Laufwerke findet beide Duplikate trotz 20+ defekten Desktop-Ordnern)
- **Tags:** Python, Pathlib, rglob, os.walk, Windows, Symlink, Robustness, Iteration

## [PATTERN] #ProductionWrapper #DebugCompression "Production Wrapper Pattern — Formatiere komplexe Telemetrie-Rohdaten in Token-effizientes AI-Studio-Format (Summary, Cause, Fix) für maximale Iterationsgeschwindigkeit"
- **Kontext:** D11 Debug Compression Engine liefert rohe Heuristik-Daten (Hard Errors, Model Drift, Latency Spikes, Confidence Score). Für AI Studio Debugging ist ein strukturiertes, Token-effizientes Format erforderlich, das LLMs schnell verarbeiten können ohne Context-Overhead.
- **Problem:** Rohdaten aus dem Debug Engine sind unstrukturiert und benötigen manuelle Interpretation. Kein dedizierter POST-Endpunkt für AI Studio Integration. Kein standardisiertes Format für Debug-Reports.
- **Lösung:** **Production Wrapper mit Formatter + POST Endpoint.**
  1. **Formatter (`debug_formatter.py`):** `format_debug_report(summary_data: dict) -> str` generiert strukturiertes Markdown mit Standard-Sections: SUMMARY (High-level Überblick), ROOT CAUSE (Technische Ursachenanalyse), FINDINGS (Detaillierte Heuristik-Ergebnisse), CONFIDENCE (Score + Interpretation), RECOMMENDED ACTION (Konkrete Handlungsempfehlungen).
  2. **POST Endpoint (`/api/skills/debug-log`):** Akzeptiert `{"trace_id": "optional", "mode": "fast|full"}`. Ruft D11 Debug Engine auf, leitet Ergebnisse durch Formatter, gibt strukturiertes Markdown zurück.
  3. **Timeout-Schutz:** 3.0s Hard Timeout auf Log-Fetch und Heuristik-Analyse via `asyncio.wait_for()`. HTTP 504 auf Timeout, HTTP 500 auf Errors.
  4. **Asyncio Anti-Pattern Fix:** `fetch_logs()` ist async → direkt mit `await` aufrufen (nicht in `run_in_executor`). `_run_heuristics()` ist sync CPU-gebunden → in `run_in_executor` ausführen.
  5. **LogEntry Attribute Mapping:** LogEntry-Objekte (timestamp, level, message, metadata) werden zu Objekten mit Attributen konvertiert, die `_run_heuristics` erwartet (status, skill, latency_ms, trace_id, payload).
  6. **Windsurf Skill:** `.windsurf/workflows/debug_log.md` mit curl.exe-Befehl für PowerShell-Kompatibilität.
- **Härtung:** Typing-Imports (`Optional, List, Dict, Any`) hinzugefügt um NameError bei Server-Start zu vermeiden. Confidence Scoring Fix: Log-Count als positives Signal, keine Fehler = hohe Confidence (0.9 für 100 Logs).
- **Tripwire:** Wenn /api/skills/debug-log hängt oder NameError bei Server-Start → Asyncio Anti-Pattern oder fehlende Typing imports.
- **Location:** `backend/services/logging/debug_formatter.py` (neu), `backend/api/routers/system.py` (POST Endpoint), `.windsurf/workflows/debug_log.md` (Skill), implementiert 2026-04-26.
- **Confidence:** High (Endpoint operational, Formatter getestet, Windsurf Skill funktioniert).
- **Tags:** ProductionWrapper, DebugCompression, Formatter, AIStudio, TokenEfficient, StructuredFormat, POSTEndpoint, Asyncio, HardTimeout

---

## [PATTERN] #GlobalInsightAggregation #MacroAnalytics "Trennung von Mikro-Debugging (Session) und Makro-Analyse (Global) zur Identifikation systemweiter Architekturschwächen"
- **Kontext:** D11 Debug Compression Engine liefert Session-level Debugging (trace_id-basiert, letzte 10 Minuten). Für System-Health Monitoring ist eine globale Analyse aller Logs erforderlich, um systemische Muster über Skills und Models hinweg zu identifizieren. Mikro-Debugging ist gut für spezifische Fehler, Makro-Analyse ist notwendig für Architektur-Optimierung.
- **Problem:** Keine globale Aggregation von Logs nach Skill und Model. Keine systemweite Pattern-Detection (z.B. "skill X hat auf allen Models hohe Fehlerquote"). Keine persistenten Insights für Trend-Analyse. Keine Trennung zwischen Session-Debugging und System-Monitoring.
- **Lösung:** **Janus Insight Engine (D12) — Globale Log-Aggregation.**
  1. **Fetcher:** `fetch_logs()` holt Logs aus Supabase für konfigurierbares Zeitfenster (default: 1 Stunde, optional 24h).
  2. **Aggregator:** `aggregate_logs()` gruppiert Logs nach Skill und Model, berechnet calls, errors, total_latency.
  3. **Metrics Calculator:** `calculate_metrics()` berechnet error_rate (errors/calls) und avg_latency_ms (total_latency/latency_count).
  4. **Pattern Detection:** `detect_patterns()` mit deterministischen Regeln: error_rate > 0.2 → "high_error_rate", avg_latency_ms > 2000 → "latency_spike", calls > 50 & error_rate == 0 → "stable".
  5. **Confidence Model:** `calculate_confidence()` mit Volumen-basiertem Scoring: base = min(1.0, calls/100), reduziert um 20% bei error_rate > 0.5.
  6. **POST Endpoint:** `/api/system/insights` mit `{"hours": 1}` Parameter. Speichert Ergebnisse persistent in `logs_insights` Tabelle.
  7. **Schema:** `InsightCreate` und `Insight` Pydantic-Modelle für logs_insights Tabelle.
- **Härtung:** Keine Physics-Engine, keine Reality-Scores (wie gefordert). Deterministische Aggregation ohne probabilistische Modelle. Test-Suite mit 4 Test-Cases (Faulty Skill, Stable Skill, Performance Problem, Multiple Skills/Models).
- **Tripwire:** Wenn globale Muster nicht erkannt werden (z.B. skill mit 50% error_rate wird als "stable" markiert) → Pattern-Detection-Regeln sind inkorrekt implementiert. Wenn Confidence bei vielen Calls nicht 1.0 erreicht → Confidence-Formel hat Fehler.
- **Location:** `backend/services/logging/insight_engine.py` (neu), `backend/api/routers/system.py` (POST Endpoint), `backend/data/schemas_logging.py` (Schema), `backend/tests/test_insight_engine.py` (Test-Suite), implementiert 2026-04-26.
- **Confidence:** High (Test-Suite 4/4 passed, deterministische Aggregation verifiziert, POST Endpoint operational).
- **Tags:** GlobalInsightAggregation, MacroAnalytics, SystemHealth, PatternDetection, SkillModelAggregation, ConfidenceModel, D12

---

## [PATTERN] #OptimizationRuleEngine #ActionFirst "Deterministische Bewertung von System-Insights zur Priorisierung von Entwicklungs-Maßnahmen (Action-First Integration)"
- **Kontext:** D12 Insight Engine liefert Metriken (error_rate, latency), aber keine konkreten Handlungsempfehlungen. Für Action-First Integration (Entwickler soll direkt wissen, was zu tun ist) ist eine Regel-Engine erforderlich, die Insights in priorisierte Actions umwandelt. Keine KI im Backend-Core, nur reine Logik mit Schwellenwerten.
- **Problem:** Keine automatische Generierung von System-Actions basierend auf Insights. Keine Priorisierung von Maßnahmen (CRITICAL > HIGH > MEDIUM > LOW). Keine Integration in AI Studio Workflow (Entwickler muss manuell aus Daten ableiten, was zu tun ist).
- **Lösung:** **Janus Optimization Engine (D13) — Rule-Based System Optimization.**
  1. **Rule Engine:** `evaluate_insight()` mit deterministischen Schwellenwerten: error_rate > 0.5 → CRITICAL MODEL_SWITCH, error_rate > 0.3 → HIGH SCALE_UP, latency > 5000ms → HIGH MODEL_SWITCH, latency > 3000ms → HIGH TIMEOUT_ADJUST, error_rate=0 & latency<1000 → LOW MONITOR.
  2. **Action Types:** MODEL_SWITCH (Model wechseln), SCALE_UP (Ressourcen hochskalieren), TIMEOUT_ADJUST (Timeout erhöhen), MONITOR (Nur überwachen).
  3. **Priority Levels:** CRITICAL (sofort), HIGH (empfohlen), MEDIUM (in Betracht ziehen), LOW (nur Monitoring).
  4. **Persistence:** `store_action()` speichert Actions in logs_actions Tabelle mit JSON-Serialisierung (`model_dump(mode='json')` für datetime).
  5. **GET Endpoint:** `/api/system/optimization-report` lädt neueste Actions und formatiert als Markdown-Report für AI Studio Integration (CRITICAL > HIGH > MEDIUM > LOW Sortierung).
  6. **Schema:** `ActionCreate` und `Action` Pydantic-Modelle für logs_actions Tabelle.
- **Härtung:** Keine KI im Backend-Core (wie gefordert). Deterministische Regeln ohne probabilistische Modelle. Test-Suite mit 7 Test-Cases (High Error Rate, Critical Error Rate, High Latency, Critical Latency, Stable System, Moderate Metrics, Action Serialization).
- **Tripwire:** Wenn Actions bei überschrittenen Schwellenwerten nicht generiert werden → Rule Engine Logik ist fehlerhaft. Wenn DateTime Serialization Fehler auftreten → `model_dump(mode='json')` vergessen. Wenn Markdown-Report nicht AI-Studio-Ready ist → Formatierung prüfen.
- **Location:** `backend/services/logging/optimization_engine.py` (neu), `backend/api/routers/system.py` (GET Endpoint), `backend/data/schemas_logging.py` (Schema), `backend/tests/test_optimization_engine.py` (Test-Suite), implementiert 2026-04-26.
- **Confidence:** High (Test-Suite 7/7 passed, deterministische Regeln verifiziert, GET Endpoint operational, Markdown-Formatierung AI-Studio-Ready).
- **Tags:** OptimizationRuleEngine, ActionFirst, SystemOptimization, RuleEngine, PriorityLevels, MarkdownReport, D13

---

## [PATTERN] #SystemEvolutionLayer #WeeklyLearning "Deterministische Trend-Analyse über Zeitfenster — Woche N vs Woche N-1 Delta-Vergleich mit automatisierter Empfehlungs-Generierung"
- **Kontext:** D14 Weekly Learning Engine analysiert historische D12 Insights über einen 14-Tage-Zeitraum, gesplittet in Woche N (aktuell) und Woche N-1 (Baseline). Das Ziel: Erkennen, ob sich das System verbessert oder verschlechtert — ohne KI, rein über deterministische Schwellenwerte.
- **Problem:** Ohne Trend-Analyse über Zeit waren Verschlechterungen nur per manuellem Vergleich erkennbar. Keine automatische Eskalation bei steigenden Fehlerraten. Kein Cost-Optimization-Signal bei stabilen Skills mit hohem Volumen. Kein Persistence-Layer für die Lern-Historie des Systems.
- **Lösung:** **D14 Weekly Learning Engine — Deterministic Trend Analysis & Recommendation Engine.**
  1. **Fetch:** `fetch_historical_data(days=14)` holt D12 Insights aus logs_insights für 2-Wochen-Vergleich.
  2. **Split:** Woche N (letzte 7 Tage) vs Woche N-1 (vorherige 7 Tage) per `datetime.utcnow() - timedelta(days=7)`.
  3. **Group:** Insights werden per `skill_model` Key gruppiert für paarweisen Vergleich.
  4. **Delta:** `error_rate_diff = avg_current - avg_baseline`, `latency_diff_pct = ((current - baseline) / baseline * 100)`.
  5. **Regression-Trigger:** ErrorRate_diff > 0.05 ODER Latency_diff > 20% → Trend "worsening". ErrorRate_diff < -0.05 ODER Latency_diff < -20% → Trend "improving".
  6. **Recommendation Engine:** Deterministische Regeln: ErrorRate > 0.3 + worsening → MODEL_SWITCH (HIGH). Latency > 3000ms + worsening → TIMEOUT_ADJUST (MEDIUM). Calls > 100 + ErrorRate == 0 → COST_OPTIMIZE (LOW).
  7. **Persistence:** `persist_report()` speichert Reports in logs_learning Tabelle. System behält Historie seiner eigenen Evolution.
  8. **Lifecycle:** `weekly_learning_scheduler` als asyncio Background-Task im FastAPI lifespan. 7-Tage Sleep-Loop. Non-blocking, crash-geschützt.
  9. **Manual Trigger:** POST `/api/system/learning-trigger` für sofortige Ausführung (Tests und Audits).
  10. **Markdown Formatter:** `format_report_to_markdown()` für AI Studio Integration (Summary, Trends, Recommendations).
- **Guardrails:** (a) Missing Baseline → stable statt crash. (b) < 2 Datenpunkte pro Gruppe → skip. (c) Division-by-zero Guard auf baseline_latency. (d) Top-level try-except im Scheduler-Loop. (e) Keine probabilistischen Modelle.
- **Tripwire:** Wenn Trends immer "stable" zeigen obwohl Fehlerraten steigen → delta threshold (0.05) prüfen. Wenn Scheduler nicht feuert → asyncio.create_task in lifespan prüfen. Wenn Persistence fehlschlägt → logs_learning Tabelle in Supabase prüfen.
- **Location:** `backend/services/logging/learning_engine.py`, `backend/api/routers/system.py` (GET + POST Endpoints), `backend/data/schemas_logging.py` (Schema), `backend/main.py` (Lifecycle), implementiert 2026-04-26.
- **Epic:** D14 — Weekly Learning Engine (System Evolution Layer)
- **Confidence:** High (38/38 Audit-Checks bestanden, deterministische Logik verifiziert, Lifecycle-Integration crash-geschützt, Persistence operational).
- **Tags:** SystemEvolutionLayer, WeeklyLearning, TrendAnalysis, DeltaComparison, DeterministicRules, RecommendationEngine, Lifecycle, D14

---

## [PATTERN] #DomainSeparation #DecisionGate "D12 (deskriptiv) → D13 (rule-basiert) → D14 (trend-analytisch) mit Decision-Gate [PROVISIONAL] als AI Studio Validierungs-Layer"
- **Kontext:** Diamond-Stack Harmonisierung (D10-D14) erfordert klare Trennung der Verantwortlichkeiten: D12 liefert deskriptive Metriken, D13 generiert rule-basierte Aktionen aus D12-Aggregaten, D14 analysiert Trends über Zeitfenster. Alle D13/D14 Outputs müssen als "Provisional" markiert werden, da AI Studio der einzige Validierungs-Gatekeeper ist.
- **Problem:** Inkonsistente Feldnamen (`skill` vs `skill_id`) über die Layer. Keine KPI-Registry in D14 (regression_score). Delta-Formel inkonsistent (absolute vs relative). Kein Decision-Gate Marker für AI Studio Validierung. D12 enthielt implizit Empfehlungs-Logik (detect_patterns) obwohl D13 dafür zuständig ist.
- **Lösung:** **Diamond-Stack Harmonisierung mit skill_id Contract und Decision-Gate:**
  1. **skill_id Contract:** `skill_id` (namespace.action format) als kanonisches Feld in D12-D14 Schemas mit `alias="skill"` für DB-Kompatibilität (Supabase Spalte bleibt `skill`). `ConfigDict(populate_by_name=True)` für bidirektionale Kompatibilität.
  2. **D12 Insight Engine (deskriptiv):** `InsightResult.skill_id` statt `skill`. `detect_patterns()` liefert nur deskriptive Labels (`high_error_rate`, `latency_spike`, `stable`) — keine Empfehlungs-Logik.
  3. **D13 Optimization Engine (rule-basiert):** `SystemAction.skill_id` mit alias. `evaluate_insight()` liest strikt aus `logs_insights` (D12-Aggregates). Alle Empfehlungs-Strings mit `[PROVISIONAL]` Decision-Gate Marker. `store_action()` nutzt `by_alias=True` für DB-Serialisierung.
  4. **D14 KPI Registry:** `regression_score = error_rate_delta * 0.6 + latency_delta * 0.4` (gewichtete Summe Woche-zu-Woche Deltas). Deterministische Delta-Formel: `delta = (current - baseline) / baseline` (konsistent für error_rate und latency). Markdown-Formatter zeigt `regression_score` in allen Trend-Sections.
  5. **D14 Decision-Gate:** Alle Empfehlungs-Strings in `generate_improvements()` mit `[PROVISIONAL]` Marker.
  6. **Endpoints:** D12 Endpoint nutzt `skill_id` und `by_alias=True`. D13 Endpoint Parameter `skill_id` (mapped to DB column `skill`).
- **Härtung:** D12 bleibt rein deskriptiv (keine Empfehlungs-Logik). D13 arbeitet strikt auf D12-Aggregaten. D14 verwendet deterministische Delta-Formel. AI Studio ist der einzige Validierungs-Gatekeeper (alle Outputs sind `[PROVISIONAL]`).
- **Tripwire:** Wenn D12 Empfehlungen generiert → Domain-Separation verletzt. Erkennbar: `detect_patterns()` gibt action_type statt pattern zurück. Wenn skill_id in DB nicht alias-kompatibel → Schema-Migration fehlt. Erkennbar: `sqlalchemy.exc.ProgrammingError: column "skill_id" does not exist`. Wenn D13/D14 Outputs ohne `[PROVISIONAL]` → Decision-Gate fehlt. Erkennbar: Empfehlungs-Strings ohne Marker.
- **Location:** `backend/data/schemas_logging.py` (skill_id + alias), `backend/services/logging/insight_engine.py` (skill_id), `backend/services/logging/optimization_engine.py` (skill_id + PROVISIONAL), `backend/services/logging/learning_engine.py` (regression_score + delta + PROVISIONAL), `backend/api/routers/system.py` (endpoints), implementiert 2026-04-26.
- **Epic:** D10-D14 STACK HARMONIZATION
- **Confidence:** High (skill_id contract mit DB-Rückwärtskompatibilität via alias. KPI Registry mit deterministischer Delta-Formel. Decision-Gate aktiv auf allen D13/D14 Outputs. 11/11 Tests passed).
- **Tags:** DomainSeparation, DecisionGate, skill_id, KPIRegistry, regression_score, delta, deterministic, harmonization, D12, D13, D14

---

## [PATTERN] #ContractRegistry #IntegrityEngine "Diamond Contract Registry — Pydantic-basierte Blueprints pro Layer mit Fail-Fast Schema Drift Prevention und IntegrityReport Scoring"
- **Kontext:** D15 Integrity Engine als finale Kontrollinstanz über D10-D14. Der Diamond-Stack wächst über mehrere Sessions und Layer hinweg. Ohne automatisierte Schema-Validierung kann Schema-Drift unbemerkt eintreten: D12 könnte ungewollt Recommendations emittieren, D13 könnte ungültige action_types generieren, D14 könnte KPI-Felder verlieren.
- **Problem:** Kein automatisierter Mechanismus zur Erkennung von Schema-Drift. Keine Validierung der Layer-Verantwortlichkeiten (D12=deskriptiv, D13=rule-basiert, D14=trend-analytisch). Kein Gate für [PROVISIONAL] Decision-Marker-Konsistenz. Keine Scoring-Metrik für Stack-Integrität.
- **Lösung:** **Diamond Contract Registry mit Fail-Fast Validation:**
  1. **CONTRACT_SPECS:** `Dict[str, LayerContract]` mit Pydantic-basierten Blueprints pro Layer. Jeder LayerContract definiert: `required_fields`, `forbidden_fields`, `allowed_actions`, `requires_provisional`.
  2. **Descriptive-Only Guard (D12):** `validate_d12_descriptive_only()` blockiert D12 Outputs mit forbidden fields (`recommendation`, `action_type`, `priority`). Severity: CRITICAL.
  3. **Allowed-Actions Guard (D13):** `validate_d13_allowed_actions()` prüft `action_type` gegen erlaubte Liste (MODEL_SWITCH, SCALE_UP, SCALE_DOWN, TIMEOUT_ADJUST, CACHE_ENABLE, LOAD_BALANCE, RETRY_CONFIG, MONITOR). Severity: CRITICAL.
  4. **KPI-Drift Guard (D14):** `validate_d14_kpi_drift()` prüft required KPI fields und allowed action_types. Severity: HIGH.
  5. **Decision-Gate Guard:** `validate_decision_gate()` prüft `[PROVISIONAL]` Marker auf D13/D14 Empfehlungen. Severity: CRITICAL.
  6. **IntegrityReport:** `integrity_score` (0.0-1.0) mit Scoring: CRITICAL=-0.3, HIGH=-0.15, MEDIUM=-0.05. Status: FAIL wenn CRITICAL>0 oder score<0.7.
  7. **Live Check:** `run_live_check()` fetcht D12/D13/D14 Daten aus Supabase und validiert gegen CONTRACT_SPECS.
- **Härtung:** Keine KI-Interpretation — nur strikte Code-Validierung. Fail-Fast bei CRITICAL Violations. schema_fix Feld benennt exakten Fix. Violations enthalten layer, rule, severity, message, schema_fix, field.
- **Tripwire:** Wenn IntegrityReport.status == "FAIL" → Schema-Drift detektiert. Erkennbar: violations[] enthält exakte Beschreibung und Fix. Wenn D12 plötzlich recommendations emittiert → DESCRIPTIVE_ONLY_GUARD feuert. Wenn D13 neue action_types einführt → INVALID_ACTION_TYPE feuert (Contract erweitern oder Action korrigieren).
- **Location:** `backend/services/logging/integrity_engine.py` (IntegrityEngine + CONTRACT_SPECS), `backend/api/routers/system.py` (GET /integrity-check), `backend/tests/test_integrity_engine.py` (8 Test-Cases), implementiert 2026-04-26.
- **Epic:** D15 — Integrity Engine (Diamond Contract Registry)
- **Confidence:** High (8/8 Tests passed, 19/19 Gesamttests green. CONTRACT_SPECS deckt alle 5 Layer ab. Fail-Fast Scoring verifiziert).
- **Tags:** ContractRegistry, IntegrityEngine, SchemaDrift, FailFast, Validation, Pydantic, D15, D12Guard, D13Guard, D14Guard, DecisionGate

---
- **Kontext:** D11 Debug Compression Engine wurde entwickelt, um Logs für AI Studio Debugging zu komprimieren. Die Engine soll deterministische Heuristiken nutzen (Hard Errors, Model Drift, Latency Spikes) und LLM-gestützte Zusammenfassung als Fallback. Wichtig: Provider-agnostisch (nutzt User's Speed-Tier Modell) und mit Timeout-Schutz gegen Blockaden.
- **Problem:** RAM-Buffer war leer (nicht mit realer Logging-System verbunden). Supabase hatte keine Logs aus den letzten 10 Minuten. Endpoint gab immer "Keine relevanten Logs" zurück, obwohl Janus aktiv war und Logs in janus_backend.log geschrieben wurden.
- **Lösung:** **Drei-Stufen-Fallback-Kaskade in LogFetcher.fetch_logs():**
  1. RAM-Buffer (Priorität, wenn gefüllt)
  2. Supabase (letzte 10 Minuten aus logs_raw Tabelle)
  3. Log-File (direkt aus janus_backend.log lesen, letzte 100 Zeilen)
  4. Empty-State (informative Message wenn alle Fallbacks leer)
- **Heuristik-Erkennung:** Deterministische Regex-basierte Pattern-Matching für:
  - Hard Errors (status='error')
  - Model Drift (provider/model Wechsel innerhalb eines Traces)
  - Latency Spikes (latency_ms > 5000)
- **Provider-Agnostic:** Nutzt `get_speed_tier_model()` für dynamische Modell-Auswahl (OpenAI, Gemini, Anthropic, etc.). Kein hartcodiertes Modell.
- **Timeout-Schutz:** 5 Sekunden Timeout pro Operation (Fetch + Heuristik). Non-blocking via `run_in_executor` für CPU-intensive Heuristik. Graceful Degradation bei Timeouts.
- **Endpoint:** GET /api/system/debug-summary in main.py (Workaround für Router-Loading-Problem). Windsurf Skill: /debug-log via curl.exe.
- **Tripwire:** Wenn Debug-Endpoint immer "Keine relevanten Logs" zurückgibt obwohl Logs existieren → Fallback-Kaskade unvollständig. Erkennbar: Log-File Fallback fehlt oder RAM-Buffer Check blockiert Supabase Fallback.
- **Location:** `backend/services/logging/debug_engine.py` (LogFetcher Fallback, LogAnalyzer Heuristik), `backend/main.py` (Endpoint), `.windsurf/workflows/debug_log.md` (Skill), implementiert 2026-04-25.
- **Epic:** D11 — Debug Compression Engine
- **Confidence:** High (Log-File Fallback verifiziert: 100 Logs aus janus_backend.log analysiert, keine kritischen Issues gefunden).
- **Tags:** DebugCompression, Logging, Heuristik, Fallback, RAM, Supabase, LogFile, ProviderAgnostic, Timeout, NonBlocking

---

## [PATTERN] #Skill #AutoEscalation "Mehrstufige Skill-Eskalation (cheap→expensive) ohne LLM-Intervention"
- **Kontext:** `filesystem.find_files` soll bei "wo finde ich xy?" schnell in Workspaces suchen (Default ~200ms) UND bei Nichtfund automatisch global auf allen Laufwerken nachschauen (~5s warm, ~20s cold). Wenn man dem LLM beide Parameter (`search_all_drives=true/false`) überlässt, trifft es oft die falsche Entscheidung (entweder zu langsam als Default oder übersieht Duplikate).
- **Pattern:** **Zwei-Phasen-Sweep mit fester Heuristik im Skill selbst** — Phase 1 läuft immer billig; wenn Phase-1-Ergebnis unter einer klaren Schwelle (hier: ≤1 Treffer) bleibt UND der User keinen expliziten Scope (`root`) gesetzt hat, eskaliert Phase 2 automatisch auf den teureren globalen Sweep. Ergebnisse werden via `existing`-Set dedupliziert. Response enthält `auto_escalated: bool` als Transparenz-Flag.
  ```python
  # Phase 1: billig
  truncated = _sweep(workspaces, apply_exclude=False, current_matches=matches)
  # Phase 2: bei Bedarf teuer
  if not truncated and len(matches) <= 1 and not explicit_root:
      auto_escalated = True
      _sweep(_enumerate_local_drives(), apply_exclude=True, current_matches=matches)
  ```
- **Warum im Skill, nicht im LLM:** (a) Das LLM muss keine Latenz-Tradeoff-Entscheidung treffen. (b) Keine Token-Verschwendung durch zweiten Tool-Call. (c) Die Heuristik ist deterministisch testbar. (d) Der User kriegt das beste UX: Frage einmal, richtige Antwort — egal ob Datei im Workspace oder außerhalb.
- **Trigger-Kriterien für Auto-Escalation allgemein:**
  1. Phase-1-Ergebnis ist **informationsarm** (leer, 1 Treffer, generische Fehlermeldung).
  2. Kein expliziter User-Scope gesetzt, der das verbieten würde.
  3. Phase-2-Kosten sind **akzeptabel** (hier: +5s, nicht +5min).
- **Counter-Pattern (NICHT):** Auto-Escalation in Phase 2 darf NIEMALS mutierend sein (z.B. auto-upgrade von `find` auf `delete`). Nur read-only/discovery-Skills qualifizieren.
- **Location:** `backend/services/filesystem_manager.py::find_files` (Auto-Escalation-Block ~Z. 404-413)
- **Confidence:** High (Live-Test mit beiden Providern OpenAI + Gemini: simple User-Frage findet beide Duplikate automatisch)
- **Tags:** Skill, AutoEscalation, Pattern, LatencyTradeoff, Filesystem, Discovery, UX

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

---

## [LESSON] #ThreadSafety #Python #Pathlib "Thread-Scope NameError — Importiere pathlib explizit in daemon-threads, um NameError zu vermeiden"
- **Kontext:** In `backend/services/tool_executor.py` wurde `from pathlib import Path` importiert, aber später im Code wurde auch `import pathlib` verwendet. In daemon-threads führte dies zu `NameError: name 'pathlib' is not defined`, da der Import-Scope nicht korrekt übernommen wurde. Der Fehler trat nur in daemon-threads auf, nicht im Haupt-Thread.
- **Problem:** Python-Imports in daemon-threads haben einen anderen Scope als im Haupt-Thread. Wenn ein Modul sowohl mit `from pathlib import Path` als auch mit `import pathlib` importiert wird, kann der Name `pathlib` in daemon-threads nicht aufgelöst werden, selbst wenn `Path` verfügbar ist. Dies führt zu `NameError` zur Laufzeit.
- **Lösung:** Verwende konsistent nur eine Import-Form. Wenn `from pathlib import Path` verwendet wird, importiere auch explizit `import pathlib` wenn der Modul-Name benötigt wird, oder nutze ausschließlich `import pathlib` und referenziere dann `pathlib.Path`.
  ```python
  # Korrekt: Beide Importe, wenn beide Formen benötigt werden
  from pathlib import Path
  import pathlib
  ```
- **Härtung:** Vermeide gemischte Import-Formen für dasselbe Modul. Wähle eine Form und bleibe dabei konsequent. In daemon-threads ist dies besonders kritisch.
- **Tripwire:** Wenn `NameError: name 'pathlib' is not defined` in daemon-threads auftritt, obwohl `from pathlib import Path` importiert wurde → gemischte Import-Formen.
- **Location:** `backend/services/tool_executor.py` (Z. 7: import pathlib hinzugefügt), gefixt 2026-04-25.
- **Confidence:** High (NameError in daemon-threads behoben durch konsistente Import-Form).
- **Tags:** ThreadSafety, Python, Pathlib, DaemonThreads, ImportScope, NameError

---

## [PATTERN] #Harvester #PathPolicy #GlobalScan "Harvester-Pattern — Nutze globalen _global_scan_mode Flag in PathPolicy, um allowed_roots für systemweite Scans zu bypassen"
- **Kontext:** Der Global-Scan soll alle lokalen Laufwerke enumerieren und indizieren, aber die PathPolicy-Validierung (`validate()`) prüft strikt, ob Pfade innerhalb der `allowed_roots` liegen. Dies führte zu "Outside allowed roots" Fehlern beim systemweiten Scan, obwohl der Scan explizit aktiviert wurde.
- **Problem:** PathPolicy ist standardmäßig auf Workspace-Isolation ausgelegt (Sicherheits-Feature). Für einen systemweiten Harvester-Scan muss diese Isolation temporär deaktiviert werden, ohne die Sicherheits-Mechanismen für normale Workspace-Scans zu kompromittieren.
- **Pattern:** **Global-Scan-Mode Flag mit Bypass-Logik.** Ein modul-weites `_global_scan_mode: bool` Flag in `path_policy.py` steuert, ob die PathPolicy-Validierung aktiv ist. `enable_global_scan_mode()` setzt das Flag auf `True`, `validate()` und `is_allowed()` prüfen das Flag und bypassen die allowed_roots-Prüfung wenn aktiv.
  ```python
  _global_scan_mode: bool = False

  def enable_global_scan_mode() -> None:
      global _global_scan_mode
      _global_scan_mode = True

  def validate(self, file_path: Path) -> None:
      if _global_scan_mode:
          return  # Bypass validation
      # Normal validation logic...
  ```
- **Warum Global Flag:** Modul-weites Flag ist Thread-sicher (Python GIL garantiert atomare Reads/Writes für einfache Bool-Variablen) und wirkt für alle Threads, die PathPolicy verwenden. Keine Notwendigkeit für Thread-Local Storage oder komplexere Synchronisation.
- **Trigger-Kriterien für Global-Scan-Mode:** (1) Datenbank ist leer (Initial-Scan). (2) Systemweiter Scan explizit angefordert. (3) Scan läuft in daemon-thread (Hintergrund-Indizierung).
- **Location:** `backend/services/rag/path_policy.py` (_global_scan_mode, enable_global_scan_mode, validate/is_allowed Bypass), `backend/main.py` (enable_global_scan_mode() Aufruf vor Thread-Start), implementiert 2026-04-25.
- **Confidence:** High (Global-Scan-Mode ist deterministisch, Bypass-Logik ist in validate() und is_allowed() implementiert, Thread-sicherheit durch GIL garantiert).
- **Tags:** Harvester, PathPolicy, GlobalScan, Bypass, ThreadSafety, PathNormalization
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

## [PATTERN] #Architecture #RAG "The Strangler-Fig Migration — run the new system alongside the old"
- **Kontext:** RAG V2 Master-Plan v1.1 — User wollte den bestehenden Legacy-RAG (PDF-Drops, Memory-Vektoren, Projekt-Collections, Skill-Routing-Index) nicht kaputt machen, obwohl V2 eine völlig andere Architektur (Hybrid Retrieval, dual Embeddings, Code-aware Chunking) bekommen soll.
- **Problem:** Big-Bang-Rewrites brechen bestehende Produktionspipelines mit 100%iger Wahrscheinlichkeit. Selbst "additive" Änderungen können scheitern, wenn sie dieselben Collections/Files/Funktionen modifizieren. Das Legacy-RAG-Surface von Janus ist komplex (6 verschiedene Collection-Nutzungsmuster, geteilte `janus_global_documents` zwischen PDFs und Memory).
- **Lösung:** Strangler-Fig-Pattern: V2 läuft physisch und logisch parallel. Kein Modifikation am Legacy-Code. V2 bekommt eigenen Chroma-Pfad (`rag_chroma_db_v2/`), eigene SQLite-DBs (`knowledge_fts_v2.db`, `knowledge_index_v2.db`), eigenen Feature-Flag-Layer (11 Flags, alle default `false`). Die Legacy-Pipeline läuft unverändert weiter. V2 ist nur via explizitem Opt-in (neuer Skill `knowledge.code_search` oder `retrieval_mode="v2"`) erreichbar. Optionaler Cutover (P9) ist eine separate Entscheidung, erst nach Full-Regression mit 500+ Queries.
- **Ergebnis:** Zero-Regression-Contract: Legacy-E2E-Tests laufen 100% grün, auch wenn V2 vollständig installiert ist. Feature-Flags ermöglichen Phase-by-Phase-Integration ohne Big-Bang. Physische Isolation verhindert, dass ein V2-Crash den Legacy-Index korrumpiert.
- **Tripwire:** Wenn ein neues Feature in denselben Collections/Files/Pfade wie bestehende Logik schreibt → Strangler-Fig verletzt. Sofort: physischer Subpfad + eigene Collections + Freeze-Contract.
- **Location:** `documentation/RAG_V2_MASTER_PLAN.md` § 1.5, § 11, 2026-04-21.
- **Confidence:** High (Pattern bewährt in Martin Fowler's Strangler Fig Application; physische Isolation ist unumkehrbarer Schutz).
- **Tags:** Architecture, RAG, StranglerFig, Migration, ZeroRegression, ParallelRun, Coexistence

## [PATTERN] #Architecture #HybridSearch "Reciprocal Rank Fusion (RRF) — the canonical baseline for combining dense + sparse"
- **Kontext:** RAG V2 braucht sowohl semantische Suche (ChromaDB Dense Embeddings, "Was meint er?") als auch lexikalische Suche (SQLite FTS5, "Wo steht exakt das Wort?"). Für Code-Snippets und Dateinamen ist FTS5 überlegen; für konzeptuelle Prosa-Queries sind Embeddings überlegen.
- **Problem:** Score-Kalibrierung zwischen Dense (0–1 Cosine) und Sparse (arbitrary BM25-style scores) ist unmöglich. Gewichtete Addition `0.7*vec + 0.3*fts` ist brüchig, weil die Score-Ranges nicht vergleichbar sind und sich mit Corpus-Größe verschieben.
- **Lösung:** Reciprocal Rank Fusion (Cormack et al. 2009) mit `score(d) = Σ_r 1/(k + rank_r(d))` und `k=60`. Benutzt nur die **Rangposition** jedes Dokuments in jedem Ranking, nicht die absoluten Scores. Damit ist die Fusion robust gegen Score-Drift und Corpus-Größen-Änderungen. Query-Router entscheidet später, welche Rankings einbezogen werden (vec-heavy, fts-heavy, balanced), aber die Fusion-Methode bleibt unverändert.
- **Ergebnis:** Deterministische, rechenbare, parameter-robuste Kombination von semantischer und lexikalischer Suche. Keine Notwendigkeit für Score-Normalisierung oder Trainingsdaten.
- **Tripwire:** Wenn eine Hybrid-Search gewichtete Score-Addition nutzt → RRF ist der saubere Ersatz. Zusätzlich: k=60 ist der canonical Wert aus der Literatur; Änderungen nur mit evaluierter Regression.
- **Location:** `documentation/RAG_V2_MASTER_PLAN.md` § 1.1, § 2, 2026-04-21.
- **Confidence:** High (SIGIR-Paper, in Produktion bei mehreren Enterprise-RAG-Systemen validiert).
- **Tags:** Architecture, HybridSearch, RRF, DenseSparse, RankingFusion, Retrieval, Baseline

## [PATTERN] #Security #Isolation "Physical Vector-Store Separation — the last line of defense against regression"
- **Kontext:** Janus' Legacy-RAG nutzt `rag_chroma_db/janus_global_documents` sowohl für PDF-Drops als auch für Memory-Vektoren (geteilt!). V2 soll denselben Chroma-Client nutzen, aber mit neuen Collections. Risiko: V2-Code könnte aus Versehen die Legacy-Collection ansprechen (z.B. falscher Collection-Name, Copy-Paste-Fehler, Bug im Ingestion-Adapter).
- **Problem:** Logische Trennung (verschiedene Collection-Namen) ist notwendig aber nicht hinreichend. Ein Bug in `client.get_or_create_collection()` mit dynamischem Namen oder ein String-Concat-Fehler könnte die Legacy-Collection treffen. Ohne physische Isolation ist der Schaden irreversibel (Embeddings gelöscht = PDFs/Memory unwiederbringlich verloren).
- **Lösung:** V2 bekommt **eigenen PersistentClient-Pfad**: `{app_data_dir}/rag_chroma_db_v2/`. Legacy bleibt in `{app_data_dir}/rag_chroma_db/`. Zusätzlich: Freeze-Contract (§ 1.5.2) verbietet V2-Code explizit, jemals `rag_chroma_db/` anzutasten. SHA-Baum-Assertion im CI verifiziert, dass `rag_chroma_db/` vor und nach V2-Runs byte-identisch bleibt.
- **Ergebnis:** Selbst ein totaler V2-Crash (infinite loop, DB corruption, accidental `collection.delete()`) kann den Legacy-Index nicht berühren. Rollback = `Remove-Item -Recurse rag_chroma_db_v2/` — keine Migration, kein Restore nötig.
- **Tripwire:** Wenn ein neues Feature denselben Datenpfad wie ein bestehendes Feature nutzt → sofort physische Separation. Ausnahme nur, wenn beide Features identische Recovery-Strategien und getestete Rollbacks haben.
- **Location:** `documentation/RAG_V2_MASTER_PLAN.md` § 1.3, § 1.5.2, § 10.1, 2026-04-21.
- **Confidence:** High (Unumkehrbarer Schutz; SHA-Assertion macht Regression sichtbar).
- **Tags:** Security, Isolation, VectorStore, ChromaDB, Regression, PhysicalSeparation, FreezeContract

## [LESSON] #AgenticAI #ToolDesign "Path-Pinning for Disambiguation — Kritische Tools müssen absolute Adressierung für autonome Mehrdeutigkeitsauflösung unterstützen"
- **Kontext:** Auto-Read-Trigger für Dubletten: Wenn `knowledge.query` mehrere Dateien mit gleichem Namen findet, soll die KI autonom `knowledge.read_full_text` für nicht-indizierte Dubletten aufrufen. Das Tool-Schema akzeptierte aber nur `filename` als Parameter, wodurch GPT den Aufruf verweigerte (kann Dublette nicht spezifisch adressieren).
- **Problem:** Eine KI kann Anweisungen ("lies diese Datei") nicht befolgen, wenn das Tool-Schema nur relative Namen (`filename`) und keine absoluten Adressen (`absolute_path`) akzeptiert. Bei Dubletten ist `filename` mehrdeutig — die KI weiß nicht, welche der 2+ Dateien gemeint ist. Ergebnis: Halluzination oder "ich kann das nicht" statt autonomer Auflösung.
- **Lösung:** **Path-Pinning-Parameter** zu `knowledge.read_full_text` hinzugefügt:
  ```python
  class GetFullDocumentTextArgs(BaseModel):
      filename: str = Field(...)
      absolute_path: Optional[str] = Field(
          None,
          description="Path-Pinning for Disambiguation: Nutze dieses Feld, um eine spezifische Dublette via absolutem Pfad zu lesen..."
      )
  ```
  Tool-Logik priorisiert `absolute_path` absolut: Wenn gesetzt, wird `filename` ignoriert, keine Dubletten-Prüfung, direktes Lesen vom angegebenen Pfad. P0.75-Direktive in Skill-JSONs instruiert GPT: "Nutze 'knowledge.read_full_text' mit dem Parameter 'absolute_path' für diesen Pfad".
- **Härtung:** Parameter-Priorität ist unidirektional: `absolute_path` > `filename`. Kein Fallback von absolute_path auf filename-Suche (wenn absolute_path gesetzt aber ungültig → Fehler, nicht silent filename-Resolution).
- **Tripwire:** Wenn ein Tool Dubletten meldet, aber die KI kann die spezifische Datei nicht autonom lesen → fehlender Pinning-Parameter im Schema. GPT-Refusal bei "[NICHT INDIZIERT...]" Hinweis ist ein klarer Indikator.
- **Location:** `backend/data/schemas.py` (GetFullDocumentTextArgs.absolute_path), `backend/services/tool_executor.py` (get_full_document_text), `backend/skills/knowledge/read_full_text.json` (P0.75 AUTO-READ TRIGGER), gefixt 2026-04-23.
- **Confidence:** High (Pattern: Kritische Tools zur Ressourcen-Interaktion brauchen immer Pinning-Parameter für Agentic Loops).
- **Tags:** AgenticAI, ToolDesign, PathPinning, Disambiguation, DuplicateResolution, AutoRead, absolute_path, knowledge.read_full_text

## [LESSON] #Python #ResourceManagement "The Shared Resource Lifecycle — Resource-Closing must happen AFTER the last possible usage point"
- **Problem:** In komplexen Funktionen mit mehreren logischen Zweigen wird eine Ressource (z.B. `DB-Connection`, `IndexStore`) oft im "Erfolgszweig" der ersten Phase geschlossen. Wenn spätere Phasen (z.B. Fallbacks oder Vorschau-Generierung) dieselbe Ressource benötigen, kommt es zu Abstürzen oder Datenverlust.
- **Lösung:** Nutze das **"Init-to-None"** Pattern kombiniert mit einem **`finally`-Block** am Ende der Hauptfunktion. Schließe die Ressource niemals "mittendrin", sondern markiere sie nur zur Schließung.
- **Beispiel:** `store = None; try: store = open(); ... finally: if store: store.close()`.
- **Location:** `backend/services/tool_executor.py` (BUG-RAG-003).

## [PATTERN] #Orchestration #Lockdown "Dispatcher-First Parameter Enforcement — Command-Chain Integrity"
- **Problem:** LLMs ignorieren bei komplexen Aufgaben oft "optionale" Parameter (wie Filenames), was zu unscharfen Tool-Calls und weitreichenden Fehlern (globale Suche statt spezifischer Datei) führt.
- **Lösung:** Wenn eine Ressource (z.B. eine Datei) im User-Text klar identifizierbar ist, darf der Orchestrator (Dispatcher) nicht darauf hoffen, dass das LLM dies korrekt mappt. Er muss die Information selbst extrahieren (Regex) und den Tool-Call mit diesen Argumenten hart erzwingen.
- **Vorteil:** Erhöht die System-Stabilität von "probabilistisch" (LLM-Laune) auf "deterministisch" (Code-Integrität).
- **Location:** `backend/services/orchestrator/execution_dispatcher.py` (F16 FINAL LOCKDOWN).

---

## [PATTERN] #DiamondSkillContract "Diamond Skill Contract — Zwang zum dreiteiligen JSON-Output {status, data, error} für autonomes Immunsystem-Routing"
- **Kontext:** D27 Diamond Skill Engineering etabliert einen unverletzlichen Kontrakt für alle Skill-Outputs. Das autonome Immunsystem (D20-D26) benötigt ein standardisiertes Format, um Skill-Ergebnisse zu validieren, zu loggen und Routing-Entscheidungen zu treffen. Ohne diesen Kontrakt kann das System nicht deterministisch unterscheiden zwischen Erfolg und Fehler.
- **Problem:** Unterschiedliche Output-Formate erschweren die automatische Validierung und erschweren die Root-Cause-Analyse. Einige Skills returnieren Rohdaten, andere Error-Strings, andere wiederum komplexe Objekte ohne klaren Status. Dies führt zu: (1) Fehlende Einheitlichkeit in D10 Telemetrie, (2) Unklare Pass/Fail Entscheidung in der ValidationEngine, (3) Unzuverlässige Routing-Entscheidungen im Self-Heal Cycle.
- **Lösung (Dreiteiliger Kontrakt):**
  1. **`status` (obligatorisch):** Entweder `"success"` oder `"error"`. Keine gemischten States wie "partial_success".
  2. **`data` (bei success):** Enthält die eigentlichen Ergebnis-Daten. MUSS bei `status: "success"` vorhanden sein.
  3. **`error` (bei error):** Enthält Fehler-Details (message, code, details). MUSS bei `status: "error"` vorhanden sein.
- **Regeln:**
  - `status` ist immer String und immer "success" oder "error"
  - Bei `status: "success"`: `data` MUSS enthalten sein, `error` MUSS fehlen oder null sein
  - Bei `status: "error"`: `error` MUSS enthalten sein, `data` KANN fehlen oder null sein
  - Keine alternativen Status-Werte (keine "pending", "partial", "warning")
- **Härtung:** Global Default Validator in `validation.py` prüft Kontrakt-Einhaltung. ValidationEngine mit `ValidationResult` (passed, validator_type, message, severity, details). Multi-Rule-Validierung: Alle Regeln müssen bestehen.
- **Tripwire:** Wenn Skill gibt Rohdaten zurück statt `{status, data}` → Kontrakt verletzt. Wenn `status` fehlt oder nicht "success"/"error" → Validation schlägt fehl. Wenn `data` und `error` beide vorhanden → Ambiguität, Validation schlägt fehl.
- **Location:** `backend/services/testing/validation.py` (ValidationEngine, ValidationResult), `documentation/02_SKILL_DEVELOPMENT.md` (V3.0), implementiert 2026-04-28 (D27).
- **Epic:** D27 — Diamond Skill Engineering & Diagnosis
- **Confidence:** High (Unverletzlicher Kontrakt, Global Default Validator, strikte Regeln).
- **Tags:** DiamondSkillContract, SkillOutput, Validation, Contract, D27, Immunsystem

---

## [PATTERN] #ModellVsSkillDiagnose "Modell vs. Skill Diagnose — 'Stärkeres Modell fixiert es -> Routing-Problem | Nichts fixiert es -> Skill-Problem'"
- **Kontext:** D27 Diagnose-Engine etabliert eine klare Unterscheidung zwischen zwei Fehler-Quellen im System: Modell-Fehler (Routing-Problem) und Skill-Fehler (Code-Problem). Diese Unterscheidung ist kritisch für das autonome Immunsystem, um die richtige Maßnahme zu ergreifen: automatischer Modell-Wechsel vs. manuelles Code-Refactoring.
- **Problem:** Wenn ein Skill degradiert ist (pass_rate < 0.5), ist unklar ob das Problem beim Modell (z.B. Overload, Rate Limit, Latenz) oder beim Skill-Code (z.B. Halluzination, Logik-Fehler, Format-Breach) liegt. Ohne diese Unterscheidung greift das Immunsystem möglicherweise falsch: Es versucht ein Routing-Update für einen defekten Skill, oder es fordert manuelle Eingriffe bei einem transienten Modell-Problem.
- **Lösung (Diagnose-Regeln):**
  1. **Pass-Rate < 0.5 + Latenz OK (nicht-timeout):** Skill-Problem (Code-Fix nötig)
     - Logik: Der Skill scheitert trotz funktionierendem Modell → Handler-Code oder Validation-Logic defekt
     - Maßnahme: Manuelles Skill-Refactoring (Entwickler-Arbeit)
  2. **Pass-Rate < 0.5 + Latenz hoch (timeout/429/500):** Modell-Problem (Routing-Wechsel)
     - Logik: Das Modell ist überlastet oder nicht verfügbar → Skill-Code ist korrekt, Infrastruktur defekt
     - Maßnahme: Diamond Routing → Automatischer Modell-Wechsel (D21-D22)
  3. **Pass-Rate ≥ 0.5:** System stabil (kein Eingriff nötig)
     - Logik: Skill funktioniert mit aktuellem Modell
     - Maßnahme: Monitoring fortsetzen, keine Änderungen
- **Erweiterte Diagnose (mit Escalation Data):**
  - `final_tier` = "escalation" → Alle Tiers ausprobiert, nichts funktioniert → Skill-Problem
  - `final_tier` = "primary" aber `pass_rate` niedrig → Validation-Fail (Format-Breach)
  - `attempts_count` ≥ 2 aber `status` = "failed" → Skill scheitert über alle Tiers → Skill-Problem
  - `latency_ms` > 3000ms aber `status` = "passed" → Timeout-Problem → Schnelleres Modell oder Caching
- **Härtung:** Monitoring Aggregator (D25) zeigt Health Snapshot mit pass_rate und Latenz. Self-Heal Cycle (D22) triggert nur bei Modell-Problemen. Skill-Entwickler-Doku (V3.0) definiert klare Diagnose-Workflow.
- **Tripwire:** Wenn Pass-Rate < 0.5 aber Routing-Wechsel wird versucht → Skill-Problem als Modell-Problem fehlklassifiziert. Wenn Pass-Rate < 0.5 aber kein Alert → Monitoring defekt. Wenn Latenz immer 0.0 → Async-Await fehlt (D18 Pattern).
- **Location:** `documentation/02_SKILL_DEVELOPMENT.md` (V3.0, TEIL 1.3), `documentation/architecture/JANUS_IMMUNE_SYSTEM.md` (Diagnose-Workflow), implementiert 2026-04-28 (D27).
- **Epic:** D27 — Diamond Skill Engineering & Diagnosis
- **Confidence:** High (Klare Unterscheidung, deterministische Regeln, integriert in Immunsystem).
- **Tags:** ModellVsSkillDiagnose, DiagnoseEngine, RootCauseAnalysis, RoutingProblem, SkillProblem, D27

 
 # #   [ L E S S O N ]   # P r o j e c t S t r u c t u r e   # S e c u r i t y   # T e s t C l e a n u p   T e s t - D a t e i e n   i n   R o o t   v e r m e i d e n ,   H a r d c o d e d   A P I   K e y s   a u s   T e s t s   e n t f e r n e n 
 
 
 
 -   * * K o n t e x t : * *   B A C K L O G - 0 0 1      T e s t - D a t e i e n   a u s   P r o j e k t - R o o t   n a c h   t e s t s /   v e r s c h i e b e n .   S y s t e m   H e a l t h   h a t t e   m e h r e r e   T e s t - D a t e i e n   ( t e s t _ c l u s t e r _ 4 . p y ,   t e s t _ g e o m e t r i e _ c h e c k . p y ,   t e s t _ l o g g i n g _ f i x . p y ,   t e s t _ o p e n a i _ t o o l s . p y ,   t e s t _ f a c e . j p g ,   t e s t _ p e r s o n a l i t i e s . j s o n )   i m   P r o j e k t - R o o t   s t a t t   i n   t e s t s /   o d e r   t e s t /   g e f u n d e n .   Z u s  t z l i c h   e n t h i e l t   t e s t _ o p e n a i _ t o o l s . p y   e i n e n   h a r d c o d e d   O p e n A I   A P I - K e y   i m   Q u e l l c o d e . 
 
 -   * * T a g s : * *   P r o j e c t S t r u c t u r e ,   S e c u r i t y ,   T e s t C l e a n u p ,   H a r d c o d e d K e y s 
 
 
 
 
 
 
 
 # #   [ P A T T E R N ]   # L a z y H e a v y R e s o u r c e S t a r t u p   " L a z y   L o a d i n g   f  r   H e a v y   R e s o u r c e s   a m   A p p - S t a r t      D a e m o n - T h r e a d   i m   F a s t A P I - L i f e s p a n   m i t   S t a t u s - T r a c k i n g " 
 -   * * K o n t e x t : * *   B A C K L O G - 0 1 8   C L I P   L a z y   L o a d i n g .   C L I P - M o d e l   ( 3 3 8 M B ,   V i T - B - 3 2 . p t )   w u r d e   s y n c h r o n   i m   V i s i o n - S e r v i c e - C o n s t r u c t o r   g e l a d e n ,   w a s   b e i   l a n g s a m e r   I n t e r n e t v e r b i n d u n g   z u   W i n d o w s - P r o c e s s - T i m e o u t   ( 1 2 0 s )   f  h r t e . 
 -   * * P r o b l e m : * *   S y n c h r o n e r   D o w n l o a d   i n   S e r v i c e - C o n s t r u c t o r   b l o c k i e r t   A p p - S t a r t .   B e i   l a n g s a m e n   N e t z w e r k e n   o d e r   S e r v e r - T i m e o u t s   t  t e t   W i n d o w s   d e n   P r o z e s s   n a c h   1 2 0   S e k u n d e n . 
 -   * * L  s u n g : * *   * * L a z y - L o a d i n g   m i t   D a e m o n - T h r e a d   i m   F a s t A P I - L i f e s p a n : * * 
     1 .   * * M o d e l - L o a d e r   S i n g l e t o n : * *   ` C l i p M o d e l L o a d e r `   m i t   S t a t u s - T r a c k i n g   ( ` m o d e l _ l o a d i n g ` ,   ` m o d e l _ l o a d e d ` ,   ` m o d e l _ e r r o r ` ) . 
     2 .   * * B a c k g r o u n d - T h r e a d : * *   ` s t a r t _ a s y n c _ l o a d ( ) `   s t a r t e t   D a e m o n - T h r e a d   f  r   ` c l i p . l o a d ( ) ` . 
     3 .   * * L i f e s p a n - T r i g g e r : * *   ` m a i n . p y `   F a s t A P I - L i f e s p a n   r u f t   ` s t a r t _ c l i p _ m o d e l _ d o w n l o a d ( ) `   n a c h   B o o t s t r a p / T o o l - R e g i s t r a t i o n ,   n i c h t   v o r   A p p - S t a r t . 
     4 .   * * S e r v i c e - I n t e g r a t i o n : * *   V i s i o n - S e r v i c e   p r  f t   ` m o d e l _ l o a d e r . i s _ r e a d y ( ) `   v o r   C L I P - I n f e r e n c e ,    b e r s p r i n g t   b e i   ` F a l s e ` . 
     5 .   * * F e h l e r b e h a n d l u n g : * *   E x c e p t i o n - H a n d l i n g   i m   T h r e a d ,   S t a t u s   w i r d   a u f   ` m o d e l _ e r r o r `   g e s e t z t ,   A p p   s t a r t e t   t r o t z d e m . 
 -   * * H  r t u n g : * *   D a e m o n - T h r e a d   ( w i r d   b e i   S h u t d o w n   b e e n d e t ) ,   S t a t u s - T r a c k i n g ,   ` i s _ r e a d y ( ) `   G u a r d ,   E x c e p t i o n - H a n d l i n g   b r i c h t   n i c h t   A p p - S t a r t   a b . 
 -   * * T r i p w i r e : * *   W e n n   B a c k e n d - S t a r t   > 1 0 s   d a u e r t   o d e r   V i s i o n - R e q u e s t s   v o r   D o w n l o a d - E n d e   c r a s h e n   !  L a z y - L o a d i n g   n i c h t   i m p l e m e n t i e r t   o d e r   T h r e a d   n i c h t   g e s t a r t e t . 
 -   * * L o c a t i o n : * *   ` b a c k e n d / s e r v i c e s / v i s i o n / m o d e l _ l o a d e r . p y ` ,   ` b a c k e n d / s e r v i c e s / v i s i o n _ s e r v i c e . p y ` ,   ` b a c k e n d / m a i n . p y `   ( l i f e s p a n ) ,   i m p l e m e n t i e r t   2 0 2 6 - 0 5 - 0 9 . 
 -   * * E p i c : * *   B A C K L O G - 0 1 8      C L I P   L a z y   L o a d i n g 
 -   * * C o n f i d e n c e : * *   H i g h   ( L a z y - L o a d i n g   P a t t e r n   i m p l e m e n t i e r t ,   S t a t u s - T r a c k i n g   v o r h a n d e n ,   A p p   s t a r t e t   o h n e   B l o c k i e r u n g ) . 
 -   * * T a g s : * *   L a z y L o a d i n g ,   F i r s t S t a r t ,   B a c k g r o u n d T h r e a d ,   C L I P ,   V i s i o n S e r v i c e ,   B A C K L O G 0 1 8 
 
 
 
 
 
 # #   [ P A T T E R N ]   # P y I n s t a l l e r   # C h r o m a D B   \ 
 
 C h r o m a D B 
 
 c o l l e c t _ d a t a _ f i l e s 
 
 P a t t e r n 
 
  
 
 c o l l e c t _ d a t a _ f i l e s 
 
 + 
 
 i n c l u d e _ p y _ f i l e s 
 
 + 
 
 h i d d e n i m p o r t s \ 
 -   * * K o n t e x t : * *   C h r o m a D B   i s t   e i n   k o m p l e x e s   P y t h o n - P a c k a g e   m i t   R u s t - E x t e n s i o n s   u n d   d y n a m i s c h e n   S u b m o d u l e n .   P y I n s t a l l e r   e r f a s s t   d i e s e   n i c h t   a u t o m a t i s c h ,   w a s   z u   N o   m o d u l e   n a m e d   ' c h r o m a d b . * '   F e h l e r n   b e i m   S t a r t   f  h r t . 
 -   * * P r o b l e m : * *   C h r o m a D B   b e n  t i g t   s o w o h l   D a t e n - D a t e i e n   ( c o n f i g ,   e m b e d d i n g s )   a l s   a u c h   P y t h o n - S u b m o d u l e   ( c h r o m a d b . t e l e m e t r y . p r o d u c t . p o s t h o g ,   c h r o m a d b . a p i . r u s t ) .   N u r   h i d d e n i m p o r t s   r e i c h t   n i c h t ,   d a   a u c h   D a t e n - D a t e i e n   f e h l e n . 
 -   * * L  s u n g : * *   K o m b i n a t i o n   a u s   c o l l e c t _ d a t a _ f i l e s ( ' c h r o m a d b ' )   f  r   D a t e n - D a t e i e n ,   c o l l e c t _ d a t a _ f i l e s ( ' c h r o m a d b ' ,   i n c l u d e _ p y _ f i l e s = T r u e )   f  r   P y t h o n - S u b m o d u l e ,   u n d   e x p l i z i t e n   h i d d e n i m p o r t s = [ ' c h r o m a d b . t e l e m e t r y . p r o d u c t . p o s t h o g ' ,   ' c h r o m a d b . a p i . r u s t ' ] . 
 -   * * P a t t e r n : * * 
     \ \ \ p y t h o n 
     f r o m   P y I n s t a l l e r . u t i l s . h o o k s   i m p o r t   c o l l e c t _ d a t a _ f i l e s 
     c h r o m a d b _ d a t a   =   c o l l e c t _ d a t a _ f i l e s ( ' c h r o m a d b ' ) 
     c h r o m a d b _ s u b m o d u l e s   =   c o l l e c t _ d a t a _ f i l e s ( ' c h r o m a d b ' ,   i n c l u d e _ p y _ f i l e s = T r u e ) 
     a l l _ d a t a s   =   [ . . . ,   c h r o m a d b _ d a t a ,   c h r o m a d b _ s u b m o d u l e s ] 
     h i d d e n i m p o r t s = [ ' c h r o m a d b . t e l e m e t r y . p r o d u c t . p o s t h o g ' ,   ' c h r o m a d b . a p i . r u s t ' ] 
     \ \ \ 
 -   * * T r i p w i r e : * *   W e n n   P y I n s t a l l e r - B u n d l e   \ N o 
 
 m o d u l e 
 
 n a m e d 
 
 c h r o m a d b . * 
 
 \   F e h l e r   z e i g t   !  c o l l e c t _ d a t a _ f i l e s   +   i n c l u d e _ p y _ f i l e s   P a t t e r n   a n w e n d e n . 
 -   * * L o c a t i o n : * *   \ j a n u s _ b a c k e n d . s p e c \   ( B A C K L O G - 0 1 7   F i x ) ,   g e f i x t   2 0 2 6 - 0 5 - 0 9 . 
 -   * * C o n f i d e n c e : * *   H i g h   ( V a l i d i e r u n g :   P y I n s t a l l e r   B u i l d   P A S S ,   E X E   S t a r t u p   P A S S ,   T o o l M a n a g e r   P A S S ,   C L I P   M o d e l   P A S S ,   S e r v i c e s   P A S S ) . 
 -   * * T a g s : * *   P y I n s t a l l e r ,   C h r o m a D B ,   c o l l e c t _ d a t a _ f i l e s ,   h i d d e n i m p o r t s ,   P a c k a g i n g ,   R u s t E x t e n s i o n s 
 
 
## Dynamic Model Selection with Provider Consistency

- **Context:** BACKLOG-019 Fix - Hardcoded gpt-5-mini caused fallback warnings. System now selects first available text model from catalog dynamically.
- **Problem:** When selecting models dynamically from catalog, provider must be set consistently to avoid Provider/Model-Mismatch. Hardcoded provider="openai" with dynamic model selection caused mismatch when first available model was from different provider (gemini, ollama).
- **Solution:** Helper function get_first_available_text_model_with_provider() returns (provider, model_id) tuple from catalog. Both main.py and calendar_ai_engine.py use this function to set provider and model consistently. Fallback path also uses provider from catalog, not hardcoded "openai".
- **Pattern:**
  ```python
  from backend.services.llm_gateway import get_first_available_text_model_with_provider
  provider, model_id = get_first_available_text_model_with_provider()
  config["last_used_provider"] = provider if provider else "openai"
  config["last_used_model"] = model_id if model_id else ""
  ```
- **Location:** backend/services/llm_gateway.py (get_first_available_text_model_with_provider), backend/main.py (bootstrap), backend/services/calendar/calendar_ai_engine.py (_resolve_provider_model_key). Fixed 2026-05-09.
- **Confidence:** High (Validation: Syntax-Check PASS, Manual Janus Test PASS, no hardcoded model IDs remain, provider/model consistency guaranteed).
- **Tags:** dynamic_model_selection, provider_consistency, model_catalog, hardcoded_models, backlog_019
