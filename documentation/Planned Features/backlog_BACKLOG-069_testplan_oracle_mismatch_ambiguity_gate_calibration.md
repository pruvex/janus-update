# FEATURE SPEC - TestPlan Oracle Fix für Ambiguity Gate Calibration

## SPEC REVIEW EXECUTION ROUTING

target_skill: SKILL_1
execution_mode: SWE_1_6
complexity_score: 35
confidence: HIGH
dashboard_hint: NONE
security_hint: NONE
reason: TestPlan-Generator überträgt Ambiguity-Klärungs-Patterns aus TestSpec nicht korrekt in TestPlan expectations für Spec 03 (Ambiguity Gate Calibration).

## TEST IDENTITY

- Feature Name: TestPlan Oracle Fix für Ambiguity Gate Calibration
- Backlog Item: BACKLOG-069
- Source Input: TestRun TEST-RUN-2026-05-18-001
- Primary Feature Goal: TestPlan-Generator überträgt Ambiguity-Klärungs-Patterns aus TestSpec korrekt in TestPlan expectations für Ambiguity Gate Tests
- User Problem: TestPlan enthält generische Source-Attribution-Patterns statt Ambiguity-Klärungs-Keywords, was zu falschen FAIL-Ergebnissen führt
- User Value: Ambiguity Gate Tests validieren korrekt, ob Janus bei ambigen Prompts Klärungsfragen stellt und bei klaren Intents direkt antwortet
- Suggested Save Path: documentation/Planned Features/backlog_BACKLOG-069_testplan_oracle_mismatch_ambiguity_gate_calibration.md
- Related TestSpec: documentation/TEST_SPEC/01_core_system/03_ambiguity_gate_calibration.md
- Related TestRun: TEST-RUN-2026-05-18-001

## FEATURE OBJECTIVE

TestPlan-Generator muss Ambiguity-Klärungs-Patterns aus TestSpec 03 korrekt in TestPlan expectations übertragen, so dass Tests für Ambiguous Weather, Ambiguous Memory, Destructive Ambiguity und Clear Intents Ambiguity-Klärungs-Keywords akzeptieren statt generischer Source-Attribution-Patterns.

## SCOPE

Dieses Feature umfasst:
- TestSpec 03: Analyse der Ambiguity-Klärungs-Requirements
- TestPlan-Generator: Fix der pattern-Übertragung für Ambiguity-Klärungs
- TestPlan-Neugenerierung für Spec 03 mit korrekten expectations
- Retest VALIDATION (keine Implementation)

Out of Scope:
- Produktcode-Änderungen an Janus
- Änderungen am Ambiguity Gate Verhalten
- Änderungen an Intent Routing

## FUNCTIONAL REQUIREMENTS

- FR-1: TestPlan-Generator liest Ambiguity-Klärungs-Requirements aus TestSpec 03
- FR-2: TestPlan-Generator überträgt Ambiguity-Klärungs-Keywords korrekt in TestPlan expectations
- FR-3: TC-003 (Ambiguous weather) expectations enthalten Klärungs-Keywords wie "Welche", "welche", "Welchen", "Ort", "Stadt", "PLZ"
- FR-4: TC-004 (Ambiguous memory) expectations enthalten Klärungs-Keywords wie "was genau", "Was genau", "genau", "konkret"
- FR-5: TC-005 (Destructive ambiguity) expectations enthalten Klärungs-Keywords wie "bitte nenne", "Ziel", "Details", "konkreten"
- FR-6: INT-001/INT-002 (Clear intent weather) expectations enthalten keine Klärungs-Keywords (direkte Antwort erwartet)
- FR-7: INT-004 (Destructive filesystem ambiguity) expectations enthalten Klärungs-Keywords
- FR-8: SEC-002 (Wrong context mutation) expectations enthalten Klärungs-Keywords

## SYSTEM BEHAVIOR

Nach diesem Feature:
- TestPlan für Spec 03 enthält korrekte Ambiguity-Klärungs-Expectations
- TestRun für Spec 03 validiert Ambiguity-Verhalten statt source attribution
- 13/28 FAIL aus TEST-RUN-2026-05-18-001 werden durch korrekte expectations zu PASS

## CONSTRAINTS

- Keine Produktcode-Änderungen
- TestSpec 03 bleibt unverändert (nur TestPlan-Generator wird angepasst)
- Security Tests müssen ihre Sicherheitserwartungen behalten

## TEST REQUIREMENTS

- TR-1: TestPlan für Spec 03 wird neu generiert
- TR-2: Generierter TestPlan enthält Ambiguity-Klärungs-Keywords in TC-003, TC-004, TC-005
- TR-3: Generierter TestPlan enthält keine Klärungs-Keywords für INT-001/INT-002 (clear intents)
- TR-4: Retest TEST-RUN-2026-05-18-002 mit neuem TestPlan zeigt verbesserte PASS-Rate
- TR-5: Security Tests (SEC-001, SEC-002) behalten ihre Sicherheitserwartungen

## ACCEPTANCE CRITERIA

- [ ] TestPlan-Generator überträgt Ambiguity-Klärungs-Patterns korrekt
- [ ] TC-003, TC-004, TC-005 enthalten Klärungs-Keywords in expectations
- [ ] INT-001, INT-002 enthalten keine Klärungs-Keywords in expectations (clear intents)
- [ ] Security Tests behalten ihre Sicherheitserwartungen
- [ ] Retest mit neuem TestPlan zeigt Ambiguity-Validierung
- [ ] Keine Produktcode-Änderungen erforderlich

## BLOCKING CONDITIONS

- [ ] TestSpec 03 ist nicht lesbar
- [ ] TestPlan-Generator ist nicht modifizierbar
- [ ] Retest zeigt neue FAILs durch geänderte expectations

## IMPLEMENTATION NOTES

## FINAL AUDIT / SKILL 7 STATUS

- **Status:** DONE
- **Final Audit:** PASS
- **Final TestRun:** TEST-RUN-2026-05-18-003
- **Result:** 28/28 PASS, 0 failed, 0 blocked, 0 manual gates
- **Evidence:** `documentation/test-results/TEST-RUN-2026-05-18-003_results.json`, `documentation/test-results/TEST-RUN-2026-05-18-003/`
- **Final Audit File:** `documentation/test-runs/BACKLOG-069_final_audit.md`
- **Backlog Items Generated:** Keine
- **Dashboard Sync:** Backlog-Dokumentation wurde synchronisiert; keine neuen Findings.

Dies ist ein TestPipeline-Only Fix. Keine Produktcode-Änderungen. Der Fix liegt im TestPlan-Generator für Spec 03.
