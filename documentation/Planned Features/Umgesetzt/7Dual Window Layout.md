Dual Window Layout (Split Workspace Engine)

🎯 Ziel des Features

Die App unterstützt zwei parallel sichtbare Chatfenster:

Window A (Primär / Fokus)
Window B (Sekundär / Assistenz)

👉 beide gleichzeitig sichtbar, unabhängig bedienbar

💎 Kernprinzip

Zwei vollwertige Arbeitskontexte in einem gemeinsamen Workspace.

🧱 Funktionale Anforderungen
1. Fixed Two-Window Architecture
Max Windows = 2
kein dynamisches Multi-Window
bewusst begrenzt für Fokus
2. Split Layout
Standard:
┌───────────────┬───────────────┐
│   Window A    │   Window B    │
│   (Primary)   │ (Secondary)   │
└───────────────┴───────────────┘
3. Independent Chat State

Jedes Fenster hat:

eigenen Chat
eigenen Scroll-State
eigene Eingabe
4. Resize Behavior (optional Phase 2)
50/50 default
optional 70/30 focus mode
5. Window Focus System

👉 basiert auf Feature 3

klick in Fenster → wird aktiv
active styling applied
🧠 State Model Erweiterung
{
  "layout": "split",
  "activeWindowId": "A",
  "windows": {
    "A": {
      "active_chat_id": "chat_123",
      "scroll": 120
    },
    "B": {
      "active_chat_id": "chat_456",
      "scroll": 42
    }
  }
}
🎨 UI/UX Anforderungen
1. Visuelle Trennung
klare vertikale Split-Line
subtle border between windows
2. Active Window Highlight
glow / border
stronger contrast
3. Inactive Window
leicht gedimmt
aber weiterhin voll interaktiv
4. Sync Behaviour

👉 bewusst NICHT synchron:

Scroll unabhängig
Input unabhängig
Chat unabhängig
⚠️ Edge Cases
1. Only one chat open
→ Window B zeigt Placeholder:
"Select a chat to open"
2. Window B empty
bleibt leerer state
keine Auto-Fill Logik
3. Window resize extreme
minimum width enforced
avoid collapse below usability threshold
4. Chat duplication
same chat in both windows erlaubt
independent scroll state
🚫 Nicht Teil dieses Features
Chat Actions (Feature 6)
Chatlist Indicators (Feature 5)
Active State Logic (Feature 3)
Taskleiste (kommt später)
🧩 Technischer Umsetzungsvorschlag
Layout Base:
.workspace {
  display: flex;
  flex-direction: row;
  height: 100vh;
}

.window {
  flex: 1;
  border-right: 1px solid #222;
}
Window Component:
function Window({ id, activeWindowId, chat }) {
  const isActive = id === activeWindowId;

  return (
    <div className={`window ${isActive ? "active" : ""}`}>
      <ChatView chatId={chat} />
    </div>
  );
}
Focus Handling:
onClickWindow = (id) => {
  setActiveWindowId(id);
};
🧪 Testfälle (QA / Playwright)
Test 1:
App öffnen
→ zwei Fenster sichtbar
Test 2:
Chat in Window A ändern
→ nur A aktualisiert
Test 3:
Click Window B
→ B becomes active
Test 4:
Same chat in A and B
→ independent states maintained
Test 5:
Resize window
→ layout remains stable
💎 Erwartetes Ergebnis
echtes „Desktop Workspace Feeling“
kein Chat-App Gefühl mehr
zwei parallele Denkflächen
🔥 Warum dieses Feature kritisch ist

Ohne das:

❌ Multi-Chat ist nur Simulation

Mit dem:

👉 echte parallele Arbeitsumgebung wie IDE + Debugger