# JANUS BETA PRIVACY NOTICE AND DATA RIGHTS - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 78
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: PRIVACY_READINESS_GATE
reason: Validate that beta testers receive clear privacy information, data-use boundaries and data-rights handling before access.

## TEST IDENTITY

- TestSpec Name: 18 Beta Privacy Notice and Data Rights
- Security Domain: Privacy / User Trust / Beta Operations
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Ensure beta testers understand what data Janus processes, where it may go, what not to upload, and how to request deletion/export or report issues.
- Launch Risk: Technical security can be strong while beta privacy expectations are unclear or legally/operationally fragile.
- Required Precondition: Staging data flows and telemetry sinks documented.

## TEST OBJECTIVE

Review beta-facing privacy notice, onboarding copy and data-rights process. Validate that the notice matches actual data flows, provider use, telemetry behavior, retention assumptions and tester responsibilities.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| PRIV-001 | Data categories | Review notice for data types | Chats, files, memory, logs, providers and telemetry are covered | Notice excerpt |
| PRIV-002 | Provider sharing | Review external provider disclosure | Model/search/RSS/wiki/geo/price provider sharing is clear | Notice excerpt |
| PRIV-003 | Sensitive uploads | Review beta warning | Users are told not to upload secrets or regulated data unless approved | Onboarding evidence |
| PRIV-004 | Retention | Review retention language | Retention/minimization assumptions are stated | Notice excerpt |
| PRIV-005 | Deletion | Request deletion dry-run | Deletion request path and owner exist | Process evidence |
| PRIV-006 | Export/access | Request data access/export dry-run | Export/access path and owner exist | Process evidence |
| PRIV-007 | Incident reporting | Report security/privacy issue | Contact route exists and is monitored | Process evidence |
| PRIV-008 | Consent/ack | Verify tester acknowledgement | Beta tester acceptance is recorded where required | UI/process evidence |
| PRIV-009 | Evidence privacy | Scan notice/test artifacts | No raw private data or secrets in privacy artifacts | Scan result |
| PRIV-010 | Gate decision | Consolidate privacy readiness | No open Critical/High privacy readiness blockers | Final audit |

## ACCEPTANCE CRITERIA

- Beta notice matches actual Janus data flows and provider behavior.
- Testers receive clear “do not upload secrets/private regulated data” guidance.
- Deletion, export/access and incident reporting paths have owners.
- Consent/acknowledgement is recorded where the beta process requires it.

## BLOCKING CONDITIONS

- No beta privacy notice.
- Notice contradicts actual telemetry/provider/data-flow behavior.
- No deletion/export or incident reporting owner.
- Beta requires real personal data with no explicit handling plan.

## REQUIRED ARTIFACTS

- Beta privacy notice or draft.
- Onboarding/acknowledgement evidence.
- Data-rights dry-run notes.
- Incident reporting evidence.
- Final privacy readiness audit.
