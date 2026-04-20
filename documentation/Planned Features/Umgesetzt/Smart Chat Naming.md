Feature-Dossier 10: Smart Chat Naming System
🧠 Feature Name

Smart Chat Naming (Semantic Title Generation)

🎯 Ziel

Automatische Generierung von:

kurzen
verständlichen
thematisch präzisen

Chat-Titeln statt:

❌ „Ich möchte ein Memory-System bauen mit…“

💎 Kernprinzip

Der Titel beschreibt das Thema, nicht den Wortlaut.

🧱 Funktionale Anforderungen
1. Automatische Titelgenerierung

Trigger:

nach 2–3 Nachrichten
oder nach erstem vollständigen Austausch
2. Titelregeln
max. 3–6 Wörter
keine Füllwörter
keine Satzzeichen
gleiche Sprache wie User
3. Beispiele
Input: "Ich baue ein Memory-System mit SQLAlchemy"
→ "Memory System Architektur"

Input: "Wie mache ich Flammkuchen?"
→ "Flammkuchen Rezept"
4. Titel aktualisieren (Auto-Rename)

Nur wenn:

Titel auto-generiert ist
Thema sich signifikant ändert
5. User Override
User kann Titel jederzeit manuell ändern
danach: ❌ kein automatisches Überschreiben mehr
🧠 LLM Prompt
Generate a short, clear title (max 5 words) for this conversation.

Rules:
- No filler words
- No punctuation
- Focus on main topic
- Language: same as user

Conversation:
{{first_messages}}
🧩 Datenstruktur
{
  "chat_id": "123",
  "title": "Memory System Architektur",
  "auto_generated": true,
  "last_topic_hash": "abc123"
}
⚙️ Logik
Titel generieren
if (!chat.title) {
  chat.title = generateTitle(messages);
}
Titel updaten
if (chat.auto_generated && topicChanged) {
  chat.title = generateTitle(messages);
}
User Override
chat.auto_generated = false;
🎨 UX Anforderungen
1. Inline Editing
klick auf Titel → editierbar
2. Hover Preview
zeigt längeren Kontext
3. Smooth Rename
kein harter Sprung
⚠️ Edge Cases
Kurze Inputs
"hi", "ok"

→ Titel:

"Neuer Chat"
Multi-Topic

→ dominantes Thema

Sprachwechsel

→ letzte dominante Sprache

🧪 Tests
sinnvoller Titel bei normalen Chats
kein Override nach User-Edit
Titel passt sich bei Themenwechsel an
keine zu langen Titel
💎 Impact

✔ bessere Übersicht
✔ schnelleres Wiederfinden
✔ wirkt sofort „fertiges Produkt“