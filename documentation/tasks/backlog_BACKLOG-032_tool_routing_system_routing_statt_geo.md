# BACKLOG TASK – BACKLOG-032 – Falsches Tool Routing: system_routing statt system.geo

**KORREKTUR:** Die ursprüngliche Task-Beschreibung war inkorrekt. Das Tool heißt bereits korrekt `system.routing`.

**EIGENTLICHES PROBLEM:** Gemini zeigt keine "Quelle: OSRM" Attribution an, während GPT sie korrekt anzeigt.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-032
- **Beeinflusst:** Intent Engine / Skill Selector / Tool Routing
- **Risiko-Einschätzung:** MEDIUM

## 3. Scope
### IN SCOPE
- Attribution-Logik prüfen: Warum zeigt GPT "Quelle: OSRM" aber Gemini nicht?
- Attribution-Logik für Gemini korrigieren
- TestSpec TC-003 korrigieren: `system.geo` → `system.routing` (bereits erledigt)

### OUT OF SCOPE
- Keine Änderung an der Antwortqualität (Antwort ist bereits korrekt)
- Keine Änderung an anderen Geo-Tools oder -Intents

## 4. Umsetzungsschritte
1. TestSpec korrigiert: `system.geo` → `system.routing` ✅
2. Attribution-Logik analysieren: `append_routing_attribution_from_tools` in `backend/renderers/attribution.py`
3. Provider-spezifische Unterschiede prüfen (GPT vs Gemini)
4. Attribution-Logik für Gemini korrigieren
5. Validierung: Beide Provider zeigen "Quelle: OSRM"

## 5. Acceptance Criteria
- [x] TestSpec TC-003 korrigiert: erwartet jetzt `system.routing`
- [x] GPT zeigt "Quelle: OSRM" Attribution ✅
- [x] Attribution-Logik für system_routing angepasst ✅
- [ ] Gemini zeigt "Quelle: OSRM" Attribution (BLOCKED durch Tool-Namen-Auflösung)
- [ ] Tieferes Problem: BACKLOG-033 erstellt

## 6. Tests / Validierung
- Manual Test (GPT): "Wie weit ist Berlin von München?" → Antwort mit "Quelle: OSRM" ✅
- Manual Test (Gemini): "Wie weit ist Berlin von München?" → Antwort OHNE "Quelle: OSRM" ❌
- Attribution-Logik angepasst: erkennt auch `system_routing` ✅
- Tieferes Problem erkannt: Gemini kann `system_routing` nicht zu `system.routing` auflösen
- BACKLOG-033 erstellt für Tool-Namen-Auflösungs-Fix ✅

## 7. Status
- **Status:** BLOCKED - WAITING FOR BACKLOG-034
- **Reason:** system.routing wird aus Tool-Liste entfernt (BACKLOG-034 erstellt)
- **Next Step:** BACKLOG-034 fixen, dann BACKLOG-032 validieren
- **Assigned Model:** SWE 1.6

## 8. Dependencies
- BACKLOG-033 (Mapping funktioniert - COMPLETED)
- BACKLOG-034 (Tool-Filter-Problem - BLOCKER)
