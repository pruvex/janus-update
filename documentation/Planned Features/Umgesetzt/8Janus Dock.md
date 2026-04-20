Perfekt — jetzt kommt der Abschluss der UX-Architektur. Das ist das Feature, das dein System endgültig von „Chat-App mit Extras“ zu einem modularen AI-Desktop (OS-Layer) hebt.

📁 Feature-Dossier 8: Modul Taskleiste (Janus Dock System)
🧠 Feature Name

Janus Dock / Module Taskbar System

🎯 Ziel des Features

Eine zentrale Taskleiste innerhalb der App, mit der der User:

Module öffnen / schließen kann
parallel zu Chats arbeiten kann
Workspaces (Image, PDF, Widgets, Tools) verwaltet

👉 ohne den Chat-Kontext zu verlieren

💎 Kernprinzip

Chats sind das Denken — Module sind die Werkzeuge.

🧱 Funktionale Anforderungen
1. Fixed Bottom Dock
┌───────────────────────────────┐
│        Workspace Area         │
│  (Dual Chat Windows A / B)    │
├───────────────────────────────┤
│  🧠 💬 🖼️ 📄 📊 ⚙️           │  ← Taskleiste
└───────────────────────────────┘
2. Module Slots

Standard Module:

🧠 Memory / Context View
💬 Chat Tools
🖼️ Image Studio
📄 PDF Viewer
📊 Widgets
⚙️ Settings / Debug
3. Dock Behavior

Jedes Icon:

toggle open/close
state persists pro session
kann minimiert bleiben
4. Floating Panels

Module öffnen sich als:

draggable panels
docked or floating
minimizable
5. Multi-Module Support

👉 mehrere Module gleichzeitig möglich

Beispiel:

Chat links
Image Studio rechts
PDF unten
🧠 State Model Erweiterung
{
  "dock": {
    "openModules": {
      "imageStudio": true,
      "pdfViewer": false,
      "widgets": true
    }
  }
}
🎨 UI/UX Anforderungen
1. Clean Minimal Dock
icons only
hover labels optional
2. Active State
🖼️ active → highlighted
3. Module Preview Indicator
small dot if module has active content
4. Drag & Positioning
panels frei verschiebbar
snap optional (grid / edges)
5. Z-Index System
Chat windows = base layer
Modules = overlay layer
⚠️ Edge Cases
1. Too many modules open

👉 Lösung:

collapse inactive modules into tray
2. Module overlaps chat
chat always interactive unless locked
3. Performance load
lazy-load modules
unload hidden modules
4. State reset
dock state persists per workspace session
🚫 Nicht Teil dieses Features
Chat system logic (Features 1–7)
Memory system internals
AI routing
🧩 Technischer Umsetzungsvorschlag
Dock Component:
function Dock({ modules, toggleModule }) {
  return (
    <div className="dock">
      {modules.map(m => (
        <DockIcon
          key={m.id}
          active={m.active}
          onClick={() => toggleModule(m.id)}
        />
      ))}
    </div>
  );
}
Module Manager:
function toggleModule(id) {
  setDockState(prev => ({
    ...prev,
    openModules: {
      ...prev.openModules,
      [id]: !prev.openModules[id]
    }
  }));
}
Panel System:
function ModulePanel({ id, children }) {
  return (
    <div className="floating-panel">
      {children}
    </div>
  );
}
🧪 Testfälle (QA / Playwright)
Test 1:
Dock Icon klicken
→ Modul öffnet sich
Test 2:
Modul schließen
→ verschwindet korrekt
Test 3:
mehrere Module öffnen
→ keine UI-Kollision
Test 4:
Chat + Module parallel
→ beide interaktiv
Test 5:
Reload Session
→ Dock State wird restored
💎 Erwartetes Ergebnis
echtes „AI Operating System Feeling“
Chats + Tools + Visuals in einem Raum
maximale Produktivität ohne Kontextwechsel
🔥 Warum dieses Feature der Abschluss ist

Ohne das:

❌ System bleibt Chat-App mit Extra Panels

Mit dem:

👉 echtes modulares Desktop-AI-System (Janus OS Layer)

🧠 Gesamtbild nach 1–8

Du hast jetzt:

2-Chat Workspace
Visual State System
direkte Chat-Steuerung
modulare Tool Layer
OS-artige UX Struktur