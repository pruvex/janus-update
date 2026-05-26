# JANUS IMMUNE SYSTEM — Diamond Architecture Dossier (D20-D26 FINAL STATE)

**Version:** 1.0.0
**Status:** 🥇 SEALED & OPERATIONAL (2026-04-28)
**Purpose:** Single Source of Truth (SSOT) for all Routing-Changes in the Janus System

---

## 1. System Overview

The Janus Immune System is a self-healing, confidence-based routing architecture that automatically optimizes model assignments based on statistical calibration and historical performance data. It consists of 6 core components (D20-D25) that work together to create an automated feedback loop for model routing.

### Core Philosophy
- **Statistical Calibration:** All routing decisions are based on data, not intuition
- **Confidence-Based Selection:** More runs = more stable decisions
- **Self-Healing:** Automatic model promotion/demotion without manual intervention
- **Audit Trail:** Complete history of all routing changes
- **Safety Gates:** Multiple protection mechanisms against over-correction

---

## 2. Component Architecture

### D20: Model Routing Calibration (Statistical Baseline)
**Purpose:** Establish statistical baseline for model performance via matrix testing.

**Key Features:**
- Matrix Test Infrastructure: POST `/api/system/run-batch-tests`
- Outer Loop (models) × Inner Loop (runs_per_model)
- Rate-Limiting: 0.5s delay between calls (429 protection)
- Trace-ID-Tracking: Unique UUID per test (400 unique IDs)
- Model-Override: Lambda with keyword arguments (provider, model, **kwargs)

**Calibration Results:**
- 10 Skills calibrated with verified assignments
- Tier 2 (Balanced): `gpt-5.4-mini` for 9 Skills (except Video)
- Tier 3 (Logic): `gpt-5.4` for all 10 Skills (Escalation)
- Special Case: `system.video_understanding` → Primary `gpt-5.4` (33% pass-rate break)

**File:** `backend/config/model_routing.json`

---

### D21: Diamond Routing Builder (Confidence-Based Selection)
**Purpose:** Build optimal routing configuration based on historical data and confidence scores.

**Key Features:**
- Confidence Bonus: More runs = more stable decision (lower bonus = better)
- Primary Selection: Best model with pass_rate ≥ 0.95
- Sorting: (pass_rate * -1 + latency_ms * 0.001 + confidence_bonus)
- Data Bridge: Aggregates historical data from D10 logs_raw
- MIN_RUNS Filter: Only models with ≥ 3 runs considered

**Algorithm:**
```python
confidence_bonus = 1.0 / (run_count + 1)  # More runs = lower bonus
score = (pass_rate * -1) + (latency_ms * 0.001) + confidence_bonus
primary = min(models, key=lambda m: score[m])  # Lowest score wins
```

**File:** `backend/services/testing/test_runner.py` (build_diamond_routing)

---

### D22: Self-Heal Cycle (Automated Model Routing Updates)
**Purpose:** Execute self-healing cycle for all skills with diamond routing logic.

**Key Features:**
- Diamond Routing: Aggregates historical data, calculates confidence
- Self-Heal Cycle: Runs diamond routing for all skills
- Automatic Updates: Applies updates via `apply_routing_update()`
- Shield Rules: Never-Degrade (new pass_rate ≥ old), Hysteresis (pass_rate +5% OR latency -20%)

**Shield Rules:**
1. **Never-Degrade:** Skip if new pass-rate < existing
2. **Hysteresis:** Update only if pass-rate increases by ≥5% OR latency decreases by ≥20%

**File:** `backend/services/testing/test_runner.py` (run_self_healing_cycle)

---

### D23: FIFO History Logging (Audit Trail)
**Purpose:** Maintain audit trail of all routing updates with FIFO limit.

**Key Features:**
- History Logging: `_log_routing_history()` writes updates to `routing_history.json`
- FIFO Limit: Max 100 entries (newest at beginning, oldest removed at end)
- History Schema: skill_id, winner, pass_rate, latency_ms, timestamp, primary_model, fallback_model, escalation_model
- Integration: Called in `apply_routing_update()` after successful update

**File:** `backend/config/routing_history.json`

---

### D24: Auto-Self-Heal Trigger (Automated Trigger with Gates)
**Purpose:** Automated trigger for self-healing cycle with safety gates.

**Key Features:**
- Auto-Trigger Endpoint: POST `/api/system/self-heal/auto`
- Cooldown Gate: 6h cooldown between triggers (persistent in `self_heal_state.json`)
- Lock Gate: `SELF_HEAL_LOCK` prevents parallel cycles
- Health-Threshold Gate: Trigger only if skills are degraded/critical
- State Persistence: `self_heal_state.json` with `last_self_heal_at` and `updated_at`
- Cooldown Update: `_update_cooldown()` called after successful self-heal

**Gates:**
1. **Cooldown:** 6 hours between triggers
2. **Lock:** Prevents parallel execution
3. **Health-Threshold:** Only trigger if degraded/critical skills exist

**File:** `backend/config/self_heal_state.json`

---

### D25: Monitoring Aggregator (Central Health & Status Hub)
**Purpose:** Central monitoring hub for the immune system (Health, History, Cooldown).

**Key Features:**
- Health Snapshot: Aggregates skill status from `model_routing.json` (healthy ≥0.95, degraded ≥0.5, critical <0.5)
- Self-Heal Status: Loads cooldown state, calculates `cooldown_active` and `remaining_minutes`
- Recent Activity: Loads last 5 entries from `routing_history.json`
- System Status: Calculates overall system status (`optimal | attention_required | critical`)
- Robustness: All file operations with try/except, missing files log warnings instead of errors

**Endpoint:** GET `/api/system/monitoring/summary`

**Response Schema:**
```json
{
  "system_status": "optimal | attention_required | critical",
  "health": {"total": 53, "healthy": 52, "degraded": 1, "critical": 0},
  "self_heal": {"cooldown_active": true, "last_run": "ISO-TS", "remaining_minutes": 348},
  "recent_updates": [...],
  "generated_at": "ISO-TS"
}
```

**File:** `backend/api/routers/system.py` (get_monitoring_summary)

---

## 3. Data Flow

### Calibration Flow (D20 → D21 → D22)
```
1. POST /api/system/run-batch-tests
   → Matrix test runs for all skills
   → Results stored in D10 logs_raw

2. D21 build_diamond_routing()
   → Aggregates historical data from D10
   → Calculates confidence scores
   → Selects Primary/Fallback/Escalation

3. D22 run_self_healing_cycle()
   → Calls D21 for each skill
   → Applies updates via Shield Rules
   → Logs to D23 routing_history.json
```

### Self-Heal Flow (D24 → D22 → D23)
```
1. POST /api/system/self-heal/auto
   → Checks Cooldown Gate (6h)
   → Checks Lock Gate (parallel prevention)
   → Checks Health-Threshold Gate

2. D22 run_self_healing_cycle()
   → Executes diamond routing
   → Applies updates
   → Updates D24 cooldown state

3. D23 _log_routing_history()
   → Logs update to routing_history.json
   → FIFO limit (100 entries)
```

### Monitoring Flow (D25)
```
GET /api/system/monitoring/summary
→ Reads model_routing.json (Health Snapshot)
→ Reads self_heal_state.json (Self-Heal Status)
→ Reads routing_history.json (Recent Activity)
→ Aggregates into single response
```

---

## 4. Configuration Files

### Dynamic Configs (backend/config/)
1. **model_routing.json** - Current routing assignments (D20, D21, D22)
2. **routing_history.json** - Audit trail of routing updates (D23)
3. **self_heal_state.json** - Cooldown state (D24)

### Static Configs (backend/config/)
- config.json - General configuration
- image_presets.json - Image generation presets
- model_catalog.json - Available models
- personalities.json - AI personalities
- style_profiles.json - Style profiles

---

## 5. API Endpoints

### Monitoring Endpoints
- `GET /api/system/health` - Health snapshot
- `GET /api/system/routing` - Current routing configuration
- `GET /api/system/self-heal/state` - Self-heal state
- `GET /api/system/routing/last-updates` - Last 5 routing updates
- `GET /api/system/health-matrix` - Health matrix for all skills
- `GET /api/system/monitoring/summary` - Central monitoring hub (D25)

### Action Endpoints
- `POST /api/system/self-heal` - Manual self-heal trigger
- `POST /api/system/self-heal/auto` - Automated self-heal trigger with gates (D24)
- `POST /api/system/run-batch-tests` - Matrix test calibration (D20)

---

## 6. Safety Mechanisms

### Shield Rules (D22)
1. **Never-Degrade:** New pass-rate must be ≥ existing pass-rate
2. **Hysteresis:** Update only if pass-rate +5% OR latency -20%

### Gates (D24)
1. **Cooldown Gate:** 6 hours between triggers
2. **Lock Gate:** Prevents parallel execution
3. **Health-Threshold Gate:** Only trigger if degraded/critical skills exist

### Robustness (D25)
- All file operations with try/except
- Missing files log warnings instead of errors
- Individual sections set to default values on failure

---

## 7. Maintenance Workflow

### Weekly Maintenance
Execute the `.windsurf/workflows/janus_maintenance.md` workflow:
1. Run calibration: POST `/api/system/run-batch-tests`
2. Generate trends: GET `/api/system/learning-report`
3. Check status: GET `/api/system/monitoring/summary`

**Purpose:** Secure statistical basis for self-healing with fresh calibration data.

---

## 8. Integration Points

### D10 Integration
- D20: Matrix test results stored in logs_raw
- D21: Aggregates historical data from logs_raw
- D16: Skill test events logged to logs_raw

### D15 Integration
- D22: All routing updates go through Contract Registry validation

### D17 Integration
- D25: Health snapshot aggregates pass_rate from model_routing.json
- D17: Problem classification uses pass_rate for root-cause analysis

---

## 9. Patterns & Lessons Learned

### Patterns
- #DiamondRouting: Confidence-based model selection with historical data
- #SelfHealingCycle: Automated model promotion/demotion with shield rules
- #FIFOHistory: Audit trail with FIFO limit for bounded storage
- #AutoTrigger: Automated trigger with multiple safety gates
- #MonitoringAggregator: Central hub for dispersed status data

### Lessons
- Statistical calibration eliminates stochastic noise from model comparisons
- Confidence bonuses stabilize decisions with more runs
- Shield rules prevent over-correction and downgrades
- FIFO limits prevent unbounded storage growth
- Multiple gates prevent excessive self-healing triggers

---

## 10. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-04-28 | Initial release - D20-D25 SEALED & OPERATIONAL |

---

**This document is the Single Source of Truth (SSOT) for all routing changes in the Janus System. Any modifications to the routing architecture must be reflected here.**
