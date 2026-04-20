JANUS VIDEO LIST SYSTEM — DIAMANTSTANDARD DOSSIER
🎯 ZIEL

Erweiterung des bestehenden funktionierenden Video-Systems um Listen-Funktionalität, ohne bestehende Single-Video-Flows zu brechen.

Bereits funktionierend:
✅ "zeig mir ein video von XY"
✅ "zeig mir das neueste video von XY"
✅ Channel Lock + Feed Authority
✅ Video Modal (Autoplay)
Neu zu implementieren:
🔥 Mehrere Videos als Liste (kein Autoplay!)
🔥 Filter (Anzahl, Datum, Thema)
🔥 UI-ready Response (für Modal-Trigger im Frontend)
🧠 GRUNDPRINZIP (KRITISCH)

👉 Single Video ≠ Video Liste

Diese beiden Fälle müssen hart getrennt werden.

Intent	Verhalten
Einzelnes Video	Autoplay + Modal
Liste	KEIN Autoplay + Liste anzeigen
🧩 ARCHITEKTUR
OPTION A (EMPFOHLEN 💎):

👉 Bestehenden video.search Skill erweitern

OPTION B:

👉 Neuer Skill video.list

➡️ Wir nehmen OPTION A, weil:

Bestehendes System bleibt stabil
Kein doppelter Code
Channel Lock bleibt intakt
⚙️ SKILL ERWEITERUNG
Neue Parameter
{
  "mode": "single | list",
  "max_results": 1,
  "published_after": null,
  "published_before": null,
  "topic_query": null
}
🧠 INTENT LOGIK (ORCHESTRATOR)
IF user_query contains:
  ("letzten", "top", "alle", "mehrere", "liste", number > 1)
THEN
  mode = "list"
ELSE
  mode = "single"
🧠 BEISPIELE
User Input	Mode
"neuestes video von xy"	single
"letzten 3 videos von xy"	list
"alle videos von xy januar 2024"	list
"video von xy über elden ring"	single
"videos von xy über elden ring"	list
🔍 BACKEND LOGIK
SINGLE MODE (UNVERÄNDERT)
- Channel Lock
- Upload Playlist Index 0
- RETURN: selected_video
LIST MODE (NEU)
- Channel Lock
- Load Upload Playlist
- Fetch N Videos (max_results)

IF filters exist:
  - filter by date
  - filter by topic (title/description match)

RETURN: videos[]
📦 RESPONSE FORMAT (KRITISCH)
SINGLE (bestehend)
{
  "selected_video": {
    "video_id": "...",
    "title": "...",
    "watch_url": "...",
    "embed_url": "..."
  }
}
LIST (NEU 💎)
{
  "videos": [
    {
      "video_id": "...",
      "title": "...",
      "channel": "...",
      "published_at": "...",
      "views": 12345,
      "thumbnail": "...",
      "watch_url": "...",
      "embed_url": "...",
      "is_embeddable": true
    }
  ],
  "count": 3
}
🛑 HARTE REGELN
❌ NIEMALS:
Autoplay bei Listen
selected_video bei Listen zurückgeben
Modal automatisch öffnen
✅ IMMER:
Saubere Liste liefern
Frontend entscheidet über Anzeige
🎨 FRONTEND LOGIK
LIST VIEW
FOR video IN videos:
  render:
    - thumbnail
    - title
    - "▶ Video anzeigen" button
BUTTON CLICK
onClick(video):
  openModal(video.embed_url)
SINGLE VIEW
onResponse(selected_video):
  openModal(selected_video.embed_url)
🔍 FILTER LOGIK
1. Anzahl
"max_results": 3
2. Datum
"published_after": "2024-01-01",
"published_before": "2024-01-31"
3. Thema
"topic_query": "elden ring"

Backend:

IF topic_query:
  filter where:
    topic_query in title OR description
💎 GOLDSTANDARD FLOW
Beispiel 1

User:
"zeig mir die letzten 3 videos von handoftrash"

➡️ Tool Call:

{
  "mode": "list",
  "channel_name": "HandOfTrash",
  "max_results": 3,
  "wants_latest": true
}
Beispiel 2

User:
"alle videos von handoftrash aus januar 2024"

{
  "mode": "list",
  "channel_name": "HandOfTrash",
  "published_after": "2024-01-01",
  "published_before": "2024-01-31"
}
Beispiel 3

User:
"videos von handoftrash über elden ring"

{
  "mode": "list",
  "channel_name": "HandOfTrash",
  "topic_query": "elden ring"
}
🧪 PLAYWRIGHT TESTS (WICHTIG)
TEST 1 — LIST MODE
Input: "letzten 3 videos von xy"

EXPECT:
- response.videos.length == 3
- NO selected_video
- NO modal trigger
TEST 2 — SINGLE MODE
Input: "neuestes video von xy"

EXPECT:
- selected_video exists
- modal opens
TEST 3 — FILTER
Input: "videos von xy januar 2024"

EXPECT:
- videos[].published_at in range
🚨 HÄUFIGSTER FEHLER (WARUM ES BEI DIR NICHT LÄUFT)

👉 Dein System behandelt LIST und SINGLE gleich.

Symptom:

Tool liefert 1 Video obwohl mehrere gewünscht
Oder startet direkt Video

Fix:
👉 mode MUSS explizit sein

💎 FINALER KERNSATZ

"Single Video = Entscheidung des Systems
Liste = Entscheidung des Users"

✅ IMPLEMENTIERUNGSREIHENFOLGE
mode Parameter einführen
Orchestrator Intent Detection
Backend LIST Pipeline
Response Format trennen
Frontend Rendering
Tests
🏁 ERGEBNIS

Nach Umsetzung kannst du:

✅ "letzten 3 videos"
✅ "videos aus monat X"
✅ "videos zu thema Y"
✅ Klick → Modal

UND:
👉 Dein bestehendes System bleibt 100% stabil

💬 OPTIONAL (NEXT LEVEL)

Später möglich:

Sortierung (views, date)
Pagination
Infinite scroll
"mehr laden" Button
🔥 FAZIT

Das ist exakt die Stelle, wo Systeme entweder:
❌ kaputt refactored werden
oder
💎 sauber skalieren

👉 Mit diesem Ansatz skalierst du sauber.