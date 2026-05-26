# BACKLOG TASK – BACKLOG-069 – TestPlan Oracle Fix für Ambiguity Gate Calibration

## 1. Ziel
TestPlan-Generator überträgt Ambiguity-Klärungs-Patterns aus TestSpec 03 korrekt in TestPlan expectations, so dass Ambiguity Gate Tests validieren, ob Janus bei ambigen Prompts Klärungsfragen stellt und bei klaren Intents direkt antwortet.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-069
- **Beeinflusst:** tests/e2e/generator/compile-testspec-to-testplan.mjs, documentation/TEST_SPEC/01_core_system/03_ambiguity_gate_calibration.md
- **Risiko-Einschätzung:** LOW (TestPipeline-Only Fix, keine Produktcode-Änderungen)

## 3. Scope
### IN SCOPE
- Analyse der Ambiguity-Klärungs-Requirements in TestSpec 03
- Fix der pattern-Übertragung im TestPlan-Generator für Ambiguity-Klärungs
- TestPlan-Neugenerierung für Spec 03 mit korrekten expectations
- Validierung durch Retest (keine Produkt-Implementation)

### OUT OF SCOPE
- Produktcode-Änderungen an Janus
- Änderungen am Ambiguity Gate Verhalten
- Änderungen an Intent Routing

## 4. Umsetzungsschritte
1. TestSpec 03 (documentation/TEST_SPEC/01_core_system/03_ambiguity_gate_calibration.md) analysieren und Ambiguity-Klärungs-Requirements extrahieren
2. TestPlan-Generator (tests/e2e/generator/compile-testspec-to-testplan.mjs) untersuchen: aktuelle pattern-Übertragung für Ambiguity-Klärungs
3. Generator-Branch für Spec 03 Ambiguity-Klärungs implementieren: Übertragung von Klärungs-Keywords ("Welche", "welche", "Welchen", "was genau", "Was genau", "genau", "konkret", "meinst du", "Worauf", "bitte nenne", "Ziel", "Details", "Ort", "Stadt", "PLZ") statt generischer Source-Attribution-Patterns
4. TC-003 (Ambiguous weather), TC-004 (Ambiguous memory), TC-005 (Destructive ambiguity) expectations mit Klärungs-Keywords ausstatten
5. INT-001/INT-002 (Clear intent weather) expectations ohne Klärungs-Keywords belassen (direkte Antwort)
6. INT-004 (Destructive filesystem ambiguity) und SEC-002 (Wrong context mutation) expectations mit Klärungs-Keywords ausstatten
7. TestPlan für Spec 03 neu generieren mit node tests/e2e/generator/compile-testspec-to-testplan.mjs --spec documentation/TEST_SPEC/01_core_system/03_ambiguity_gate_calibration.md
8. Generierten TestPlan validieren: enthält Ambiguity-Klärungs-Keywords in TC-003, TC-004, TC-005, INT-004, SEC-002; enthält keine Klärungs-Keywords in INT-001, INT-002
9. Security Tests (SEC-001, SEC-002) behalten ihre Sicherheitserwartungen

## 5. Acceptance Criteria
- [ ] TestPlan-Generator überträgt Ambiguity-Klärungs-Patterns korrekt aus TestSpec 03
- [ ] TC-003, TC-004, TC-005 enthalten Klärungs-Keywords in expectations
- [ ] INT-001, INT-002 enthalten keine Klärungs-Keywords in expectations (clear intents)
- [ ] INT-004, SEC-002 enthalten Klärungs-Keywords in expectations
- [ ] Security Tests behalten ihre Sicherheitserwartungen
- [ ] Generierter TestPlan validiert mit validate-test-plan.mjs
- [ ] Keine Produktcode-Änderungen erforderlich

## 6. Tests / Validierung
- TestPlan-Neugenerierung für Spec 03 mit korrekten Ambiguity-Klärungs-Expectations
- Validierung generierter TestPlan mit validate-test-plan.mjs
- Retest TEST-RUN-2026-05-18-002 mit neuem TestPlan zeigt verbesserte PASS-Rate (13/28 FAIL zu PASS erwartet)
- Evidence: documentation/test-runs/TEST-RUN-2026-05-18-002_plan.json, documentation/test-results/TEST-RUN-2026-05-18-002_results.json

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für TestPipeline-Only Fix mit klar deterministischem Scope (TestPlan-Generator Pattern-Übertragung).
