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
- [x] **Phase 1 (Pre-Check):** `/pre-check` ausführen.
- [x] **Phase 2 (Implementierung):**
  - [x] Erweitere schemas_logging.py um LearningReport und SystemImprovement Modelle
  - [x] Implementiere learning_engine.py mit LearningEngine Klasse
  - [x] Implementiere fetch_historical_data(days=7) Methode
  - [x] Implementiere calculate_trends() Methode
  - [x] Erweitere system.py um GET /api/system/learning-report Endpoint
  - [x] **Phase 2.1 (D14-B):** Mathematische Delta-Logik und Empfehlungs-Engine
    - [x] Woche N vs Woche N-1 Vergleich
    - [x] Regression-Trigger (ErrorRate_diff > 0.05, Latency_diff > 20%)
    - [x] Deterministische Regeln (MODEL_SWITCH, TIMEOUT_ADJUST, COST_OPTIMIZE)
    - [x] Markdown-Formatter für AI Studio
  - [x] **Phase 2.2 (D14-D):** Lifecycle Integration
    - [x] Persistence Schema für logs_learning Tabelle
    - [x] Background Scheduler in backend/main.py lifespan
    - [x] POST /api/system/learning-trigger Manual-Endpoint
    - [x] Guardrails für Non-Blocking und Error-Handling
- [x] **Phase 3 (Testing):** 38/38 Audit-Checks passed (D14_post_impl_audit.md)
- [x] **Phase 4 (Post-Check):** `/post-impl` ausgeführt — 🥇 SEALED
- [ ] **Phase 5 (Audit - Optional):** `/opus-audit` bei Bedarf ausführen.

## 5. Test-Vorgaben
- [ ] Regression: `python -m pytest backend/tests -q` 
- [ ] Targeted: Test der LearningEngine mit historischen Insights

## 6. Ergebnis & Audit-Trail
_Wird automatisch durch /post-impl ausgefüllt._

## 7. Debugging-Log
_Wird bei Bedarf ausgefüllt._
