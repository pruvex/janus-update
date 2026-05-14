# TestRun Results: TEST-RUN-2026-05-13-002

## Summary
**TestRunId**: TEST-RUN-2026-05-13-002
**Capability**: Intent Recognition & Tool Routing Engine
**TestSpec**: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
**TestPlan**: documentation/test-runs/TEST-RUN-2026-05-13-BENCHMARK-FINAL.json
**Test Date**: 2026-05-13
**Execution Mode**: LIVE_VISUAL
**Target**: JANUS_CHAT
**BaseUrl**: http://localhost:5173/ (corrected per Port Sanity Rule)

## Test Results

### Overall Result: TEST AUTOMATION FAILED

### Failure Reason: GENERATOR_V2_2_MODEL_SELECTION_NOT_WORKING

### Infrastructure Status
- **Frontend**: ACCESSIBLE (http://localhost:5173/)
- **Backend**: RUNNING (http://127.0.0.1:8001/api/health)
- **BaseUrl**: Corrected to http://localhost:5173/

### Test Execution Attempt
- **Generator Service**: PASSED (generated 12 tests with model_selection_v1 strategy)
- **Validator Service**: PASSED (11 checks)
- **Playwright Execution**: FAILED (12/12 tests failed)
- **Tests Executed**: 12/12 (all failed due to model selection issue)
- **Root Cause**: Generator V2.2 model_selection_v1 strategy defined but not functional

### Generator V2.2 Analysis
**What Was Added:**
- TestPlan updated with `"modelSelection": "model_selection_v1"` strategy
- Generated runner includes model_selection_v1 functions (selectModel, waitSendButtonReady, resolveHeaderProviderValue)
- beforeEach block includes MODEL_PLAN_MAP and PROVIDER_PLAN_MAP generation
- beforeEach attempts to call selectModel() before each test

**What Failed:**
- Model dropdown still shows "-- Keine Modelle ausgewählt --" (No models selected)
- selectModel() function not successfully populating model dropdown
- Send button remains disabled (no model selected)
- All tests fail before chat interaction can occur

**Possible Root Causes:**
1. Model dropdown element selectors incorrect (#chat-header-model-A not found)
2. Provider dropdown element selectors incorrect (#chat-header-provider-A not found)
3. Model options not loaded when selectModel() is called
4. Timing issue: models load asynchronously after page load
5. MODEL_PLAN_MAP testCaseId resolution failing

### Expected Test Coverage (Not Validated)
- TC-001-GPT/GEMINI: Weather inference → system.weather
- TC-002-GPT/GEMINI: Wikipedia query → system.wikipedia_summary
- TC-003-GPT/GEMINI: Geo distance → system.routing (OSRM attribution)
- TC-004-GPT/GEMINI: RSS news → system.rss_news
- TC-005-GPT/GEMINI: Ambiguous request → Clarification required
- PINJ-001-GPT/GEMINI: Prompt Injection Hard-Deny

### Security Gates (Not Validated)
- **PINJ-001 Hard-Deny**: NOT TESTED (model selection failed)
- **TC-003 Attribution ("Quelle: OSRM")**: NOT TESTED (model selection failed)

### Key Questions (Cannot Answer)
- **Does "Quelle: OSRM" appear in TC-003?** - NOT TESTED (model selection failed)
- **Does PINJ-001 block Heise-News cleanly?** - NOT TESTED (model selection failed)
- **Does Janus switch providers correctly in header?** - NOT OBSERVED (model selection failed)

## Automation Evidence

### Generator Command (Attempt 1 - Original)
```bash
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-13-BENCHMARK-FINAL.json --out tests/e2e/generated/TEST-RUN-2026-05-13-002.live.spec.js
```
**Result**: GENERATED (12 tests, no modelSelection strategy)

### TestPlan Update
Added `"modelSelection": "model_selection_v1"` to strategies section

### Generator Command (Attempt 2 - With modelSelection)
```bash
node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-13-BENCHMARK-FINAL.json --out tests/e2e/generated/TEST-RUN-2026-05-13-002.live.spec.js
```
**Result**: GENERATED (12 tests, model_selection_v1 functions defined)

### Validator Command
```bash
node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-13-BENCHMARK-FINAL.json --runner tests/e2e/generated/TEST-RUN-2026-05-13-002.live.spec.js
```
**Result**: VALIDATION PASSED (11 checks)

### Runner Command
```bash
npx playwright test tests/e2e/generated/TEST-RUN-2026-05-13-002.live.spec.js --headed
```
**Result**: FAILED (12/12 tests - model selection not functional)

### Playwright Report
- HTML Report: http://localhost:50644
- Screenshots: 12 test-failure screenshots captured
- Videos: 12 test-failure videos captured
- Evidence: Only 1 evidence file (TC-001 from previous test run, not current run)

## Required Actions

### Generator V2.2 Debugging
The model_selection_v1 strategy needs debugging:
1. Verify element selectors: #chat-header-provider-A, #chat-header-model-A
2. Add diagnostic logging to selectModel() function
3. Check if model options are loaded before selection
4. Verify MODEL_PLAN_MAP and PROVIDER_PLAN_MAP population
5. Add retry logic for asynchronous model loading

### Options for Validation
**Option A**: Manual Testing (Immediate)
- Start frontend: `npm run start-dev`
- Manually select GPT model (gpt-5.4-nano) and run TC-001 through TC-005 + PINJ-001
- Manually select Gemini model (gemini-3-flash-preview) and run TC-001 through TC-005 + PINJ-001
- Record results manually
- Answer key questions: OSRM attribution, PINJ-001 Hard-Deny

**Option B**: Fix Generator (Deferred)
- Debug selectModel() function with element selector verification
- Add diagnostic logging to beforeEach
- Test with manual Playwright inspection
- Regenerate runner and re-run automated tests

**Option C**: Hybrid Approach (Recommended)
- Perform manual validation NOW to answer key questions for v0.4.17-beta.31 Diamond Standard
- Debug generator for future test automation
- Document manual findings in TestResult

## Findings

### BLOCKER: Generator V2.2 Model Selection Not Functional
- model_selection_v1 strategy defined in TestPlan and generated runner
- selectModel() function defined but not successfully populating dropdown
- Element selectors may be incorrect or timing issue with model loading
- This is a test infrastructure issue, not a product issue
- Product functionality cannot be validated without working model selection

### Risk Assessment
- **Risk Level**: HIGH (cannot validate critical routing functionality)
- **Impact**: Unable to verify v0.4.17-beta.31 fixes for intent routing
- **Provider Parity**: Not validated (GPT vs Gemini comparison not possible)
- **Security Gates**: Not validated (PINJ-001 Hard-Deny not tested)

### Recommendation
**Immediate Action**: Manual testing required to validate:
1. TC-003: "Quelle: OSRM" attribution
2. PINJ-001: Prompt Injection Hard-Deny for Heise-News

**Generator Debug**: Add element selector verification and diagnostic logging to selectModel() function to understand why model dropdown is not being populated.
