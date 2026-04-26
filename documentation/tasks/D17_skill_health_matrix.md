# Task D17 — Skill Health Matrix & Decision Interface

## Section 1: Ziel
Aufbau der Skill Health Matrix und des Decision Interfaces für AI Studio.
- Batch Runner: TestRunner iteriert über alle Skills in backend/skills/
- Health Matrix: pass_rate + escalation_rate pro Skill aus D10 Telemetrie
- Problem-Klassifikation: MODEL_WEAKNESS, PROMPT_ISSUE, VALIDATION_FAIL, TIMEOUT mit Confidence Score
- D13 Decision Report: Markdown-Report für degraded Skills (< 0.9 pass_rate)
- API: GET /api/system/health-matrix, GET /api/system/decision-report

## Section 2: Impact-Analyse
- **Basiert auf:** D16 (Deterministic Quality System — Test Runner, Escalation Engine, D10 Integration), D12 (InsightEngine), D13 (OptimizationEngine)
- **Beeinflusst:** backend/services/testing/test_runner.py, backend/services/logging/insight_engine.py, backend/services/logging/optimization_engine.py, backend/api/routers/system.py
- **Risiko-Einschätzung:** LOW — Additive changes only. No existing logic modified, only extended. Escalation logs are read-only source.

## Section 3: Implementierungs-Details

### Phase 1 (D17-PHASE-1) — Batch Runner
- `discover_skills()` function in test_runner.py
- `run_batch_tests()` method iterates all skill JSON files in backend/skills/

### Phase 2 (D17-PHASE-2) — Health Matrix & Endpoints
- `InsightEngine.generate_health_matrix()` from D10 skill_test events
- `OptimizationEngine.generate_decision_report()` Markdown formatter
- GET /api/system/health-matrix
- GET /api/system/decision-report

### Phase 3 (D17-PHASE-3) — Problem Classification
- `ProblemCategory` enum: MODEL_WEAKNESS, PROMPT_ISSUE, VALIDATION_FAIL, TIMEOUT, HEALTHY
- `SkillProblemProfile` model: skill_id, categories, confidence, recommendation
- `ProblemClassifier` in optimization_engine.py
- Enhanced D10 payload: final_tier, attempts_count
- Integration in decision report

## Section 4: Betroffene Dateien
- `backend/services/testing/test_runner.py` — _log_to_d10 payload enhancement
- `backend/services/logging/optimization_engine.py` — ProblemClassifier
- `backend/api/routers/system.py` — decision-report enhanced output

## Section 5: Test-Verifikation
- Classification rules are deterministic (no AI)
- [PROVISIONAL] prefix on all recommendations (D15 compliance)
- model_routing.json NOT modified (Zero Mutability guardrail)

## Section 6: Status
- Phase 1 & 2: ✅ COMPLETE (2026-04-26)
- Phase 3: 🔄 IN PROGRESS
