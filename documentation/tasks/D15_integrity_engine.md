# D15: Integrity Engine — Diamond Contract Registry & Stack Validation

**Status:** 🥇 SEALED & COMPLETE
**Epic:** D15 Integrity Engine
**Version:** V0.4.26-beta.48
**Task-IDs:** D15-A (Contract Registry), D15-B (Cross-Layer Validation), D15-C (Action Validation Gate)

---

## Architektur

D15 ist die finale Kontrollinstanz über D10-D14. Keine KI-Interpretation — nur strikte Code-Validierung und Pydantic-Schema-Checks.

### Signal-Flow
```
D12 Output ──┐
D13 Output ──┼── D15 IntegrityEngine.validate_stack_integrity() ──► IntegrityReport (JSON)
D14 Output ──┘
```

### Contract Registry (CONTRACT_SPECS)
Definiert den exakten Soll-Zustand für jeden Layer:

| Layer | Required Fields | Forbidden Patterns | Allowed Actions |
|-------|----------------|-------------------|-----------------|
| D10 | event_type, timestamp | — | — |
| D11 | — | — | — |
| D12 | skill_id, model, calls, error_rate, avg_latency_ms, patterns, confidence | recommendation, action_type | — |
| D13 | skill_id, model, action_type, priority, recommendation | — | MODEL_SWITCH, SCALE_UP, SCALE_DOWN, TIMEOUT_ADJUST, CACHE_ENABLE, LOAD_BALANCE, RETRY_CONFIG, MONITOR |
| D14 | scope, model, issue, trend, recommendation, regression_score | — | MODEL_SWITCH, TIMEOUT_ADJUST, COST_OPTIMIZE, MONITOR, MAINTAIN |

### Validation Rules
1. **Descriptive-Only Guard (D12):** Blockiere D12 Outputs die `recommendation` oder `action_type` enthalten.
2. **Allowed-Actions Guard (D13):** Verifiziere dass D13 action_type nur aus ALLOWED_ACTIONS stammt.
3. **KPI-Drift Guard:** Schema-Version-Vergleich für KPI-Konsistenz.
4. **Decision-Gate Guard:** Alle D13/D14 Empfehlungen müssen `[PROVISIONAL]` enthalten.

### Output: IntegrityReport
```json
{
  "timestamp": "2026-04-26T18:30:00Z",
  "integrity_score": 1.0,
  "status": "PASS",
  "layers_checked": 5,
  "violations": [],
  "schema_version": "V0.4.26"
}
```

---

## Endpoint

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/system/integrity-check` | Run full D15 stack integrity validation |

---

## Files

- `backend/services/logging/integrity_engine.py` — IntegrityEngine + CONTRACT_SPECS
- `backend/api/routers/system.py` — GET /integrity-check endpoint
- `backend/tests/test_integrity_engine.py` — Test suite with violation injection
- `documentation/tasks/D15_integrity_engine.md` — This document
