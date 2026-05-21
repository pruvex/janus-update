# TEST RUN RESULT - TEST-RUN-2026-05-21-005

## Metadata

- **TestRun ID:** TEST-RUN-2026-05-21-005
- **Title:** Janus Staging Environment Security Baseline
- **Status:** BLOCKED
- **Result JSON:** documentation/test-results/TEST-RUN-2026-05-21-005_results.json
- **Result Directory:** documentation/test-results/TEST-RUN-2026-05-21-005
- **Updated At:** 2026-05-21T00:36:05.806Z

## Summary

- **Total Tests:** 10
- **Passed:** 1
- **Failed:** 0
- **Blocked:** 9
- **Manual Gate Required:** 1
- **PassRatePct:** 10.00
- **FailRatePct:** 0.00
- **BlockedRatePct:** 90.00

## Failed Or Non-Pass Tests

| TestCase | Result | Classification | Evidence | Notes |
|---|---|---|---|---|
| STG-001 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-001_evidence.json | Explicit non-local JANUS_STAGING_FRONTEND_URL and JANUS_STAGING_HEALTH_URL are required. |
| STG-002 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-002_evidence.json | Staging metadata URL and explicit environment name are required. |
| STG-003 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-003_evidence.json | Redacted staging and production datastore identifiers are required to prove isolation. |
| STG-004 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-004_evidence.json | Approved staging secret source is required. |
| STG-005 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-005_evidence.json | JANUS_STAGING_BACKEND_URL is required for debug-route probing. |
| STG-006 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-006_evidence.json | Build version and sourcemap policy are required. |
| STG-007 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-007_evidence.json | Provider mode and cost cap are required. |
| STG-008 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-008_evidence.json | Deployment commit and rollback target are required. |
| STG-010 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-010_evidence.json | Staging gate is BLOCKED until explicit non-local staging configuration is provided. |

## All Tests

| TestCase | Result | Classification | Evidence |
|---|---|---|---|
| STG-001 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-001_evidence.json |
| STG-002 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-002_evidence.json |
| STG-003 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-003_evidence.json |
| STG-004 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-004_evidence.json |
| STG-005 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-005_evidence.json |
| STG-006 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-006_evidence.json |
| STG-007 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-007_evidence.json |
| STG-008 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-008_evidence.json |
| STG-009 | PASS | STAGING_EVIDENCE_HYGIENE_PASS | documentation/test-results/TEST-RUN-2026-05-21-005/STG-009_evidence.json |
| STG-010 | BLOCKED | STAGING_ENVIRONMENT_NOT_CONFIGURED | documentation/test-results/TEST-RUN-2026-05-21-005/STG-010_evidence.json |
