FIAMAN-DOSSIER – JANUS CALENDAR MODAL (DIAMOND STANDARD)
Version 1.0 – Full Production Specification
1. 🧭 PRODUKTDEFINITION
1.1 Name

Janus Calendar Modal

1.2 Typ

Modulares UI- und Service-System innerhalb von Janus zur zentralisierten Verwaltung und intelligenten Steuerung von Kalenderdaten.

1.3 Kernidee

Janus Calendar ist kein eigenständiger Kalender, sondern:

eine intelligente Steuerungs- und Abstraktionsschicht über bestehenden Kalender-Systemen

Primäre Integrationen:

Google Calendar (Phase 1)
Microsoft Outlook Calendar (Phase 2)
CalDAV / Apple Calendar (Phase 3)
1.4 Problemdefinition

Nutzer haben heute:

mehrere Kalenderquellen
keine zentrale Übersicht
schlechte UX für Planung über Systeme hinweg
keine KI-gestützte Optimierung
1.5 Lösung

Janus bietet:

einheitliche Timeline-Ansicht
bidirektionale Synchronisation
AI-basierte Planung und Optimierung
direkte Steuerung aller Kalender ohne externe Apps
2. 🧠 PRODUKTPRINZIPIEN
2.1 Source-of-Truth Architektur
Externe Kalender bleiben Datenquelle
Janus ist:
State Layer
UX Layer
AI Orchestration Layer
2.2 AI-first Design

Kalender ist nicht statisch, sondern dynamisch steuerbar:

Planung in natürlicher Sprache
automatische Optimierung von Zeitplänen
intelligente Konfliktlösung
2.3 Zero-friction Interaction
keine externen Kalender nötig
keine Redirects
Inline Editing überall
sofortige visuelle Updates (optimistic UI)
2.4 Multi-source Aggregation

Alle Kalender werden vereinheitlicht:

Google
Outlook
Apple (CalDAV)
lokale Janus Events
3. 🧩 FUNKTIONALE ANFORDERUNGEN
3.1 Kalenderanzeige
Views:
Agenda View (Standard)
Week View
Day View
Features:
Farbliche Kennzeichnung nach Quelle
Scrollbare Timeline
Echtzeit-Sync Status Indikatoren
3.2 Event Management (CRUD)
Create Event
Read Event
Update Event
Delete Event
UX:
Inline Editing
Drag & Drop Rescheduling
Quick Edit Panel
3.3 Synchronisation
Mechanik:
Google Calendar API (Phase 1)
Webhooks oder Polling Sync
Konflikterkennung
Sync States:
synced
pending
conflict
external_modified
3.4 AI Calendar Control
Eingabe:
Natural Language Commands
Selected time ranges
Context-aware prompts
Beispiele:
„Plane meinen Tag effizient“
„Verschiebe alle Meetings auf den Nachmittag“
„Blocke 3 Stunden Fokuszeit morgen“
„Reduziere Meeting-Dichte diese Woche“
Ausgabe:

AI generiert:

Event Creation Actions
Update Actions
Move Actions
Delete Actions
Action Schema:
type CalendarAIAction =
  | { type: "create"; event: JanusCalendarEvent }
  | { type: "update"; id: string; changes: Partial<JanusCalendarEvent> }
  | { type: "delete"; id: string }
  | { type: "move"; id: string; newStart: Date; newEnd: Date };
3.5 Quick Actions
New Event
Schedule Meeting
Find Free Slot
Block Focus Time
Optimize Day
Move All Meetings
3.6 Conflict Handling

Erkennung:

Zeitüberschneidungen
externe Änderungen
Recurring Event Konflikte

Auflösung:

User Action > External > AI Suggestion
visuelle Konfliktmarkierung
diff-basierte Vorschläge
4. 🖥️ UI / UX SPEZIFIKATION
4.1 Modal Layout
┌──────────────────────────────────────────────┐
│ Header: Calendar / Sync Status / AI Input   │
├───────────────┬──────────────────────────────┤
│ Sidebar       │ Main Timeline View           │
│ - Filters     │ - Agenda / Week / Day        │
│ - Calendars   │ - Events                     │
│ - Sources     │                              │
├───────────────┴──────────────────────────────┤
│ Quick Action Bar + AI Command Input          │
└──────────────────────────────────────────────┘
4.2 Komponentenstruktur
Root
CalendarModal
Views
CalendarTimelineView
CalendarDayView
CalendarWeekView
Entities
CalendarEventCard
EventEditorInline
ConflictIndicator
Controls
QuickActionBar
AICommandInput
FilterSidebar
4.3 UX-Regeln
Änderungen sofort sichtbar (optimistic UI)
keine Popups für Standard-Editing
Drag & Drop standardisiert
Sync läuft unsichtbar im Hintergrund
keine externe Kalender-App erforderlich
5. 🧠 DATENMODELL (UNIFIED CALENDAR SCHEMA)
type JanusCalendarEvent = {
  id: string;

  title: string;
  description?: string;

  start: Date;
  end: Date;

  timezone: string;

  location?: string;

  attendees?: string[];

  source: "google" | "outlook" | "caldav" | "janus-local";

  externalId?: string;

  recurrenceRule?: string;

  status: "confirmed" | "tentative" | "cancelled";

  syncState: "synced" | "pending" | "conflict";

  lastModified: Date;
};
5.1 Event States
confirmed
tentative
cancelled
5.2 Sync States
synced
pending
conflict
6. 🔄 ARCHITEKTUR
6.1 Systemübersicht
UI Layer (Janus Modal)
        ↓
Calendar Service Layer
        ↓
Unified Event Model
        ↓
Adapter Layer
   ├── Google Calendar API
   ├── Microsoft Graph API
   └── CalDAV / Apple
6.2 Adapter Prinzip

Jeder Kalenderanbieter ist ein Adapter:

normalize input → Janus Event
transform output → Provider format
6.3 Sync Engine
polling (MVP)
optional webhook-based sync (Google Push API)
conflict detection layer
reconciliation engine
7. 🤖 AI SYSTEM DESIGN
7.1 AI Input Types
natural language
selected events
time range context
calendar state snapshot
7.2 AI Output Types
structured action plan
diff-based schedule changes
optimized schedule proposals
7.3 AI Execution Flow
User input
AI generates plan
Plan preview (UI)
User approval
Execution via Calendar Service Layer
8. 🧪 QA / TESTING SPEZIFIKATION (PLAYWRIGHT)
8.1 Test Setup Requirements
Mock Google Calendar API
deterministic event dataset
time control (fixed clock)
8.2 Test Cases
TEST 1 – Event Rendering
open modal
verify events from API render correctly
TEST 2 – Create Event
create event via UI
assert API POST call
TEST 3 – Edit Event Inline
click event
change title
assert PATCH request
TEST 4 – Drag & Drop Reschedule
move event
assert updated time persisted
TEST 5 – AI Command Execution

Input:

“move all meetings to afternoon”

Expected:

AI returns structured actions
preview UI shown
user confirmation required
API updates executed
TEST 6 – Sync Conflict
simulate external calendar update
open modal
verify conflict state appears
TEST 7 – Multi-event Update
bulk selection
apply AI optimization
verify batch update calls
9. ⚙️ PERFORMANCE REQUIREMENTS
UI response < 100ms (optimistic rendering)
Sync latency < 3s
support 10.000+ events
smooth drag & drop (60 FPS)
background sync non-blocking
10. 🔐 EDGE CASE HANDLING
timezone mismatches
recurring event expansion
external deletion of event
duplicate event detection
partial sync failures
11. 🚀 ROADMAP
Phase 1 (MVP)
Google Calendar integration
basic UI modal
CRUD operations
Phase 2
drag & drop
quick actions
AI suggestions (non-executing)
Phase 3
full AI execution engine
Microsoft integration
conflict resolution UI
Phase 4
Apple/CalDAV integration
team scheduling mode
shared calendars
12. 🧾 DEFINITION OF DONE

Das Modul gilt als abgeschlossen wenn:

Google Calendar vollständig integriert ist
UI vollständig ohne externe Apps nutzbar ist
CRUD stabil + getestet ist
Sync zuverlässig funktioniert
AI Actions teilweise ausführbar sind
Playwright Test Suite vollständig grün ist
🧠 FINAL STATEMENT

Janus Calendar ist kein Kalender.

Es ist:

ein AI-gestütztes Zeit- und Planungssystem über allen bestehenden Kalendern hinweg

SYSTEMÜBERSICHT

Janus Calendar besteht aus 4 Kernsystemen:

🧩 1. UI LAYER (Calendar Modal)
React/Frontend-Komponente
Visualisierung + Interaktion
AI Input + Event Editing
⚙️ 2. CALENDAR SERVICE LAYER (CORE ENGINE)
Event Management
State Management
Sync Orchestration
🔄 3. SYNC ENGINE (Provider Layer)
Google Calendar API (Phase 1)
Microsoft Graph API (Phase 2)
CalDAV (Phase 3)
🤖 4. AI PLANNING ENGINE
Natural Language → Actions
Schedule Optimization
Conflict Resolution Suggestions
2. 🖥️ FRONTEND ARCHITECTURE (REACT SPEC)
2.1 Component Tree
CalendarModal
 ├── CalendarHeader
 │    ├── SyncStatusIndicator
 │    ├── AICommandInput
 │
 ├── CalendarSidebar
 │    ├── CalendarFilters
 │    ├── CalendarSourcesList
 │
 ├── CalendarTimelineView
 │    ├── DayColumn[]
 │    │     ├── CalendarEventCard
 │    │     ├── EventConflictMarker
 │
 ├── QuickActionBar
 ├── EventEditorInline
2.2 State Management

Empfohlen:

Zustand oder Redux Toolkit
Global State
type CalendarState = {
  events: JanusCalendarEvent[];
  selectedEventId?: string;
  viewMode: "day" | "week" | "agenda";

  loading: boolean;
  syncStatus: "idle" | "syncing" | "error";

  aiSuggestions: CalendarAIAction[];
};
2.3 Optimistic UI Strategy
UI update sofort
API call im Hintergrund
rollback bei Fehler
3. ⚙️ CALENDAR CORE ENGINE
3.1 Responsibilities
Event normalization
conflict detection
state reconciliation
unified event store
3.2 Event Store Logic
class CalendarStore {
  events: Map<string, JanusCalendarEvent>;

  addEvent(event) {}
  updateEvent(id, changes) {}
  deleteEvent(id) {}

  getEventsByDate(date) {}
}
3.3 Conflict Detection Engine
function detectConflicts(events: JanusCalendarEvent[]) {
  return events.filter((a, i) =>
    events.some((b, j) =>
      i !== j &&
      a.start < b.end &&
      a.end > b.start
    )
  );
}
3.4 Recurrence Handling
RRULE parsing
expansion in memory view
lazy expansion for performance
4. 🔄 SYNC ENGINE (GOOGLE + FUTURE PROVIDERS)
4.1 Adapter Pattern
interface CalendarAdapter {
  fetchEvents(): Promise<JanusCalendarEvent[]>;
  createEvent(event): Promise<void>;
  updateEvent(id, changes): Promise<void>;
  deleteEvent(id): Promise<void>;
}
4.2 Google Calendar Adapter
OAuth2 Flow
Google Calendar API v3
incremental sync
4.3 Sync Strategy
Hybrid Sync Model:
Initial full fetch
delta sync via updatedAt
fallback polling
4.4 Conflict Resolution Rules

Priority Order:

User action (Janus UI)
External update
AI suggestion
4.5 Sync States
type SyncState =
  | "synced"
  | "pending"
  | "conflict"
  | "external_update";
5. 🤖 AI CALENDAR ENGINE
5.1 Pipeline
User Input
   ↓
Context Builder
   ↓
LLM Planner
   ↓
Action Generator
   ↓
Validation Layer
   ↓
UI Preview
   ↓
Execution Engine
5.2 Context Model

AI bekommt:

alle Events (compressed)
freie Zeitblöcke
user preferences (optional später)
current focus load
5.3 AI Output Format
type CalendarAIPlan = {
  summary: string;
  actions: CalendarAIAction[];
  riskLevel: "low" | "medium" | "high";
};
5.4 Optimization Strategies
reduce context switching
group meetings
preserve deep work blocks
minimize fragmentation
5.5 Example AI Behavior

Input:

"optimize my day"

Output:

move meetings into 2 blocks
create 3h focus block
remove gaps < 30min
6. 🧪 PLAYWRIGHT TEST ARCHITECTURE
6.1 Test Setup
mocked calendar API
deterministic time system
seeded events dataset
6.2 Test Harness
beforeEach(() => {
  mockGoogleCalendarAPI();
  setFixedTime("2026-01-01T09:00:00Z");
});
6.3 Core Tests
TEST A – Load Calendar
open modal
expect events visible
assert correct grouping
TEST B – Create Event
click “new event”
fill form
save
assert API call
TEST C – Inline Edit
click event title
edit
blur
assert update call
TEST D – Drag & Drop
move event
assert new timestamps
TEST E – AI Execution

Input:

"move meetings to afternoon"

Expected:

AI plan shown
user approval required
API updates triggered
TEST F – Sync Conflict
external update simulation
UI reload
conflict marker shown
TEST G – Bulk AI Optimization
select multiple events
run AI optimize
verify batch updates
7. ⚡ PERFORMANCE ENGINEERING
7.1 Targets
UI render < 100ms
event operations < 50ms
sync latency < 3s
10k+ events supported
7.2 Optimization Techniques
virtualized timeline rendering
memoized event components
batched state updates
debounced sync writes
8. 🔐 EDGE CASE SYSTEM
8.1 Covered Cases
timezone drift
duplicate events
deleted external events
partial sync failure
recurring event exceptions
8.2 Recovery Strategy
automatic re-sync
soft rollback
conflict UI resolution
9. 🧱 FUTURE EXTENSIONS
Phase 2
Microsoft Graph integration
calendar sharing
Phase 3
Apple CalDAV support
offline-first mode
Phase 4
full AI auto-scheduler
team coordination mode
meeting negotiation agent
10. 🧾 FINAL DEFINITION OF SYSTEM

Janus Calendar System is:

a real-time AI-driven orchestration layer for time management across multiple calendar ecosystems

🧠 ABSCHLUSS

Das ist jetzt kein UI-Feature mehr.

Das ist:

🧠 Scheduling Intelligence Engine
🔄 Multi-provider Sync System
🤖 AI Planning Layer
🖥️ Interactive Control Surface

FIAMAN-DOSSIER – JANUS CALENDAR CORE ENGINE + AI SCHEDULING SYSTEM
Version 3.0 – Production Brain Layer
TEIL A — 🔄 GOOGLE SYNC ENGINE (PRODUCTION READY)
1. 🧠 ARCHITEKTURÜBERSICHT
Janus Calendar Core
        ↓
Sync Orchestrator
        ↓
Provider Adapter Layer
   ├── Google Calendar Adapter
   ├── Microsoft Graph Adapter (future)
   └── CalDAV Adapter (future)
        ↓
External APIs
2. ⚙️ CORE SYNC ENGINE
2.1 Responsibilities
Fetch Events (initial + incremental)
Normalize Events
Push Changes (create/update/delete)
Detect Conflicts
Maintain Sync State
2.2 CORE CLASS (PRODUCTION STYLE)
export class CalendarSyncEngine {
  constructor(
    private adapter: CalendarAdapter,
    private store: CalendarStore
  ) {}

  async fullSync() {
    const externalEvents = await this.adapter.fetchEvents();

    const normalized = externalEvents.map(this.normalize);

    this.store.replaceAll(normalized);

    return normalized;
  }

  async incrementalSync() {
    const updates = await this.adapter.fetchUpdatedSince(
      this.store.getLastSyncTimestamp()
    );

    updates.forEach(event => {
      const normalized = this.normalize(event);
      this.store.upsert(normalized);
    });

    this.store.setLastSyncTimestamp(new Date());
  }

  async pushCreate(event: JanusCalendarEvent) {
    const external = this.denormalize(event);
    const result = await this.adapter.createEvent(external);

    this.store.markSynced(event.id, result.externalId);
  }

  async pushUpdate(event: JanusCalendarEvent) {
    const external = this.denormalize(event);
    await this.adapter.updateEvent(event.externalId!, external);

    this.store.markSynced(event.id);
  }

  async pushDelete(event: JanusCalendarEvent) {
    await this.adapter.deleteEvent(event.externalId!);

    this.store.remove(event.id);
  }

  private normalize(event: any): JanusCalendarEvent {
    return {
      id: event.id,
      title: event.summary,
      start: new Date(event.start.dateTime),
      end: new Date(event.end.dateTime),
      timezone: event.start.timeZone,
      source: "google",
      externalId: event.id,
      status: "confirmed",
      syncState: "synced",
      lastModified: new Date()
    };
  }

  private denormalize(event: JanusCalendarEvent) {
    return {
      summary: event.title,
      start: { dateTime: event.start.toISOString() },
      end: { dateTime: event.end.toISOString() }
    };
  }
}
3. 🔌 GOOGLE CALENDAR ADAPTER
import { google } from "googleapis";

export class GoogleCalendarAdapter implements CalendarAdapter {
  private calendar;

  constructor(authClient: any) {
    this.calendar = google.calendar({
      version: "v3",
      auth: authClient
    });
  }

  async fetchEvents() {
    const res = await this.calendar.events.list({
      calendarId: "primary",
      singleEvents: true,
      orderBy: "startTime"
    });

    return res.data.items ?? [];
  }

  async createEvent(event: any) {
    const res = await this.calendar.events.insert({
      calendarId: "primary",
      requestBody: event
    });

    return res.data;
  }

  async updateEvent(id: string, event: any) {
    await this.calendar.events.update({
      calendarId: "primary",
      eventId: id,
      requestBody: event
    });
  }

  async deleteEvent(id: string) {
    await this.calendar.events.delete({
      calendarId: "primary",
      eventId: id
    });
  }
}
4. ⚠️ CONFLICT ENGINE
export function detectConflicts(events: JanusCalendarEvent[]) {
  const conflicts: string[] = [];

  for (let i = 0; i < events.length; i++) {
    for (let j = i + 1; j < events.length; j++) {
      const a = events[i];
      const b = events[j];

      const overlap =
        a.start < b.end &&
        a.end > b.start;

      if (overlap) {
        conflicts.push(a.id);
        conflicts.push(b.id);
      }
    }
  }

  return new Set(conflicts);
}
5. 🔁 SYNC STRATEGY (PRODUCTION)
Hybrid Model:
Full Sync → initial load
Delta Sync → every X minutes
Event-based Sync → UI triggers
Sync Priority Rules:
User action (Janus UI)
External update
AI suggestion
6. 🤖 AI SCHEDULING SYSTEM (PROMPT ENGINE)
1. 🧠 CORE PURPOSE

AI ist nicht Chatbot — sondern:

Deterministischer Scheduling-Optimizer

2. 📥 AI INPUT CONTEXT (CRITICAL)
{
  "current_time": "2026-05-01T10:00:00Z",
  "events": [...],
  "free_blocks": [...],
  "user_preferences": {
    "deep_work_preference": true,
    "meeting_limit_per_day": 6
  },
  "constraints": {
    "no_overlap": true,
    "working_hours": "09:00-18:00"
  }
}
3. 🧾 SYSTEM PROMPT (PRODUCTION GRADE)
You are Janus Calendar AI, a deterministic scheduling engine.

Your task:
- Optimize user schedules
- Reduce fragmentation
- Maximize deep work blocks
- Minimize context switching

Rules:
1. Never create overlapping events.
2. Respect existing confirmed events unless explicitly told otherwise.
3. Prefer grouping meetings into contiguous blocks.
4. Preserve at least 2-hour uninterrupted focus blocks where possible.
5. Do not hallucinate events.
6. Output ONLY structured actions.

Output format MUST be JSON:
{
  "summary": string,
  "actions": [
    {
      "type": "create | update | delete | move",
      "eventId": string?,
      "payload": object
    }
  ],
  "riskLevel": "low | medium | high"
}
4. 🧠 AI PLANNER FUNCTION
export async function generateSchedulePlan(input: any) {
  const prompt = buildPrompt(input);

  const response = await llm.call(prompt);

  return JSON.parse(response);
}
5. 📊 AI OPTIMIZATION STRATEGIES
5.1 Deep Work Maximization
merge small gaps
block 2–4h sessions
5.2 Meeting Compression
group meetings into clusters
avoid scattering
5.3 Context Switch Reduction
minimize back-to-back domain switching
5.4 Energy Model (optional future)
mornings = deep work
afternoons = meetings
6. 🔄 AI → EXECUTION PIPELINE
User Input
   ↓
Context Builder
   ↓
AI Planner
   ↓
Validation Layer
   ↓
Diff Generator
   ↓
User Preview UI
   ↓
Execution Engine (Sync Engine)
7. 🧪 AI TEST SPEC (PLAYWRIGHT + MOCK LLM)
TEST 1 – Valid Schedule Optimization

Input:

"optimize my day"

Assert:

AI returns actions
no overlaps
focus blocks created
TEST 2 – No Event Fabrication

Assert:

only existing events modified
no new random events
TEST 3 – Conflict Awareness

Simulate overlap → AI must resolve or flag risk

TEST 4 – Bulk Move

Move all meetings → afternoon cluster

8. ⚡ PERFORMANCE REQUIREMENTS
Sync Engine:
< 2s delta sync
< 5s full sync
AI Engine:
< 3s response time
deterministic JSON output
9. 🧠 FINAL SYSTEM DEFINITION

Janus Calendar Engine besteht aus:

🔄 Sync Layer
Google Calendar Integration
bidirectional sync
conflict resolution
🤖 AI Layer
scheduling intelligence
optimization engine
structured action generation
🧩 Core Layer
unified event model
state management
UI orchestration
🚀 ABSCHLUSS

Du hast jetzt zwei Dinge:

1. Production Sync Engine

→ echte Google Calendar Integration

2. AI Scheduling Brain

→ deterministische Planungsintelligenz