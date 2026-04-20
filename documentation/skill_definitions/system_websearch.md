# Skill-Spezifikation: system.websearch (V2.0)

## 1. Funktionale Vision
Der visuelle Informant für Releases, News und Events. Liefert High-End Listen mit dem Ziel: "Keine Anschlussfragen nötig".

## 2. Kern-Kompetenzen
- **High-End Listen:** Strukturierte Daten mit Thumbnails (Roadmap) und Kurz-Infos.
- **Smart Fallback:** Automatischer globaler Research (Englisch) bei Technik/News-Themen.
- **Wikipedia-Bann:** Routing zu Wikipedia erfolgt exklusiv über den Planner/Wiki-Skill.

## 3. Nahtlose Integration
- **Seamless UX:** Erkennt Preise in News-Artikeln und triggert intern `system.price_comparison` zur Verifizierung.
- **Skill-Brücke:** Schlägt proaktiv Kalender-Einträge für gefundene Termine vor.

## 4. Benchmark & Tiering
- **OpenAI:** `gpt-5.4-mini` (Balanced)
- **Gemini:** `gemini-3-flash` (Speed)
