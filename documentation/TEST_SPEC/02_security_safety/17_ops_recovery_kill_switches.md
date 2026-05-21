# JANUS OPS RECOVERY KILL SWITCHES - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 82
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: OPS_RECOVERY_GATE
reason: Validate that operators can contain beta incidents quickly without code changes or unsafe manual database surgery.

## TEST IDENTITY

- TestSpec Name: 17 Ops Recovery Kill Switches
- Security Domain: Operations / Incident Response / Recovery
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Prove Janus has practical controls to disable risky paths, rotate credentials, lock users and recover from beta incidents.
- Launch Risk: A secure app can still be unsafe for beta if there is no fast containment path for provider burn, tool abuse, data leak reports or bad deployments.
- Required Precondition: Staging environment and operator access defined.

## TEST OBJECTIVE

Validate kill switches and recovery runbooks through safe dry-runs. Operators must be able to disable provider access, external tools, write/destructive tools, user accounts, memory/RAG features and telemetry levels, then restore normal operation.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| OPS-001 | Provider switch | Disable cloud provider access | Provider calls stop; user message safe | Config/action evidence |
| OPS-002 | Tool class switch | Disable external/current-data tools | Tools stop or return controlled unavailable state | Tool evidence |
| OPS-003 | Destructive/write switch | Disable file/memory/calendar write actions | Writes blocked while reads behave as configured | Tool evidence |
| OPS-004 | User lock | Suspend beta user | User loses access without affecting others | Auth evidence |
| OPS-005 | Key rotation | Dry-run API/JWT/provider key rotation | Rotation steps documented and retestable | Runbook evidence |
| OPS-006 | Telemetry mode | Increase/decrease log level safely | No PII introduced; mode change observable | Log evidence |
| OPS-007 | Rollback | Validate rollback target and process | Known previous build can be restored | Deploy evidence |
| OPS-008 | Data deletion | Dry-run beta user deletion/export request | Deletion/export path documented | Privacy ops evidence |
| OPS-009 | Incident contact | Verify reporting path | Security/privacy contact and triage owner exist | Process evidence |
| OPS-010 | Gate decision | Consolidate ops readiness | No open Critical/High ops blockers | Final audit |

## ACCEPTANCE CRITERIA

- Critical kill switches are documented, owned and dry-run.
- Operators can contain provider/tool/user incidents quickly.
- Rollback target and key rotation path are known.
- Incident reporting and beta privacy requests have owners.

## BLOCKING CONDITIONS

- No way to disable costly provider/tool paths quickly.
- No user suspension path.
- Unknown rollback path.
- No owner for beta security/privacy incidents.

## REQUIRED ARTIFACTS

- Kill-switch inventory.
- Dry-run logs or screenshots.
- Rotation and rollback runbooks.
- Incident contact and ownership record.
- Final ops readiness audit.
