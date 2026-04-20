FEATURE DOSSIER: VIDEO UNDERSTANDING SKILL (Transcript / Summary / Compare Engine)
🧠 1. ZIEL DES FEATURES

Der Video Understanding Skill ermöglicht Janus, Inhalte aus Videos semantisch zu verstehen, zusammenzufassen und zu vergleichen.

💥 CORE VALUE

💎 „Janus versteht Videos wie Textdokumente – nicht nur als Abspielmedium.“

🚨 2. PROBLEM (AKTUELLER ZUSTAND)
❌ Video = Black Box
User schaut Video im Modal
Kontext geht verloren
Inhalte müssen manuell konsumiert werden
❌ Limitierung
kein echtes Verständnis
keine Vergleichsfunktion
keine Wissensextraktion
💎 3. LÖSUNG

👉 Extrahiere Video-Transkript → transformiere in strukturierte Wissensrepräsentation → nutze LLM für Aufgaben (Summary, Compare, Explain)

🧱 4. ARCHITEKTURPOSITION
User Prompt
   ↓
Janus Intent Detection
   ↓
Video Context Resolver (Modal / last videoId)
   ↓
💎 Video Understanding Skill (THIS)
   ↓
Transcript Retrieval Layer
   ↓
LLM Processing Engine
   ↓
Chat Output / Actions (MCL optional)
⚙️ 5. TECHNISCHER KONTRAKT
📥 INPUT (Pydantic)
class VideoUnderstandingInput(BaseModel):
    video_id: str
    task: str  # summarize | explain | compare | extract_steps | critique
    second_video_id: str | None = None
    language: str = "de"
    detail_level: str = "medium"
📤 OUTPUT
class VideoUnderstandingOutput(BaseModel):
    summary: str
    key_points: list[str]
    structured_notes: dict | None
    comparison: dict | None
    source_video_ids: list[str]
🔍 6. TRANSCRIPT RETRIEVAL LAYER
🎯 Primärquelle

👉 YouTube Data API (captions endpoint)

🔄 Fallbacks
🥈 Option 2:
yt-dlp (subtitle extraction)
🥉 Option 3:
Audio → Speech-to-Text Pipeline (später)
❗ REQUIREMENT

Video ohne Transcript → Skill muss sauber fallbacken

🧠 7. CORE PIPELINE
STEP 1: VIDEO VALIDIERUNG
video exists
captions available (if possible)
STEP 2: TRANSCRIPT NORMALISIERUNG
remove timestamps
merge sentence fragments
language detection
STEP 3: CHUNKING
Transcript → chunks (2000–4000 tokens)
STEP 4: LLM PROCESSING
TASK TYPES:
🟢 Summary
Kurzfassung
strukturierte Punkte
🟡 Explanation
vereinfachte Erklärung
🔵 Extraction
Schritt-für-Schritt Guides
🔴 Comparison
Video A vs Video B
⚖️ 8. VIDEO COMPARISON ENGINE
INPUT:
{
  "video_a": "...",
  "video_b": "...",
  "criteria": ["clarity", "depth", "accuracy"]
}
OUTPUT:
Gemeinsamkeiten
Unterschiede
Empfehlung
Use-case suitability
🧩 9. CONTEXT BINDING (WICHTIG)
Modal Integration

Wenn Video im Modal geöffnet wurde:

last_active_video_id → stored in session context
Chat Example:

User:

„fass das zusammen“

👉 Janus erkennt:

active video context
🖥️ 10. OUTPUT FORMATS
🟢 Summary
- Hauptidee
- Key Points
- Fazit
🟡 Structured Notes
{
  "sections": [],
  "steps": []
}
🔵 Comparison
{
  "video_a": {},
  "video_b": {},
  "winner": "A",
  "reason": ""
}
⚠️ 11. EDGE CASES
❗ Kein Transcript verfügbar

→ fallback:

„Kein Text verfügbar“
optional Audio-STT später
❗ Sehr lange Videos

→ chunk + map-reduce summarization

❗ Mehrsprachigkeit

→ auto language detection + translation layer

🔐 12. PERFORMANCE & RELIABILITY
Caching (WICHTIG)
transcript cache pro video_id
TTL: 24h–7d
Parallelisierung
chunk processing parallel möglich
🧠 13. SKILL INTELLIGENCE LEVELS
Level 1:
einfache Zusammenfassung
Level 2:
strukturierte Notizen
Level 3:
Vergleich + Analyse
Level 4:
Multi-Video Knowledge Synthesis
📡 14. INTEGRATION MIT MCL
Optional Action Output:
{
  "actions": [
    {
      "type": "update_chat",
      "payload": {
        "message": "Summary generated"
      }
    }
  ]
}
🔥 15. SYSTEM-DEFINITION

💎 Der Video Understanding Skill transformiert Videos in strukturierte, wiederverwendbare Wissenseinheiten.

🚀 16. ZUKUNFTS-EXTENSIONS
automatische Lernnotizen
Quiz Generator aus Videos
Knowledge Base Speicherung
„Erkläre mir das wie einem Anfänger“-Modus
Multi-Video Research Mode
💎 FINAL STATEMENT

❌ Video = passiver Content
✔ Video = strukturierte Wissensquelle

💎 „Janus macht aus Videos Wissen, nicht nur Wiedergabe.“