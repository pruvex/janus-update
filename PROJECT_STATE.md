# PROJECT_STATE.md (Diamond-OS V0.4.31-beta.76)
**Zweck:** Schlanke Triage-Uebersicht fuer den aktuellen Projektzustand.
**Aktualisiert:** 2026-05-03 (🥇 SEALED: The Calendar Intelligence Trilogy + Deictic Fallback + Guided Mode)

---

## CURRENT_SESSION_DELTA (Kompakt)

| Epic / Task | Status | Kurzstand |
|---|---|---|
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
