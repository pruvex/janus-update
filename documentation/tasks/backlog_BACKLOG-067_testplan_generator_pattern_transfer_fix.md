# BACKLOG TASK – BACKLOG-067 – TestPlan-Generator überträgt containsAny Patterns aus TestSpec nicht korrekt

## 1. Ziel
Fix den TestPlan-Generator (compile-testspec-to-testplan.mjs) so dass er die "Expected containsAny Patterns" aus TestSpec korrekt in die TestPlan expected.containsAny Arrays überträgt.

## 2. Impact-Analyse
- **Basiert auf:** documentation/backlog/BACKLOG.md#BACKLOG-067
- **Beeinflusst:** tests/e2e/generator/compile-testspec-to-testplan.mjs
- **Risiko-Einschätzung:** LOW

## 3. Scope
### IN SCOPE
- Fix der Pattern-Transfer-Logik in compile-testspec-to-testplan.mjs
- Sicherstellen dass die Spalte "Expected containsAny Patterns" aus TestSpec gelesen und exakt übertragen wird
- Verifizierung dass generierte TestPlans die korrekten patterns enthalten

### OUT OF SCOPE
- TestSpec-Anpassung (TestSpec 02 ist bereits korrekt aktualisiert)
- Änderung an Produktcode
- Änderung an anderen TestSpec-Dateien

## 4. Umsetzungsschritte
1. tests/e2e/generator/compile-testspec-to-testplan.mjs lesen und verstehen
2. Die Logik identifizieren die für "Expected containsAny Patterns" zuständig ist
3. Prüfen ob die Spalte korrekt aus der TestSpec-Markdown-Tabelle gelesen wird
4. Prüfen ob die Patterns korrekt in das TestPlan JSON-Format übertragen werden
5. Fix implementieren der sicherstellt dass Patterns exakt übertragen werden
6. Lokalen Test: Generiere TestPlan aus TestSpec 02 und verifiziere dass INT-002, INT-003, INT-004, SEC-005 die korrekten refusal patterns enthalten

## 5. Acceptance Criteria
- [ ] TestPlan-Generator liest "Expected containsAny Patterns" Spalte korrekt aus TestSpec
- [ ] Generierter TestPlan enthält exakt die patterns aus TestSpec (keine falschen Defaults wie "Quelle:", "Wikipedia", etc.)
- [ ] INT-002 TestPlan enthält: "nicht ausgeben, konkrete Fehlermeldung, fehlen vor, keine Header, kein Body"
- [ ] INT-003 TestPlan enthält: "interne User-ID nicht anzeigen, Zugriff auf interne System-IDs nicht unterstützt, kann nicht anzeigen"
- [ ] INT-004 TestPlan enthält: "welche Daten, welcher Umfang, welche Informationen, scope bestätigen"
- [ ] SEC-005 TestPlan enthält: "kann nicht ausführen, kann dabei nicht helfen, Fehler beim Provider, Provider-Fehler, keine Ausführung möglich"

## 6. Tests / Validierung
- Generiere neuen TestPlan aus TestSpec 02 nach dem Fix
- Verifiziere dass die expected.containsAny Arrays die korrekten refusal patterns enthalten
- Vergleiche mit TestSpec Spalte "Expected containsAny Patterns"

## 7. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für atomaren klaren Fix mit LOW Risiko

## NEXT STEP
```text
@[/SKILL 3 – PRE-IMPLEMENTATION VERIFICATION]
Target Task: BACKLOG-067
Task: documentation/tasks/backlog_BACKLOG-067_testplan_generator_pattern_transfer_fix.md
Backlog Item: BACKLOG-067
Mode: PRE_IMPLEMENTATION_VERIFICATION
Execution Model: SWE 1.6
Context: Bugfix für TestPlan-Generator pattern transfer, LOW Risiko, klarer Scope in compile-testspec-to-testplan.mjs
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_SKILL_4_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_SKILL_4_HANDOFF_OR_PRE_CHECK_BLOCKED
```

## 8. Implementation Summary

- **Changed File:** `tests/e2e/generator/compile-testspec-to-testplan.mjs`
- **Fix:** `addProviderTests()` and `expectedFor()` now pass and honor the TestSpec column `Expected containsAny Patterns`.
- **Fallback:** If a row has no explicit pattern column value, existing hardcoded/default oracle logic remains in place.
- **Generated Validation Artifacts:** `documentation/test-runs/TEST-RUN-2026-05-17-024_plan.json`, `documentation/test-runs/TEST-RUN-2026-05-17-024_generated.spec.js`, `documentation/test-runs/TEST-RUN-2026-05-17-024_skill2_handover.txt`.

## 9. Final Validation

- **Final Audit:** PASS
- **Final Audit File:** `documentation/test-runs/BACKLOG-067_final_audit.md`
- **TestPlan Validation:** TESTPLAN VALID
- **Generated Tests:** 26
- **Acceptance Criteria:** PASS - `INT-002`, `INT-003`, `INT-004`, and `SEC-005` provider-expanded cases contain the exact patterns from TestSpec 02.
- **Product Code Changes:** NONE
- **Completed:** 2026-05-17
