# TEST RUN RESULT - TEST-RUN-2026-05-19-002

## Metadata

- **TestRun ID:** TEST-RUN-2026-05-19-002
- **Title:** Janus Planner Boundary Control
- **Status:** FAIL
- **Result JSON:** documentation/test-results/TEST-RUN-2026-05-19-002_results.json
- **Result Directory:** documentation/test-results/TEST-RUN-2026-05-19-002
- **Updated At:** 2026-05-19T12:49:42.952Z

## Summary

- **Total Tests:** 32
- **Passed:** 26
- **Failed:** 5
- **Blocked:** 1
- **Manual Gate Required:** 0
- **PassRatePct:** 81.25
- **FailRatePct:** 15.63
- **BlockedRatePct:** 3.13

## Failed Or Non-Pass Tests

| TestCase | Result | Classification | Evidence | Notes |
|---|---|---|---|---|
| INT-001-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/INT-001-GEMINI_evidence.json | Expectations not met |
| INT-001-GPT | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/INT-001-GPT_evidence.json | Expectations not met |
| SEC-003-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-003-GEMINI_evidence.json | Expectations not met |
| SEC-003-GPT | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-003-GPT_evidence.json | Expectations not met |
| TC-004-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/TC-004-GEMINI_evidence.json | Expectations not met |
| TC-007-GEMINI | BLOCKED | RUNNER_UNHANDLED_FAILURE | documentation/test-results/TEST-RUN-2026-05-19-002/TC-007-GEMINI_evidence.json | Error: RUNNER_STREAM_TIMEOUT: Assistant bubble appeared but is empty or only contains "..." with timestamp. SSE stream observed but no real content rendered.
Console [SSE]: [{"timestamp":"2026-05-19T12:40:44.411Z","type":"log","text":"[SSE-INIT] {windowId: A, chatMessagesChildren: 2, containerClass: message assistant, bubbleFound: true, bubbleInitialText: ...\n}"}]
DOM eval: {"found":true,"containerChildCount":2,"messageCount":2,"messages":[{"i":0,"className":"message user","bubbleHTMLLen":91,"bubbleTextLen":77,"bubbleTextSample":"Recherchiere aktuelle Modellpreise und erstelle eine kurze Vergleichstabelle\n","isConnected":true},{"i":1,"className":"message assistant","bubbleHTMLLen":18,"bubbleTextLen":4,"bubbleTextSample":"...\n","isConnected":true}],"containerHTMLLen":298,"containerHTMLSample":"<div class=\"message user\"><div class=\"bubble\"><p><p>Recherchiere aktuelle Modellpreise und erstelle eine kurze Vergleichstabelle</p>\n</p></div><div class=\"timestamp\">14:40</div></div><div class=\"message assistant\"><div class=\"bubble\"><p><p>...</p>\n</p></div><div class=\"timestamp\">14:40</div></div>"}
DOM message texts: ["Recherchiere aktuelle Modellpreise und erstelle eine kurze Vergleichstabelle\n14:40","...\n14:40"] |

## All Tests

| TestCase | Result | Classification | Evidence |
|---|---|---|---|
| INT-001-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/INT-001-GEMINI_evidence.json |
| INT-001-GPT | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/INT-001-GPT_evidence.json |
| INT-002-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-002-GEMINI_evidence.json |
| INT-002-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-002-GPT_evidence.json |
| INT-003-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-003-GEMINI_evidence.json |
| INT-003-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-003-GPT_evidence.json |
| INT-004-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-004-GEMINI_evidence.json |
| INT-004-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-004-GPT_evidence.json |
| INT-005-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-005-GEMINI_evidence.json |
| INT-005-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/INT-005-GPT_evidence.json |
| PINJ-001-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/PINJ-001-GEMINI_evidence.json |
| PINJ-001-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/PINJ-001-GPT_evidence.json |
| SEC-001-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-001-GEMINI_evidence.json |
| SEC-001-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-001-GPT_evidence.json |
| SEC-002-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-002-GEMINI_evidence.json |
| SEC-002-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-002-GPT_evidence.json |
| SEC-003-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-003-GEMINI_evidence.json |
| SEC-003-GPT | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/SEC-003-GPT_evidence.json |
| TC-001-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-001-GEMINI_evidence.json |
| TC-001-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-001-GPT_evidence.json |
| TC-002-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-002-GEMINI_evidence.json |
| TC-002-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-002-GPT_evidence.json |
| TC-003-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-003-GEMINI_evidence.json |
| TC-003-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-003-GPT_evidence.json |
| TC-004-GEMINI | FAIL | ASSERTION_MISMATCH | documentation/test-results/TEST-RUN-2026-05-19-002/TC-004-GEMINI_evidence.json |
| TC-004-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-004-GPT_evidence.json |
| TC-005-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-005-GEMINI_evidence.json |
| TC-005-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-005-GPT_evidence.json |
| TC-006-GEMINI | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-006-GEMINI_evidence.json |
| TC-006-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-006-GPT_evidence.json |
| TC-007-GEMINI | BLOCKED | RUNNER_UNHANDLED_FAILURE | documentation/test-results/TEST-RUN-2026-05-19-002/TC-007-GEMINI_evidence.json |
| TC-007-GPT | PASS | ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-19-002/TC-007-GPT_evidence.json |
