# DIAMOND TASK: Janus Mail — AI-Native E-Mail-System

---
task_id: 20260502-060
status: PLANNING
assigned_to: TBD
confidence_level: MEDIUM
created_at: 2026-05-02 02:18
updated_at: 2026-05-02 02:18
source_dossier: documentation/Planned Features/janus mail.md
cu_total: 28 (geschätzt)
completion_gate:
  tests: false
  audit_trail: false
  lessons_learned: false
  user_control: false
  regression_green: false
---

# 1 Task Description

Janus erhält ein Mail-Modul als KI-natives Kommunikationssystem. E-Mails werden in strukturierte, priorisierte und handlungsorientierte Wissenseinheiten transformiert. Das System baut auf der bestehenden `gmail_tools.py`-Infrastruktur auf und folgt dem Calendar-Module-Pattern (TASK-058).

**Core Value:**

> Janus verwandelt deine Inbox von "Mails abarbeiten" in "relevante Kommunikation verstehen und entscheiden".

**Diamond-Ziel:**

- Mail-Modal im bestehenden MCL/Dock-System integriert.
- Thread-first Inbox mit AI-Analyse (Summary, Intent, Priority, Actions).
- CRUD über bestehende `gmail_tools.py`-Funktionen.
- AI-gesteuerte Antwortgenerierung mit User-Confirmation.
- Kein Architektur-Redesign; Aufbau auf bestehendem Skill/Tool-System.
- Gmail-only in MVP; Multi-Provider als Future Extension.

---

# 2 Bewertung des Feature-Dossiers

## Einschätzung: 5/10 Diamond Standard

Das Original-Dossier hat eine starke Vision (AI-first, Action-oriented, Thread-centric), aber die Umsetzungsplanung passt nicht zur Janus-Architektur:

- **Falscher Tech-Stack**: Beschreibt TypeScript-Module, Janus nutzt Python + Vanilla JS.
- **Ignoriert bestehende Infrastruktur**: `gmail_tools.py` (List, Read, Send) existiert bereits production-ready.
- **Standalone-Architektur**: Schlägt eigene Module vor statt Janus-Patterns zu folgen.
- **Kein Diamond-Prozess**: Keine Phasen, CUs, Completion Gates, Guardrails.

Dieser Task-Plan übernimmt die Vision, baut aber die Umsetzung komplett auf der realen Janus-Architektur auf.

## Was bereits existiert (NICHT neu bauen)

| Funktion | Datei | Status |
|---|---|---|
| Google OAuth2 Auth | `backend/tools/gmail_tools.py` | Production |
| List Emails (mit Query-Filter) | `get_latest_emails()` | Production |
| Read Email (mit Body-Extraktion) | `read_email()` | Production |
| Send Email (mit Attachment) | `send_email()` | Production |
| Email Body Parser (HTML→Text) | `_get_email_body()` | Production |
| Gmail Service Auth | `_get_gmail_service()` | Production |
| Skill: list_emails | `backend/skills/communication/list_emails.json` | Production |
| Skill: read_email | `backend/skills/communication/read_email.json` | Production |
| Skill: send_email | `backend/skills/communication/send_email.json` | Production |
| Skill: find_contact_and_email | `backend/skills/communication/find_contact_and_email.json` | Production |
| Tool Contract v1 | `backend/tools/tool_contract_v1.py` | Production |
| LLM Gateway | `backend/services/llm_gateway.py` | Production |
| Memory System | `backend/services/memory_*.py` | Production |

## Was NEU gebaut werden muss

| Bereich | Beschreibung | Priorität |
|---|---|---|
| Mail Service Layer | Thread-Auflösung, Normalisierung, Caching | P0 |
| Mail API Router | REST-Endpoints für Mail-Modal (nicht Tool-basiert) | P0 |
| Mail Schemas | Pydantic-Modelle für Threads, AI-Metadaten | P0 |
| Mail Modal UI | Thread-Liste, Inbox-View im MCL/Dock-System | P0 |
| AI Mail Engine | Summary, Intent, Priority, Action Extraction | P1 |
| Reply Generator | KI-gesteuerte Antwortgenerierung | P1 |
| Mail Memory Mirror | Kompakter Mail-Snapshot für Chat-Kontext (analog Calendar Memory) | P2 |
| Smart Views | Filtered Views: Needs Reply, Waiting, High Priority | P2 |
| Composer | Mail-Verfassen mit AI-Rewrite | P2 |

## Haupt-Risiken

| Risiko | Severity | Mitigation |
|---|---|---|
| Gmail API Rate Limits (Quota 250/s) | Medium | Caching im Service Layer, Pagination, Delta-Sync |
| Thread-Auflösung komplex (In-Reply-To, References) | High | Phase 1 nutzt Gmail-native threadId, kein eigenes Threading |
| AI-Kosten bei vielen Mails | Medium | Batch-Processing, nur ungelesene Mails analysieren, Priority-Gate |
| Scope Creep (Multi-Provider zu früh) | High | MVP = Gmail only. Provider-Abstraktion erst nach Gmail-Stabilität |
| HTML-Mail-Rendering im Modal | Medium | Sanitized HTML mit DOMPurify (bereits im Projekt), Fallback auf Text |
| Vanilla JS UI-Komplexität | Medium | Strikte Modularisierung, Calendar-Modal als Pattern-Vorlage |

---

# 3 Current Architecture Reference

| Bereich | Datei / Komponente | Rolle |
|---|---|---|
| Gmail Backend | `backend/tools/gmail_tools.py` | Gmail CRUD, OAuth2, Body-Parser |
| Google Auth | `gmail_tools._get_gmail_service()` | OAuth2 via Keyring |
| Tool Registry | `backend/tool_registry.py` | Skill-Routing |
| Skill Definitions | `backend/skills/communication/*.json` | 4 Mail-Skills registriert |
| Modal System | `frontend/js/modal-api.js` | MCL Facade — Dock-basierte Modals |
| Window State | `frontend/js/window-state.js` | Zentraler State für Dock-Module |
| Dock System | `frontend/js/dock.js` | Dock-Bar UI und Modulverwaltung |
| Calendar (Referenz-Pattern) | `backend/services/calendar/` | Service-Layer-Pattern für neue Module |
| Calendar Router (Referenz) | `backend/api/routers/calendar.py` | Router-Pattern für neue Module |
| Calendar Schemas (Referenz) | `backend/data/schemas_calendar.py` | Schema-Pattern für neue Module |
| Calendar Memory (Referenz) | `backend/services/calendar/calendar_memory.py` | Memory-Mirror-Pattern |
| LLM Gateway | `backend/services/llm_gateway.py` | Provider-agnostische LLM-Aufrufe |
| Chat Orchestrator | `backend/services/chat_orchestrator.py` | Chat-Pipeline + Kontext-Injection |
| Memory Service | `backend/services/memory_*.py` | Fact-Storage + Retrieval |
| Styles | `frontend/css/style.css`, `frontend/css/calendar-modal.css` | Haupt-Stylesheets |
| HTML Entry | `frontend/index.html` | DOM-Struktur aller Modals |

---

# 4 Architekturprinzipien

- **Reuse first:** Backend-Funktionen aus `gmail_tools.py` werden vom neuen Service Layer gewrappt, nicht dupliziert.
- **Calendar-Pattern:** Architektur folgt exakt dem TASK-058-Muster: `services/mail/` + `api/routers/mail.py` + `data/schemas_mail.py`.
- **MCL-Integration:** Mail Modal nutzt das bestehende Dock/Window-State-System.
- **Gmail-native Threading:** Phase 1-3 nutzt Gmails `threadId` für Thread-Auflösung — kein eigenes Threading-System.
- **AI as Advisor:** AI analysiert und schlägt vor, aber keine automatischen Aktionen.
- **Source-of-Truth extern:** Gmail bleibt Datenquelle; Janus ist AI/UX-Layer.
- **Vanilla JS:** Kein React, kein Framework — konsistent mit der bestehenden Codebase.
- **Progressive Enhancement:** Inbox-Liste → Threads → AI-Analyse → Reply-Gen → Smart Views.

---

# 5 Zielarchitektur

```text
Frontend (Mail Modal)
  ├── Inbox View (Thread-Liste)
  ├── Thread View (Konversation)
  ├── AI Panel (Summary, Intent, Actions)
  ├── Composer (mit AI-Rewrite)
  └── Smart View Tabs
        ↓ REST API
Backend (Mail Router)
  ├── GET  /api/mail/threads
  ├── GET  /api/mail/threads/{id}
  ├── POST /api/mail/send
  ├── POST /api/mail/reply
  ├── POST /api/mail/ai/analyze
  ├── POST /api/mail/ai/reply
  ├── PUT  /api/mail/threads/{id}/labels
  ├── DELETE /api/mail/threads/{id}
  └── GET  /api/mail/sync/status
        ↓
Mail Service Layer
  ├── Thread Resolution (via Gmail threadId)
  ├── Mail Normalization (Gmail → JanusMail)
  ├── AI Pipeline (Summary, Intent, Priority, Actions)
  ├── Reply Generator
  └── Mail Memory Mirror
        ↓
Existing gmail_tools.py (Gmail API)
```

---

# 6 Datenmodell

## JanusMailMessage (normalisierte Nachricht)

```python
class JanusMailMessage(BaseModel):
    id: str
    thread_id: str
    from_address: MailParticipant
    to: list[MailParticipant] = []
    cc: list[MailParticipant] = []
    subject: str
    body_text: str
    body_html: str | None = None
    snippet: str
    timestamp: datetime
    labels: list[str] = []
    is_read: bool = True
    is_starred: bool = False
    has_attachments: bool = False
    attachments: list[MailAttachment] = []

class MailParticipant(BaseModel):
    name: str = ""
    email: str

class MailAttachment(BaseModel):
    filename: str
    mime_type: str
    size_bytes: int = 0
```

## JanusMailThread (Thread mit AI-Metadaten)

```python
class JanusMailThread(BaseModel):
    id: str
    subject: str
    participants: list[MailParticipant]
    messages: list[JanusMailMessage]
    last_updated: datetime
    message_count: int
    snippet: str
    labels: list[str] = []
    is_unread: bool = False

    ai: MailAIMetadata | None = None

class MailAIMetadata(BaseModel):
    summary: str = ""
    intent: Literal["request", "information", "meeting",
                     "confirmation", "marketing", "system", "unknown"] = "unknown"
    priority_score: float = 0.5  # 0.0-1.0
    actionables: list[str] = []
    suggested_reply_tone: Literal["formal", "casual", "brief", "detailed"] | None = None
    status: Literal["needs_reply", "waiting", "done", "fyi"] = "fyi"
```

## MailAIReply (generierte Antwort)

```python
class MailAIReplyRequest(BaseModel):
    thread_id: str
    instruction: str = ""
    tone: Literal["formal", "casual", "brief", "detailed"] = "casual"
    language: str = "de"

class MailAIReplyResponse(BaseModel):
    draft_text: str
    tone_used: str
    based_on_messages: int
    confidence: float
```

---

# 7 Technical Contracts

## Thread-Liste (Inbox)

```http
GET /api/mail/threads?max_results=20&query=&label=INBOX&smart_view=
```

Response:
```json
{
  "threads": [JanusMailThread],
  "total_count": 42,
  "unread_count": 7,
  "sync_status": "synced"
}
```

## Thread Detail

```http
GET /api/mail/threads/{thread_id}
```

Response:
```json
{
  "thread": JanusMailThread,
  "ai": MailAIMetadata
}
```

## AI-Analyse (on-demand)

```http
POST /api/mail/ai/analyze
```

```json
{
  "thread_id": "string",
  "force_refresh": false
}
```

Response:
```json
{
  "thread_id": "string",
  "ai": MailAIMetadata
}
```

## AI Reply Generation

```http
POST /api/mail/ai/reply
```

```json
{
  "thread_id": "string",
  "instruction": "Kurz ablehnen",
  "tone": "formal",
  "language": "de"
}
```

Response:
```json
{
  "draft_text": "string",
  "tone_used": "formal",
  "confidence": 0.85
}
```

## Send / Reply

```http
POST /api/mail/send
POST /api/mail/reply
```

```json
{
  "thread_id": "string (nur bei reply)",
  "to": "email@example.com",
  "subject": "string",
  "body": "string",
  "attachment_path": "string | null"
}
```

---

# 8 AI System Design

## AI-Analyse-Pipeline

```text
Thread laden (alle Messages)
  ↓
Context Builder (letzte 5 Messages + Teilnehmer + Labels)
  ↓
LLM Call (via llm_gateway, JSON-Output)
  ↓
Response Parser + Validation (Pydantic)
  ↓
MailAIMetadata zurück an UI
```

## System Prompt (Mail Analyzer)

```text
You are Janus Mail AI, an intelligent email analysis engine.

Your task:
- Summarize the email thread concisely (1-2 sentences, German)
- Classify the intent (request, information, meeting, confirmation, marketing, system)
- Compute a priority score (0.0 = irrelevant, 1.0 = urgent)
- Extract concrete actionables (what the user needs to do)
- Determine thread status (needs_reply, waiting, done, fyi)

Rules:
1. Summarize in the user's language (German unless English thread).
2. Priority considers: sender importance, urgency keywords, response delay, thread length.
3. Actionables must be concrete: "Antwort senden", not "Mail lesen".
4. Marketing/System mails get priority < 0.2 unless user-relevant.
5. Output ONLY structured JSON.

Output format:
{
  "summary": "string",
  "intent": "request|information|meeting|confirmation|marketing|system",
  "priority_score": 0.0-1.0,
  "actionables": ["string"],
  "status": "needs_reply|waiting|done|fyi",
  "suggested_reply_tone": "formal|casual|brief|detailed|null"
}
```

## System Prompt (Reply Generator)

```text
You are Janus Mail AI, generating email replies.

Context:
- Full thread history
- User instruction (e.g. "Kurz ablehnen", "Termin bestätigen")
- Requested tone and language

Rules:
1. Match the tone precisely (formal/casual/brief/detailed).
2. Reference relevant thread context naturally.
3. Do NOT add information not in the thread.
4. Keep it concise unless "detailed" tone is requested.
5. Output ONLY the reply text, no metadata.
6. Default language: German.
```

---

# 9 Exakte Datei-Level Impact Analysis

| Datei | Aktion | Beschreibung |
|---|---|---|
| `backend/data/schemas_mail.py` | **CREATE** | Pydantic-Modelle: JanusMailMessage, JanusMailThread, MailAIMetadata, etc. |
| `backend/services/mail/__init__.py` | **CREATE** | Package-Init |
| `backend/services/mail/mail_service.py` | **CREATE** | Service Layer: wrappt gmail_tools.py, Thread-Auflösung, Normalisierung |
| `backend/services/mail/mail_ai_engine.py` | **CREATE** (Phase 3) | AI-Analyse-Pipeline: Summary, Intent, Priority, Actions |
| `backend/services/mail/mail_reply_generator.py` | **CREATE** (Phase 4) | AI Reply Generation |
| `backend/services/mail/mail_memory.py` | **CREATE** (Phase 5) | Memory-Mirror analog calendar_memory.py |
| `backend/api/routers/mail.py` | **CREATE** | REST-Endpoints: threads, send, reply, ai/analyze, ai/reply |
| `frontend/js/mail-modal.js` | **CREATE** | Haupt-UI: Modal, Inbox-View, Thread-View, AI Panel |
| `frontend/css/mail-modal.css` | **CREATE** | Mail-spezifische Styles |
| `frontend/index.html` | **MODIFY** | Mail Modal DOM-Container + Dock-Button |
| `frontend/js/modal-api.js` | **MODIFY** | RENDERER_MAP + DOCK_HOST_ELEMENT_IDS um "mail" erweitern |
| `frontend/js/dock.js` | **MODIFY** | Mail-Icon in Dock-Bar registrieren |
| `frontend/js/window-state.js` | **MODIFY** | Mail-Modul als Dock-Module registrieren |
| `backend/main.py` | **MODIFY** | Router-Registrierung für /api/mail |
| `backend/tests/test_mail_service.py` | **CREATE** | Service + API Tests |
| `backend/tests/test_mail_ai.py` | **CREATE** (Phase 3) | AI-Engine Tests |

## Nicht anfassen ohne expliziten Grund

- `backend/tools/gmail_tools.py` — Production-Code. Service Layer wrappt, nicht modifizieren.
- `backend/services/chat_orchestrator.py` — Erst in Phase 5 (Memory Mirror) minimal berühren.
- `backend/llm_providers/*/service.py` — Keine Provider-Mutation.
- `backend/config/model_routing.json` — Kein Touch.
- `backend/skills/communication/*.json` — Bestehende Skills bleiben für Chat-basierte Tool-Calls.
- `backend/tools/calendar_tools.py` — Kein Touch.
- `backend/services/calendar/*` — Kein Touch.

---

# 10 UI / UX Specification

## Modal Layout

```text
┌──────────────────────────────────────────────────────┐
│ Header: "Mail" │ Smart View Tabs │ Sync Status │ ⟳   │
├──────────────┬───────────────────────────────────────┤
│ Thread-Liste │ Thread Detail                         │
│              │ ┌───────────────────────────────────┐ │
│ ┌──────────┐ │ │ Message 1 (collapsed)             │ │
│ │ Thread 1 │ │ │ Message 2 (collapsed)             │ │
│ │ ★ Prio   │ │ │ Message 3 (expanded, latest)      │ │
│ │ Snippet  │ │ │                                   │ │
│ ├──────────┤ │ ├───────────────────────────────────┤ │
│ │ Thread 2 │ │ │ AI Panel                          │ │
│ │ · normal │ │ │ Summary: ...                      │ │
│ │ Snippet  │ │ │ Intent: Anfrage                   │ │
│ ├──────────┤ │ │ Actions: [Antworten] [Archivieren]│ │
│ │ ...      │ │ │ Priority: ████░░ 0.7              │ │
│ └──────────┘ │ └───────────────────────────────────┘ │
├──────────────┴───────────────────────────────────────┤
│ Quick Reply │ AI Command: "Kurz zusagen"   │ [Send]  │
└──────────────────────────────────────────────────────┘
```

## Smart View Tabs

- **Alle** — Alle Threads chronologisch
- **Antwort nötig** — status == "needs_reply"
- **Wartend** — status == "waiting"
- **Wichtig** — priority_score >= 0.7
- **Erledigt** — status == "done"

## Thread-Liste (linke Spalte)

- Thread-Card: Absender, Betreff, Snippet, Zeitstempel
- Visuelles Priority-Indikator (farbiger linker Rand)
- Ungelesen-Indikator (fetter Text)
- AI-Badge: Intent-Icon (Brief, Kalender, Info, etc.)

## Thread Detail (rechte Spalte)

- Chronologische Nachrichten, neueste unten
- Collapsed by default, letzte expanded
- From/To/CC Header pro Nachricht
- HTML-Body (sanitized mit DOMPurify) oder Text-Fallback
- Attachment-Liste mit Download-Links (future)

## AI Panel (unterhalb Thread Detail)

- Summary (1-2 Sätze)
- Intent-Badge
- Priority-Bar (visuell)
- Actionables als klickbare Chips
- "AI Antwort generieren" Button

## Composer (Footer)

- Quick-Reply Input (einzeilig, Enter = Send)
- AI Command Input ("Kurz zusagen", "Formal ablehnen")
- Full Composer (Toggle): To, CC, Subject, Body, Attachment
- AI Rewrite Button im Full Composer

---

# 11 MCL/Dock Integration Contract

## Registration in modal-api.js

```javascript
export const RENDERER_MAP = Object.freeze({
  // ... existing entries ...
  mail: "mail",
});
```

## Registration in DOCK_HOST_ELEMENT_IDS

```javascript
const DOCK_HOST_ELEMENT_IDS = Object.freeze({
  // ... existing entries ...
  mail: "mail-modal",
});
```

## Dock Button

- Icon: Mail-SVG (Lucide `mail` icon, konsistent mit bestehendem Icon-Set)
- Position: In der Dock-Bar neben Calendar
- Click → `dockOpen("mail")`
- Badge: Unread-Count auf dem Icon (future Phase)

---

# 12 Implementation Phases

## Phase 1 — Mail Service Layer + Basic API (Backend-Fundament)
**CU: 4**

**Ziel:** Backend-Infrastruktur: Service Layer wrappt gmail_tools.py, Thread-Auflösung, REST-Endpoints.

- [ ] `backend/data/schemas_mail.py` — Pydantic-Modelle: MailParticipant, JanusMailMessage, JanusMailThread, MailAIMetadata (Stub), API Request/Response Schemas.
- [ ] `backend/services/mail/__init__.py` — Package-Init.
- [ ] `backend/services/mail/mail_service.py` — Service Layer:
  - `list_threads(max_results, query, label)` → wrappt `get_latest_emails()`, gruppiert nach threadId
  - `get_thread(thread_id)` → lädt alle Messages eines Threads, normalisiert zu JanusMailThread
  - `send_mail(to, subject, body, attachment)` → wrappt `send_email()`
  - `reply_to_thread(thread_id, body)` → Reply-Logik (In-Reply-To Header)
  - `_normalize_gmail_message(raw_msg)` → Gmail-Format → JanusMailMessage
  - `_resolve_participants(headers)` → Header-Parsing für From/To/CC
- [ ] `backend/api/routers/mail.py` — REST-Endpoints:
  - `GET /api/mail/threads` — Thread-Liste
  - `GET /api/mail/threads/{thread_id}` — Thread Detail
  - `POST /api/mail/send` — Neue Mail senden
  - `POST /api/mail/reply` — Thread-Reply
  - `GET /api/mail/sync/status` — Sync Health
- [ ] `backend/main.py` — Router-Registrierung: `app.include_router(mail_router, prefix="/api/mail")`
- [ ] `backend/tests/test_mail_service.py` — Tests:
  - `test_normalize_gmail_message()` — Gmail-Format → JanusMailMessage korrekt
  - `test_list_threads_endpoint()` — GET /threads liefert Daten
  - `test_get_thread_detail()` — GET /threads/{id} liefert Messages
  - `test_send_mail_endpoint()` — POST /send ruft gmail_tools auf
  - `test_reply_endpoint()` — POST /reply mit thread_id

**Completion Gate:** API-Endpoints erreichbar, Gmail-Daten korrekt normalisiert, Tests grün.

---

## Phase 2 — Mail Modal UI (Frontend-Grundgerüst)
**CU: 5**

**Ziel:** Mail-Modal im Dock sichtbar, Thread-Liste anzeigen, Thread-Detail lesbar.

- [ ] `frontend/index.html` — `<div id="mail-modal">` Container mit Header, Split-View, Footer.
- [ ] `frontend/js/mail-modal.js` — Modal-Grundstruktur:
  - Thread-Liste (linke Spalte) mit Lazy Loading
  - Thread-Detail (rechte Spalte) mit Message-Rendering
  - Header mit Tabs-Platzhalter und Sync-Status
  - Footer mit Quick-Reply Input
  - Event-basierte Kommunikation (CustomEvents)
- [ ] `frontend/css/mail-modal.css` — Styling:
  - Split-View Layout (30% Liste / 70% Detail)
  - Thread-Cards mit Priority-Indikator
  - Message-Bubbles mit Collapsed/Expanded State
  - Responsive Design
- [ ] `frontend/js/modal-api.js` — RENDERER_MAP und DOCK_HOST_ELEMENT_IDS um "mail" erweitern.
- [ ] `frontend/js/dock.js` — Mail-Icon in Dock-Bar.
- [ ] `frontend/js/window-state.js` — Mail-Modul als Dock-Module registrieren.
- [ ] Thread-Liste: Click → lädt Thread-Detail via API
- [ ] Thread-Detail: Messages chronologisch, letzte expanded
- [ ] HTML-Body: Sanitized mit DOMPurify, Text-Fallback
- [ ] Quick Reply: Einzeiliges Input, Enter → POST /api/mail/reply
- [ ] Send: "Neue Mail" Button → Minimal-Composer (To, Subject, Body)

**Completion Gate:** Modal öffnet über Dock, Thread-Liste zeigt Mails, Thread-Detail zeigt Konversation, Quick Reply funktioniert.

---

## Phase 3 — AI-Analyse-Engine (Intelligence Layer)
**CU: 5**

**Ziel:** Jede Mail/Thread wird KI-analysiert: Summary, Intent, Priority, Actionables.

- [ ] `backend/services/mail/mail_ai_engine.py` — AI Engine:
  - `analyze_thread(thread: JanusMailThread) → MailAIMetadata`
  - System Prompt (siehe Abschnitt 8)
  - Context Builder: Letzte 5 Messages + Participants + Labels
  - JSON-Parser mit Code-Fence-Stripping (analog calendar_ai_engine.py)
  - LLM-Call über bestehenden `llm_gateway`
  - Caching: AI-Ergebnisse pro Thread-ID + last_updated (kein Re-Analyse wenn unverändert)
  - Fallback bei LLM-Fehler: Default-MailAIMetadata
- [ ] `backend/api/routers/mail.py` — Neuer Endpoint:
  - `POST /api/mail/ai/analyze` — On-demand AI-Analyse
- [ ] Backend: Batch-Analyse — Bei `GET /threads` optional AI-Metadaten für Top-N mitliefern
- [ ] Frontend: AI Panel im Thread-Detail:
  - Summary anzeigen
  - Intent-Badge (farbig)
  - Priority-Bar (visuell, 0.0-1.0)
  - Actionables als Chips
  - "Analysieren" Button (falls noch kein AI-Result)
- [ ] Frontend: Thread-Liste AI-Enrichment:
  - Priority-Farbe am linken Rand (rot/orange/grün)
  - Intent-Icon neben Betreff
  - Status-Badge ("Antwort nötig", "Wartend")
- [ ] `backend/tests/test_mail_ai.py` — Tests:
  - `test_analyze_returns_valid_metadata()` — Output ist valide MailAIMetadata
  - `test_analyze_caching()` — Zweiter Call nutzt Cache
  - `test_analyze_fallback()` — LLM-Fehler → Default-Metadata
  - `test_intent_classification()` — Bekannte Mails → korrekte Intents

**Completion Gate:** AI-Panel zeigt Analyse, Thread-Liste hat Priority-Indikatoren, Caching funktioniert.

---

## Phase 4 — AI Reply Generator + Smart Views
**CU: 5**

**Ziel:** KI-generierte Antworten mit User-Confirmation, Smart-View-Tabs.

- [ ] `backend/services/mail/mail_reply_generator.py` — Reply Generator:
  - `generate_reply(thread, instruction, tone, language) → MailAIReplyResponse`
  - System Prompt (siehe Abschnitt 8)
  - Context: Vollständiger Thread + User-Instruction
  - Tone-Control: formal / casual / brief / detailed
  - Language-Default: Deutsch
  - LLM-Call über llm_gateway
- [ ] `backend/api/routers/mail.py` — Neuer Endpoint:
  - `POST /api/mail/ai/reply` — AI-Antwort generieren
- [ ] Frontend: AI Reply Flow:
  - "AI Antwort" Button im AI Panel → Instruction-Input
  - Vorschläge: "Kurz zusagen", "Formal ablehnen", "Mehr Infos erfragen", "Termin bestätigen"
  - Preview: Generierter Text in Composer-Bereich
  - User kann editieren → dann senden
  - Kein Auto-Send ohne User-Confirmation
- [ ] Frontend: Smart View Tabs:
  - Tab-Leiste im Header: Alle | Antwort nötig | Wartend | Wichtig | Erledigt
  - Filter basiert auf MailAIMetadata.status und priority_score
  - Tabs laden Daten mit entsprechenden Query-Parametern
  - Tab-Counter (Anzahl Threads pro View)
- [ ] Frontend: Composer-Verbesserungen:
  - Full Composer Toggle (To, CC, Subject, Body)
  - AI Rewrite Button ("Formaler", "Kürzer", "Freundlicher")
  - Attachment-Hinweis (Upload-Pfad eingeben, analog bestehender send_email)
- [ ] Tests:
  - `test_reply_generation()` — AI generiert validen Text
  - `test_reply_tone_control()` — Tone beeinflusst Output
  - `test_smart_view_filtering()` — Korrekte Thread-Filterung

**Completion Gate:** AI-Reply funktioniert E2E (Instruction → Preview → Edit → Send), Smart Views filtern korrekt.

---

## Phase 5 — Mail Memory Mirror + Orchestrator-Integration
**CU: 4**

**Ziel:** Janus kann Mail-Kontext im Chat nutzen, proaktive Hinweise zu offenen Mails.

- [ ] `backend/services/mail/mail_memory.py` — Memory Mirror (analog calendar_memory.py):
  - `build_mail_snapshot()` → Kompakter Snapshot der letzten ungelesenen/wichtigen Mails
  - Snapshot-Format: Top-5 Threads mit Summary, Priority, Status
  - Upsert als Memory-Eintrag (category="mail_snapshot")
  - Derived Summary: "3 Mails brauchen Antwort, 1 Meeting-Anfrage"
- [ ] `backend/api/routers/mail.py` — Neuer Endpoint:
  - `GET /api/mail/sync/memory` — Memory-Snapshot aktualisieren
- [ ] `backend/services/chat_orchestrator.py` — Minimale Integration:
  - Bei Mail-/Kommunikations-Signalen im Chat: Mail-Snapshot injizieren
  - Analog zur Calendar-Memory-Injection
  - Proaktive Hinweise (optional, Feature-Flag `JANUS_MAIL_PROACTIVE_HINTS`)
- [ ] Frontend: Mail-Badge auf Dock-Icon (Unread-Count)
- [ ] Frontend: Mail-Tages-Widget (analog calendar-day-widget):
  - Kompakte Übersicht: "3 unbeantwortet, 1 wichtig"
  - Click → öffnet Mail-Modal
- [ ] Tests:
  - `test_mail_snapshot_build()` — Snapshot enthält korrekte Daten
  - `test_mail_memory_upsert()` — Memory-Eintrag wird gespeichert
  - `test_orchestrator_injection()` — Chat-Kontext enthält Mail-Snapshot bei Trigger

**Completion Gate:** Chat kennt Mail-Kontext, Dock-Badge zeigt Unread-Count, Memory-Mirror stabil.

---

## Phase 6 — Polish + Performance (Future)
**CU: 5 (optional, nicht MVP-kritisch)**

**Ziel:** UX-Feinschliff, Performance-Optimierung, erweiterte Features.

- [ ] Pagination: Infinite Scroll in Thread-Liste
- [ ] Delta-Sync: Polling alle 60s für neue Mails
- [ ] Mail-Search: Semantic Search über Mail-Inhalte
- [ ] Label-Management: Labels zuweisen/entfernen
- [ ] Keyboard Navigation: Shortcuts (j/k = Thread wechseln, r = Reply, a = Archive)
- [ ] Mail-Notifications: Desktop-Notifications bei neuen wichtigen Mails
- [ ] Performance: Virtualisiertes Rendering für 100+ Threads
- [ ] Accessibility: ARIA-Labels, Screenreader
- [ ] IMAP-Provider-Abstraktion (Vorbereitung für Multi-Provider)

**Completion Gate:** Smooth UX, <300ms Modal-Öffnung, <500ms Thread-Liste.

---

# 13 Acceptance Criteria

## Must-have (Phase 1-2)

- [ ] Mail Modal öffnet über Dock-Bar.
- [ ] Thread-Liste zeigt Gmail-Threads korrekt.
- [ ] Thread-Detail zeigt Konversation chronologisch.
- [ ] Quick Reply funktioniert (Text → Send → Gmail).
- [ ] Neue Mail senden funktioniert.
- [ ] HTML-Mails werden sanitized dargestellt.
- [ ] Modal integriert sich sauber in MCL/Dock-System.

## Should-have (Phase 3-4)

- [ ] AI analysiert Threads (Summary, Intent, Priority).
- [ ] AI generiert Reply-Vorschläge.
- [ ] User kann AI-Reply vor Senden editieren.
- [ ] Smart Views filtern nach Status/Priority.
- [ ] Priority-Indikatoren in Thread-Liste.

## Won't-have in MVP

- [ ] IMAP-/Outlook-Integration.
- [ ] Offline-First Modus.
- [ ] Drag & Drop für Labels.
- [ ] Attachment-Upload (nur Pfad-Eingabe).
- [ ] Automatisches AI-Senden ohne User-Confirmation.
- [ ] Eigenes Threading (nutzt Gmail threadId).
- [ ] Lokale Mail-Datenbank (Gmail ist Source-of-Truth).

## Forbidden Actions (Must-not)

- [ ] Keine Modifikation von `gmail_tools.py` — Service Layer wrappt.
- [ ] Keine AI-Aktion ohne User-Confirmation.
- [ ] Kein eigenes Fenstersystem — MCL/Dock verwenden.
- [ ] Keine hardcodierten Google-API-Calls im Frontend.
- [ ] Kein localStorage für Mail-Daten — Mails kommen immer vom Backend.
- [ ] Keine eigene OAuth2-Implementierung — bestehenden Flow nutzen.
- [ ] Kein Multi-Provider in Phase 1-4 — Gmail only.

---

# 14 Test Plan

## Unit Tests (Backend)

- `test_normalize_gmail_message()` — Gmail-Format → JanusMailMessage korrekt
- `test_resolve_participants()` — Header-Parsing für From/To/CC
- `test_thread_grouping()` — Messages korrekt nach threadId gruppiert
- `test_list_threads_endpoint()` — GET /threads liefert paginierte Daten
- `test_get_thread_detail()` — GET /threads/{id} liefert alle Messages
- `test_send_mail_via_api()` — POST /send ruft gmail_tools.send_email() auf
- `test_reply_via_api()` — POST /reply mit korrektem In-Reply-To
- `test_ai_analyze_valid_output()` — AI Engine liefert valide MailAIMetadata
- `test_ai_analyze_caching()` — Zweiter Call nutzt Cache
- `test_ai_reply_generation()` — Reply Generator liefert Text
- `test_ai_reply_tone()` — Tone-Parameter beeinflusst Output
- `test_smart_view_filter()` — Status-basierte Filterung korrekt
- `test_mail_snapshot()` — Memory Mirror erzeugt korrekten Snapshot

## Integration Tests

- Modal öffnet über Dock → Threads werden geladen
- Thread auswählen → Detail-View zeigt Messages
- Quick Reply → Mail wird gesendet, Thread aktualisiert
- AI Analyse → Panel zeigt Summary + Intent + Priority
- AI Reply → Preview → Edit → Send → Erfolgreich
- Smart View Tabs → Korrekte Filterung
- Memory Mirror → Chat kennt Mail-Kontext

## UI / Manual Verification

- Mail-Icon in Dock-Bar sichtbar und klickbar
- Modal nutzt korrekten Z-Index (über Chat, unter Settings)
- Thread-Cards haben konsistentes Styling
- HTML-Mails werden sicher gerendert (kein XSS)
- AI Panel zeigt korrekte Daten
- Smart View Tabs schalten korrekt um
- Quick Reply Input funktioniert mit Enter-Key
- Composer öffnet/schließt korrekt

---

# 15 Performance Requirements

| Metrik | Ziel |
|---|---|
| Modal-Öffnung | < 300ms |
| Thread-Liste laden (20 Threads) | < 1s |
| Thread-Detail laden | < 500ms |
| AI-Analyse (einzelner Thread) | < 5s |
| AI-Reply-Generation | < 5s |
| Quick Reply Send | < 2s |
| Smart View Switch | < 300ms |

---

# 16 Diamond Guardrails

- Keine Mutation von `gmail_tools.py` — das ist der Production-Kern.
- Keine AI-Mail-Aktion ohne User-Confirmation.
- Keine Mail-Mutation bei API-Fehler — graceful degradation.
- Jede neue Datei muss dem Calendar-Pattern folgen.
- MCL/Dock-Integration muss vollständig sein.
- Alle API-Responses müssen Pydantic-validiert sein.
- Frontend-Code muss vanilla JS sein.
- Mail CSS darf bestehende Styles nicht brechen — eigenes CSS-File.
- Gmail only in MVP — kein Multi-Provider-Code ohne explizite Entscheidung.
- HTML-Mail-Rendering MUSS DOMPurify nutzen (XSS-Schutz).
- AI-Kosten im Blick: Keine Batch-Analyse aller Mails ohne User-Trigger.

---

# 17 Abhängigkeiten & Voraussetzungen

| Abhängigkeit | Status | Blocker? |
|---|---|---|
| Google OAuth2 funktioniert | ✅ Production (calendar + gmail) | Nein |
| gmail_tools.py production-ready | ✅ Production | Nein |
| MCL/Dock-System stabil | ✅ Production (Calendar nutzt es) | Nein |
| LLM Gateway verfügbar | ✅ Production | Nein |
| Calendar Module als Pattern-Referenz | ✅ SEALED | Nein |
| DOMPurify im Frontend | ✅ Vorhanden (package.json) | Nein |
| Memory System (für Phase 5) | ✅ Production | Nein |
| TASK-059 Calendar Memory (Pattern-Ref) | ✅ V1 Complete | Nein |

**Fazit:** Keine Blocker. Alle Voraussetzungen sind erfüllt.

---

# 18 Vergleich: Original-Dossier vs. Diamond-Plan

| Aspekt | Original-Dossier | Diamond-Plan |
|---|---|---|
| Tech-Stack | TypeScript (.ts) | Python + Vanilla JS |
| Bestehende Infrastruktur | Ignoriert | gmail_tools.py als Basis |
| Provider-Strategie | Gmail + IMAP + Outlook sofort | Gmail only, Multi-Provider future |
| Storage | Eigene SQLite + IndexedDB | Gmail als Source-of-Truth, kein lokales Storage |
| Threading | Eigenes Thread-System | Gmail threadId |
| UI-Framework | Unspezifiziert | MCL/Dock (Vanilla JS) |
| AI-Integration | Eigene AI-Module | LLM Gateway + bestehende Infrastruktur |
| Phasen | "Build Order" (9 Punkte) | 6 Diamond-Phasen mit CUs und Gates |
| File Impact | Keine Analyse | 15+ Dateien spezifiziert |
| Tests | Generischer Playwright | Unit + Integration + Manual |
| Guardrails | Keine | 11 explizite Regeln |
| Risiken | Keine Analyse | 6 Risiken mit Mitigation |
| Scope | Vollständiger Mailclient | Fokussiertes AI-Mail-Modul |

---

# 19 AI Studio Orchestration Plan

## Triage-Einschätzung

| Feld | Wert |
|---|---|
| Geschätzte Dateien | 12-16 (neu) + 4 (modify) |
| Schema-Touch | Ja (neue Pydantic-Modelle) |
| Provider-Touch | Nein (nutzt bestehende gmail_tools.py) |
| Breaking-Change-Risiko | Niedrig (rein additiv) |
| CU Gesamt | 28 |
| Empfehlung | Phase 1-2 zusammen → Review → Phase 3 → Review → Phase 4-5 |

## Empfohlene Reihenfolge

1. **Phase 1+2** parallel planen (Backend + Frontend Grundgerüst) → **CU 9**
2. **SWE Review** nach Phase 2 (API + UI funktional)
3. **Phase 3** (AI Engine) → **CU 5**
4. **SWE Review** nach Phase 3 (AI korrekt)
5. **Phase 4** (Reply Gen + Smart Views) → **CU 5**
6. **Phase 5** (Memory Mirror) → **CU 4**
7. **Final Review + Sealing**

---

# 20 Success Definition

TASK-060 ist Diamond-fertig, wenn Janus ein Mail-Modal hat, das:

- Über die Dock-Bar geöffnet wird und sich ins MCL-System integriert.
- Gmail-Threads in einer Thread-Liste mit AI-Enrichment anzeigt.
- Thread-Detail mit chronologischer Konversation und AI-Panel darstellt.
- AI-gesteuerte Analyse (Summary, Intent, Priority, Actions) pro Thread bietet.
- AI-generierte Antworten mit User-Confirmation unterstützt.
- Smart Views für Status-basierte Filterung hat.
- Mail-Kontext über Memory Mirror in den Chat injizieren kann.
- Auf den bestehenden `gmail_tools.py`-Funktionen aufbaut, ohne sie zu verändern.

**Final Claim:**

> Janus gibt dir die Kontrolle über deine E-Mails — intelligent priorisiert, KI-analysiert und handlungsorientiert.
