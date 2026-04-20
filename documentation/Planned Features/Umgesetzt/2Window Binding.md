Chat ↔ Window Binding (Deterministische Zuordnung & Steuerung)

🎯 Ziel des Features

Sicherstellen, dass:

Chats gezielt in Fenster geladen werden
das Verhalten für den User vorhersehbar und konsistent ist
die Grundlage für spätere Features (Active Bar, Actions, etc.) entsteht
💎 Kernprinzip

Ein Chat wird IMMER in das aktuell aktive Fenster geladen.

Keine Magie. Keine versteckten Regeln.
👉 Deterministisches Verhalten

🧱 Funktionale Anforderungen
1. Chat-Auswahl (Primary Action)
Verhalten:
Klick auf Chat in Chatliste →
👉 lädt Chat in aktives Fenster
Beispiel:
Window A = aktiv
User klickt „Projektplanung“

→ Chat wird in Window A geladen
🧠 Warum das wichtig ist
User weiß IMMER, was passiert
kein „wo ist mein Chat jetzt hin?“-Moment
extrem wichtig für Vertrauen ins System
2. Fenster ersetzt bestehenden Chat
wenn bereits ein Chat im Fenster offen ist:
👉 wird dieser ersetzt
Beispiel:
Window A zeigt Chat X
User klickt Chat Y

→ Window A zeigt jetzt Chat Y
3. Window B Verhalten
funktioniert identisch zu Window A
keine Sonderlogik
Beispiel:
Window B aktiv
User klickt Chat Z

→ Chat Z wird in Window B geladen
🧠 State-Logik (Erweiterung aus Feature 1)
{
  "windows": {
    "A": {
      "active_chat_id": "chat_123",
      "is_active": true
    },
    "B": {
      "active_chat_id": "chat_456",
      "is_active": false,
      "is_open": true
    }
  }
}
🔁 Core Regel (zentral!)
Chat Click → setChatForWindow(activeWindowId, chatId)
🎨 UI/UX Anforderungen
1. Aktives Fenster ist entscheidend
visuell klar erkennbar (aus Feature 1)
bestimmt Ziel der Aktion
2. Kein automatisches Umschalten

❌ NICHT:

„wenn Chat schon offen ist, springe zu anderem Fenster“

👉 das kommt später (wenn überhaupt)

3. Keine versteckte Logik

❌ KEIN:

„intelligentes Routing“
„best guess“

👉 nur klare, direkte Zuordnung

⚠️ Edge Cases
1. Chat ist bereits in anderem Fenster offen
Phase 2 Verhalten:

👉 erlaubt

Beispiel:
Window A → Chat X
Window B → Chat Y

User klickt Chat X während Window B aktiv ist

→ Window B zeigt jetzt auch Chat X

👉 Ergebnis:

gleiche Chats in beiden Fenstern möglich
KEIN Block / KEIN Redirect
2. Kein aktives Fenster

👉 darf nicht passieren (Feature 1 garantiert das)

🚫 Nicht Teil dieses Features
Anzeige, welcher Chat wo offen ist
Active Chat Bar
Chat Actions (↗ etc.)
intelligente Vermeidung von Duplikaten
🧩 Technischer Umsetzungsvorschlag
Core Funktion:
function handleChatClick(chatId) {
  const activeWindow = getActiveWindow();
  setChatForWindow(activeWindow, chatId);
}
State Update:
windows[activeWindowId].activeChatId = chatId;
🧪 Testfälle (QA / Playwright)
Test 1:
Window A aktiv
Klick auf Chat X
→ Chat X erscheint in Window A
Test 2:
Window B aktiv
Klick auf Chat Y
→ Chat Y erscheint in Window B
Test 3:
Window A zeigt Chat X
Klick auf Chat Y
→ Chat Y ersetzt Chat X
Test 4:
gleicher Chat in beiden Fenstern möglich
💎 Erwartetes Ergebnis
100% vorhersehbares Verhalten
keine Verwirrung beim Öffnen von Chats
stabile Grundlage für alle kommenden UI-Features