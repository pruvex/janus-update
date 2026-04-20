Feature-Dossier 11: Smart Chat Grouping + Sorting System
🧠 Feature Name

Smart Chat Grouping + Hybrid Sorting

🎯 Ziel

Chats werden:

automatisch thematisch gruppiert
aber User kann jederzeit Sortierung wählen
💎 Kernprinzip

AI organisiert — User kontrolliert.

🧱 Funktionale Anforderungen
1. Smart Grouping (AI)

Chats werden automatisch gruppiert:

📁 Coding
📁 Kochen
📁 Privat
📁 Business
📁 Allgemein
2. Klassifikation
Kategorien (Start)
coding
cooking
personal
business
research
general
LLM Prompt
Classify this conversation into one category:

Categories:
- coding
- cooking
- personal
- business
- research
- general

Conversation:
{{messages}}
3. Speicherung
{
  "chat_id": "123",
  "group": "coding",
  "tags": ["python", "backend"]
}
4. User Override
Chat kann manuell verschoben werden
danach keine Auto-Korrektur mehr
🔽 5. SORTING SYSTEM (KRITISCH)
Dropdown UI
Sortieren nach:
[ Chronologisch ▼ ]
Optionen
Chronologisch (neueste zuerst)
Chronologisch (älteste zuerst)
Smart Gruppen (AI)
Zuletzt aktiv
Nach Titel (A–Z)
State Speicherung
{
  "chatListSortMode": "chronological_desc"
}
🧩 Rendering Logik
Chronologisch
Chat A
Chat B
Chat C
Smart Gruppen
📁 Coding
  - Chat A
  - Chat C

📁 Kochen
  - Chat B
🎨 UX Anforderungen
1. Gruppen UI
collapsible
merkt sich Zustand
2. Active Chat Anzeige
farblich markiert (A/B System!)
3. Suchfunktion

👉 unabhängig von Sortierung

4. Scroll-Verhalten
Position bleibt erhalten
⚠️ Edge Cases
Unklare Chats

→ Gruppe:

Allgemein
Multi-Topic

→ dominantes Thema

falsche Klassifikation

→ User korrigiert

🧪 Tests
korrekte Gruppierung
Sortierung funktioniert
Wechsel zwischen Modi stabil
User Override bleibt bestehen
💎 Warum das wichtig ist

Ohne:

❌ Chaos bei vielen Chats

Mit:

✔ Struktur
✔ Skalierbarkeit
✔ echtes Knowledge-System

🔥 Kombination Feature 10 + 11
📁 Coding
  - Memory System Architektur
  - SQLAlchemy Bugfix

👉 fühlt sich an wie:

IDE
Notion
AI Knowledge Base
🚀 Finaler Impact (beide Features zusammen)

Du bekommst:

saubere Chat-Namen
automatische Struktur
volle User-Kontrolle

👉 Ergebnis:

Dein System ist nicht mehr Chat-App — sondern Wissenssystem.