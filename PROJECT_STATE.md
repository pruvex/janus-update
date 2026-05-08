# PROJECT_STATE.md (Diamond-OS V0.4.31-beta.82)
**Zweck:** Schlanke Triage-Uebersicht fuer den aktuellen Projektzustand.
**Aktualisiert:** 2026-05-05 (TASK-069 Capability Overview & Auto-Update Gold-Standard — Beta.10 Bridge Release)

---

## CURRENT_SESSION_DELTA (Kompakt)

| Epic / Task | Status | Kurzstand |
|---|---|---|
| **TASK-030 Video List System - Chat-Wechsel Persistenz-Fix** | 🥇 SEALED | Video-Liste Persistenz nach Chat-Wechsel behoben. Sender-Bedingung erweitert auf "bot" || "model", appendVideoReopenLink Parameter videoListMetadata hinzugefügt, wireVideoReopenLink übergibt videoListMetadata an appendVideoReopenLink, appendMessage generiert Markdown mit Header (wie SSE-Stream) beim Chat-Reload. Backend-Logging hinzugefügt zur Verfolgung von video_list_metadata. max_results=3 → max_results=payload.max_results in video_tools.py. Manueller Test bestanden. Version: 0.4.17-beta.19. |
| **TASK-069 Capability Overview & Auto-Update Gold-Standard** | 🥇 SEALED | Implemented deterministic capability response (Fast-Path) with hardened normalization. Resolved systemic auto-update failures (ReferenceError, SHA-Mismatch). Engineered an atomic "Golden Build" pipeline using js-yaml for single-source-of-truth hashes and Octokit for controlled GitHub publishing. Bridge update verified: Automatic transition from beta.9 to beta.10 successful. Version: 0.4.17-beta.10. |
| **TASK-068 Auto Update System** | 🥇 SEALED | Deterministic Auto Update System for Electron with state machine persistence, SHA256 manifest validation, secure IPC bridge, and state-driven UI. T1-T8 complete. Files: electron/update-state.cjs, electron/update-security.cjs, electron/update-manager.cjs, main.electron.cjs, frontend/preload.js, frontend/js/update-ui.js, frontend/js/app.js, frontend/css/update-ui.css, frontend/index.html, scripts/generate_update_manifest.cjs. Tests: Node unit tests (16 passed), Playwright E2E (7 passed). Version: 0.4.17-beta.3. Audit: PASS WITH FIXES. |
| **Command Dispatch Integrity Fix** | 🥇 SEALED | Implemented memory.delete skill and /tools command interceptor, but hard-disabled dispatcher (Task-066 safety brake). /tools commands now bypass LLM and dispatch directly to ToolExecutor, but the interceptor is disabled for stability. memory.delete skill remains implemented but registration commented out in tool_registry.py to prevent hallucination loops. Files: memory_tools.py (handle_memory_delete, MemoryDeleteArgs, memory_delete_tool), schemas.py (MemoryDeleteArgs), tool_registry.py (commented out), tool_executor.py (aliases added), chat_orchestrator.py (_try_tools_command with safety brake). |
| **TASK-066 Memory Context Bleed Prevention** | 🥇 SEALED | Threshold-Tuning: Minimum-Priority für Memory-Retrieval von 0.50 auf 0.65 angehoben. Reduziert Context Bleed (irrelevante alte Einträge im Prompt) und verbessert Antwortqualität bei kleinen Modellen wie Gemini Flash. Files: memory_budget.py (default priority), crud_service.py (legacy_priority, enriched_priority). Tests: 28/28 passed. |
| **Gemini Tool-Loop Fix** | 🥇 SEALED | Fixed Gemini V3 response generation gap: After successful tool execution, Gemini often returned no text (empty `round_text`). Solution: (1) System-Instruction trigger after tool results forcing text generation; (2) Fallback extracting `message`/`output` from successful tool results. Files: execution_engine.py (run_tool_loop_stream). No DB schema changes. Chat history remains clean. |
| **The Calendar Intelligence Trilogy** | 🥇 SEALED | TASK-065 (Contextual Entity Resolver), TASK-066 (Calendar Creation Detection), TASK-067 (Guided Assistant Mode) — Complete calendar mutation stack with entity resolution, creation/mutation disambiguation, and guided assistant mode for safe mutations. |
| TASK-065 Contextual Entity Resolver | 🥇 SEALED | Smart Entity Resolver: fuzzy + temporal disambiguation against `calendar_snapshot` before forced `find_and_update_event`. RESOLVED → pre-filled `event_id` + title (API get, skip fuzzy). AMBIGUOUS/WEAK → force `list_events`. NOT_FOUND/short query → no calendar tool (LLM clarification). **Extension:** Deictic context fallback using full_user_text for pronoun detection ("ihn", "den", "da") + orchestrator_context.history for clean chat history. Files: entity_resolver.py, execution_dispatcher.py, calendar_tools.py, schemas.py, find_and_update_event.json. Tests: test_entity_resolver.py (15/15). |
| TASK-064 Calendar Mutation Detection | 🥇 SEALED | Breaking the Calendar Listing Prison. Added is_calendar_mutation detection to IntentEngineV2 to distinguish between pure calendar queries (listing) and calendar mutations (updates). When is_calendar_mutation is true, the system no longer forces calendar.list_events tool_choice, allowing the model to reach calendar.find_and_update_event for mutation operations. **Extension:** Guard added to prevent BUG-SYS-019 fact-telling pattern ("mein/meine") from overriding calendar mutation intent. Calendar mutation beats personal_recall. Files: intent_engine.py, execution_dispatcher.py. |
| TASK-063 Proactive Calendar Updates | 🥇 SEALED | Proactive Calendar Updates implementation. Sharpened calendar update keywords in IntentEngineV2 ("bring", "ergänze", "ergänzen", "hinzufügen", "mit"). Added calendar.find_and_update_event as mandatory skill for calendar intents in CapabilityRegistry. Added proactive calendar mutation rule in prompt_registry.py to prioritize calendar updates over pure memory logging. Files: intent_engine.py, capability_registry.py, prompt_registry.py. |
| **Calendar Intelligence Extensions** | 🥇 SEALED | Guided Mode Schema Fix: event_title_query made Optional[str] in FindAndUpdateCalendarEventArgs (schemas.py) and find_and_update_calendar_event (calendar_tools.py). Allows models to patch by ID directly when Guided Mode is active without inventing search strings. Added ValueError guard: "Entweder event_id oder event_title_query muss angegeben werden." Files: schemas.py, calendar_tools.py. |
| TASK-062 Intent-to-Selector Gap Fix | 🥇 SEALED | Fixed Intent-to-Selector gap. Sharpened calendar keywords in IntentEngineV2 ("habe ich", "was habe ich", "was steht an", "steht an", "meine termine", "meinen termin", "meinen terminen"). Verified CapabilityRegistry returns calendar.list_events as mandatory for calendar intents. Added safety net in ExecutionDispatcher to inject calendar.list_events if is_calendar_intent is true but selector returned empty. Files: intent_engine.py, execution_dispatcher.py. |
| TASK-061 SkillSelector Intent-Aware | 🥇 SEALED | SkillSelector is now Intent-Aware & Policy-Driven. Integration of IntentEngineV2 detection results into SkillSelector.get_relevant_skills() for intent-based skill filtering. File: chat_orchestrator.py (lines 1238, 1328). |
| TASK-060 Agent Planner Overhaul | 🥇 SEALED | Harmonisierung von AgentPlanner und SkillSelector mit IntentEngineV2 und CapabilityRegistry. Einführung von PlannerContext/PlannerProviderProfile, Kalender-Guard (forbidden_skill_ids), 14-Tage Wochentag-Kalender, capability_registry Integration. Files: prompt_registry.py, execution_dispatcher.py, schemas.py, execution_engine.py, chat_orchestrator.py. |
| TASK-059 Kalender-Memory-Mirror | ✅ V1 IMPLEMENTED | Kompakter Kalender-Snapshot in Memory (`category=calendar_snapshot`) mit Enrichment, Derived Summary, gefilterter Chat-Injection und Proaktiv-Hinweisen hinter `JANUS_CALENDAR_PROACTIVE_HINTS`. |
| TASK-058 Janus Kalender | 🥇 SEALED | Phase 1-4 COMPLETE + Sync Hardening + Protocol Hardening: Pagination (maxResults=250), PATCH-Verify-Fallback, conferenceDataVersion=1, Output-Only-Key-Filterung, forensische Logs. Frontend: calendar-refresh Event, adaptive event cards, detail panel, duration buttons, all-day checkbox, --cal-hour-height CSS variable. Patterns: #GeminiV3Protocol (thought_signature), #GeminiNameSanitization (dot/underscore tolerance), #CalendarSnapshotIntegrity (invalidation after mutations). |
| TASK-057 Context Awareness | 🥇 SEALED | Kontext-/Intent-Haertung abgeschlossen; Provider-agnostische Self-Healing- und Summary-Veto-Logik stabil. |
| TASK-056 Prompt Caching | 🥇 SEALED | Provider-agnostisches Prompt-Caching inkl. Savings-Metriken und UI-Visualisierung abgeschlossen. |
| D27 Diamond Skill Engineering | 🥇 SEALED | Skill-Contract `{status,data,error}` und Modell-vs-Skill-Diagnose verbindlich definiert. |
| D26 System Sealing | 🥇 SEALED | Cleanup + Integritaetspruefung der Routing-/Self-Heal-Konfigurationen abgeschlossen. |
| D25 Monitoring Aggregator | 🥇 SEALED | Zentraler Endpoint `/api/system/monitoring/summary` aggregiert Health, Cooldown und History. |
| D24 Auto Self-Heal Trigger | 🥇 SEALED | Automatischer Trigger mit Cooldown-, Lock- und Health-Gates produktiv. |
| D23 FIFO History Logging | 🥇 SEALED | Routing-Historie mit FIFO-Begrenzung und Audit-Trail stabil. |
| D22 Self-Heal Cycle | 🥇 SEALED | Automatisierte Routing-Updates mit Shield-Regeln und Diamond-Logik aktiv. |
| D21 Diamond Routing Builder | 🥇 SEALED | Confidence-basierte Modellwahl ueber historische Runs operational. |
| D20 Model Routing Seal | 🥇 SEALED | Kalibrierte Modellzuweisungen per Matrix-Tests verifiziert und versioniert. |
| D19 Escalation Engine | 🥇 SEALED | Tier-basierte Eskalationspfade fuer Skill-Ausfuehrungen produktiv. |
| D18 Wiring Fix | 🥇 SEALED | Pipeline-Blocker (Imports, DB-Lifecycle, Tool-Wiring) behoben. |
| D17 Skill Health Matrix | 🥇 SEALED | Batch-Health-Matrix + deterministische Problemklassifikation etabliert. |
| D16 Deterministic Quality System | 🥇 SEALED | Deterministische Skill-Tests und Stabilitaetsregeln implementiert. |
| D15 Integrity Engine | 🥇 SEALED | Contract-Registry und Drift-Validierung fuer Logging-/Skill-Strukturen aktiv. |
| D14 Weekly Learning Engine | 🥇 HARMONIZED | Lern- und Evolutionsebene mit KPI-Registry integriert. |
| D13 Optimization Engine | 🥇 HARMONIZED | Regelbasierte Optimierungsentscheidungen und Action-Persistenz verfuegbar. |
| D12 Insight Engine | 🥇 HARMONIZED | Globale Log-Aggregation, Mustererkennung und Confidence-Metriken aktiv. |
| D11 Production Wrapper | 🥇 SEALED | Debug/Formatter-Endpoints und Diagnose-Workflows robust in Betrieb. |
| D10 Telemetry Foundation | 🥇 SEALED | Logging-Pipeline mit Schema-Sync, Queueing und DLQ-Light finalisiert. |

---

## SECTION 2 — SESSION_LOG (kurz)

| Timestamp | Task / Feature | Editor | Result | Audit | Version | Validation / Notes |
|---|---|---|---|---|---|---|
| 2026-05-07 | BACKLOG-011 Video Modal False-Positive Fix | SWE 1.6 | DONE | PASS | 0.4.17-beta.17 | URL-Detection Fallback deaktiviert, modal_request ausschließlich aus video.search tool_results. Backend-Override erzwingt mode="list" für Gemini. response_finalizer.py + tool_executor.py + video_search.json. Skill 6 Debug (3 Iterationen). |
| 2026-05-07 | BACKLOG-010 Image Move Regression Fix | SWE 1.6 | DONE | PASS | 0.4.17-beta.16 | Deterministischer Tool-Loop Guard für Desktop Image Move. Provider-agnostisch (gpt-5.4-nano + Gemini PASS). execution_engine.py erweitert. |
| 2026-05-05 | TASK-069 Beta.11 Native Diamond Release | SWE 1.6 | PUBLISHED | N/A | 0.4.17-beta.11 | First native Diamond release with optimized update UI. Real-time progress indicators, 0%-rule implementation, sidebar polish. |
| 2026-05-05 | TASK-069.36 Update UI Polish | KIMI-FIRST | DONE | N/A | 0.4.17-beta.11 | Optimized sidebar footer messages, implemented 0%-rule, added min-height to prevent jumping. |
| 2026-05-05 | TASK-069 Beta.10 Bridge Release | SWE 1.6 | PUBLISHED | N/A | 0.4.17-beta.10 | Final bridge release with hardened multi-hash validation and atomic pipeline sync. Disabled differential downloads. Published to GitHub. |
| 2026-05-05 | TASK-069 Beta.9 Golden Release | SWE 1.6 | PUBLISHED | N/A | 0.4.17-beta.9 | Hardened build pipeline with full rebuild, differential downloads disabled. Publish script updated for optional blockmap. Published to GitHub. |
| 2026-05-05 | TASK-069 Beta.8 Validator Fix | SWE 1.6 | PUBLISHED | N/A | 0.4.17-beta.8 | Fixed critical client-side validation bug (multi-hash aware). Published to GitHub. |
| 2026-05-05 | TASK-069 Beta.6 Clean Slate | Cursor / SWE | DONE | N/A | 0.4.17-beta.6 | Version bump after Beta.5 production release. |
| 2026-05-05 | TASK-069 Beta.5 Production Release | Cursor / SWE | PUBLISHED | N/A | 0.4.17-beta.5 | Release published to GitHub. Manifest integrity verified. |
| 2026-05-05 | TASK-069 Beta.5 Production Build Prep | Cursor / SWE | DONE | N/A | 0.4.17-beta.5 | DevTools: development-only (NODE_ENV check). Final Auto-Update Verification Run. |
| 2026-05-05 | TASK-069 `task_069_capability_overview_response_diamond_plan.md` | Cursor / SWE | DONE | PASS WITH FIXES | 0.4.17-beta.4 | pytest registry+help 21 ok; Playwright capability-overview 2 ok; JSON registry ok |

---

## TASK-058 Janus Kalender (Neu, knackig)

**Zielbild:** Ein zentrales Kalender-Modal mit Agenda/Tag/Woche, Inline-CRUD, AI-Planvorschau und expliziter User-Bestaetigung vor Mutationen.
**Aktueller Stand:** SEALED & COMPLETE. Backend-Router + Service + AI-Engine produktiv; Frontend mit View-Toggle, Timeline-Rendering, Diff-Overlay und Batch-Apply implementiert.
**Sync Hardening 2026-05-01:** Pagination (maxResults=250, pageToken-Loop), PATCH-Verify-Fallback, conferenceDataVersion=1, Output-Only-Key-Filterung, forensische Logging-Signale (organizer.self, verify-mismatch). Frontend: calendar-refresh Event, adaptive event cards, detail panel, duration buttons, all-day checkbox, --cal-hour-height CSS variable.

**Kern-Dateien:**
- `backend/api/routers/calendar.py`
- `backend/services/calendar/calendar_service.py`
- `backend/services/calendar/calendar_ai_engine.py`
- `frontend/js/calendar-modal.js`
- `frontend/css/calendar-modal.css`
- `frontend/index.html`
- `backend/tests/test_calendar_modal.py`
- `backend/tools/calendar_tools.py` (Sync Hardening)
- `backend/data/schemas.py` (duration_minutes)

**Tages-Panel (Kalender-Widget-Rail) & Release:** `frontend/js/calendar-day-widget.js`, `frontend/js/calendar-day-stats.js`, `frontend/css/calendar-day-widget.css`, `frontend/js/app.js` (Chat-Grenzen). Produktion: Backend + Electron laden **`frontend/dist`** (`npm run build` inkl. `verify-frontend-dist.cjs`). Siehe `documentation/tasks/task_calendar_day_widget_rail_diamond.md`.

---

## TASK-059 Kalender-Memory-Mirror (V1)

**Zielbild:** Janus kann aktuelle Kalenderlage aus einem kompakten Memory-Spiegel in den Chat-Kontext ziehen, ohne für jede einfache Terminfrage zwingend einen sichtbaren Tool-Roundtrip zu brauchen.
**Aktueller Stand:** V1 implementiert. `backend/services/calendar/calendar_memory.py` erzeugt Snapshot v1 mit `events[]`, Enrichment (`event_type`, `importance`, `movable`) und `derived` Block. `backend/api/routers/calendar.py` upsertet den Snapshot bei Kalenderabrufen/Mutationen und bietet `/api/calendar/sync/memory`. `backend/services/chat_orchestrator.py` injiziert nur bei Kalender-/Planungssignalen einen auf heute+morgen begrenzten Kontextblock; proaktive Konflikthinweise bleiben per `JANUS_CALENDAR_PROACTIVE_HINTS` default off.
**Tests:** `python -m pytest backend/tests/test_calendar_memory.py backend/tests/test_calendar_modal.py` → 26 passed.

---

## Observability & Integrity Stack (D10-D27)

Der komplette Observability-/Self-Heal-/Integrity-Stack (D10-D27) bleibt aktiv und verifiziert.  
Routing-, Monitoring-, Diagnose- und Lernpfade sind zusammenhaengend verdrahtet und dienen weiterhin als Governance-Schicht fuer neue Features.
