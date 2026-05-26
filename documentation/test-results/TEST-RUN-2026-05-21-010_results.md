# TEST RUN RESULT - TEST-RUN-2026-05-21-010

- **Spec:** Beta Abuse Limits and Cost Controls
- **Status:** PASS
- **Result JSON:** documentation/test-results/TEST-RUN-2026-05-21-010_results.json
- **Result Directory:** documentation/test-results/TEST-RUN-2026-05-21-010
- **Summary:** 10 passed, 0 failed, 0 blocked, 0 manual gates.

## Matrix

| Test-ID | Result | Classification | Evidence |
|---|---:|---|---|
| ABUSE-001 | PASS | PER_USER_BURST_LIMIT_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-001_evidence.json |
| ABUSE-002 | PASS | GLOBAL_BURST_LIMIT_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-002_evidence.json |
| ABUSE-003 | PASS | PROVIDER_SPEND_GATE_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-003_evidence.json |
| ABUSE-004 | PASS | RETRY_STORM_GATE_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-004_evidence.json |
| ABUSE-005 | PASS | TOOL_CALL_FLOOD_GATE_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-005_evidence.json |
| ABUSE-006 | PASS | EXTERNAL_CRAWL_GATE_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-006_evidence.json |
| ABUSE-007 | PASS | UPLOAD_SIZE_LIMIT_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-007_evidence.json |
| ABUSE-008 | PASS | SAFE_LIMIT_WORDING_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-008_evidence.json |
| ABUSE-009 | PASS | ABUSE_ALERT_PRIVACY_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-009_evidence.json |
| ABUSE-010 | PASS | BETA_ABUSE_GATE_DECISION_PASS | documentation/test-results/TEST-RUN-2026-05-21-010/ABUSE-010_evidence.json |

## Verification

- `python -m py_compile backend/main.py backend/api/routers/images.py backend/api/routers/rag.py backend/services/chat_orchestrator.py backend/services/orchestrator/execution_dispatcher.py` -> PASS
- `python -m pytest backend/tests/test_beta_abuse_limits.py -q` -> PASS, `5 passed`
- `npx playwright test --config tests/e2e/generated/TEST-RUN-2026-05-21-010.beta-abuse.playwright.config.js --reporter=list` -> PASS, `10 passed`
