# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-004
- **Backlog Title:** Intent-Resolver erkennt Filesystem-Befehle fälschlich als Calendar-Intent
- **Type:** BUG

## 2. Problem / Wunsch
Filesystem-Befehle werden vom Intent-Resolver fälschlich als Calendar-Intent erkannt, was dazu führt, dass calendar.list_events erzwungen wird statt Filesystem-Tools aufzurufen. Dies resultiert in 504 Deadline Exceeded Fehlern und blockiert kritische Filesystem-Operationen.

## 3. Expected Behavior
Prompt "erstell auf dem desktop einen ordner 'Bilder' und verschiebe jpg/png dateien" wird als Filesystem-Intent erkannt und filesystem.create_directory / filesystem.move_files aufgerufen.

## 4. Current Behavior
Entity-Resolver erkennt "Ordner" als WEAK_MATCH (unterhalb des Threshold), zwingt calendar.list_events (VIDEO-FORCE), Filesystem-Tools werden nie aufgerufen, Request endet mit 504 Deadline Exceeded. Massive GEMINI-THOUGHT-SIGNATURE Loop logs zeigen wiederholte Aufrufe von calendar_list_events.

## 5. Scope
### IN SCOPE
- Intent-Resolver: Priorisierung von Filesystem-Keywords über Calendar-Keywords bei eindeutigem Dateisystem-Kontext
- Entity-Resolver: Aggressives Calendar-Safety-Net bei Wörtern wie "Ordner" reduzieren
- Orchestrator: Vermeidung von VIDEO-FORCE bei Filesystem-Intents
- Skill-Selector: Korrekte Erkennung von Filesystem- vs Calendar-Intents

### OUT OF SCOPE
- Calendar-Funktionalität ändern (nur bei Filesystem-Intents)
- Allgemeine Intent-Resolver-Architektur neu designen
- Neue Tools hinzufügen

## 6. Functional Requirements
- Intent-Resolver muss Filesystem-Keywords (desktop, ordner, dateien, verschiebe, erstellen) höher priorisieren als Calendar-Keywords (ordner, events) wenn der Kontext eindeutig Dateisystem-Operationen anfordert
- Entity-Resolver darf keine WEAK_MATCH Calendar-Entities erzwingen wenn Filesystem-Tools verfügbar sind und der Prompt Filesystem-Operationen anfordert
- VIDEO-FORCE darf nicht bei Filesystem-Intents angewendet werden
- Fallback-Logik muss Filesystem-Tools bevorzugen wenn Calendar-List-Events keinen Sinn ergibt

## 7. Acceptance Criteria
- [ ] Filesystem-Intents werden korrekt erkannt (nicht als Calendar-Intent)
- [ ] "Ordner" im Kontext von Dateisystem-Operationen wird nicht als Calendar-Entity gematcht
- [ ] Filesystem-Tools werden aufgerufen wenn Prompt eindeutig Filesystem-Operation anfordert
- [ ] Kein 504 Timeout durch falsch erzwungene Tools

## 8. Evidence
- Backend-Log: `💎 ENTITY-RESOLVER FALLBACK_TO_LIST: mutation target 'Ordner' is WEAK_MATCH (below_threshold). Forcing list_events for provider=gemini`
- Backend-Log: `💎 VIDEO-FORCE (stream): Forcing tool_choice=calendar.list_events on iteration 0`
- Frontend-Konsole: `[SSE] Error chunk: 504 Deadline Exceeded`
- Massive GEMINI-THOUGHT-SIGNATURE Loop logs (calendar_list_events wird wiederholt aufgerufen)
- Reproduktions-Prompt: "hi, erstell auf dem desktop einen ordener "Bilder" und verschiebe alles jpg und png dateien vom desktop in diesen ordner"

## 9. Risks
- Änderung an Intent-Resolver könnte andere Intents beeinflussen (Regression)
- Entity-Resolver Änderung könnte Calendar-Fälle brechen
- Komplexe Interaktion zwischen Intent-Resolver, Entity-Resolver, Orchestrator, Skill-Selector

## 10. Validation Mapping
- Filesystem-Intents werden korrekt erkannt → Manueller Test mit Reproduktions-Prompt
- "Ordner" wird nicht als Calendar-Entity gematcht → Backend-Log Prüfung auf ENTITY-RESOLVER FALLBACK_TO_LIST
- Filesystem-Tools werden aufgerufen → Backend-Log Prüfung auf filesystem.create_directory / filesystem.move_files Aufrufe
- Kein 504 Timeout → Frontend-Konsole Prüfung auf erfolgreiche Response

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
