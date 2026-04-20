ARCHITECTURE DOSSIER: MODAL API LAYER (MCL) – JANUS SYSTEM CONTRACT
🧠 1. Ziel des Systems

Der Modal API Layer (MCL) ist die zentrale Kommunikationsschnittstelle zwischen Skills, AI-Logik und dem Universal Modal System.

Er definiert:

💎 Wie Inhalte systematisch in Modals überführt, gesteuert und zurückgeführt werden.

💥 Core Value

💎 „Kein Feature spricht direkt mit UI — alles geht durch einen klaren, stabilen Contract Layer.“

🧱 2. ARCHITEKTURPOSITION
System Layer Stack
[ Skills / AI Logic ]
        ↓
💎 MCL (Modal API Layer)
        ↓
[ Universal Modal System ]
        ↓
[ Renderers (Video / Image / PDF / Tools) ]
        ↓
[ UI Runtime ]
🧠 3. PROBLEM, DAS GELÖST WIRD
❌ Ohne MCL:
Skills öffnen direkt Modals
jedes Feature implementiert UI-Logik selbst
keine Standardisierung
hohe Kopplung zwischen AI & UI
❌ Folgen:
schwer skalierbar
inkonsistente UX
doppelte Logik
hohe technische Schulden
✅ Mit MCL:

💎 Alle Features sprechen eine einheitliche API-Sprache

🧩 4. KERNPRINZIPIEN
🧠 1. Separation of Concerns
Skills = Entscheidung & Daten
MCL = Übersetzung & Routing
Modal System = Rendering
🔒 2. Strict Contract Enforcement
nur validierte Modal Requests erlaubt
kein direkter UI-Zugriff aus Skills
🔄 3. Bidirectional State Flow
Modal → System → Skill Context Update
🧱 4. Renderer Abstraction
Content ist entkoppelt von Darstellung
⚙️ 5. CORE API DESIGN
📤 OPEN MODAL REQUEST
{
  "action": "open_modal",
  "type": "video | image | pdf | tool | custom",
  "payload": {
    "source": "youtube",
    "url": "...",
    "title": "..."
  },
  "options": {
    "draggable": true,
    "resizable": true,
    "start_state": "open"
  }
}
📌 UPDATE MODAL STATE
{
  "action": "update_modal",
  "modal_id": "string",
  "state": {
    "position": { "x": 0, "y": 0 },
    "size": { "w": 800, "h": 600 },
    "status": "open | minimized | pinned"
  }
}
❌ CLOSE MODAL
{
  "action": "close_modal",
  "modal_id": "string"
}
🔁 SYNC BACK TO SKILL CONTEXT
{
  "action": "modal_event",
  "event": "closed | pinned | interacted",
  "modal_id": "string",
  "context": {}
}
🧠 6. VALIDATION LAYER
MCL prüft:
type exists
payload valid
renderer available
no illegal UI bypass
❗ Invalid Request Handling:

→ fallback:

"unsupported_modal_request"
🎯 7. ROUTING LOGIK
MCL entscheidet:
type → renderer mapping

Beispiel:

Type	Renderer
video	VideoRenderer
image	ImageRenderer
pdf	PDFRenderer
tool	ToolRenderer
🖥️ 8. INTEGRATION MIT UNIVERSAL MODAL SYSTEM
MCL ist NICHT UI

Es:

erzeugt Modal Requests
verwaltet State
validiert Struktur

👉 Universal Modal System:

rendert
zeigt UI
verwaltet Window Behavior
📌 9. SKILL INTEGRATION (EXTREM WICHTIG)
Skill spricht NICHT UI direkt
❌ falsch:

Skill → Modal Component

✅ richtig:

Skill → MCL → Modal System

Beispiel Flow:
User Intent
   ↓
Video Skill
   ↓
MCL.open_modal()
   ↓
Universal Modal System
   ↓
Video Renderer
🔄 10. EVENT SYSTEM
MCL emittiert Events:
modal_opened
modal_closed
modal_pinned
modal_resized
Events gehen zurück an:
Skill Context
Task System
State Store
⚠️ 11. EDGE CASES
❗ Invalid Payload

→ reject + fallback response

❗ Missing Renderer

→ fallback renderer (error view)

❗ Multiple Modals Conflict

→ z-index resolver

❗ State desync

→ authoritative store sync

🔐 12. SAFETY RULES
Skills dürfen UI nicht direkt manipulieren
alle UI Änderungen laufen durch MCL
keine bypass calls erlaubt
🚀 13. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1:
Basic open_modal API
Phase 2:
State updates + close handling
Phase 3:
Renderer routing
Phase 4:
Event system
Phase 5:
Full Skill Integration
🧠💎 14. SYSTEM-DEFINITION

💎 MCL ist das Übersetzungs- und Kontrollsystem zwischen AI-Logik und UI-Runtime.

💎 FINAL FAZIT

Mit MCL erreichst du:

❌ keine UI-Logik in Skills
❌ keine direkte Modal-Kopplung
❌ keine Feature-UI-Silos

💎 „Alle visuellen Aktionen werden zu kontrollierten, validierten System-Events.“

👉 MCL ist das Nervensystem zwischen Denken (AI) und Sehen (UI)