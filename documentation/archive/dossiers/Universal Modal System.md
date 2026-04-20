FEATURE 13 (REFACTORED): UNIVERSAL MODAL SYSTEM (UI RUNTIME ENGINE)
🧠 1. Ziel des Systems

Das Universal Modal System ist die UI-Runtime-Engine von Janus, die alle visuellen Inhalte (Videos, Bilder, PDFs, Tools, etc.) als einheitliche Fenster verarbeitet.

👉 Es ist ausschließlich für:

Rendering
Window Management
User Interaction

zuständig.

💥 Core Value

💎 „Ein einziges Window-System für alle visuellen Inhalte – unabhängig vom Feature.“

🧱 2. ARCHITEKTURPOSITION (FINAL)
System Stack
[ Skills / AI Logic ]
        ↓
[ MCL – Modal API Layer ]
        ↓
💎 Universal Modal System (THIS)
        ↓
[ Renderers ]
        ↓
[ UI Output ]
🧠 3. KLARE ABGRENZUNG
❌ Universal Modal System DARF NICHT:
keine API Entscheidungen treffen
keine Skill Logik enthalten
keine Routing-Entscheidungen machen
keine Business Logik enthalten
✅ Universal Modal System DARF:
Modals rendern
Fenster verwalten
User Interactions verarbeiten
State anzeigen
Animationen steuern
🧩 4. KERNPRINZIPIEN
🧠 1. Pure Rendering Layer

UI reagiert nur auf MCL-Instruktionen

🔄 2. Stateless Logic (extern verwaltet)
State kommt aus MCL / Store
UI ist nur Darstellungsschicht
🧱 3. Window = Primitive Unit

Alles ist ein Window:

Video
Image
PDF
Tool
Gallery
📌 4. Consistent UX Layer

Alle Fenster haben:

Drag
Resize
Minimize
Pin (Taskbar)
⚙️ 5. CORE COMPONENTS
🪟 Modal Container
Root Window Element
handles layout + layering
🎬 Renderer Host
Modal → renders Content Renderer
📦 Window Manager
z-index control
positioning
resizing
📌 Taskbar Bridge
pinned modals
minimized state handling
🔁 6. SYSTEM FLOW (FINAL)
User Intent
   ↓
Skill executes
   ↓
MCL creates modal request
   ↓
Universal Modal System receives instruction
   ↓
Window created
   ↓
Renderer attached
   ↓
User interacts
   ↓
State update → back to MCL
🎨 7. WINDOW STATE MODEL
{
  "modal_id": "string",
  "type": "video | image | pdf | tool | custom",
  "state": "open | minimized | pinned | closed",
  "position": { "x": 120, "y": 80 },
  "size": { "w": 900, "h": 600 },
  "z_index": 5
}
🖥️ 8. RENDERING SYSTEM
Renderer Mapping kommt NICHT hier rein

👉 kommt ausschließlich aus MCL

Universal Modal System macht nur:
Receive → Attach Renderer → Display
📌 9. TASKBAR INTEGRATION
Verhalten:
minimierte Modals → Taskbar Icon
pinned Modals → persistent
restore → full window state
Taskbar Item:
{
  "modal_id": "abc",
  "label": "YouTube Video",
  "type": "video",
  "state": "pinned"
}
⚠️ 10. EDGE CASE HANDLING
❗ Multiple Windows

→ z-index manager

❗ Resize Conflicts

→ constraint system

❗ Lost Window State

→ restore session fallback

❗ Renderer Missing

→ fallback UI screen

🔐 11. SAFETY & STABILITY
no direct skill access
no API calls
no business logic
deterministic rendering only
🚀 12. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1:
Basic modal window open/close
Phase 2:
drag + resize + state sync
Phase 3:
renderer mounting system
Phase 4:
taskbar integration
Phase 5:
multi-window persistence
🧠💎 13. SYSTEM-DEFINITION

💎 Das Universal Modal System ist die reine UI-Ausführungsschicht von Janus.

💎 FINAL RESULT (ARCHITEKTUR-KORREKT)
Vorher (falsch gedacht):
Video Feature hat eigenes Modal
Image Feature hat eigenes Modal
Chaos entsteht
Jetzt (korrekt):
MCL entscheidet
Universal Modal System rendert
Skills bleiben sauber

💎 „Ein System. Viele Inhalte. Keine Duplikate.“