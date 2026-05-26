# TEST RUN RESULT - TEST-RUN-2026-05-20-019

## Metadata

- **TestRun ID:** TEST-RUN-2026-05-20-019
- **Title:** Janus Skill Registry Integrity
- **Status:** PASS
- **Result JSON:** documentation/test-results/TEST-RUN-2026-05-20-019_results.json
- **Result Directory:** documentation/test-results/TEST-RUN-2026-05-20-019
- **Updated At:** 2026-05-20T21:50:30.000Z

## Summary

- **Total Tests:** 6
- **Passed:** 6
- **Failed:** 0
- **Blocked:** 0
- **Manual Gate Required:** 0
- **PassRatePct:** 100.00

## Evidence

| TestCase | Result | Classification | Evidence |
|---|---|---|---|
| TC-001 | PASS | STATIC_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/TC-001_evidence.json |
| TC-002 | PASS | STATIC_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/TC-002_evidence.json |
| TC-003/SEC-001 | PASS | STATIC_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/TC-003_SEC-001_evidence.json |
| TC-004 | PASS | ROUTING_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/TC-004_evidence.json |
| TC-005 | PASS | ROUTING_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/TC-005_evidence.json |
| PINJ-001 | PASS | STATIC_ASSERTION_PASS | documentation/test-results/TEST-RUN-2026-05-20-019/PINJ-001_evidence.json |

## Notes

- Static registry integrity is now enforced by `backend/tests/test_skill_selector_capability_registry_integrity.py`.
- Live LLM/provider execution was not required for these deterministic regression checks.
