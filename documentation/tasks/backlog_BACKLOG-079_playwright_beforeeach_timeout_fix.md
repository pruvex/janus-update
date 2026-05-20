# TASK – backlog_BACKLOG-079_playwright_beforeeach_timeout_fix

## 1. Ziel
Behebe das beforeEach Timeout-Problem im Playwright TestRunner, das 42 Tests in TEST-RUN-2026-05-19-007 blockierte.

## 2. Backlog Identity
- **Backlog Item:** BACKLOG-079
- **Backlog Status:** DONE
- **Quelle:** TEST-RUN-2026-05-19-007

## 3. Impact-Analyse
- **Beeinflusst:** TestRunner / Playwright Configuration, TEST-RUN-2026-05-19-007 (42 BLOCKED Tests)
- **Risiko-Einschätzung:** MEDIUM
- **Aufwand:** M

## 4. Scope
### IN SCOPE
- Analyse der beforeEach Hook-Implementierung im generierten TestRunner
- Identifikation der Ursache für 120000ms Timeout
- Fix der beforeEach Hook-Logik oder Timeout-Konfiguration
- Validierung dass alle 42 Tests erfolgreich ausgeführt werden können
- Update der Playwright-Konfiguration falls nötig

### OUT OF SCOPE
- Änderung an Test-Inhalten oder Test-Logik
- Änderung an Produkt-Code
- Änderung an TestSpec oder TestPlan

## 5. Umsetzungsschritte
1. Analysiere die beforeEach Hook-Implementierung in tests/e2e/generator/compile-testspec-to-testplan.mjs
2. Identifiziere die Ursache für das 120000ms Timeout (z.B. blocking operation, missing await, resource contention)
3. Prüfe die Playwright-Konfiguration (playwright.config.js) für Timeout-Einstellungen
4. Implementiere den Fix (z.B. await hinzufügen, Timeout erhöhen, blocking operation entfernen)
5. Führe einen Smoke-Test mit einem der geblockten Tests aus
6. Führe alle 42 Tests erneut aus um sicherzustellen dass kein Timeout mehr auftritt

## 6. Acceptance Criteria
- [x] beforeEach Hook Timeout wird behoben
- [x] Alle zuvor geblockten Tests werden nicht mehr durch den 120000ms beforeEach-Timeout blockiert
- [x] Retest wurde als TEST-RUN-2026-05-19-008 ausgefuehrt
- [x] Keine Regression im TestRunner-Start durch den Timeout-Fix

## 7. Tests / Validierung
- Manuelles Prüfen dass beforeEach Hook keine blocking Operation enthält
- Ausführen eines Smoke-Tests mit einem der geblockten Tests
- Ausführen aller 57 Tests aus TEST-RUN-2026-05-19-007 um sicherzustellen dass alle Tests laufen
- Prüfen dass keine neuen Timeout-Fehler auftreten

## 8. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für TestRunner-Infrastruktur-Fix mit MEDIUM Risiko und M Aufwand.

## 9. Skill 7 Abschluss
- **Status:** DONE
- **Final Audit:** documentation/test-runs/BACKLOG-079_final_audit.md
- **Validierung:** TEST-RUN-2026-05-19-008 lief mit 57 Tests durch; der urspruengliche 42-Test-beforeEach-Timeout-Blocker ist behoben.
- **Follow-up:** Die verbleibenden roten Spec-06-Findings sind separate AI-Safety-/Oracle-/Flaky-Follow-ups und nicht Teil dieses Runner-Fixes.
