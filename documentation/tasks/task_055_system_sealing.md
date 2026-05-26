# Task 055: D26 System Sealing

## 1. Ziel & Kontext
Cleanup von Legacy-Artefakten und finale Validierung der Observability- und Self-Heal-Architektur (D20-D25).

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** D20-D25 Observability & Self-Heal System
- **Beeinflusst:** Keine (Cleanup-Task)
- **Risiko-Einschätzung:** LOW (Cleanup und Validierung, keine Mutationen)

## 3. Betroffene Dateien
backend/config/ (model_routing.json, self_heal_state.json, routing_history.json)
backend/api/routers/system.py
PROJECT_STATE.md

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** 
  - Legacy-Entfernung: harvest_baseline.py und temporäre Test-Runner löschen
  - Prüfe backend/config/ auf Konsistenz
  - Code-Audit: Monitoring-Endpoints in system.py prüfen
  - Integritäts-Check: Backend starten und /api/system/monitoring/summary aufrufen
- [ ] **Phase 3 (Testing):** Endpoint-Test mit curl
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: `curl http://localhost:8001/api/system/monitoring/summary`

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
