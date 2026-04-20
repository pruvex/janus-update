Chatlist State Indicators (Window Mapping in List View)

🎯 Ziel des Features

Die Chatliste soll jederzeit klar zeigen:

welcher Chat in welchem Fenster geöffnet ist
welcher Chat aktiv bearbeitet wird
welche Chats gerade „im Workspace liegen“

👉 ohne dass der User Fenster suchen muss

💎 Kernprinzip

Die Chatliste ist nicht nur Navigation — sie ist ein Spiegel des aktuellen Workspace-Zustands.

🧱 Funktionale Anforderungen
1. Window-Zuordnung sichtbar machen

Jeder Chat kann folgende States haben:

in Window A geöffnet
in Window B geöffnet
in keinem Fenster
Beispiel:
Projektplanung     🟣 A
Details            🔵 B
Ideen              ○
2. Active Window Highlight

Wenn ein Chat im aktiven Fenster ist:

Projektplanung     🟣 A ● ACTIVE
3. Multi-Window Support

Ein Chat kann in beiden Fenstern sein:

Projektplanung     🟣 A 🔵 B
4. Click Behavior bleibt unverändert

👉 wichtig: Feature 5 ändert NICHT die Logik aus Feature 2

Klick → öffnet im aktiven Fenster
5. Optional: Quick Switch Indikator

Wenn Chat in anderem Fenster offen ist:

Projektplanung     ↗ Switch Window
🧠 State Mapping

Erweiterung aus Feature 4:

{
  "windows": {
    "A": { "active_chat_id": "chat_123" },
    "B": { "active_chat_id": "chat_456" }
  }
}
Ableitung für Chatliste:
chat_123 → A
chat_456 → B
🎨 UI/UX Anforderungen
1. Minimalistische Anzeige
keine langen Texte
nur Icons + kurze Labels
2. Farbkonsistenz
🟣 Window A
🔵 Window B

👉 exakt wie Active Bar (Feature 4)

3. ACTIVE State zusätzlich
kleiner Dot oder Bold Text
4. Hover Details (optional)
Open in: Window A + B
Active in: Window A
⚠️ Edge Cases
1. Chat in keinem Fenster
Ideen   ○
2. Chat in beiden Fenstern
Projektplanung   🟣 A 🔵 B
3. Fenster geschlossen
Markierung verschwindet sofort
4. Active Window wechselt
ACTIVE Indicator wandert sofort
🚫 Nicht Teil dieses Features
Chat Opening Logic
Window Management
Active Bar
Sortierung / Views
🧩 Technischer Umsetzungsvorschlag
Mapping Function:
function getChatWindowState(chatId, windows) {
  const inA = windows.A.active_chat_id === chatId;
  const inB = windows.B.active_chat_id === chatId;

  return { inA, inB };
}
Render Logic:
if (inA) show("🟣 A");
if (inB) show("🔵 B");
Active Check:
const isActive =
  windows[activeWindowId].active_chat_id === chatId;
🧪 Testfälle (QA / Playwright)
Test 1:
Chat in Window A öffnen
→ Liste zeigt 🟣 A
Test 2:
Chat in Window B öffnen
→ Liste zeigt 🔵 B
Test 3:
Chat in beiden Fenstern
→ beide Marker sichtbar
Test 4:
Active Window wechseln
→ ACTIVE Indicator wandert
Test 5:
Window schließen
→ Marker verschwindet
💎 Erwartetes Ergebnis
Chatliste wird zum „System-Status-Display“
User versteht Workspace sofort visuell
kein mentaler Kontextverlust mehr
🔥 Warum dieses Feature wichtig ist

Ohne es:

❌ Chatliste ist nur Navigation

Mit ihm:

👉 Chatliste wird ein Live-Mirror des Systems