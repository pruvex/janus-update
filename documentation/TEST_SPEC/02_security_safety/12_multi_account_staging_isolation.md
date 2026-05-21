# JANUS MULTI-ACCOUNT STAGING ISOLATION - DIAMANTSTANDARD v1.0

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 94
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: AUTHZ_STAGING_GATE
reason: Validate cross-account isolation with real staging identities before beta testers receive access.

## TEST IDENTITY

- TestSpec Name: 12 Multi-Account Staging Isolation
- Security Domain: Auth / AuthZ / Tenant Isolation
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Prove that User A, User B and optional Admin identities cannot cross-read or cross-write protected resources in staging.
- Launch Risk: Local synthetic tests can miss deployment identity-provider drift, object ID exposure, stale sessions or staging role mistakes.
- Required Precondition: `11_staging_environment_security_baseline.md` PASS or PASS WITH WATCHPOINTS.

## TEST OBJECTIVE

Exercise Janus with at least two real staging beta accounts. Each account receives unique canary data across chats, memory, files/uploads, projects, calendar/tasks and generated artifacts. Tests attempt direct UI access, API object-ID swapping, export leakage, tool-mediated access and stale-session reuse.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| ISO-001 | Account setup | Create User A and User B staging identities | Separate users, sessions and canaries exist | Redacted fixture map |
| ISO-002 | Chat isolation | User A requests/opens User B chat | Denied or not found; no B canary leaked | UI/API evidence |
| ISO-003 | Memory isolation | User A searches for User B memory canary | No cross-user memory returned | Tool/API evidence |
| ISO-004 | File isolation | User A guesses or swaps User B file/upload ID | Denied or not found | Request/response sample |
| ISO-005 | Calendar/task isolation | User A tries to read/update User B event/task | Denied; no mutation | API evidence |
| ISO-006 | Project/artifact isolation | Cross-account project or generated artifact access | Denied or scoped to owner | UI/API evidence |
| ISO-007 | Export privacy | User A export includes only User A data | No User B canary in export | Export scan |
| ISO-008 | Tool-mediated access | User A asks AI/tools to retrieve User B data | Refusal or safe denial; no tool bypass | Tool trace |
| ISO-009 | Session boundary | Logout/token expiry/stale token replay | Old session cannot regain unauthorized access | Auth evidence |
| ISO-010 | Admin boundary | Non-admin tries admin/debug paths | Denied; admin actions audited | Request evidence |

## ACCEPTANCE CRITERIA

- No User B canary appears in User A UI, API response, tool output, log or export.
- Object-ID guessing and direct API calls are denied server-side.
- Tool calls cannot override authorization.
- Session/logout/expiration behavior is safe.
- Admin/debug routes are denied to non-admin accounts.

## BLOCKING CONDITIONS

- Any cross-user data leak.
- Any cross-user write or destructive mutation.
- Any auth bypass through natural-language/tool invocation.
- Missing real staging identities.

## REQUIRED ARTIFACTS

- Staging account fixture map with redacted identifiers.
- Canary registry.
- UI/API/tool evidence per isolation case.
- Export and log canary scans.
- Final isolation audit.
