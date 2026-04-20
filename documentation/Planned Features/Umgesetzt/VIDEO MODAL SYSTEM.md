FEATURE 12: VIDEO MODAL SYSTEM + VIDEO SKILL (AI-STUDIO READY)
🧠 1. Ziel des Features

Janus kann auf Anfrage:

relevante Videos finden (z. B. Tutorials, Erklärungen)
diese direkt in einem interaktiven Modal-Player anzeigen
und optional in die Taskleiste integrieren
💥 Core Value

💎 „Information wird nicht nur erklärt — sie wird direkt gezeigt.“

🎯 2. User Experience (Endzustand)
💬 User sagt:

„Zeig mir ein Video, wie man Flammkuchen macht“

👉 Ergebnis:
Chat-Antwort + Kontext
🎬 Video öffnet sich im Modal
optional:
in Taskleiste pinnen
speichern
🧩 3. SYSTEMKOMPONENTEN
1. 🎬 Video Skill

→ findet passende Videos

2. 🖥️ Modal Renderer

→ zeigt Video im Overlay

3. 📌 Taskleisten Integration

→ macht Video persistent

💎 4. SKILL DESIGN (V2.4 STANDARD)
🔹 Ebene 1: Funktionale Vision

Finde ein relevantes Video zur User-Anfrage und liefere strukturierte Daten für Rendering.

🔹 Ebene 2: Input Schema
{
  "query": "string",
  "language": "string (optional)",
  "max_results": "int (default: 3)"
}
🔹 Output Schema
{
  "videos": [
    {
      "title": "string",
      "url": "string",
      "platform": "youtube",
      "thumbnail": "string",
      "duration": "string",
      "channel": "string"
    }
  ]
}
🔹 Ebene 3: Logik
Query → Video API (z. B. YouTube)
Ranking:
Relevanz
Qualität
Sprache
Rückgabe: Top Ergebnisse
🔹 Ebene 4: Metadaten
{
  "skill_name": "video_search",
  "optimal_model_tier": "small"
}
🔹 Ebene 5: Sprach-Ebene
keine Halluzinationen
keine Fake-Videos
nur echte Ergebnisse
🔹 Ebene 6: Renderer

Renderer entscheidet:

Modal öffnen
Video embed anzeigen
ggf. Liste anzeigen
🔹 Ebene 8: Agentic Integration

Beispiel Chain:

User → Intent erkannt
      → video_search
      → Modal Renderer
      → optional: Taskleisten-Pinning
🖥️ 5. VIDEO MODAL SYSTEM
🎬 Eigenschaften
draggable
resizable
closable
persistierbar
📐 Layout
Header
Titel
Quelle (z. B. YouTube)
Aktionen:
📌 Pin
❌ Close
Body
Video Player (Embed)
optional:
Beschreibung
Channel
Footer
„Im Chat speichern“
„In Galerie speichern“
„Neuen Chat daraus erstellen“
🎨 6. UX STATES
Default
Modal geöffnet
Video autoplay optional
Minimized
als Mini-Player unten
Pinned

→ wandert in Taskleiste

📌 7. TASKLEISTEN INTEGRATION
Verhalten:
Video wird als Modul behandelt
erscheint als Icon in Taskleiste
Funktionen:
reopen
close
wechseln zwischen Videos
UX:

💎 „Video wird Teil des Workflows, nicht nur temporärer Content“

⚙️ 8. TECHNISCHE ARCHITEKTUR
Komponenten:
VideoSkillService
ModalManager
TaskbarManager
PlayerComponent
Flow:
User Prompt
   ↓
Intent Detection
   ↓
video_search Skill
   ↓
Renderer entscheidet: Modal öffnen
   ↓
User Interaction
   ↓
optional: Taskleiste Pin
⚠️ 9. EDGE CASES
❗ Kein Video gefunden

→ Fallback:

alternative Vorschläge
Textantwort
❗ mehrere gute Videos

→ Auswahl anzeigen

❗ langsames Laden

→ lazy loading + placeholder

🔐 10. SAFETY & CONTROL
keine Autoplay-Flut
Nutzer entscheidet über Öffnung
vollständige Kontrolle
🚀 11. IMPLEMENTIERUNGSREIHENFOLGE
Phase 1
Video Skill (Search)
Phase 2
Modal Player
Phase 3
Taskleisten Integration
Phase 4
Multi-Video + AI Features
🧠💎 12. ADVANCED FEATURES
🤖 AI Video Understanding
Zusammenfassung
Key Moments
Timestamp Navigation
💬 Beispiel:

„Spring zu der Stelle, wo der Teig gemacht wird“

💎 13. FINAL FAZIT

Dieses Feature verwandelt Janus von:

❌ Text-Assistant

zu:

💎 multimodalem, visuellem Assistenzsystem

👉 perfekt kombinierbar mit:

Multi-Chat
Task-System
Taskleiste