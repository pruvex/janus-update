anus / Pruki AI OS — Diamond UX System v1.0
💎 0. SYSTEM-DEFINITION
Ziel

Ein modulares AI-Arbeitsbetriebssystem, bestehend aus:

2 parallelen Chat-Workspaces
globalem Kontext-Mapping
direkter Chat-Steuerung
modularem Tool-Dock
synchronisiertem State-System
Grundprinzip

Chat = Denken
Fenster = Kontext
Dock = Tools
UI = Echtzeit-Abbild des Systems

🧱 1. GESAMTARCHITEKTUR (HIGH LEVEL)
┌──────────────────────────────────────────────┐
│              MODULE DOCK (Feature 8)         │
├──────────────────────────────────────────────┤
│  WINDOW A              │     WINDOW B        │
│  (Chat Context A)      │   (Chat Context B)  │
│  (Feature 7)           │   (Feature 7)       │
├──────────────────────────────────────────────┤
│   ACTIVE CHAT BAR (Feature 4)               │
├──────────────────────────────────────────────┤
│   CHAT LIST + STATE INDICATORS (5)          │
├──────────────────────────────────────────────┤
│   INPUT / ACTIONS (Feature 6)               │
└──────────────────────────────────────────────┘
🔄 2. DATA FLOW ARCHITECTURE
🧠 Central State Store (Single Source of Truth)
{
  "activeWindowId": "A",
  "windows": {
    "A": { "active_chat_id": "chat_123" },
    "B": { "active_chat_id": "chat_456" }
  },
  "dock": {
    "openModules": {
      "imageStudio": true,
      "pdfViewer": false
    }
  },
  "chatStates": {
    "chat_123": { "inA": true, "inB": false },
    "chat_456": { "inA": false, "inB": true }
  }
}
🔁 Flow Prinzip
User Action
   ↓
Chat Action Layer (Feature 6)
   ↓
State Update (Central Store)
   ↓
UI Re-render (All Features)
   ↓
Active Bar + Chatlist + Windows + Dock sync
🧠 3. FEATURE INTERAKTIONEN (KRITISCH)
🔵 Feature 3 → Feature 4
Active Window bestimmt Active Chat Bar
🟣 Feature 4 → Feature 5
Active Bar bestimmt Chatlist Highlight
🟢 Feature 5 → Feature 6
Chatlist Actions manipulieren Window State
🟡 Feature 6 → Feature 7
Chat Actions steuern Dual Window Layout
🟠 Feature 7 → Feature 8
Dock ist unabhängig, aber kontextsensitiv
🧩 4. SYSTEMREGELN (HARD RULES)
RULE 1 — Single Source of Truth

👉 Nur Central State darf UI bestimmen

RULE 2 — Kein UI besitzt eigene Logik
UI = pure representation
RULE 3 — Window Limit Fix
MAX WINDOWS = 2
RULE 4 — Chat ist unabhängig von Fenster
Chat lebt im State, nicht im UI
RULE 5 — Module sind overlay-layer
Dock beeinflusst Chat nicht direkt
⚡ 5. EVENT SYSTEM (CORE ENGINE)
Events
CHAT_OPENED
CHAT_SWITCHED
WINDOW_FOCUSED
MODULE_TOGGLED
CHAT_ASSIGNED_TO_WINDOW
Event Flow
Action → Event → State Mutation → UI Sync
🧪 6. MASTER PLAYWRIGHT TEST SUITE
🧪 CATEGORY A — Dual Window
open chat in A
open chat in B
switch focus
duplicate chat
🧪 CATEGORY B — Active Sync
change window → bar updates
change chat → list updates
cross-window consistency
🧪 CATEGORY C — Chatlist Indicators
correct A/B markers
active highlight moves
scroll preservation
🧪 CATEGORY D — Chat Actions
open in A/B
switch window
override existing chat
🧪 CATEGORY E — Dock System
open module
close module
multi-module overlap
persistence after reload
🧪 CATEGORY F — FULL SYSTEM
2 chats + dock + list + bar sync
no desync allowed
no stale state allowed
🔥 7. PERFORMANCE RULES
RULE 1 — No redundant re-renders
only state-driven updates
RULE 2 — Lazy modules
Dock modules loaded on demand
RULE 3 — Chat virtualization
long chats must be virtualized
🧠 8. DESIGN PHILOSOPHY
❌ Old Model
Chat App + Features
✅ New Model

AI Operating System

Core shift:
Layer	Meaning
Chat	Thinking
Window	Context
Dock	Tools
State	Truth
UI	Mirror
💎 9. FINAL ARCHITECTURE INSIGHT
Wichtigster Punkt:

👉 ALLES hängt am State System

Wenn das sauber ist:

UI trivial
Features stabil
keine Bugs zwischen Fenstern
kein Kontextverlust
🚀 10. IMPLEMENTATION ORDER (FINAL)
PHASE 1
Feature 1–2 (Dual Chat Core + Assignment)
PHASE 2
Feature 3–5 (Active System + List Sync)
PHASE 3
Feature 6–7 (Actions + Dual Layout polish)
PHASE 4
Feature 8 (Dock System)
PHASE 5
Full Playwright Regression Suite
🧩 RESULT

Du hast jetzt:

✔ vollständige UX-Architektur
✔ State-Machine Design
✔ Event-System
✔ UI-Hierarchie
✔ Teststrategie
✔ Implementierungsreihenfolge