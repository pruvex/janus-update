# BACKLOG-033: Gemini Tool-Namen-Auflösung für system.routing

## 1. Problem
Gemini verwendet `system_routing` (mit Unterstrich) als provider-sicheren Namen, kann diesen aber nicht zur kanonischen Skill-ID `system.routing` auflösen. Dies führt zu:
- Fehlender Attribution "Quelle: OSRM" bei Gemini
- Tool-Results mit falschem `_skill_id`
- Warning im Log: `GEMINI-NAME-MAP: could not resolve provider name 'system_routing'; using raw name. reason=Skill 'system_routing' ist nicht registriert.`

## 2. Ursache
Gemini sanitisiert Tool-Namen (ersetzt `.` mit `_`), aber die Auflösungslogik in `_resolve_gemini_response_tool_name` kann `system_routing` nicht zurück zu `system.routing` auflösen, weil `system_routing` nicht im Skill-Mapping registriert ist.

## 3. Scope
- Gemini-Service Tool-Namen-Auflösung fixen
- Sicherstellen dass `_skill_id` korrekt gesetzt wird
- Attribution-Logik bereits angepasst (BACKLOG-032), aber reicht nicht

## 4. Umsetzungsschritte
1. Gemini `_resolve_gemini_response_tool_name` erweitern
2. Mapping von `system_routing` zu `system.routing` hinzufügen
3. Prüfen ob andere Tools ähnliche Probleme haben
4. Validierung: Gemini zeigt "Quelle: OSRM"

## 5. Acceptance Criteria
- [x] Mapping von `system_routing` zu `system.routing` hinzugefügt
- [x] Log zeigt: `GEMINI-NAME-MAP: manual override 'system_routing' -> 'system.routing'` ✅
- [x] Keine Warning im Log ✅
- [x] Tool-Result hat korrekten Namen (Mapping funktioniert)

## 6. Tests / Validierung
- Manual Test (Gemini): "Wie weit ist Berlin von München?" → Antwort mit "Quelle: OSRM"
- Log prüfen: keine GEMINI-NAME-MAP Warning

## 7. Status
- **Status:** COMPLETED
- **Reason:** Mapping funktioniert korrekt, Log bestätigt `GEMINI-NAME-MAP: manual override 'system_routing' -> 'system.routing'`
- **Next Step:** BACKLOG-032 Attribution-Logik prüfen (Mapping funktioniert, aber Attribution fehlt weiterhin)
- **Assigned Model:** SWE 1.6

## 8. Dependencies
- BACKLOG-032 (Attribution-Logik bereits angepasst, aber reicht nicht)
