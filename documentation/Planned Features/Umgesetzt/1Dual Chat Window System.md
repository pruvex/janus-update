Dual Chat Window System (Core Interaction Layer)

🎯 Ziel des Features

Der User soll zwei unabhängige Chatfenster parallel nutzen können, um:

mehrere Kontexte gleichzeitig zu bearbeiten
zwischen „Planung“ und „Details“ zu wechseln
effizienter mit dem globalen Memory-System zu arbeiten
💎 Kernprinzip

Zwei gleichwertige Chatfenster, die parallel existieren und unabhängig voneinander gesteuert werden.

🧱 Funktionale Anforderungen
1. Zwei Chatfenster
Window A (Standard aktiv)
Window B (optional zuschaltbar)
2. Jedes Fenster hat:
eigenen active_chat_id
eigenen Nachrichtenverlauf (UI-seitig)
Zugriff auf globales Memory (bereits vorhanden)
3. Fokus-System
genau ein Fenster ist aktiv
Klick in Fenster → setzt Fokus
aktives Fenster wird visuell hervorgehoben
4. Initialverhalten
Start:
nur Window A sichtbar
Window B geschlossen / leer
Öffnen von Window B:
wird durch UI-Action ausgelöst (später: Active Bar Button)
5. Verhalten bei Chat-Auswahl
Klick auf Chat in Liste → öffnet Chat im aktiven Fenster
bestehender Chat im Fenster wird ersetzt
🧠 State-Modell (wichtig für Umsetzung)
{
  "windows": {
    "A": {
      "active_chat_id": "chat_123",
      "is_active": true
    },
    "B": {
      "active_chat_id": null,
      "is_active": false,
      "is_open": false
    }
  }
}
🔁 State-Regeln
nur ein Fenster kann is_active = true haben
Window B kann is_open = false sein (nicht gerendert)
wenn Window B geöffnet wird:
bekommt es initial keinen Chat oder optional neuen Chat
🎨 UI/UX Anforderungen
Fensterlayout:
nebeneinander (Split View)
gleiche Größe (50/50)
Active State:
visuell hervorgehoben (z. B. Border oder Glow)
klar erkennbar, wo Eingaben landen
Interaktion:
Klick in Fenster → Fokus setzen
Eingabe geht immer an aktives Fenster
⚠️ Edge Cases
1. Window B schließen
Zustand wird entfernt oder gespeichert
Fokus geht zurück auf Window A
2. Chat bereits in anderem Fenster offen
(Phase 1): erlauben (kein Blocking)
spätere Optimierung möglich
3. Kein aktives Fenster (verhindern!)
System muss immer ein aktives Fenster haben
🚫 Nicht Teil dieses Features

(kommt später!)

Active Chat Bar
Chatlist Indicators
Chat Actions (↗ etc.)
Taskleiste
Chat-to-Chat Kommunikation
🧩 Technischer Umsetzungsvorschlag
Frontend:
React State / Store (z. B. Zustand, Redux, Context)
zentrale Window-State-Verwaltung
Struktur:
const windows = {
  A: { activeChatId: null, isActive: true },
  B: { activeChatId: null, isActive: false, isOpen: false }
};
Aktionen:
setActiveWindow(windowId)
setChatForWindow(windowId, chatId)
openSecondWindow()
closeSecondWindow()
🧪 Testfälle (wichtig für QA / Playwright später)
Test 1:
Klick in Window B → wird aktiv
Test 2:
Chat auswählen → wird im aktiven Fenster geladen
Test 3:
Window B öffnen → erscheint korrekt
Test 4:
Window B schließen → Fokus springt zurück
💎 Erwartetes Ergebnis
zwei parallel nutzbare Chatfenster
stabile Fokuslogik
klare Grundlage für alle weiteren Features