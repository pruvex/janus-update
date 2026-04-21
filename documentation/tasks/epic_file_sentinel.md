# Task EPIC-FILE-SENTINEL: Etablierung eines Zero-Trust Dateisystem-Zugriffs (Path Sentinel) mit granularem User-Consent-Flow (Sealed Grant) und einer asynchronen, sicheren globalen Dateisuche.

## 1. Ziel & Kontext
Etablierung eines Zero-Trust Dateisystem-Zugriffs (Path Sentinel) mit granularem User-Consent-Flow (Sealed Grant) und einer asynchronen, sicheren globalen Dateisuche.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** [welche bestehenden Systeme/Tasks]
- **Beeinflusst:** [welche anderen Systeme könnten betroffen sein]
- **Risiko-Einschätzung:** [LOW / MEDIUM / HIGH]

## 3. Betroffene Dateien
backend/services/path_sentinel/*, backend/services/orchestrator/execution_dispatcher.py, backend/api/routers/consent.py, backend/data/models.py, frontend/js/app.js, frontend/js/consent-modal.js, backend/tools/filesystem_tools.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** [Haupt-Implementierungsschritte hier eintragen]
- [ ] **Phase 3 (Testing):** [Spezifische Testbefehle hier eintragen]
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: <specific test command>

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
