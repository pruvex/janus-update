# JANUS PACKAGED LOCAL BETA PROFILE ISOLATION - DIAMANTSTANDARD v1.1

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 94
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: AUTHZ_LOCAL_PROFILE_GATE
reason: Validate cross-profile beta isolation for Janus' real packaged Electron deployment model before beta testers receive access.

## TEST IDENTITY

- TestSpec Name: 12 Multi-Account Staging Isolation
- Local Deployment Interpretation: Packaged local Electron beta profile isolation.
- Security Domain: Auth / AuthZ / Profile Isolation / IDOR Resistance
- Source Input: Category 2 production-readiness extension
- Primary Test Goal: Prove that Beta Profile A and Beta Profile B do not cross-read or cross-write protected local resources.
- Launch Risk: A local desktop beta can accidentally share AppData, SQLite state, files, generated artifacts, JWT/session data or tool outputs across beta profiles if runtime roots or test fixtures are not isolated.
- Required Precondition: `11_staging_environment_security_baseline.md` PASS.

## DEPLOYMENT MODEL NOTE

Janus is a local Electron desktop app, not a hosted SaaS staging environment. Therefore this gate does not pretend that two cloud tenants exist inside one hosted backend. For beta-readiness, User A and User B are modeled as separate packaged-local beta profiles with separate AppData roots, SQLite databases, file/upload roots, generated artifact roots and local session state.

Any future hosted/staging deployment must rerun this spec with real staging identities and server-side tenant IDs before public launch.

## TEST OBJECTIVE

Exercise Janus with at least two beta-profile identities. Each profile receives unique canary data across chats, memory, files/uploads, projects, calendar/tasks and generated artifacts. Tests attempt direct object-ID swapping, export leakage, tool-mediated access and stale-session reuse within the packaged-local deployment model.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| ISO-001 | Profile setup | Create Beta Profile A and Beta Profile B fixture roots | Separate AppData, DB, file and artifact roots exist | Redacted fixture map |
| ISO-002 | Chat isolation | Profile A attempts to resolve Profile B chat/message IDs | Not found in Profile A DB; no B canary leaked | SQLite evidence |
| ISO-003 | Memory isolation | Profile A searches for Profile B memory canary | No cross-profile memory returned | SQLite evidence |
| ISO-004 | File/upload isolation | Profile A guesses or swaps Profile B upload path/ID | No B upload exists under A root | Filesystem evidence |
| ISO-005 | Calendar/task isolation | Profile A attempts to resolve Profile B task/event canary | Not found in Profile A DB; no mutation | SQLite evidence |
| ISO-006 | Project/artifact isolation | Cross-profile project and generated artifact access | A export/root contains only A data | DB/filesystem evidence |
| ISO-007 | Export privacy | Profile A export is scanned for Profile B canaries | No B canary in export | Export scan |
| ISO-008 | Tool-mediated access | User asks tools/AI to retrieve User B/Profile B data | Cross-user gate refuses before tools/LLM | Static and unit evidence |
| ISO-009 | Session boundary | Stale/foreign token or session data is reused | JWT expiration and profile-local session roots are enforced | Auth/static evidence |
| ISO-010 | Admin/debug boundary | Non-admin local beta profile tries admin/debug assumptions | No admin role model is exposed; debug surfaces remain local/dev-gated | Code/config evidence |

## ACCEPTANCE CRITERIA

- No Profile B canary appears in Profile A DB, filesystem root, generated artifact root, export, tool output or evidence.
- Object-ID guessing is harmless across profile roots because data stores are separate.
- Tool-mediated cross-user/profile requests are refused before LLM/tool execution.
- JWT/session implementation validates expiration and does not create a shared hosted-session claim.
- Admin/debug routes are not exposed as beta multi-account surfaces.

## BLOCKING CONDITIONS

- Any Profile B canary visible in Profile A evidence.
- Any cross-profile write or destructive mutation.
- Any auth/tool bypass for another user/profile.
- Any documentation or runner claiming SaaS-style multi-tenant staging PASS without real staging identities.

## REQUIRED ARTIFACTS

- Redacted beta profile fixture map.
- Canary registry.
- SQLite, filesystem, export and tool-gate evidence per isolation case.
- Final profile-isolation audit.
