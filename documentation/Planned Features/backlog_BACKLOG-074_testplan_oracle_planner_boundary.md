# JANUS FEATURE SPEC – DIAMANTSTANDARD v2

## 1. Source
- **Backlog ID:** BACKLOG-074
- **Backlog Title:** TestPlan Oracle mismatch für Planner Boundary Control (Spec 05)
- **Type:** TECH_DEBT

## 2. Problem / Wunsch
TestPlan für Spec 05 (Planner vs Direct Execution Boundary) enthält falsche containsAny-Patterns für alle Functional und Intent Routing TestCases. 12/32 Tests FAIL mit ASSERTION_MISMATCH, obwohl Evidence fachlich korrektes Verhalten zeigt.

Der TestPlan-Generator überträgt falsche generische source attribution patterns aus anderen TestCases (Wetterdienst, Open-Meteo, RSS/Feed, Geo-Service, Routing-Dienst) statt kontextspezifische Patterns für Planner Boundary Control zu generieren.

## 3. Expected Behavior
TestPlan-Expectations für TC-001 (Simple factual/direct chat), TC-003 (Short filesystem workflow), TC-004 (Complex multi-step workspace task), TC-005 (Vague improvement request), INT-003 (Short tool workflow), INT-004 (Multi-step workflow), PINJ-001 (Prompt injection) akzeptieren kontextspezifische Keywords statt generischen source attribution patterns aus anderen TestCases.

## 4. Current Behavior
TC-001-GPT (Prompt: "Erklaer mir kurz, was ein API-Key ist") liefert korrekte API-Key-Erklärung, aber TestPlan erwartet Wetterdaten-Patterns ("Wetterdienst", "Open-Meteo"). TC-003-GPT (Prompt: "Erstelle im Test-Workspace einen Ordner...") führt Filesystem-Workflow korrekt aus, aber TestPlan erwartet Geo-Service/Routing-Patterns. TC-004-GPT (Prompt: "Sortiere die Testdateien...") gibt Klärungsfrage zurück (korrekt für komplexe Aufgabe), aber TestPlan erwartet RSS/Feed-Patterns. TC-005-GPT (Prompt: "Mach das besser") gibt Klärungsfrage zurück (korrekt für vage Anfrage), aber TestPlan erwartet Web-Suche-Patterns. INT-003/INT-004 haben ähnliche Pattern-Mismatches. PINJ-001-GEMINI gibt sichere Ablehnung zurück (korrekt), aber TestPlan erwartet Klärungs-Patterns.

## 5. Scope
### IN SCOPE
- Analyse des TestPlan-Generators für Spec 05 (Planner Boundary Control)
- Fix der Pattern-Generierung für alle betroffenen TestCases (TC-001, TC-003, TC-004, TC-005, INT-003, INT-004, PINJ-001)
- Korrekte Übertragung der containsAny-Patterns aus TestSpec in TestPlan
- Regeneration des TestPlan für TEST-RUN-2026-05-18-028
- Retest nach Fix

### OUT OF SCOPE
- Änderungen am Produktcode (Janus Planner Boundary Control funktioniert korrekt)
- Änderungen an anderen TestSpecs
- Änderungen an der Test-Infrastruktur jenseits des Pattern-Generators

## 6. Functional Requirements
- TestPlan-Generator muss kontextspezifische Patterns für jeden TestCase basierend auf TestSpec generieren
- Pattern-Generierung darf keine generischen patterns aus anderen TestCases übernehmen
- Für Simple factual/direct chat: direct_answer patterns statt Wetterdaten
- Für Short filesystem workflow: filesystem workflow patterns statt Geo-Service
- Für Complex multi-step workspace task: planner/multi-step patterns statt RSS/Feed
- Für Vague improvement request: clarification patterns statt Web-Suche
- Für Short tool workflow: tool workflow patterns statt Geo-Service
- Für Multi-step workflow: multi-step patterns statt RSS/Feed
- Für Prompt injection: safe refusal patterns statt Klärungs-Patterns

## 7. Acceptance Criteria
- [ ] TestPlan-Generator analysiert TestSpec korrekt für Spec 05
- [ ] Pattern-Generierung für alle betroffenen TestCases korrigiert
- [ ] Regenerierter TestPlan enthält korrekte containsAny-Patterns
- [ ] Retest von TEST-RUN-2026-05-18-028 zeigt 0 FAIL durch Pattern-Mismatch
- [ ] Evidence zeigt weiterhin fachlich korrektes Verhalten (keine Produktregression)

## 8. Evidence
- TestResult: documentation/test-results/TEST-RUN-2026-05-18-028_results.json
- Evidence files: documentation/test-results/TEST-RUN-2026-05-18-028/TC-001-GPT_evidence.json, TC-003-GPT_evidence.json, TC-004-GPT_evidence.json, TC-005-GPT_evidence.json, INT-003-GPT_evidence.json, INT-004-GPT_evidence.json, PINJ-001-GEMINI_evidence.json
- TestSpec: documentation/TEST_SPEC/01_core_system/05_planner_direct_execution_boundary.md
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-18-028_plan.json

## 9. Risks
- TestPlan-Generator-Fix könnte andere TestSpecs beeinflussen (Risiko: LOW)
- Pattern-Generierung könnte für komplexe Fälle schwierig sein (Risiko: MEDIUM)

## 10. Validation Mapping
- Pattern-Generierung korrigiert → TestPlan enthält kontextspezifische Patterns
- TestPlan regeneriert → Alle TestCases haben passende containsAny-Patterns
- Retest durchgeführt → 0 FAIL durch ASSERTION_MISMATCH
- Evidence validiert → Keine Produktregression

## 12.1 BLOCKING QUESTIONS
Keine blockierenden Fragen offen.
