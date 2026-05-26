# TASK – backlog_BACKLOG-080_playwright_duplicate_installation_collision

## 1. Ziel
Entferne duplicate @playwright/test requirement in root node_modules und frontend/node_modules, das "Requiring @playwright/test second time" Fehler bei Testausführung verursacht.

## 2. Backlog Identity
- **Backlog Item:** BACKLOG-080
- **Backlog Status:** DONE
- **Quelle:** BACKLOG-079 Execution

## 3. Impact-Analyse
- **Beeinflusst:** TestRunner / Playwright Configuration / Dependency Management
- **Betroffene Tests:** Alle Playwright-Tests (blockiert BACKLOG-079 Verifikation)
- **Risiko-Einschätzung:** LOW
- **Aufwand:** S

## 4. Scope
### IN SCOPE
- Identifikation der duplicate @playwright/test Installation
- Entfernung der duplicate Installation (frontend/node_modules oder root node_modules)
- Validierung dass Playwright-Testausführung ohne Konfigurationsfehler läuft
- Aktualisierung von package.json oder package-lock.json falls nötig

### OUT OF SCOPE
- Änderung an Produkt-Code
- Änderung an Test-Inhalten
- Änderung an Playwright-Konfiguration (außer dependency-bezogen)

## 5. Umsetzungsschritte
1. Prüfe package.json in root und frontend für @playwright/test dependency
2. Identifiziere welche Installation redundant ist
3. Entferne die duplicate Installation (wahrscheinlich frontend/node_modules)
4. Aktualisiere package.json und package-lock.json falls nötig
5. Führe npm install oder npm ci aus um dependencies zu bereinigen
6. Führe einen Smoke-Test mit einem Playwright-Test aus um sicherzustellen dass kein Konfigurationsfehler auftritt

## 6. Acceptance Criteria
- [x] Duplicate @playwright/test requirement entfernt
- [x] Playwright-Testausfuehrung laeuft ohne "Requiring @playwright/test second time" Fehler
- [x] BACKLOG-079 Verifikation kann durchgefuehrt werden
- [x] Keine Regression im Playwright-Smoke-Test

## 7. Tests / Validierung
- Manuelles Prüfen dass nur eine @playwright/test Installation existiert
- Ausführen eines Playwright-Tests um sicherzustellen dass kein Konfigurationsfehler auftritt
- Prüfen dass BACKLOG-079 Verifikation erfolgreich durchgeführt werden kann

## 8. Model
- **Assigned Model:** SWE 1.6
- **Reason:** Backlog-Handoff für Dependency-Management-Fix mit LOW Risiko und S Aufwand.

## 9. Skill 7 Abschluss
- **Status:** DONE
- **Final Audit:** documentation/test-runs/BACKLOG-080_final_audit.md
- **Validierung:** Playwright-Smoke-Test lief ohne duplicate-Dependency-Konfigurationsfehler; BACKLOG-079-Retest wurde wieder moeglich.
