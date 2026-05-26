# JANUS TESTRESULT – DIAMOND STANDARD v1.0

## TESTRUN IDENTITY

- TestRun ID: TEST-RUN-2026-05-12-001-COMPETE-STATISTICS
- Title: Janus Intent Engine Core TestSpec - Provider Competition Statistics
- Capability: Intent Recognition & Tool Routing Engine
- TestSpec: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json
- Generated Runner: tests/e2e/generated/TEST-RUN-2026-05-12-001-COMPETE-STATISTICS.live.spec.js
- Execution Mode: LIVE_VISUAL
- Execution Date: 2026-05-12
- Execution Model: SWE 1.6
- Previous TestRun: TEST-RUN-2026-05-12-001-FINAL-V1

## AUTOMATION EVIDENCE

### Generator Service (3A)
- **Command**: `node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --out tests/e2e/generated/TEST-RUN-2026-05-12-001-COMPETE-STATISTICS.live.spec.js`
- **Result**: SUCCESS
- **Tests Generated**: 13
- **Strategies**: send=chat_window_scoped_send_v1, wait=assistant_stream_complete_v1, evidence=capture_network_v1, evaluate=contains_any_v1

### Validator Service (3B)
- **Command**: `node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --runner tests/e2e/generated/TEST-RUN-2026-05-12-001-COMPETE-STATISTICS.live.spec.js`
- **Result**: PASSED
- **Checks**: 11 validation checks passed
- **Generated Runner Manually Edited**: NEIN

### Runner Service (3C)
- **Command**: `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-12-001-COMPETE-STATISTICS.live.spec.js --headed --workers=1`
- **Result**: BLOCKED
- **Tests Executed**: 1/13 (1 blocked, 12 did not run due to serial mode)
- **Failure Classification**: RUNNER_STREAM_TIMEOUT (Frontend Rendering Error)

## TEST EXECUTION SUMMARY

### Overall Result: BLOCKED

**Status**: The test execution was blocked by the same frontend rendering failure as the previous test run. The SSE stream was observed (backend responded), but the frontend failed to render the assistant message content. Despite BACKLOG-025 being marked as DONE, the "win is not defined" JavaScript error persists.

### Test Results by Category

- **Functional Tests**: 0/5 passed (1 blocked, 4 did not run)
- **Intent Routing Tests**: 0/4 passed (4 did not run)
- **Security Tests**: 0/1 passed (1 did not run)
- **Prompt Injection Tests**: 0/1 passed (1 did not run)
- **Live Tests**: 0/2 passed (2 did not run)
- **Total**: 0/13 tests completed successfully

## PROVIDER COMPETITION STATISTICS

### Provider Win Analysis: BLOCKED

**NOTE**: No provider competition statistics could be generated because all tests were blocked by the same frontend rendering error ("win is not defined"). The following table shows the INTENDED comparison that could not be executed:

| Intent Category | GPT (gpt-5.4-nano) | Gemini (gemini-3-flash-preview) | Winner | Status |
|-----------------|-------------------|--------------------------------|--------|--------|
| Weather Intent | TC-001, LTC-001 | N/A | BLOCKED | Not executed |
| Wikipedia Query | TC-002, INT-002 | N/A | BLOCKED | Not executed |
| Geo Distance | TC-003 | N/A | BLOCKED | Not executed |
| RSS News | TC-004, INT-004 | N/A | BLOCKED | Not executed |
| Ambiguity Detection | TC-005, INT-003, LTC-002 | LTC-002 | BLOCKED | Not executed |
| Security/Prompt Injection | SEC-001, PINJ-001 | N/A | BLOCKED | Not executed |

### Provider Matrix Summary

**GPT (gpt-5.4-nano)**:
- Intended Tests: 11
- Completed: 0
- Blocked: 11
- Win Rate: N/A (blocked)

**Gemini (gemini-3-flash-preview)**:
- Intended Tests: 2
- Completed: 0
- Blocked: 2
- Win Rate: N/A (blocked)

## DETAILED FAILURE ANALYSIS

### Blocked Test: TC-001
- **Test ID**: TC-001
- **Name**: Weather inference - Brauche ich morgen in München einen Regenschirm?
- **Type**: functional
- **Provider**: GPT
- **Model**: gpt-5.4-nano
- **Prompt**: "Brauche ich morgen in München einen Regenschirm?"
- **Expected**: Contains any of ["Regen", "wetter", "München"], toolCallExpected: system.weather

### Error Classification
- **Classification**: RUNNER_STREAM_TIMEOUT
- **Error Message**: `RUNNER_STREAM_TIMEOUT: Assistant bubble appeared but is empty or only contains "..." with timestamp. SSE stream observed but no real content rendered.`
- **Root Cause**: Frontend JavaScript error prevents message rendering

### Diagnostic Evidence
- **Console [SSE]**: `[]` (no SSE console logs observed)
- **DOM eval**: `{"found":true,"containerChildCount":0,"messageCount":0,"messages":[],"containerHTMLLen":0,"containerHTMLSample":""}`
- **DOM message texts**: `"ERR: win is not defined"`
- **Page Snapshot**: Janus UI loaded successfully, chat windows visible, but assistant message container empty

### Root Cause Analysis
The failure indicates a **frontend JavaScript error** that persists from the previous test run:
1. The SSE stream was successfully observed (backend `/api/chat/stream` request was made)
2. The assistant bubble appeared in the DOM
3. However, the bubble remained empty or only contained "..." with timestamp
4. DOM evaluation shows `containerChildCount: 0` and `messageCount: 0` - no messages were actually rendered
5. The critical error: `"ERR: win is not defined"` suggests a JavaScript reference error in the frontend rendering code

This is **not** a backend/provider issue - the backend responded and the stream was initiated. The failure is in the **frontend stream-render pipeline** where a JavaScript error prevents the message content from being rendered.

### Comparison with Previous TestRun
- **Previous TestRun**: TEST-RUN-2026-05-12-001-FINAL-V1
- **Previous Result**: BLOCKED (same error: "win is not defined")
- **BACKLOG-025 Status**: DONE (marked as completed on 2026-05-12)
- **Fix Applied**: BACKLOG-025 was marked as DONE with validation evidence claiming "Manueller Janus Test PASS - 'win is not defined' Fehler behoben"
- **Current Result**: BLOCKED (same error persists)

### Critical Issue: BACKLOG-025 Fix Ineffective
**Severity**: CRITICAL

Despite BACKLOG-025 being marked as DONE with "Manueller Janus Test PASS", the actual frontend error "win is not defined" persists in the automated test environment. This indicates one of the following:
1. The fix was not actually applied to the codebase
2. The fix was incomplete or incorrect
3. The manual test environment differs from the automated test environment
4. The fix was reverted or overwritten

**Recommendation**: BACKLOG-025 should be reopened and investigated. The validation evidence claiming "Manueller Janus Test PASS" appears to be incorrect or incomplete.

## EVIDENCE ARTIFACTS

### Playwright Artifacts
- **Screenshot**: test-results\tests-e2e-generated-TEST-R-<hash>--München-einen-Regenschirm--janus-chromium\test-failed-1.png
- **Video**: test-results\tests-e2e-generated-TEST-R-<hash>--München-einen-Regenschirm--janus-chromium\video.webm
- **Trace**: test-results\tests-e2e-generated-TEST-R-<hash>--München-einen-Regenschirm--janus-chromium\trace.zip
- **Error Context**: test-results\tests-e2e-generated-TEST-R-<hash>--München-einen-Regenschirm--janus-chromium\error-context.md

### Backend Logs
- Backend started successfully on port 8001
- Test database: `sqlite:///./tmp/e2e_janus.db`
- Vector service initialized successfully
- Auth token endpoint: `POST /api/auth/token` returned 200 OK
- Ollama provider connections established (localhost:11434)

## FINDINGS

### Critical Finding: FRONTEND_RENDERING_FAILURE (PERSISTENT - BACKLOG-025 FIX INEFFECTIVE)
- **Severity**: CRITICAL
- **Scope**: Frontend stream-render pipeline
- **Category**: Functional
- **Description**: The frontend JavaScript code has a reference error ("win is not defined") that prevents assistant message content from being rendered after SSE stream initiation. Despite BACKLOG-025 being marked as DONE with claimed manual test PASS, the error persists in the automated test environment.
- **Impact**: Blocks all live E2E tests that rely on assistant response rendering; prevents provider competition analysis
- **Evidence**: DOM evaluation shows empty message container, JavaScript error in message texts, same error in consecutive test runs, BACKLOG-025 marked DONE but fix not working
- **Persistence**: Error appeared in TEST-RUN-2026-05-12-001, persisted in TEST-RUN-2026-05-12-001-FINAL-V1, and now in TEST-RUN-2026-05-12-001-COMPETE-STATISTICS

### Secondary Finding: BACKLOG_VALIDATION_DISCREPANCY
- **Severity**: HIGH
- **Scope**: Backlog validation process
- **Category**: Test Infrastructure
- **Description**: BACKLOG-025 was marked as DONE with validation evidence claiming "Manueller Janus Test PASS - 'win is not defined' Fehler behoben", but the automated test shows the error still exists. This indicates a discrepancy between manual validation and automated test results.
- **Impact**: Wasted test execution time, incorrect backlog state, potential false sense of completion
- **Evidence**: BACKLOG-025 Status: DONE, Validation evidence claims fix verified, but automated test shows same error
- **Recommendation**: Reopen BACKLOG-025, investigate why manual validation passed but automated test fails, ensure proper fix is applied and verified in both environments

## SECURITY / PRIVACY / PROMPT-INJECTION GATE STATUS

- **User Data Involved**: NO
- **Destructive Operations Possible**: YES (weather tool calls)
- **External Content Involved**: YES (weather APIs)
- **Prompt Injection Surface**: HIGH (RSS feeds, web content)
- **Test Sandbox Required**: YES
- **Security Tests Executed**: NO (blocked by frontend error)
- **Prompt Injection Tests Executed**: NO (blocked by frontend error)
- **Gate Status**: NOT VALIDATED (tests blocked)

## COST AND TOKEN EVIDENCE

- **Cost Goal**: Minimal tool usage per intent
- **Token Goal**: < optimized responses per query
- **Smallest Model First**: YES (gpt-5.4-nano used)
- **Escalation Limit**: Only on ambiguity or failure cases
- **Actual Usage**: Not measurable due to frontend rendering failure

## PROVIDER AND MODEL MATRIX

- **GPT**: gpt-5.4-nano (smallest viable) - attempted but blocked by frontend error
- **Gemini**: gemini-3-flash-preview (smallest viable) - not reached due to test blockage
- **Escalation**: Not applicable (tests did not complete)

## RECOMMENDATION

### Immediate Action Required
BACKLOG-025 must be reopened and investigated. The claimed fix for the "win is not defined" JavaScript error is not working in the automated test environment. One of the following must be done:
1. Verify if the fix was actually applied to the codebase
2. If applied, verify why it's not working in the automated environment
3. If not applied, apply the actual fix
4. Re-validate with both manual and automated tests before marking DONE again

### Recommended Next Step
Route to TEST SKILL 4 – FINDING TRIAGE AND ROUTING for:
1. **Finding Classification**: FRONTEND_RENDERING_FAILURE (CRITICAL severity, PERSISTENT, BACKLOG-025 FIX INEFFECTIVE)
2. **Recommended Action**: Reopen BACKLOG-025, investigate and fix the "win is not defined" JavaScript error in the frontend stream-render pipeline
3. **Backlog Recommendation**: Ensure BACKLOG-025 validation evidence is accurate and reflects actual automated test results
4. **Retest Required**: YES - full test suite must be re-executed after frontend fix
5. **Fix Verification**: Verify that the fix is actually applied and works in both manual and automated test environments

## CONFIDENCE SCORE

- **Test Execution Confidence**: 0% (blocked by frontend error)
- **Finding Confidence**: HIGH (clear diagnostic evidence, consistent across multiple runs, BACKLOG validation discrepancy confirmed)
- **Overall TestRun Confidence**: LOW (no functional tests completed, same error persists, BACKLOG validation issue identified)

## TESTRESULT METADATA

- **Generated By**: TEST SKILL 3 – LIVE JANUS TEST EXECUTION
- **Execution Model**: SWE 1.6
- **Automation Compliance**: YES (generator-first, validator-passed)
- **Manual Intervention Required**: YES (test process killed due to stuck state)
- **Evidence Complete**: PARTIAL (Playwright artifacts, backend logs, diagnostics available but full execution blocked)
- **Retest Mode**: LIVE_RETEST
- **Provider Competition**: BLOCKED (no statistics available due to frontend error)
