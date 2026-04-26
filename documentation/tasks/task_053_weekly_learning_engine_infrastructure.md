# Task 053: Aufbau der Daten-Infrastruktur für die Weekly Learning Engine (D14)

## 1. Ziel & Kontext
Aufbau der Daten-Infrastruktur für die Weekly Learning Engine (D14) zur systematischen Analyse von System-Performance-Trends über Zeit.

## 2. Impact-Analyse & Abhängigkeiten
- **Basiert auf:** D12 Insight Engine (logs_insights als Datenquelle)
- **Beeinflusst:** D14 Weekly Learning Engine (Phase 2)
- **Risiko-Einschätzung:** MEDIUM

## 3. Betroffene Dateien
- backend/data/schemas_logging.py
- backend/services/logging/learning_engine.py (neu)
- backend/api/routers/system.py

## 4. Umsetzungsschritte (Diamond-Flow)
- [ ] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [ ] **Phase 2 (Implementierung):**
  - Erweitere schemas_logging.py um LearningReport und SystemImprovement Modelle
  - Implementiere learning_engine.py mit LearningEngine Klasse
  - Implementiere fetch_historical_data(days=7) Methode
  - Implementiere calculate_trends() Methode
  - Erweitere system.py um GET /api/system/learning-report Endpoint
- [ ] **Phase 3 (Testing):** Test der LearningEngine mit Dummy-Daten
- [ ] **Phase 4 (Post-Check):** `/post-impl` ausführen.
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: Test der LearningEngine mit historischen Insights

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
