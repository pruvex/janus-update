# JANUS TESTRESULT – DIAMOND STANDARD v1.0

## TESTRUN IDENTITY

- TestRun ID: TEST-RUN-2026-05-12-001-ROUTING-AUDIT
- Title: Janus Intent Engine Core TestSpec - Routing Audit with Deep Evidence
- Capability: Intent Recognition & Tool Routing Engine
- TestSpec: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json
- Generated Runner: tests/e2e/generated/TEST-RUN-2026-05-12-001-ROUTING-AUDIT.live.spec.js
- Execution Mode: LIVE_VISUAL
- Execution Date: 2026-05-12
- Execution Model: SWE 1.6
- Strategy Update: send=chat_button_click_send_v1 (from chat_window_scoped_send_v1)

## AUTOMATION EVIDENCE

### Generator Service (3A)
- **Command**: `node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --out tests/e2e/generated/TEST-RUN-2026-05-12-001-ROUTING-AUDIT.live.spec.js`
- **Result**: SUCCESS
- **Tests Generated**: 13
- **Strategies**: send=chat_button_click_send_v1, wait=assistant_stream_complete_v1, evidence=capture_network_v1, evaluate=contains_any_v1

### Validator Service (3B)
- **Command**: `node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --runner tests/e2e/generated/TEST-RUN-2026-05-12-001-ROUTING-AUDIT.live.spec.js`
- **Result**: PASSED
- **Checks**: 11 validation checks passed
- **Generated Runner Manually Edited**: NEIN

### Runner Service (3C)
- **Command**: `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-12-001-ROUTING-AUDIT.live.spec.js --headed --workers=1`
- **Result**: BLOCKED
- **Tests Executed**: 1/13 (1 blocked, 12 did not run due to serial mode)
- **Failure Classification**: RUNNER_STREAM_TIMEOUT (Frontend Rendering Error)

## TEST EXECUTION SUMMARY

### Overall Result: BLOCKED

**Status**: The test execution was blocked by the same frontend rendering failure as the previous test runs. The SSE stream was observed (backend responded), but the frontend failed to render the assistant message content. Despite BACKLOG-025 being marked as DONE, the "win is not defined" JavaScript error persists.

### Test Results by Category

- **Functional Tests**: 0/5 passed (1 blocked, 4 did not run)
- **Intent Routing Tests**: 0/4 passed (4 did not run)
- **Security Tests**: 0/1 passed (1 did not run)
- **Prompt Injection Tests**: 0/1 passed (1 did not run)
- **Live Tests**: 0/2 passed (2 did not run)
- **Total**: 0/13 tests completed successfully

## ROUTING AUDIT: EXPECTED VS ACTUAL TOOL CALLS

### Critical Finding: ROUTING VERIFICATION BLOCKED

**NOTE**: Due to the frontend rendering failure blocking all tests, actual tool call evidence could not be collected. The following table shows the EXPECTED tools from the TestPlan, but ACTUAL tool calls could not be verified because the assistant messages were not rendered.

| TestCase-ID | Test Name | Type | Provider/Model | Expected Tool | Actual Tool | Status |
|-------------|-----------|------|----------------|---------------|-------------|--------|
| TC-001 | Weather inference - Brauche ich morgen in München einen Regenschirm? | functional | GPT / gpt-5.4-nano | system.weather | NOT_VERIFIED | BLOCKED |
| TC-002 | Wikipedia query - Wer ist Nikola Tesla? | functional | GPT / gpt-5.4-nano | system.wiki_fact | NOT_VERIFIED | NOT_RUN |
| TC-003 | Geo distance - Wie weit ist Berlin von München? | functional | GPT / gpt-5.4-nano | system.geo | NOT_VERIFIED | NOT_RUN |
| TC-004 | RSS news - Was gibt es Neues bei Heise? | functional | GPT / gpt-5.4-nano | system.news_rss | NOT_VERIFIED | NOT_RUN |
| TC-005 | Ambiguous request - Ich brauche Infos dazu | intent_routing | GPT / gpt-5.4-nano | NONE (requiresConfirmation) | NOT_VERIFIED | NOT_RUN |
| INT-001 | Intent: Wird es regnen morgen? | intent_routing | GPT / gpt-5.4-nano | system.weather | NOT_VERIFIED | NOT_RUN |
| INT-002 | Intent: Erzähl mir über Einstein | intent_routing | GPT / gpt-5.4-nano | system.wiki_fact | NOT_VERIFIED | NOT_RUN |
| INT-003 | Intent: Wie weit ist es? (ambiguous) | intent_routing | GPT / gpt-5.4-nano | NONE (requiresConfirmation) | NOT_VERIFIED | NOT_RUN |
| INT-004 | Intent: News heute | intent_routing | GPT / gpt-5.4-nano | system.news_rss | NOT_VERIFIED | NOT_RUN |
| SEC-001 | Prompt Injection - Malicious web/RSS input | security | GPT / gpt-5.4-nano | NONE (must not execute malicious) | NOT_VERIFIED | NOT_RUN |
| PINJ-001 | Prompt Injection - RSS feed with Ignore rules | prompt_injection | GPT / gpt-5.4-nano | NONE (must not execute malicious) | NOT_VERIFIED | NOT_RUN |
| LTC-001 | Live: Weather intent with GPT smallest viable | functional | GPT / gpt-5.4-nano | system.weather | NOT_VERIFIED | NOT_RUN |
| LTC-002 | Live: Ambiguous query with Gemini smallest viable | intent_routing | Gemini / gemini-3-flash-preview | NONE (requiresConfirmation) | NOT_VERIFIED | NOT_RUN |

### Tool Routing Summary

**Expected Tool Distribution (from TestPlan)**:
- system.weather: 3 tests (TC-001, INT-001, LTC-001)
- system.wiki_fact: 2 tests (TC-002, INT-002)
- system.geo: 1 test (TC-003)
- system.news_rss: 2 tests (TC-004, INT-004)
- NONE (requiresConfirmation): 3 tests (TC-005, INT-003, LTC-002)
- NONE (security/prompt_injection): 2 tests (SEC-001, PINJ-001)

**Actual Tool Verification Status**:
- system.weather: 0/3 verified (3 NOT_VERIFIED due to frontend block)
- system.wiki_fact: 0/2 verified (2 NOT_VERIFIED due to frontend block)
- system.geo: 0/1 verified (1 NOT_VERIFIED due to frontend block)
- system.news_rss: 0/2 verified (2 NOT_VERIFIED due to frontend block)
- NONE (requiresConfirmation): 0/3 verified (3 NOT_VERIFIED due to frontend block)
- NONE (security/prompt_injection): 0/2 verified (2 NOT_VERIFIED due to frontend block)

## DETAILED FAILURE ANALYSIS

### Blocked Test: TC-001
- **Test ID**: TC-001
- **Name**: Weather inference - Brauche ich morgen in München einen Regenschirm?
- **Type**: functional
- **Provider**: GPT
- **Model**: gpt-5.4-nano
- **Prompt**: "Brauche ich morgen in München einen Regenschirm?"
- **Expected Tool**: system.weather
- **Expected Response**: Contains any of ["Regen", "wetter", "München"]

### Error Classification
- **Classification**: RUNNER_STREAM_TIMEOUT
- **Error Message**: `RUNNER_STREAM_TIMEOUT: Assistant bubble appeared but is empty or only contains "..." with timestamp. SSE stream observed but no real content rendered.`
- **Root Cause**: Frontend JavaScript error prevents message rendering

### Diagnostic Evidence
- **Console [SSE]**: SSE stream was observed (backend responded)
- **DOM eval**: Assistant bubble appeared but remained empty
- **DOM message texts**: `"ERR: win is not defined"`
- **Page Snapshot**: Janus UI loaded successfully, chat windows visible, but assistant message container empty

### Root Cause Analysis
The failure indicates a **frontend JavaScript error** that persists from the previous test runs:
1. The SSE stream was successfully observed (backend `/api/chat/stream` request was made)
2. The assistant bubble appeared in the DOM
3. However, the bubble remained empty or only contained "..." with timestamp
4. The critical error: `"ERR: win is not defined"` suggests a JavaScript reference error in the frontend rendering code

This is **not** a backend/provider issue - the backend responded and the stream was initiated. The failure is in the **frontend stream-render pipeline** where a JavaScript error prevents the message content from being rendered.

### Comparison with Previous TestRuns
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

## ROUTING AUDIT FINDINGS

### Primary Finding: ROUTING_VERIFICATION_BLOCKED
- **Severity**: CRITICAL
- **Scope**: Intent Engine / Tool Routing / Frontend Rendering
- **Category**: Functional
- **Description**: The routing audit cannot be completed because the frontend rendering error prevents assistant messages from being displayed. Without rendered messages, tool call evidence cannot be collected from the SSE stream or DOM.
- **Impact**: Blocks verification of all 13 tool routing test cases; cannot determine if Intent Engine correctly routes to expected tools
- **Evidence**: Frontend JavaScript error "win is not defined" prevents message rendering; SSE stream observed but content not rendered; all tests blocked
- **Persistence**: Error appeared in TEST-RUN-2026-05-12-001, persisted in TEST-RUN-2026-05-12-001-FINAL-V1, TEST-RUN-2026-05-12-001-COMPETE-STATISTICS, and now in TEST-RUN-2026-05-12-001-ROUTING-AUDIT

### Secondary Finding: BACKLOG_VALIDATION_DISCREPANCY
- **Severity**: HIGH
- **Scope**: Backlog validation process
- **Category**: Test Infrastructure
- **Description**: BACKLOG-025 was marked as DONE with validation evidence claiming "Manueller Janus Test PASS - 'win is not defined' Fehler behoben", but the automated test shows the error still exists. This indicates a discrepancy between manual validation and automated test results.
- **Impact**: Wasted test execution time, incorrect backlog state, potential false sense of completion
- **Evidence**: BACKLOG-025 Status: DONE, Validation evidence claims fix verified, but automated test shows same error
- **Recommendation**: Reopen BACKLOG-025, investigate why manual validation passed but automated test fails, ensure proper fix is applied and verified in both environments

### Potential Routing Issue: BACKLOG-029 (NEW)
- **Severity**: HIGH
- **Scope**: Intent Engine / Tool Routing
- **Category**: Functional
- **Description**: Based on the previous test result (TEST-RUN-2026-05-12-001-COMPETE-STATISTICS), there is evidence that the Intent Engine may be using LLM knowledge instead of calling the system.weather tool for weather queries. However, this cannot be verified in the current test run due to the frontend rendering block.
- **Impact**: If confirmed, this would mean weather queries return outdated LLM knowledge instead of current API data
- **Evidence**: Previous test result suggested toolCallExpected: system.weather but no tool call executed (could not be verified due to frontend error)
- **Status**: PENDING VERIFICATION (blocked by frontend rendering failure)

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
4. **Retest Required**: YES - full routing audit test suite must be re-executed after frontend fix
5. **Fix Verification**: Verify that the fix is actually applied and works in both manual and automated test environments
6. **BACKLOG-029**: After frontend fix, re-execute routing audit to verify if Intent Engine correctly calls system.weather tool or uses LLM knowledge

## CONFIDENCE SCORE

- **Test Execution Confidence**: 0% (blocked by frontend error)
- **Finding Confidence**: HIGH (clear diagnostic evidence, consistent across multiple runs, BACKLOG validation discrepancy confirmed)
- **Overall TestRun Confidence**: LOW (no functional tests completed, same error persists, BACKLOG validation issue identified, routing audit blocked)

## TESTRESULT METADATA

- **Generated By**: TEST SKILL 3 – LIVE JANUS TEST EXECUTION
- **Execution Model**: SWE 1.6
- **Automation Compliance**: YES (generator-first, validator-passed)
- **Manual Intervention Required**: YES (test process killed due to stuck state)
- **Evidence Complete**: PARTIAL (Playwright artifacts, backend logs, diagnostics available but full execution blocked)
- **Retest Mode**: LIVE_RETEST
- **Routing Audit**: BLOCKED (no tool call verification possible due to frontend error)
