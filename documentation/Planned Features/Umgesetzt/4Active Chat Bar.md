Active Chat Bar (Global Context Overview)

🎯 Ziel des Features

Der User soll immer sofort sehen, welche zwei Chats aktuell aktiv sind — unabhängig davon:

wie lang die Chatliste ist
wo die Chats in der Liste stehen
welches Fenster gerade fokussiert ist
💎 Kernprinzip

Der aktive Arbeitskontext ist IMMER sichtbar, unabhängig von Navigation.

🧱 Funktionale Anforderungen
1. Anzeige der aktiven Chats

Die Bar zeigt:

Chat in Window A
Chat in Window B (optional)
Beispiel:
ACTIVE CONTEXT
🟣 Planning Chat
🔵 Detail Chat
2. Live-Synchronisation

Die Bar aktualisiert sich sofort bei:

Chatwechsel
Fensterwechsel
Chat-Neuzuweisung
3. Klick-Verhalten
Klick auf Chat in Bar:
bringt Window in Fokus
bringt Chat in Sicht (falls nötig)
4. + Button (Second Window)

Wenn nur 1 Chat aktiv ist:

🟣 Planning Chat   [+ Add Second Chat]

👉 öffnet Window B

5. Sync mit Window State

Die Bar ist kein eigenes System, sondern nur:

eine Darstellung von Active Window State

🧠 State Mapping
{
  "activeWindowId": "A",
  "windows": {
    "A": { "active_chat_id": "chat_123" },
    "B": { "active_chat_id": "chat_456" }
  }
}
Bar rendert daraus:
A → chat_123
B → chat_456
🎨 UI/UX Anforderungen
1. Position
direkt über Chatliste
immer sichtbar (sticky)
2. Visuelle Trennung
leicht abgesetzt (Border / Background shade)
aber nicht dominant
3. Farbkodierung (deine Idee)
Window A → 🟣
Window B → 🔵

👉 exakt konsistent mit vorherigem Design

4. Status Anzeige

Optional:

ACTIVE label für fokussiertes Window
⚠️ Edge Cases
1. Nur 1 Chat aktiv
🟣 Planning Chat   [+ Add Second Chat]
2. Window B geschlossen
Bar zeigt nur Window A
kein leerer Platzhalter
3. Chat wird gewechselt
sofortige Live-Update ohne Delay
4. gleicher Chat in beiden Fenstern

👉 erlaubt, aber:

Bar zeigt ihn doppelt (mit Window Label)
🚫 Nicht Teil dieses Features
Chatliste Sortierung
Window Management Logik
Active State Definition (kommt aus Feature 3)
Chat Actions (↗ etc.)
🧩 Technische Umsetzung
Render Logic:
function ActiveChatBar({ windows }) {
  return (
    <div>
      {windows.A.active_chat_id && (
        <ChatChip color="purple" chatId={windows.A.active_chat_id} />
      )}
      {windows.B?.active_chat_id && (
        <ChatChip color="blue" chatId={windows.B.active_chat_id} />
      )}
    </div>
  );
}
Click Behavior:
onClick(chatId) => {
  focusWindowByChat(chatId);
}
🧪 Testfälle (QA / Playwright)
Test 1:
Chat in Window A ändern
→ Bar aktualisiert sofort
Test 2:
Window B öffnen
→ Chat erscheint in Bar
Test 3:
Klick auf Bar Chat
→ entsprechendes Window wird fokussiert
Test 4:
nur 1 Chat aktiv
→ Button „Add Second Chat“ sichtbar
💎 Erwartetes Ergebnis
User sieht IMMER den aktuellen Arbeitskontext
keine mentale Suche nötig
perfekte Ergänzung zu 2-Window-System
🔥 Warum dieses Feature wichtig ist

Ohne das:

❌ User verliert Kontext in langen Chatlisten
❌ Multi-Window wird unübersichtlich

Mit dem:

👉 „Ich sehe sofort, woran ich arbeite“