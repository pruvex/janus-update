JANUS MAIL — COMPLETE SYSTEM DOSSIER (DIAMOND STANDARD)
0. VISION

Janus Mail ist kein Mailclient.

Janus Mail ist:

Ein KI-natives Kommunikationssystem, das E-Mail in strukturierte, priorisierte und handlungsorientierte Wissenseinheiten transformiert.

Ziel:

Weg von „Inbox abarbeiten“
Hin zu „relevante Kommunikation verstehen und entscheiden“
1. CORE PRINCIPLES
1.1 AI-FIRST
Jede Mail wird automatisch analysiert
KI ist integraler Bestandteil jeder Interaktion
Keine „KI als Feature“, sondern KI als Systemebene
1.2 UNIFIED COMMUNICATION MODEL
Alle Provider → ein Datenmodell
Threads → zentrale Einheit
Kommunikation wird normalisiert
1.3 LOCAL-FIRST + SYNC
Lokale Datenbank als Wahrheitsschicht
Provider nur als Datenquelle
Offline-first möglich
1.4 ACTION-ORIENTED UX
Fokus: „Was muss ich tun?“
Nicht: „Welche Mails habe ich?“
2. SYSTEM ARCHITECTURE
2.1 HIGH-LEVEL
Janus Mail
│
├── mail-core
├── provider-layer
├── sync-engine
├── ai-layer
├── storage-layer
└── ui-shell
2.2 MODULE BREAKDOWN
2.2.1 mail-core

Verantwortung:

Normalisierung aller Mails
Thread-Auflösung
Status-Management

Komponenten:

mail-core/
├── mail-normalizer.ts
├── thread-resolver.ts
├── mail-state-machine.ts
└── event-bus.ts
2.2.2 provider-layer
providers/
├── gmail/
├── imap/
├── outlook/
└── smtp/

Interface:

interface MailProvider {
  connect(auth): Promise<void>
  fetchMessages(cursor): Promise<RawMail[]>
  send(mail): Promise<void>
  syncFolders(): Promise<Folder[]>
}
2.2.3 sync-engine
sync-engine/
├── scheduler.ts
├── delta-sync.ts
├── webhook-handler.ts
└── retry-queue.ts

Flow:

Fetch → Normalize → Store → Index → AI → Emit Event
2.2.4 storage-layer

Technologie:

SQLite (Desktop)
IndexedDB (Fallback/Web)

Schema:

tables:
- accounts
- mails
- threads
- attachments
- labels
- ai_metadata
2.2.5 ai-layer
ai/
├── summarizer.ts
├── reply-generator.ts
├── intent-classifier.ts
├── priority-engine.ts
└── action-extractor.ts
2.2.6 ui-shell
ui/
├── inbox/
├── thread/
├── composer/
├── ai-panel/
└── search/
3. CANONICAL DATA MODEL
3.1 MAIL OBJECT
{
  "id": "uuid",
  "accountId": "string",
  "provider": "gmail | imap | outlook",

  "from": { "name": "", "email": "" },
  "to": [],
  "cc": [],

  "subject": "",
  "body": {
    "text": "",
    "html": ""
  },

  "timestamp": 0,
  "threadId": "",

  "labels": [],
  "folder": "inbox",

  "attachments": [],

  "flags": {
    "read": false,
    "starred": false,
    "replied": false
  },

  "ai": {
    "summary": "",
    "intent": "",
    "priorityScore": 0,
    "actionables": [],
    "entities": []
  }
}
3.2 THREAD MODEL
{
  "id": "thread-uuid",
  "mailIds": [],
  "participants": [],
  "lastUpdated": 0,

  "ai": {
    "globalSummary": "",
    "status": "needs_reply | waiting | done",
    "priority": 0.0
  }
}
4. AI SYSTEM DESIGN
4.1 PIPELINE
New Mail →
  Summarize →
  Classify Intent →
  Extract Actions →
  Compute Priority →
  Update Thread
4.2 INTENT TYPES
- request
- information
- meeting
- confirmation
- marketing
- system
4.3 PRIORITY ENGINE

Inputs:

Sender importance
Keywords
Thread history
Response delay
User behavior

Output:

0.0 – 1.0
4.4 ACTION EXTRACTION

Beispiele:

„Antwort erforderlich“
„Termin bestätigen“
„Datei prüfen“
„Entscheidung treffen“
4.5 REPLY GENERATION

Prompt-Struktur:

INPUT:
- Full thread
- Last message
- User style profile

TASK:
Generate reply based on:
- tone
- intent
- brevity level
5. UX & UI DESIGN
5.1 LAYOUT
┌───────────────────────────────┐
│ Global Search + Command Bar   │
├──────────────┬────────────────┤
│ Sidebar      │ Main View      │
│              │                │
│ Accounts     │ Inbox / Thread │
│ Smart Views  │                │
├──────────────┴────────────────┤
│ Contextual AI Panel           │
└───────────────────────────────┘
5.2 SIDEBAR
Accounts
Unified Inbox
Smart Views:
Requires Response
Waiting
High Priority
Meetings
AI Highlights
5.3 INBOX VIEW (THREAD-FIRST)

Thread Card:

Sender
Subject

AI Insight:
→ Wichtig – Antwort erforderlich

Summary:
→ Kunde wartet auf Feedback

Actions:
[Reply] [Summarize] [Task]
5.4 THREAD VIEW

Links:

Chronologische Konversation

Rechts:

AI Panel
5.5 AI PANEL
Summary:
→ Kurzüberblick

Intent:
→ Anfrage

Actionables:
→ Antworten
→ Entscheidung treffen

Suggested Replies:
[Option 1]
[Option 2]
5.6 COMPOSER

Features:

AI rewrite
Tone control
Context awareness

Commands:

„Kurz antworten“
„Ablehnen“
„Mehr Infos erfragen“
5.7 SEARCH
Full-text
Semantic search
Filter:
Sender
Intent
Priority
6. INTERACTION MODEL
6.1 COMMAND BAR (GLOBAL)

User kann schreiben:

„Zeig mir wichtige Mails“
„Antworten die noch offen sind“
„Fasse letzten Thread zusammen“
6.2 ZERO-CLICK ACTIONS

System schlägt automatisch vor:

Reply
Archive
Convert to task
6.3 CONTEXT-AWARE UI

UI passt sich an:

Thread wichtig → größer dargestellt
Unwichtig → minimiert
7. PROVIDER IMPLEMENTATION DETAILS
7.1 GMAIL
OAuth2
Gmail API
Push Notifications (Watch API)
7.2 IMAP
IDLE support
Periodic sync fallback
SMTP für Versand
7.3 OUTLOOK
Microsoft Graph API
Webhook subscriptions
8. SYNC STRATEGY
8.1 DELTA SYNC
Nur Änderungen laden
Cursor-based
8.2 LOCAL CACHE
Alle Threads lokal verfügbar
Schnelle Suche
8.3 CONFLICT RESOLUTION
Server wins für Status
Local override für AI metadata
9. PERFORMANCE DESIGN
Lazy loading Threads
Virtualized lists
Background AI processing
Indexed search
10. SECURITY
OAuth Token Encryption
Local DB encryption
No plaintext credentials
11. PLAYWRIGHT QA STRATEGY
11.1 TEST STRUCTURE
tests/
├── mail-inbox.spec.ts
├── thread-view.spec.ts
├── composer.spec.ts
└── ai-actions.spec.ts
11.2 CORE TEST CASES
Inbox
Threads werden korrekt geladen
Priority sorting funktioniert
Thread
Konversation korrekt dargestellt
AI Panel sichtbar
Composer
AI Reply generiert Text
Send funktioniert
Sync
Neue Mail erscheint automatisch
11.3 EXAMPLE TEST
test("AI reply generation", async ({ page }) => {
  await page.openThread("thread-1")
  await page.click("Generate Reply")

  const text = await page.getReplyText()
  expect(text.length).toBeGreaterThan(10)
})
12. FUTURE EXTENSIONS
Kalenderintegration
Task-System
CRM Layer
Voice interaction
Auto-agents (Mail automatisch beantworten)
13. FINAL SYSTEM DEFINITION

Janus Mail ist:

ein provider-unabhängiger Mail-Core
ein KI-gestütztes Entscheidungs-System
ein lokal-first Kommunikationslayer
ein modulares, erweiterbares System
14. BUILD ORDER (EMPFOHLEN)
Mail Core + Datenmodell
Gmail Provider
Basic UI (Inbox + Thread)
AI Summary
Reply Generator
Smart Views
IMAP Provider
Full AI Layer
Performance Optimierung
15. ABSCHLUSS

Wenn dieses System sauber umgesetzt wird, hast du:

Kein Mailfeature — sondern eine der stärksten Komponenten in ganz Janus.

Das Ding wird:

Produktivität massiv erhöhen
Differenzierung schaffen
die Grundlage für weitere KI-Module bilden

END OF DOSSIER