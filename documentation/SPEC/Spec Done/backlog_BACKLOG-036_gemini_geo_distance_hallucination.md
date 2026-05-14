# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-036
- **Backlog Title:** Gemini Halluzination: Geo-Distanz ohne Tool-Call (TC-003)
- **Type:** BUG

## 2. Problem / Wunsch
Gemini antwortet auf Geo-Distanz-Abfragen ("Wie weit ist Berlin von München?") ohne Tool-Call zu system.routing. Die Antwort enthält die Distanz (585 km) aber keine "Quelle: OSRM" Attribution. GPT führt korrekt Tool-Call aus und zeigt Attribution. Dies ist ein Provider-Parity-Problem spezifisch für Gemini.

## 3. Expected Behavior
Bei Geo-Distanz-Abfragen sollte Gemini system.routing Tool aufrufen und "Quelle: OSRM" Attribution anzeigen.

## 4. Current Behavior
Gemini antwortet mit Halluzination (Distanz ohne Tool-Call). GPT ruft system.routing korrekt auf.

## 5. Scope
### IN SCOPE
- Analyse warum Gemini system.routing nicht aufruft bei Geo-Distanz-Intents
- Intent-Routing-Logik für Gemini spezifisch prüfen
- Tool-Selection-Logik für Gemini prüfen
- Fix damit Gemini system.routing aufruft wie GPT
- Attribution-Logik sicherstellen für Gemini

### OUT OF SCOPE
- Änderungen an GPT-Routing (funktioniert bereits)
- Änderungen an anderen Tool-Typen
- Allgemeine Performance-Optimierung

## 6. Functional Requirements
- Gemini muss system.routing Tool bei Geo-Distanz-Intents aufrufen
- Gemini muss "Quelle: OSRM" Attribution anzeigen
- Tool-Routing muss für Gemini wie für GPT funktionieren

## 7. Acceptance Criteria
- [ ] Gemini ruft system.routing Tool bei Geo-Distanz-Abfragen auf
- [ ] Gemini zeigt "Quelle: OSRM" Attribution an
- [ ] Tool-Routing funktioniert für Gemini wie für GPT

## 8. Evidence
- TestRun: TEST-RUN-2026-05-13-BENCHMARK-V2-5
- TC-003-GEMINI evidence: documentation/test-results/TEST-RUN-2026-05-13-002/TC-003-GEMINI_evidence.json
- TC-003-GPT evidence: documentation/test-results/TEST-RUN-2026-05-13-002/TC-003-GPT_evidence.json
- Classification: TOOL_ROUTING_FAILURE
- Note: "Expected tool 'system.routing' was not triggered. Tools called: none"

## 9. Risks
- Provider-spezifische Fixes könnten andere Gemini-Intents beeinflussen
- Änderungen am Intent-Engine könnten GPT-Verhalten ändern (Regression)

## 10. Validation Mapping
- Gemini ruft system.routing Tool bei Geo-Distanz-Abfragen auf → Manueller Janus Test mit Gemini
- Gemini zeigt "Quelle: OSRM" Attribution an → Manueller Janus Test mit Gemini
- Tool-Routing funktioniert für Gemini wie für GPT → Vergleich Gemini vs GPT

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.

## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** PASS
- **Completed At:** 2026-05-14
- **Completed By:** SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
- **Validation Evidence:** Skill 6 Final Audit PASS after Skill 5 Debug + manual retest PASS (Playwright E2E Test TASK-036-02)
