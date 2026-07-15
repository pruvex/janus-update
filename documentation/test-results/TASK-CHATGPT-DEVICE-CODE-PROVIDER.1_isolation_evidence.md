# TASK-CHATGPT-DEVICE-CODE-PROVIDER.1 - Controlled Isolation Evidence

## Evidence Boundary

- Runtime: bundled official Codex `0.144.4`
- Auth transport: Codex App Server only
- Login mode under test: `chatgptDeviceCode`
- Credential policy: `keyring` with the Janus-only `CODEX_HOME`
- Production activation revision: unset
- Account labels: `Account A` is the parallel Codex desktop account; `Account B` is reserved for the fresh Janus device-code login
- Redaction rule: no names, email addresses, account/workspace identifiers, tokens, cookies, device codes, verification values, auth URLs, keyring contents, or credential values

## Controlled Sequence

| Time | Step | Result | Account-A observation | Notes |
| --- | --- | --- | --- | --- |
| 2026-07-15 00:07 +02:00 | Explicit authority received | PASS | Baseline reported healthy before sequence | User authorized the official device-code two-account test. |
| 2026-07-15 00:07 +02:00 | Janus baseline read with refresh disabled | PASS | Pending | Janus-only store reported connected ChatGPT auth and no pending login; only non-sensitive booleans/state were emitted. |
| 2026-07-15 00:10 +02:00 | Operator observation after baseline read | PASS | Account A unchanged | Same account, quota, settings, and connected state reported visible. |
| 2026-07-15 00:17 +02:00 | Janus-only logout of the pre-existing session | PASS | Pending | Janus returned disconnected, no auth mode, and no pending login. A redacted diagnostic reported that the old Janus token was already invalidated; no credential value was emitted. |
| 2026-07-15 00:20 +02:00 | Operator observation after Janus-only logout | PASS | Account A unchanged | Same account, quota, settings, and connected state reported visible. |
| 2026-07-15 00:28 +02:00 | Fresh official device-code login started | PASS | Observation required after completion | The pinned App Server returned only the approved official verification destination and a transient code. The code was passed in memory to the browser controller, never emitted to chat/log/evidence. The official page requires the operator to sign into Account B before code submission. |
| 2026-07-15 00:34 +02:00 | Official Account-B device authorization gate | NEEDS_INFO | Account A not changed by this step | The official page reported that Codex device-code authorization is disabled for Account B. The attempt was terminated, no matching Janus App Server process remained, and the transient code was removed without emission. |
| 2026-07-15 00:45 +02:00 | Operator enabled Account-B device authorization | PASS | No Account-A action requested | Operator confirmed the provider-owned Codex device-code authorization setting was enabled in the browser for Account B. |
| 2026-07-15 00:48 +02:00 | Fresh official retry started | PASS | Observation required after completion | A new pinned App Server attempt returned the allowlisted official verification destination and a fresh transient code held only in memory. The official page opened and redirected to OpenAI sign-in; Janus remains connecting with login pending and no retry reason. |
| 2026-07-15 01:03 +02:00 | Browser-session mismatch and timeout cleanup | NEEDS_INFO | No Account-A action occurred | The operator was signed into Account B in a normal browser, while the separate Codex in-app OpenAI tab still required sign-in. The pending device attempt expired before that sign-in; Codex removed the transient code, stopped the worker, and reopened the generic official OpenAI login page for Account-B authentication before the next fresh attempt. |
| 2026-07-15 01:11 +02:00 | In-app browser handoff correction | PASS | No Account-A action occurred | Root cause of the invisible tab was local orchestration: `tabs.finalize` had been called with a tab object instead of the required `{ keep: [{ tab, status }] }` options shape, so the tab was omitted and closed. Codex reopened the generic official page, enabled browser visibility, and finalized it with explicit handoff retention. No device-code attempt is active. |
| 2026-07-15 01:15 +02:00 | Fresh official code submitted and login completed | PASS | Observation required now | The operator authenticated Account B in the retained official tab. Codex started a new pinned App Server attempt, validated only the code shape, distributed the memory-only code across the unique official one-time-code fields, and submitted it. The official success page appeared; redacted Janus state became connected with auth mode `chatgpt`, no pending login, and no retry reason. The transient code was cleared and not emitted. |
| 2026-07-15 01:17 +02:00 | Operator observation after fresh Account-B login | PASS | Account A unchanged | Same Account-A identity, quota, settings, and connected state reported visible. |
| 2026-07-15 01:23 +02:00 | Janus lifecycle restart persistence read without refresh | PASS | Observation required now | The original lifecycle exited completely. A new lifecycle against the same isolated Janus home used `account/read` with refresh disabled and returned connected ChatGPT auth, no pending login, and no retry reason. A shutdown-time SQLite panic was reproduced by an import-only Janus backend probe with no App Server or account action, proving it is a pre-existing Vector/Skill-index import side effect rather than an auth/persistence failure. Zero matching Janus App Server processes remained. |
| 2026-07-15 01:24 +02:00 | Operator observation after Janus restart/read | PASS | Account A unchanged | The operator reported Account A unchanged in response to the current post-restart gate. |
| 2026-07-15 01:25 +02:00 | Janus-owned Account-B token refresh | PASS | Observation required now | A new isolated lifecycle executed exactly one `account/read` with refresh enabled. Redacted state remained connected with auth mode `chatgpt`, no pending login, and no retry reason. The previously isolated backend-import panic recurred only at Python process shutdown; zero matching Janus App Server processes remained. |
| 2026-07-15 01:27 +02:00 | Operator observation after Janus-owned refresh | PASS | Account A unchanged | Operator confirmed Account A in Codex remained fully healthy after the Account-B refresh. |
| 2026-07-15 01:30 +02:00 | Final Janus-only Account-B logout | PASS | Final observation required now | Exactly one isolated `account/logout` returned disconnected state with no auth mode, pending login, or retry reason. The known backend-import panic recurred only at Python shutdown; zero matching Janus App Server processes remained. |
| 2026-07-15 01:35 +02:00 | Final operator observation after Janus-only logout | PASS | Account A unchanged | Operator confirmed Account A in Codex remained fully healthy after the final Janus-only Account-B logout. |

## Current Gate

- Live evidence gate: PASS.
- Fresh Account-B login, restart persistence without refresh, owned refresh, Janus-only logout, and every independent Account-A non-interference observation passed.
- Next required action: build the compact audit package and route Task `.1` to independent final audit while production remains default-deny.
- No credential inspection, revocation experiment, Account-A mutation, commit, push, or sync occurred.
- The pre-existing Vector/Skill-index backend-import side effect remains outside this auth task; production stays disabled pending later Task `.5`.
