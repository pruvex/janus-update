FEATURE DOSSIER: VIDEO SEARCH SKILL (YouTube Integration)
🧠 1. Ziel des Features

Der Video Search Skill ermöglicht es Janus, zuverlässig funktionierende, relevante YouTube-Videos zu finden und direkt im Modal-System darzustellen.

💥 Core Value

💎 „Janus liefert echte, funktionierende Videos — keine halluzinierten Links.“

🚨 2. PROBLEM (KRITISCH)
❌ Aktueller Zustand
LLM generiert YouTube-Links selbst
Videos sind:
gelöscht
privat
falsch
nicht einbettbar
❌ Ergebnis

„Dieses Video ist nicht mehr verfügbar“

💎 Lösung

👉 Alle Videos kommen ausschließlich aus echten APIs

🧱 3. ARCHITEKTURPOSITION
User Prompt
   ↓
Janus (Intent Detection)
   ↓
💎 Video Search Skill (THIS)
   ↓
YouTube API
   ↓
Validiertes Video
   ↓
MCL (Modal Request)
   ↓
Universal Modal System
   ↓
Video Renderer
⚙️ 4. TECHNISCHER KONTRAKT
📥 INPUT (Pydantic Schema)
class VideoSearchInput(BaseModel):
    query: str
    max_results: int = 5
    min_views: int = 10000
    safe_search: bool = True
📤 OUTPUT (Pydantic Schema)
class VideoResult(BaseModel):
    video_id: str
    title: str
    channel: str
    views: int
    thumbnail: str
    embed_url: str

class VideoSearchOutput(BaseModel):
    selected_video: VideoResult
🔍 5. KERNLOGIK
Schritt 1: Query vorbereiten
User Prompt → saubere Suchanfrage
ggf. vereinfachen / präzisieren
Schritt 2: API Call

👉 YouTube Data API

GET https://www.googleapis.com/youtube/v3/search
Schritt 3: Details abrufen
GET /videos?part=statistics,status
Schritt 4: Validierung
❗ Video MUSS:
existieren
öffentlich sein
embeddable = true
Views > min_views
Schritt 5: Ranking
Kriterien:
Relevanz (Titel vs Query)
Views
Kanalqualität
Aktualität
Schritt 6: Bestes Video auswählen
🎯 6. OUTPUT → MCL INTEGRATION
💎 Wichtig:

Kein URL-Spam — nur strukturierte Daten

{
  "actions": [
    {
      "type": "open_modal",
      "modal_type": "video",
      "payload": {
        "videoId": "abc123",
        "title": "Flammkuchen Rezept",
        "embedUrl": "https://www.youtube.com/embed/abc123"
      }
    }
  ]
}
🖥️ 7. VIDEO RENDERER (FRONTEND)
🎬 iFrame Nutzung
<iframe
  src="https://www.youtube.com/embed/VIDEO_ID"
  allowfullscreen
></iframe>
❗ WICHTIG:

❌ NICHT:

youtube.com/watch?v=
💎 SONDERN:
youtube.com/embed/
🔐 8. VALIDATION LAYER
Backend Checks:
video_id vorhanden
embed erlaubt
nicht privat / gelöscht
Fallback:
{
  "text": "Ich konnte kein passendes Video finden."
}
🔄 9. RESILIENCE
Retry Logik:
API Fehler → Retry (max 2x)
keine Ergebnisse → Query anpassen
Fallback Strategie:
breitere Suche
weniger strenge Filter
📊 10. QUALITÄTSFILTER
Default Filter:
min_views: 10k–50k
Sprache passend zum User
keine Shorts (optional)
Optional:
max Duration
HD bevorzugen
🧠 11. SMART QUERY OPTIMIZATION
Beispiele:

User:

„Zeig mir wie man Flammkuchen macht“

→ Query:

flammkuchen rezept einfach deutsch

User:

„React Tutorial“

→ Query:

react tutorial beginner 2025
⚠️ 12. EDGE CASES
❗ Keine Ergebnisse

→ Fallback-Message

❗ Video nicht embeddable

→ nächstes Video nehmen

❗ Region-Lock

→ API filtert (so gut wie möglich)

🔐 13. SICHERHEIT
keine direkte URL vom LLM
nur API-Daten verwenden
keine Script-Injection
📈 14. BENCHMARKING

Testfälle:

Rezept-Videos
Tutorials
Produktvideos
Ziel:
100% funktionierende Videos
hohe Relevanz
🧠💎 15. SYSTEM-DEFINITION

💎 Der Video Search Skill ist die einzige Quelle für Video-Inhalte in Janus.

🚀 16. ERWEITERUNGEN (ZUKUNFT)
mehrere Videos anzeigen (Gallery-Modal)
Autoplay Playlist
Video Summary (AI)
Timestamp Navigation
💎 FINAL FAZIT

❌ keine kaputten Links
❌ keine Halluzinationen

💎 „Jedes Video ist valide, relevant und direkt abspielbar.“