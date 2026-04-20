Chat Actions (Direct Manipulation Layer für Chats)

🎯 Ziel des Features

Der User soll direkt in der Chatliste:

Chats zwischen Fenstern verschieben können
Chats gezielt in Window A oder B öffnen können
ohne Umwege kontrollieren, wo ein Chat landet

👉 kein Denken mehr nötig: nur Aktion wählen

💎 Kernprinzip

Jeder Chat hat eine kleine „Aktionsleiste“, mit der er aktiv gesteuert werden kann.

🧱 Funktionale Anforderungen
1. Chat Actions pro List Item

Jeder Chat bekommt zusätzliche Controls:

Open in Window A
Open in Window B
Switch to active window
Optional: Focus
Beispiel UI:
Projektplanung   🟣 A 🔵 B   ↗  A  B
2. Open in specific Window
Verhalten:
Klick „A“ → Chat wird in Window A geladen
Klick „B“ → Chat wird in Window B geladen
3. Override Behavior
Chat wird im Ziel-Fenster ersetzt
keine Duplikat-Blockierung
4. Quick Focus Action (↗)
↗ = open + focus window
5. No-Guessing Principle

👉 jede Aktion ist explizit

kein „smart routing“
kein hidden logic
🧠 State Behavior
Example:
{
  "windows": {
    "A": { "active_chat_id": "chat_123" },
    "B": { "active_chat_id": "chat_456" }
  }
}
Action:
User clicks "B" on Chat X
→ windows.B.active_chat_id = X
→ activeWindow unchanged
🎨 UI/UX Anforderungen
1. Actions nur im Hover sichtbar
clean list default
actions appear on hover
2. Icons statt Text (optional später)
↗ = focus
A = open in A
B = open in B
3. Clear spacing
Actions dürfen nicht „Chat Text“ überladen
4. Visual feedback
kurz highlight window when action triggered
⚠️ Edge Cases
1. Chat already in window

👉 erlaubt

einfach replace
2. Chat in both windows
User clicks A again
→ refresh content in A
3. No active window (should never happen)

👉 fallback to Window A

4. Rapid switching
last action wins
no race conditions
🚫 Nicht Teil dieses Features
Active State Definition (Feature 3)
Chatlist Indicators (Feature 5)
Window UI Rendering
Memory / Backend Logic
🧩 Technischer Umsetzungsvorschlag
Core Handler:
function openChatInWindow(chatId, windowId) {
  windows[windowId].active_chat_id = chatId;
}
Focus Action:
function focusChat(chatId) {
  const windowId = getWindowContaining(chatId);
  setActiveWindow(windowId);
}
UI Mapping:
onClickA = () => openChatInWindow(chatId, "A");
onClickB = () => openChatInWindow(chatId, "B");
🧪 Testfälle (QA / Playwright)
Test 1:
Klick A on Chat X
→ X appears in Window A
Test 2:
Klick B on Chat X
→ X appears in Window B
Test 3:
↗ clicked
→ correct window focused + chat visible
Test 4:
rapid switching A → B → A
→ last action wins
💎 Erwartetes Ergebnis
volle Kontrolle über Chat Placement
kein „wo ist mein Chat?“ Problem
extrem schnelle Workflow-Steuerung
🔥 Warum dieses Feature wichtig ist

Ohne das:

❌ System ist nur halb steuerbar

Mit dem:

👉 User wird zum „Orchestrator seiner Chats“