# JANUS STAGING ENVIRONMENT SECURITY BASELINE - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 88
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: STAGING_GATE
reason: Validate that the staging environment matches the intended beta-production security posture before external testers receive access.

## TEST IDENTITY

- TestSpec Name: 11 Staging Environment Security Baseline
- Security Domain: Staging / Beta Production Readiness
- Source Input: Category 2 follow-up after local Security ReviewSpec Suite
- Primary Test Goal: Prove that the target staging URL, backend, frontend, environment variables, secrets and deployment topology are real, isolated, reproducible and safe for beta validation.
- Launch Risk: Local security tests can pass while staging has wrong origins, debug flags, missing TLS, exposed sourcemaps, stale secrets, permissive telemetry or non-isolated data stores.
- Required Precondition: Security TestSpecs 01-10 PASS or PASS WITH WATCHPOINTS.
- Required Result Markdown: documentation/test-results/<test_run_id>_results.md
- Required Result JSON: documentation/test-results/<test_run_id>_results.json

## TEST OBJECTIVE

Validate that Janus has a dedicated staging environment that is not a developer laptop, not production, not using real user data, and not relying on hidden local state. The environment must expose a stable URL, health endpoint, configured secrets, isolated database/storage, expected provider mode and reproducible deployment metadata.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| STG-001 | Reachability | Open staging frontend and backend health URL | Both are reachable over HTTPS or a documented beta-approved transport | URL, status, response sample |
| STG-002 | Environment identity | Query/version-check staging metadata | Environment clearly identifies as staging/beta, not dev or production | Version/build metadata |
| STG-003 | Data isolation | Inspect DB/storage/project identifiers | Staging uses isolated DB/storage and no production data source | Redacted config evidence |
| STG-004 | Secret source | Inspect secret loading path | Secrets come from deployment secret store or documented staging config, not repo files | Redacted env map |
| STG-005 | Debug mode | Check debug flags, stack traces and dev endpoints | Debug output is disabled or admin-only | Request/response evidence |
| STG-006 | Build artifact | Inspect frontend build settings | No unapproved sourcemaps, local-only URLs or dev overlays exposed | Bundle/build evidence |
| STG-007 | Provider mode | Trigger safe provider smoke path | Provider keys are staging/beta scoped and cost-capped | Redacted provider evidence |
| STG-008 | Rollback metadata | Inspect deploy/version provenance | Current build has commit/version and rollback target documented | Deployment record |
| STG-009 | Result hygiene | Review test artifacts | Evidence contains no raw secrets, cookies or real user data | Privacy scan |
| STG-010 | Gate decision | Consolidate staging findings | PASS / PASS WITH WATCHPOINTS / FAIL with owner and rationale | Final audit |

## ACCEPTANCE CRITERIA

- Staging has a stable target URL and health endpoint.
- Staging data stores are isolated from production and real personal data.
- No raw secrets are stored in repo, frontend bundle, test evidence or public responses.
- Debug behavior is disabled or access-controlled.
- Deployment version and rollback path are documented.
- No open Critical or unaccepted High findings remain.

## BLOCKING CONDITIONS

- Staging is unreachable or only works through a developer-local process.
- Production database/storage/provider keys are used without explicit written approval.
- Debug stack traces, secrets or real user data are externally observable.
- Build provenance or rollback path is unknown.

## REQUIRED ARTIFACTS

- Staging environment map.
- Redacted env/secret-source evidence.
- Health/version response evidence.
- Build/deployment provenance.
- Privacy scan for generated evidence.
- Final staging gate audit.
