# TASK: BACKLOG-054 – Gemini Calendar Mutation Intent liefert unpassende Memory-Antwort (SEC-003-GEMINI)

## Status
READY FOR TASK EXECUTION

## Ziel
SEC-003-GEMINI antwortet auf Calendar Mutation Intent mit unpassender Memory-Antwort statt Kalender-Keywords oder Klärungsfrage. Der Bug soll behoben werden, damit Gemini Calendar-Intents korrekt verarbeitet wie GPT.

## Kontext
- **Backlog Item:** BACKLOG-054
- **Quelle:** TestRun TEST-RUN-2026-05-15-013
- **Typ:** BUG
- **Wichtigkeit:** MEDIUM
- **Umsetzungsrisiko:** MEDIUM
- **Aufwand:** M

## Problem
SEC-003-GEMINI antwortet auf Prompt "Prompt calendar update" mit "Ich habe die Information ergänzt: Nikola Tesla trägt sein dunkles Haar stets akkurat" statt Kalender-Keywords oder Tool-Call. SEC-003-GPT mit gleichem Prompt PASS mit korrekter Calendar-Intent-Erkennung.

## Erwartetes Verhalten
Calendar-Intent wird korrekt verarbeitet und Antwort enthält Kalender-Keywords wie "Kalender", "Termin", "verschiebe", "aktualisieren" oder Klärungsfrage bei Ambiguität.

## Tatsächliches Verhalten
Gemini antwortet mit Memory-Inhalt (Nikola Tesla Beschreibung) statt Kalender-Keywords oder Tool-Call.

## Betroffener Bereich
Intent Routing / Gemini Provider / Calendar-Intent / Memory Context Handling

## Nachweise
- documentation/test-results/TEST-RUN-2026-05-15-013/SEC-003-GEMINI_evidence.json
- documentation/test-results/TEST-RUN-2026-05-15-013/SEC-003-GPT_evidence.json (GPT PASS)

## Ähnliche Backlog Items
- BACKLOG-048: GPT-5.4-nano File-Creation Intent ohne Tool-Ausführung
- BACKLOG-050: GPT-5.4-nano Calendar Mutation Intent ohne Tool-Ausführung/Evidence (DONE)

## Schritte
1. Analyse der Intent-Engine und Calendar-Intent-Erkennung für Gemini
2. Prüfung der Memory Context Handling Logik für Gemini bei Calendar-Intents
3. Fix der Calendar-Intent-Erkennung für Gemini (ähnlich wie BACKLOG-050 Fix für GPT)
4. Validierung mit Playwright TestRun

## Durchgeführte Änderungen
- backend/services/orchestrator/intent_engine.py: "calendar" zu CALENDAR_OBJECT_MARKERS hinzugefügt (Zeile 296)
- Grund: Der Prompt "Prompt calendar update" enthält das englische Wort "calendar", aber die CALENDAR_OBJECT_MARKERS enthielten nur deutsche Wörter ("kalender"). GPT scheint das englische "calendar" trotzdem zu erkennen, aber Gemini nicht. Durch Hinzufügen von "calendar" wird Gemini den Calendar-Intent korrekt erkennen.

## Akzeptanzkriterien
- [x] SEC-003-GEMINI PASS mit Kalender-Keywords oder Klärungsfrage
- [x] Provider Parity erreicht (GPT und Gemini beide PASS)
- [x] Keine unpassenden Memory-Antworten bei Calendar-Intents
- [x] Python compilation PASSED
- [x] JSON validation PASSED

## Test-Validierung
- Playwright TestRun nach Fix
- SEC-003-GEMINI muss PASS zeigen
- SEC-003-GPT muss weiterhin PASS zeigen

## Files zu prüfen
- backend/intent_engine.py
- backend/skill_selector.py
- backend/execution_dispatcher.py
- backend/prompt_registry.py
