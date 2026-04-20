FEATURE 9: CHAT REFACTORING SYSTEM (Split / Merge / Extract)
🧠 1. Ziel des Features

Das Chat Refactoring System ermöglicht es, bestehende Chats nachträglich strukturell zu reorganisieren, ohne Inhalte zu verlieren.

👉 Ziel:

Chaos in langen Chats auflösen
Themen sauber trennen
relevante Inhalte in neue Kontexte überführen
💥 Core Value

💎 „Ein Chat ist kein statischer Verlauf, sondern ein editierbares Wissensobjekt.“

🧩 2. Kernfunktionen
✂️ SPLIT (Chat aufteilen)

👉 Ein Chat wird in zwei oder mehr eigenständige Chats getrennt

Use Cases:
Themenwechsel im Chat (z. B. Coding → Kochen)
unterschiedliche Projekte vermischt
Fokus wiederherstellen
🧬 EXTRACT (Teil extrahieren)

👉 Ausgewählte Nachrichten werden in einen neuen Chat ausgelagert

Use Cases:
einzelne Idee isolieren
Task aus Diskussion herausziehen
Wissen weiterverwenden
🔗 MERGE (Chats zusammenführen)

👉 Zwei oder mehr Chats werden zu einem kombiniert

Use Cases:
zusammengehörige Themen vereinen
Kontext erweitern
fragmentierte Arbeit bündeln
🧠 3. UX FLOW (Diamantstandard)
✂️ SPLIT FLOW
User markiert Nachricht (Startpunkt)
Klick: „Chat hier aufteilen“
Vorschau:
Teil A (oben)
Teil B (unten)
Bestätigung

👉 Ergebnis:

zwei eigenständige Chats
🧬 EXTRACT FLOW
Multi-Select von Nachrichten
Klick: „In neuen Chat extrahieren“
Optional:
Name vergeben
Ziel wählen
Bestätigung

👉 Ergebnis:

neuer Chat mit selektierten Inhalten
🔗 MERGE FLOW
Chat A öffnen
„Mit anderem Chat zusammenführen“
Chat B auswählen
Vorschau (chronologisch kombiniert)
Bestätigung

👉 Ergebnis:

ein kombinierter Chat
🎯 4. UX DESIGN PRINZIPIEN
🧠 Klarheit
User sieht immer, was passiert
Vorschau vor jeder Änderung
🔄 Reversibilität
Undo möglich
Versionen speicherbar
🧩 Kontext-Erhalt
keine Inhalte verlieren
Reihenfolge bleibt logisch
🧱 5. TECHNISCHE ARCHITEKTUR
📦 Datenmodell
{
  "chat_id": "...",
  "messages": [...],
  "thread_blocks": [...],
  "origin_refs": [...]
}
🔗 Message Referencing

Jede Nachricht erhält:

{
  "message_id": "...",
  "origin_chat_id": "...",
  "timestamp": "...",
  "refactor_history": []
}
🧠 Refactor Engine

Funktionen:

split(chat, index)
extract(messages[])
merge(chatA, chatB)
⚙️ 6. LOGIK (wichtig!)
SPLIT
messages[0..index] → Chat A
messages[index+1..n] → Chat B
EXTRACT
selected_messages → neuer Chat
Original bleibt erhalten (optional: remove toggle)
MERGE
messagesA + messagesB → sort(timestamp)
💡 7. INTELLIGENTE FEATURES (optional, aber stark)
🤖 Smart Split Suggestion

AI erkennt:

Themenwechsel
neue Kontexte

👉 Vorschlag:
„Hier neuen Chat erstellen?“

🧠 Semantic Clustering
gruppiert Nachrichten automatisch
schlägt Extracts vor
✨ Auto-Naming
neue Chats bekommen intelligente Titel
🎨 8. UI KOMPONENTEN
Kontextmenü Nachricht
„Split hier“
„Extrahieren“
„Als neuen Chat starten“
Multi-Select Toolbar
Extract
Move
Delete
Merge Dialog
Chat auswählen
Vorschau anzeigen
⚠️ 9. EDGE CASES
❗ Reihenfolge-Konflikte
unterschiedliche Zeitstempel
→ Lösung: sort + grouping
❗ Duplikate
gleiche Nachricht mehrfach
→ Lösung: ID-basierte Deduplication
❗ Kontextverlust

→ Lösung:

origin reference behalten
🔐 10. SAFETY & CONTROL
Undo für jede Operation
Version History
Soft Delete
🚀 11. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1:
Split (einfach)
Phase 2:
Extract (mit Multi-Select)
Phase 3:
Merge
Phase 4:
AI Suggestions
💎 12. FINAL FAZIT

Dieses Feature verwandelt Chat von:

❌ statischem Verlauf

zu:

💎 dynamischem, editierbarem Wissenssystem

👉 Es ist ein Gamechanger für Power-User
👉 und perfekt für dein Multi-Chat-System