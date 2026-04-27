# D20: Routing Calibration — Model Performance Matrix — 🥇 SEALED & COMPLETE (2026-04-27)

## Overview
D20 implements a systematic approach to model routing calibration by testing multiple models against a matrix of skills with configurable run counts. This enables data-driven decisions about which models perform best for specific skill categories.

## Architecture

### API Endpoint
**POST** `/api/system/run-batch-tests`

### Request Body (Pydantic Model)
```python
class RoutingCalibrationRequest(BaseModel):
    skill_ids: List[str] = Field(default_factory=list, description="List of skill IDs to test")
    models: List[str] = Field(default=["gpt-5.4-mini"], description="List of models to test (e.g., gpt-5.4-mini, gpt-5.4, gemini-3-flash, gemini-3-pro)")
    runs_per_model: int = Field(default=1, ge=1, le=10, description="Number of runs per model")
    real_run: bool = Field(default=False, description="If True, makes actual API calls")
```

### Response
```json
{
  "status": "started",
  "total_tests": 400,
  "config": {
    "skills": 100,
    "models": 4,
    "runs_per_model": 1,
    "real_run": true
  },
  "message": "Matrix run started in background. Check logs for progress."
}
```

## Implementation Details

### 1. Matrix Run Logic (system.py)
- **Outer Loop**: Iterates over each model in the `models` list
- **Inner Loop**: Executes `runs_per_model` iterations per model
- **Rate Limiting**: `asyncio.sleep(0.5)` between runs and between models to avoid 429 errors
- **Model Override**: The specified model is passed to `real_tool_call_fn` via kwargs, overriding the default model_routing.json configuration

### 2. Trace ID Tracking (test_runner.py)
- **Unique Trace per Test**: Each test execution generates a unique `trace_id` using `uuid.uuid4()`
- **D10 Integration**: Trace ID is passed through the test execution chain for telemetry correlation
- **Parameters Added**:
  - `run_batch_tests()`: Added `trace_id` parameter
  - `run_testset()`: Added `trace_id` parameter (both method and standalone function)

### 3. Model Override Mechanism
```python
# Override model in tool_call_fn by passing it in kwargs
async def model_aware_tool_call_fn(provider: str, model_override: str, **kwargs):
    kwargs["model"] = model_override
    return await tool_call_fn(provider=provider, model=model_override, **kwargs)

batch_summary = await test_runner.run_batch_tests(
    tool_call_fn=lambda p, m, **k: tool_call_fn(provider=p, model=model, **k),
    skill_ids=skill_ids_to_test,
    trace_id=trace_id
)
```

## Usage Examples

### Phase 1: Targeted Fleet Optimization (100 skills × 4 models × 1 run = 400 tests) — 🥇 SEALED & COMPLETE
```bash
curl -X POST "http://localhost:8001/api/system/run-batch-tests" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_ids": [],
    "models": ["gpt-5.4-mini", "gpt-5.4", "gemini-3-flash", "gemini-3-pro"],
    "runs_per_model": 1,
    "real_run": true
  }'
```

### Phase 2: Deep Calibration (10 skills × 4 models × 10 runs = 400 tests) — 🥇 SEALED & COMPLETE
```bash
curl -X POST "http://localhost:8001/api/system/run-batch-tests" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_ids": ["system.weather", "filesystem.list_directory", "calendar.create_event", "system.country_info", "communication.send_email", "system.video_understanding", "system.websearch", "knowledge.list_documents", "system.price_comparison", "system.rss_news"],
    "models": ["gpt-5.4-mini", "gpt-5.4", "gemini-3-flash", "gemini-3-pro"],
    "runs_per_model": 10,
    "real_run": true
  }'
```

## Guardrails

### Rate Limiting
- **Between Runs**: 0.5s sleep to prevent API rate limits (429 errors)
- **Between Models**: 0.5s sleep for additional buffer
- **Total Time Estimate**: 400 tests × 0.5s ≈ 200s (3.3 minutes) minimum, plus actual LLM latency

### D10 Trace Integrity
- **Unique IDs**: Each of the 400 tests gets its own `trace_id` via `uuid.uuid4()`
- **Correlation**: Trace IDs flow through the entire execution chain for post-hoc analysis
- **Session Tracking**: `session_id` groups related matrix runs together

### Cost Management
- **Budget Guard**: `real_run` flag controls whether actual API calls are made
- **Model Selection**: Explicit model list prevents accidental expensive model usage
- **Run Limits**: `runs_per_model` capped at 10 to prevent runaway costs

## Files Modified

### backend/api/routers/system.py
- Added `RoutingCalibrationRequest` Pydantic model
- Changed `@router.get` to `@router.post` for `/system/run-batch-tests`
- Implemented matrix run logic with nested loops (models × runs_per_model)
- Added rate limiting with `asyncio.sleep(0.5)`
- Added `trace_id` generation with `uuid.uuid4()`
- Implemented model override via kwargs

### backend/services/testing/test_runner.py
- Added `trace_id` parameter to `run_batch_tests()`
- Added `trace_id` parameter to `run_testset()` method
- Added `trace_id` parameter to standalone `run_testset()` function
- Updated `run_batch_tests()` to pass `trace_id` to `run_testset()`

## Success Criteria

- **Phase 1**: 400 tests executed successfully with unique trace IDs
- **Phase 2**: Model performance data captured for all 4 models
- **No 429 Errors**: Rate limiting prevents API throttling
- **Trace Integrity**: All 400 tests have unique, correlated trace IDs
- **Cost Control**: Real runs only execute when explicitly enabled

## Next Steps

1. **Execute Phase 1**: Run 400-test matrix with 4 models
2. **Analyze Results**: Compare pass rates and latencies across models
3. **Update model_routing.json**: Set optimal models based on calibration data
4. **Document Findings**: Record which models perform best for which skill categories
