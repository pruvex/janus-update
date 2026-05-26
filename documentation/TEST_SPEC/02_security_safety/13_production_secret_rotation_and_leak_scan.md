# JANUS PRODUCTION SECRET ROTATION AND LEAK SCAN - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 90
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: SECRET_ROTATION_GATE
reason: Validate that beta-facing credentials are rotated, scoped, stored safely and absent from artifacts before tester access.

## TEST IDENTITY

- TestSpec Name: 13 Production Secret Rotation and Leak Scan
- Security Domain: Secret Management
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Ensure no development/test credential survives into beta production and no secret is leaked through repo, bundle, logs, telemetry or evidence.
- Launch Risk: A previously safe local app can become unsafe if old keys, `.env` values, webhook URLs, provider tokens or session secrets remain valid.
- Required Precondition: Security 01 and 08 PASS; staging environment identified.

## TEST OBJECTIVE

Rotate or explicitly certify all beta-facing secrets, then scan all relevant surfaces for raw credential values and credential-shaped patterns. Evidence must record presence/absence, source system and rotation status without writing raw secrets.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| SECROT-001 | Inventory | Build secret inventory | All secret classes listed with owner and storage source | Redacted inventory |
| SECROT-002 | Rotation | Rotate provider/API/session/webhook secrets | Old known dev/test secrets invalid; new secrets scoped | Rotation record |
| SECROT-003 | Repo scan | Scan tracked/untracked repo files | No raw secret values or live key shapes | Scan report |
| SECROT-004 | Bundle scan | Scan frontend build and sourcemaps | No server secrets or raw env values | Bundle scan |
| SECROT-005 | Log scan | Scan local/staging logs and telemetry exports | No raw secrets, cookies or bearer tokens | Log scan |
| SECROT-006 | Result scan | Scan test artifacts and evidence | No raw secrets in JSON/Markdown/evidence | Artifact scan |
| SECROT-007 | Runtime response scan | Trigger errors and public endpoints | No secret/debug leakage in responses | Response samples |
| SECROT-008 | Key scope | Verify provider keys are least-privilege/cost-capped where possible | Scopes/limits documented | Provider settings evidence |
| SECROT-009 | Emergency rotation | Dry-run rotation runbook | Owner can rotate and invalidate quickly | Runbook evidence |
| SECROT-010 | Gate decision | Consolidate secret findings | No open Critical/High secret findings | Final audit |

## ACCEPTANCE CRITERIA

- Every beta-facing secret has owner, storage location, rotation status and scope.
- Known dev/test secrets are invalid or explicitly not used in beta.
- Repo, bundle, logs, telemetry, responses and artifacts scan clean.
- Emergency rotation path is documented and tested by dry run.

## BLOCKING CONDITIONS

- Any live raw secret in public bundle, repo, response, logs or evidence.
- Unknown secret owner or unknown secret storage.
- Reuse of development secrets for beta without explicit accepted risk.

## REQUIRED ARTIFACTS

- Redacted secret inventory.
- Rotation checklist.
- Scan outputs for repo, bundle, logs, responses and artifacts.
- Emergency rotation runbook.
- Final secret gate audit.
