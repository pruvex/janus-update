Perfekt, jetzt kommen wir zu einem der wichtigsten Teile überhaupt — das ist der Punkt, wo sich dein System „richtig“ anfühlt oder eben nicht.

📁 Feature-Dossier 3: Active State System
🧠 Feature Name

Active State System (Focus & Interaction Control)

🎯 Ziel des Features

Sicherstellen, dass:

immer klar ist, welches Fenster aktiv ist
alle User-Aktionen eindeutig einem Fenster zugeordnet werden
das System sich „kontrollierbar“ und nicht chaotisch anfühlt
💎 Kernprinzip

Es gibt IMMER genau EIN aktives Fenster.

Dieses Fenster ist:

Ziel für Chat-Auswahl
Ziel für Eingaben
visuell hervorgehoben
🧱 Funktionale Anforderungen
1. Genau ein aktives Fenster
Active Window ∈ {A, B}
niemals 0
niemals 2 gleichzeitig
2. Fokus wechseln
Interaktion:
Klick in Window A → A wird aktiv
Klick in Window B → B wird aktiv
Beispiel:
User klickt in Window B

→ Window B = aktiv
→ Window A = inaktiv
3. Eingaben gehen immer an aktives Fenster
Texteingabe
Prompt senden
Tool-Aufrufe

👉 alles geht an das aktive Fenster

4. Chat-Auswahl nutzt Active State

(Verbindung zu Feature 2)

Chat Click → goes to active window
🧠 State-Modell

Erweiterung von Feature 1 & 2:

{
  "activeWindowId": "A",
  "windows": {
    "A": {
      "active_chat_id": "chat_123"
    },
    "B": {
      "active_chat_id": "chat_456",
      "is_open": true
    }
  }
}
🎨 UI/UX Anforderungen (sehr wichtig)
1. Aktives Fenster MUSS sichtbar sein

👉 keine Diskussion, das ist kritisch

Empfohlene Varianten:
Option A (empfohlen):
farbige Border (z. B. lila/türkis)
leichtes Glow
Option B:
Header hervorgehoben

👉 Wichtig:

sofort sichtbar, ohne nachdenken

2. Inaktives Fenster visuell reduziert
leicht gedimmt
weniger Kontrast

👉 aber NICHT deaktiviert

3. Cursor-Logik
Cursor erscheint nur im aktiven Fenster
verhindert Fehl-Eingaben
⚠️ Edge Cases
1. Window B wird geöffnet

👉 Standard:

Window B öffnet → wird automatisch aktiv

Warum:

User will damit arbeiten
2. Window B wird geschlossen
Window B schließen → Window A wird aktiv
3. Beide Fenster haben gleichen Chat

👉 erlaubt (wie in Feature 2)

Active State bleibt unabhängig davon

4. Kein aktives Fenster verhindern

👉 Systemregel:

activeWindowId darf niemals null sein
🚫 Nicht Teil dieses Features
Anzeige in Chatliste
Active Chat Bar
Chat Actions
Farben pro Chat (nur pro Fenster!)
🧩 Technischer Umsetzungsvorschlag
State:
const [activeWindowId, setActiveWindowId] = useState("A");
Fokus setzen:
function setActiveWindow(windowId) {
  setActiveWindowId(windowId);
}
Nutzung:
const isActive = activeWindowId === "A";
🧪 Testfälle (QA / Playwright)
Test 1:
Klick in Window B
→ Window B wird aktiv
Test 2:
Eingabe senden
→ landet im aktiven Fenster
Test 3:
Chat auswählen
→ wird im aktiven Fenster geladen
Test 4:
Window B schließen
→ Window A wird aktiv
💎 Erwartetes Ergebnis
User weiß IMMER, wo er gerade arbeitet
keine Fehlzuweisungen
stabiles, kontrolliertes Gefühl
🔥 Warum dieses Feature kritisch ist

Ohne das:

❌ Chaos
❌ falsche Chats werden überschrieben
❌ Frust

Mit dem:

👉 fühlt sich dein System sofort „pro“ an