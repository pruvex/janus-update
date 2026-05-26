# JANUS TESTRESULT – DIAMOND STANDARD v1.0

## TESTRUN IDENTITY

- TestRun ID: TEST-RUN-2026-05-12-001-TRUTH-REPORT
- Title: Janus Intent Engine Core TestSpec - Truth Report with Complete Tool Routing Documentation
- Capability: Intent Recognition & Tool Routing Engine
- TestSpec: documentation/TEST_SPEC/REVIEW EXECUTION ROUTING.md
- TestPlan: documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json
- Generated Runner: tests/e2e/generated/TEST-RUN-2026-05-12-001-TRUTH-REPORT.live.spec.js
- Execution Mode: LIVE_VISUAL
- Execution Date: 2026-05-12
- Execution Model: SWE 1.6
- Timeout Configuration: testCaseMs=120000, assistantResponseMs=60000
- Strategy Configuration: send=chat_button_click_send_v1, wait=assistant_stream_complete_v1, evidence=capture_network_v1, evaluate=contains_any_v1

## AUTOMATION EVIDENCE

### Generator Service (3A)
- **Command**: `node tests/e2e/generator/generate-live-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --out tests/e2e/generated/TEST-RUN-2026-05-12-001-TRUTH-REPORT.live.spec.js`
- **Result**: SUCCESS
- **Tests Generated**: 13
- **Strategies**: send=chat_button_click_send_v1, wait=assistant_stream_complete_v1, evidence=capture_network_v1, evaluate=contains_any_v1

### Validator Service (3B)
- **Command**: `node tests/e2e/generator/validate-runner.mjs --plan documentation/test-runs/TEST-RUN-2026-05-12-001_plan.json --runner tests/e2e/generated/TEST-RUN-2026-05-12-001-TRUTH-REPORT.live.spec.js`
- **Result**: PASSED
- **Checks**: 11 validation checks passed
- **Generated Runner Manually Edited**: NEIN

### Runner Service (3C)
- **Command**: `npx playwright test tests/e2e/generated/TEST-RUN-2026-05-12-001-TRUTH-REPORT.live.spec.js --headed --workers=1`
- **Result**: BLOCKED
- **Tests Executed**: 1/13 (1 blocked, 12 did not run due to serial mode)
- **Failure Classification**: RUNNER_STREAM_TIMEOUT (Frontend Rendering Error)

## TEST EXECUTION SUMMARY

### Overall Result: BLOCKED

**Status**: The test execution was blocked by the same frontend rendering failure as all previous test runs. The SSE stream was observed (backend responded), but the frontend failed to render the assistant message content. Despite BACKLOG-025 and BACKLOG-030 being marked as DONE, the "win is not defined" JavaScript error persists.

### Test Results by Category

- **Functional Tests**: 0/5 passed (1 blocked, 4 did not run)
- **Intent Routing Tests**: 0/4 passed (4 did not run)
- **Security Tests**: 0/1 passed (1 did not run)
- **Prompt Injection Tests**: 0/1 passed (1 did not run)
- **Live Tests**: 0/2 passed (2 did not run)
- **Total**: 0/13 tests completed successfully

## COMPLETE TOOL ROUTING DOCUMENTATION FOR ALL 13 CASES

| TestCase-ID | Tool Expected | Tool Called | Result | Notes |
|-------------|---------------|-------------|--------|-------|
| TC-001 | system.weather | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Frontend error prevented tool call verification |
| TC-002 | system.wiki_fact | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| TC-003 | system.geo | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| TC-004 | system.news_rss | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| TC-005 | none (requiresConfirmation) | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| INT-001 | system.weather | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| INT-002 | system.wiki_fact | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| INT-003 | none (requiresConfirmation) | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| INT-004 | system.news_rss | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| SEC-001 | none (must not execute malicious) | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| PINJ-001 | none (must not execute malicious) | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| LTC-001 | system.weather | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |
| LTC-002 | none (requiresConfirmation) | NOT_VERIFIED | TOOL_ROUTING_FAILURE | Test did not run - blocked by TC-001 failure |

## TOOL ROUTING ANALYSIS

### Expected Tool Distribution (from TestPlan)
- **system.weather**: 3 tests (TC-001, INT-001, LTC-001)
- **system.wiki_fact**: 2 tests (TC-002, INT-002)
- **system.geo**: 1 test (TC-003)
- **system.news_rss**: 2 tests (TC-004, INT-004)
- **none (requiresConfirmation)**: 3 tests (TC-005, INT-003, LTC-002)
- **none (security/prompt_injection)**: 2 tests (SEC-001, PINJ-001)

### Actual Tool Call Verification Status
- **system.weather**: 0/3 verified (3 NOT_VERIFIED due to frontend block)
- **system.wiki_fact**: 0/2 verified (2 NOT_VERIFIED due to frontend block)
- **system.geo**: 0/1 verified (1 NOT_VERIFIED due to frontend block)
- **system.news_rss**: 0/2 verified (2 NOT_VERIFIED due to frontend block)
- **none (requiresConfirmation)**: 0/3 verified (3 NOT_VERIFIED due to frontend block)
- **none (security/prompt_injection)**: 0/2 verified (2 NOT_VERIFIED due to frontend block)

### Tool Routing Success Rate
- **Overall Success Rate**: 0% (0/13 tests verified)
- **Functional Tool Routing**: 0% (0/5 tests verified)
- **Intent Routing**: 0% (0/4 tests verified)
- **Security Routing**: 0% (0/1 test verified)
- **Prompt Injection Routing**: 0% (0/1 test verified)
- **Live Routing**: 0% (0/2 tests verified)

## DETAILED FAILURE ANALYSIS

### Blocked Test: TC-001
- **Test ID**: TC-001
- **Name**: Weather inference - Brauche ich morgen in München einen Regenschirm?
- **Type**: functional
- **Provider**: GPT
- **Model**: gpt-5.4-nano
- **Prompt**: "Brauche ich morgen in München einen Regenschirm?"
- **Expected Tool**: system.weather
- **Actual Tool Called**: NOT_VERIFIED
- **Result**: TOOL_ROUTING_FAILURE
- **Notes**: Frontend error prevented tool call verification

### Error Classification
- **Classification**: RUNNER_STREAM_TIMEOUT
- **Error Message**: `RUNNER_STREAM_TIMEOUT: Assistant bubble appeared but is empty or only contains "..." with timestamp. SSE stream observed but no real content rendered.`
- **Root Cause**: Frontend JavaScript error prevents message rendering

### Diagnostic Evidence
- **Console [SSE]**: SSE stream was observed (backend responded)
- **DOM eval**: Assistant bubble appeared but remained empty
- **DOM message texts**: `"ERR: win is not defined"`
- **Page Snapshot**: Janus UI loaded successfully, chat windows visible, but assistant message container empty
- **Backend Evidence**: Backend processed the query with Model: gpt-5.4-nano, Input Tokens: 206, Output Tokens: 16, Total Cost: 0.00005514 €; Second request: Input Tokens: 4401, Output Tokens: 101, Total Cost: 0.00090671 €

### Root Cause Analysis
The failure indicates a **frontend JavaScript error** that persists from the previous test runs:
1. The SSE stream was successfully observed (backend `/api/chat/stream` request was made)
2. The assistant bubble appeared in the DOM
3. However, the bubble remained empty or only contained "..." with timestamp
4. The critical error: `"ERR: win is not defined"` suggests a JavaScript reference error in the frontend rendering code
5. This is **not** a backend/provider issue - the backend responded and the stream was initiated
6. The failure is in the **frontend stream-render pipeline** where a JavaScript error prevents the message content from being rendered

### Comparison with Previous TestRuns
- **TEST-RUN-2026-05-12-001**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-FINAL-V1**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-COMPETE-STATISTICS**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-ROUTING-AUDIT**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-ULTIMATE-V2**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-FINAL-REPORT**: BLOCKED (same error)
- **TEST-RUN-2026-05-12-001-TRUTH-REPORT**: BLOCKED (same error)
- **BACKLOG-025 Status**: DONE (marked as completed on 2026-05-12)
- **BACKLOG-030 Status**: DONE (marked as completed on 2026-05-12)
- **BACKLOG-029 Status**: OPEN (marked as OPEN on 2026-05-12)

### Critical Issue: BACKLOG-025 AND BACKLOG-030 FIX INEFFECTIVE
**Severity**: CRITICAL

Despite BACKLOG-025 and BACKLOG-030 being marked as DONE with validation evidence claiming fixes were verified, the actual frontend error "win is not defined" persists in the automated test environment. This indicates one of the following:
1. The fixes were not actually applied to the codebase
2. The fixes were incomplete or incorrect
3. The manual test environment differs from the automated test environment
4. The fixes were reverted or overwritten

**Recommendation**: Both BACKLOG-025 and BACKLOG-030 should be reopened and investigated. The validation evidence claiming fixes were verified appears to be incorrect or incomplete.

## ROUTING AUDIT FINDINGS

### Primary Finding: ROUTING_VERIFICATION_BLOCKED
- **Severity**: CRITICAL
- **Scope**: Intent Engine / Tool Routing / Frontend Rendering
- **Category**: Functional
- **Description**: The routing audit cannot be completed because the frontend rendering error prevents assistant messages from being displayed. Without rendered messages, tool call evidence cannot be collected from the SSE stream or DOM.
- **Impact**: Blocks verification of all 13 tool routing test cases; cannot determine if Intent Engine correctly routes to expected tools; cannot assess tool routing success rate (currently 0%)
- **Evidence**: Frontend JavaScript error "win is not defined" prevents message rendering; SSE stream observed but content not rendered; all tests blocked; error persists across 7 test runs
- **Persistence**: Error appeared in all 7 test runs: TEST-RUN-2026-05-12-001, FINAL-V1, COMPETE-STATISTICS, ROUTING-AUDIT, ULTIMATE-V2, FINAL-REPORT, TRUTH-REPORT

### Secondary Finding: BACKLOG_VALIDATION_DISCREPANCY
- **Severity**: CRITICAL
- **Scope**: Backlog validation process
- **Category**: Test Infrastructure
- **Description**: BACKLOG-025 and BACKLOG-030 were marked as DONE with validation evidence claiming fixes were verified, but the automated test shows the error still exists. This indicates a discrepancy between manual validation and automated test results.
- **Impact**: Wasted test execution time, incorrect backlog state, potential false sense of completion, repeated test runs without progress
- **Evidence**: BACKLOG-025 Status: DONE, BACKLOG-030 Status: DONE, but automated test shows same error across 7 test runs
- **Recommendation**: Reopen BACKLOG-025 and BACKLOG-030, investigate why manual validation passed but automated test fails, ensure proper fixes are applied and verified in both environments

### Tertiary Finding: BACKLOG-029 REOPENED
- **Severity**: HIGH
- **Scope**: Backlog management
- **Category**: Process
- **Description**: BACKLOG-029 was reopened with status OPEN and title "OPEN - Routing Bug (Weather Intent)". This is the correct action given that the weather routing issue persists despite BACKLOG-029 being marked as DONE.
- **Impact**: Correct backlog state for the weather routing issue
- **Recommendation**: After frontend fix is applied, re-execute routing audit to verify if Intent Engine correctly calls system.weather tool or uses LLM knowledge

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
- **Actual Usage**: Partial evidence from backend logs (TC-001: Input Tokens: 206, Output Tokens: 16, Cost: 0.00005514 €; Second request: Input Tokens: 4401, Output Tokens: 101, Cost: 0.00090671 €), but full usage not measurable due to frontend rendering failure

## PROVIDER AND MODEL MATRIX

- **GPT**: gpt-5.4-nano (smallest viable) - attempted but blocked by frontend error
- **Gemini**: gemini-3-flash-preview (smallest viable) - not reached due to test blockage
- **Escalation**: Not applicable (tests did not complete)

## RECOMMENDATION

### Immediate Action Required
BACKLOG-025 and BACKLOG-030 must be reopened and investigated. The claimed fixes for the "win is not defined" JavaScript error and the weather routing issue are not working in the automated test environment. One of the following must be done:
1. Verify if the fixes were actually applied to the codebase
2. If applied, verify why they're not working in the automated environment
3. If not applied, apply the actual fixes
4. Re-validate with both manual and automated tests before marking DONE again

### Recommended Next Step
Route to TEST SKILL 4 – FINDING TRIAGE AND ROUTING for:
1. **Finding Classification**: FRONTEND_RENDERING_FAILURE (CRITICAL severity, PERSISTENT, BACKLOG-025 FIX INEFFECTIVE)
2. **Finding Classification**: ROUTING_VERIFICATION_FAILURE (CRITICAL severity, PERSISTENT, BACKLOG-030 FIX INEFFECTIVE)
3. **Recommended Action**: Reopen BACKLOG-025 and BACKLOG-030, investigate and fix the "win is not defined" JavaScript error in the frontend stream-render pipeline and the weather routing issue
4. **Backlog Recommendation**: Ensure BACKLOG-025 and BACKLOG-030 validation evidence is accurate and reflects actual automated test results
5. **Retest Required**: YES - full routing audit test suite must be re-executed after fixes
6. **Fix Verification**: Verify that the fixes are actually applied and work in both manual and automated test environments
7. **BACKLOG-029**: After fixes are applied, re-execute routing audit to verify if Intent Engine correctly calls system.weather tool or uses LLM knowledge
8. **Process Improvement**: Implement automated validation checks before marking backlog items as DONE to prevent manual/automated test discrepancies

## CONFIDENCE SCORE

- **Test Execution Confidence**: 0% (blocked by frontend error)
- **Finding Confidence**: HIGH (clear diagnostic evidence, consistent across 7 test runs, BACKLOG validation discrepancy confirmed for 2 items, fix ineffectiveness confirmed)
- **Overall TestRun Confidence**: LOW (no functional tests completed, same error persists across 7 test runs, BACKLOG validation issue identified for 2 items, routing audit blocked, tool routing success rate 0%)

## TESTRESULT METADATA

- **Generated By**: TEST SKILL 3 – LIVE JANUS TEST EXECUTION
- **Execution Model**: SWE 1.6
- **Automation Compliance**: YES (generator-first, validator-passed)
- **Manual Intervention Required**: YES (test process killed due to stuck state)
- **Evidence Complete**: PARTIAL (Playwright artifacts, backend logs, diagnostics available but full execution blocked)
- **Retest Mode**: LIVE_RETEST
- **Routing Audit**: BLOCKED (no tool call verification possible due to frontend error)
- **Complete Tool Routing Documentation**: YES (13 test cases with Tool Expected, Tool Called, Result, Notes columns)
- **Tool Routing Success Rate**: 0% (0/13 tests verified)
