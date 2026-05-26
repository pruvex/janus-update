# Task 054: D25 Monitoring Aggregator

## 1. Ziel & Kontext
Implementierung des Aggregator-Endpoints GET /api/system/monitoring/summary zur zentralen Überwachung des Immunsystems (Health, History, Cooldown).

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** D20-D24 Self-Heal System
- **Beeinflusst:** Monitoring-Dashboard, Health-Checks
- **Risiko-Einschätzung:** LOW (Read-only Endpoint, keine Mutationen)

## 3. Betroffene Dateien
backend/api/routers/system.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):** 
  - GET /api/system/monitoring/summary Endpoint erstellen
  - Health Snapshot aus model_routing.json aggregieren
  - Self-Heal Status aus self_heal_state.json laden
  - Recent Activity aus routing_history.json lesen
  - Response Schema implementieren
  - Robustheit: Fehlerbehandlung für fehlende Dateien
- [ ] **Phase 3 (Testing):** Endpoint mit curl testen
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: `curl http://localhost:8001/api/system/monitoring/summary`

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
