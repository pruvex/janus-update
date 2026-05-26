# TASK – backlog_BACKLOG-085_spec06_evidence_honesty_oracle_refinement

## 1. Ziel
Aktualisiere TestPlan-Expectations für TC-008-GPT und TC-008-GEMINI, um korrektes Evidence-Honesty-Verhalten abzubilden. BACKLOG-081 Analyse ergab Oracle-Mismatch statt Produktverhalten.

## 2. Backlog Identity
- **Backlog Item:** BACKLOG-085
- **Backlog Status:** DONE
- **Quelle:** BACKLOG-081 Execution

## 3. Impact-Analyse
- **Beeinflusst:** TestPlan Oracle / Evidence Honesty Pattern
- **Betroffene TestCases:** TC-008-GPT, TC-008-GEMINI
- **Risiko-Einschätzung:** LOW
- **Aufwand:** S

## 4. Scope
### IN SCOPE
- Review TestPlan expectations für TC-008-GPT und TC-008-GEMINI
- Update expected patterns um korrektes Evidence-Honesty-Verhalten abzubilden
- Ensure expectations align mit Produktverhalten (Ablehnung ohne Evidenz)
- Focused retest um aktualisierte expectations zu validieren

### OUT OF SCOPE
- Produktcode-Änderungen (Produktverhalten ist korrekt)
- Kopieren sensibler Prompts/Payloads in Docs/Chat
- Änderung an nicht verwandten TestSpec Fällen

## 5. Umsetzungsschritte
1. Review TestPlan expectations für TC-008-GPT und TC-008-GEMINI aus TEST-RUN-2026-05-19-008
2. Identifiziere welche patterns aktualisiert werden müssen
3. Update expected patterns um korrektes Evidence-Honesty-Verhalten abzubilden
4. Führe focused retest für TC-008-GPT und TC-008-GEMINI aus
5. Validiere dass keine sensiblen Payloads in Dokumentation kopiert wurden

## 6. Acceptance Criteria
- [x] TC-008-GPT focused retest PASS
- [x] TC-008-GEMINI focused retest PASS
- [x] Expectations match korrektes Evidence-Honesty-Verhalten
- [x] Keine sensiblen Payloads in Dokumentation

## 7. Tests / Validierung
- Focused retest für TC-008-GPT und TC-008-GEMINI
- Validierung dass TestPlan-Expectations korrekt aktualisiert sind
- Prüfung dass keine sensiblen Payloads in Handoff/Doku kopiert wurden

## 8. Model
- **Assigned Model:** SWE 1.6
- **Reason:** TestPlan/TestSpec refinement für Oracle-Mismatch mit klaren failing IDs und LOW Implementierungsscope.

## 9. Execution Ergebnis
- **Ergebnis:** TestPlan-Generator Oracle verfeinert
- **Analyse:** `containsAny` war bereits passend, aber `mustNotContain` blockierte einzelne Evidence-/Status-Woerter auch dann, wenn sie in einer korrekten Ablehnung negiert wurden.
- **Aenderung:** `TC-008` nutzt jetzt `evidenceHonestyExpected()`; das Oracle verbietet nur noch klare unsafe Erfolgsbehauptungen statt einzelner Status-Woerter.
- **Geaenderte Datei:** tests/e2e/generator/compile-testspec-to-testplan.mjs
- **Neuer TestPlan:** documentation/test-runs/TEST-RUN-2026-05-19-009_plan.json
- **Validator:** TESTPLAN VALID, 57 Tests
- **Status:** TESTPLAN_REGENERATED_READY_FOR_TEST_SKILL_2
- **Anmerkung:** Kein Produktcode-Change; keine sensiblen Payloads in Doku/Handoff kopiert.

## 10. Final Audit
- **Status:** DONE
- **Final Audit:** documentation/test-runs/BACKLOG-085_final_audit.md
- **Focused Retest:** TEST-RUN-2026-05-20-001
- **Result:** TC-008-GPT PASS, TC-008-GEMINI PASS
