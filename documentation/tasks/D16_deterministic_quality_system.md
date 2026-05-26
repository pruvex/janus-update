# D16: Deterministic Quality System for Janus-Skills

**Status:** 🔄 IN PROGRESS (2026-04-26)
**Epic:** D16 — Skill Stability System
**Goal:** Build a deterministic quality system for Janus-Skills, moving from "probabilistic hope" to "measured stability"

---

## Overview

D16 provides automated testing, validation, and escalation capabilities for Janus-Skills. It ensures skills can be tested deterministically across different model tiers (Primary → Fallback → Escalation) with automatic health monitoring.

## Architecture

### Core Components

1. **Test Generator** (`backend/services/testing/test_generator.py`)
   - Generates deterministic test blueprints for skills
   - Creates 3 test types: happy_path, edge_case, failure_case
   - Rule-based (NO AI generation)
   - Outputs JSON blueprints to `config/skill_tests/`

2. **Validation Engine** (`backend/services/testing/validation.py`)
   - Deterministic validation rules
   - Validators: contains, not_contains, regex, not_crash
   - STRICTLY FORBIDDEN: No AI-based validation

3. **Model Router** (`backend/services/routing/model_router.py`)
   - Loads skill-to-model mappings from `backend/config/model_routing.json`
   - Provides routing configuration (Primary, Fallback, Escalation)
   - Fallback to global defaults for unmapped skills

4. **Escalation Engine** (`backend/services/routing/escalation.py`)
   - Executes tool calls with automatic escalation
   - Chain: Primary → Fallback → Escalation
   - Cost tracking per tier
   - Circuit breaker protection

5. **Test Runner** (`backend/services/testing/test_runner.py`)
   - Executes test blueprints with escalation
   - D10 Integration: Logs each test via `log_event()`
   - Generates AI Studio compatible health reports
   - Async execution

6. **API Endpoint** (`backend/api/routers/system.py`)
   - `GET /api/system/run-skill-tests/{skill_id}`
   - Manual trigger for skill testing
   - Returns health summary

---

## Configuration

### Model Routing Config

**File:** `backend/config/model_routing.json`

```json
{
  "default_tiers": {
    "primary": {
      "provider": "openai",
      "model": "gpt-4o-mini"
    },
    "fallback": {
      "provider": "openai",
      "model": "gpt-4o"
    },
    "escalation": {
      "provider": "openai",
      "model": "gpt-4-turbo"
    }
  },
  "skill_mappings": {}
}
```

### Test Blueprints

**Directory:** `config/skill_tests/`

Format: `{skill_id}_test.json`

```json
{
  "skill_id": "system.weather",
  "skill_type": "tool",
  "generated_at": "2026-04-26T19:00:00.000Z",
  "tests": {
    "happy_path": {
      "name": "happy_path",
      "description": "Standard successful execution",
      "input": {"parameters": {"query": "test query"}},
      "validation": {
        "type": "contains",
        "field": "status",
        "value": "success"
      }
    },
    "edge_case": {
      "name": "edge_case",
      "description": "Boundary condition or unusual input",
      "input": {"parameters": {"query": ""}},
      "validation": {
        "type": "not_crash",
        "description": "Should not crash on edge input"
      }
    },
    "failure_case": {
      "name": "failure_case",
      "description": "Invalid input or error condition",
      "input": {"parameters": null},
      "validation": {
        "type": "contains",
        "field": "status",
        "value": "error"
      }
    }
  }
}
```

---

## API Usage

### Run Skill Tests

**Endpoint:** `GET /api/system/run-skill-tests/{skill_id}?skill_type=tool`

**Parameters:**
- `skill_id`: Unique skill identifier (e.g., "system.weather")
- `skill_type`: Type of skill (default: "tool", options: "tool", "agent", "renderer")

**Example Request:**
```bash
curl http://localhost:8001/api/system/run-skill-tests/system.weather?skill_type=tool
```

**Response:**
```json
{
  "skill_id": "system.weather",
  "skill_type": "tool",
  "test_summary": {
    "skill_id": "system.weather",
    "test_count": 3,
    "passed_count": 3,
    "results": [...],
    "health_summary": {
      "skill_id": "system.weather",
      "health_score": 1.0,
      "total_tests": 3,
      "passed_tests": 3,
      "failed_tests": 0,
      "avg_latency_ms": 100.0,
      "total_escalation_attempts": 3,
      "generated_at": "2026-04-26T19:00:00.000Z",
      "status": "healthy"
    }
  },
  "health_summary": {...},
  "generated_at": "2026-04-26T19:00:00.000Z"
}
```

---

## D10 Integration

### Event Logging

Each test execution logs to D10 via `log_event()`:

- **event_type:** "skill_test"
- **payload:** `{ test_type, errors }`
- **trace_id:** Unique identifier for test run
- **session_id:** Optional session identifier

### Health Summary

The health summary includes:
- `health_score`: 0.0 to 1.0 (passed_tests / total_tests)
- `status`: "healthy" (≥0.8), "degraded" (≥0.5), "unhealthy" (<0.5)
- `avg_latency_ms`: Average latency across tests
- `total_escalation_attempts`: Number of escalation chain executions

---

## Guardrails

### Port 8001
All internal API calls must use port 8001.

### Circuit Breaker
- Escalation engine trips circuit breaker after full escalation failure
- Prevents infinite retry loops
- Can be reset via `reset_circuit_breaker()`

### Clean Registry
- All test runs include `trace_id` for tracking
- No orphaned test runs without trace_id

### Size Guard
- Generated JSON blueprints in `config/skill_tests/` kept small
- Minimal payload size for D10 logging

### Fail-Fast
- System measures deterministically, does not guess
- Validation is rule-based, not AI-based

---

## Implementation Status

### Phase 1: Structure & Registry (A1) ✅
- ✅ Created `backend/services/testing/` directory
- ✅ Created `backend/services/routing/` directory
- ✅ Initialized `backend/config/model_routing.json`
- ✅ Registered Epic D16 in `01_CENTRAL_TASK_REGISTRY.md`

### Phase 2: Test Generator & Validation (G17) ✅
- ✅ Implemented `test_generator.py` with `generate_testset()`
- ✅ Implemented `validation.py` with deterministic engine
- ✅ Validators: contains, not_contains, regex, not_crash

### Phase 3: Routing & Escalation (C7) ✅
- ✅ Implemented `model_router.py` with `get_routing_config()`
- ✅ Implemented `escalation.py` with `execute_with_escalation()`
- ✅ Circuit breaker protection
- ✅ Cost tracking per tier

### Phase 4: Test Runner & D10 Integration (D10) ✅
- ✅ Implemented `test_runner.py` with async execution
- ✅ D10 integration via `log_event()`
- ✅ AI Studio compatible health summary

### Phase 5: API Endpoint ✅
- ✅ Implemented `GET /api/system/run-skill-tests/{skill_id}`
- ✅ Mock tool execution for testing
- ✅ Error handling (404/500)
- ✅ Async endpoint

---

## Next Steps

### Production Tool Executor Linkage
- Replace mock `tool_call_fn` with actual `ToolExecutor` integration
- Configure API key retrieval via `keyring`
- Implement skill-specific tool execution logic

### Skill-Specific Test Blueprints
- Add custom test configurations for critical skills
- Define skill-specific validation rules
- Add skill type templates (agent, renderer)

### Continuous Integration
- Integrate with CI/CD pipeline
- Automated testing on skill changes
- Health monitoring dashboard

---

## Patterns

### #DeterministicTesting
Rule-based test generation without AI dependency for reproducible results.

### #EscalationChain
Primary → Fallback → Escalation pattern with automatic cost tracking and circuit breaker.

### #TelemetryIntegration
D10 logging for all test executions with trace_id for clean registry.

---

## References

- Task Registry: `01_CENTRAL_TASK_REGISTRY.md` (Epic D16)
- D10 Logging: `backend/services/logging/logger_core.py`
- Tool Executor: `backend/services/tool_executor.py`
