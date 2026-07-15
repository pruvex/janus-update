PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-DEVICE-CODE-PROVIDER.1
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
Task Breakdown: documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md
Spec: documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Sol
Assigned Intelligence: high
Fallback: 5.6 Terra / high only with SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT recorded
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- The actually bundled `@openai/codex` runtime is pinned to `0.144.4`; its generated App Server schema exposes `chatgptDeviceCode`, `userCode`, and `verificationUrl`.
- Official pinned source `rust-v0.144.4` routes `account/login/start` with `chatgptDeviceCode` through `request_device_code` and `complete_device_code_login`; completion persists through the configured Codex auth storage. Janus must use only this App Server contract and must not own OAuth tokens or call private auth endpoints.
- The same pinned source derives both direct-keyring and Windows encrypted-secrets keyring identities from the canonical `CODEX_HOME`. On Windows, the keyring backend defaults to `Secrets`, which stores the auth payload in a local encrypted secrets file and stores its key under an OS-keyring account derived from the canonical home. The Janus-only absolute `JANUS_CODEX_HOME` therefore supplies a separately named persistent credential boundary without importing another Codex client's credential slot.
- This source-level feasibility proof does not override the prior failed browser-flow evidence. Task `.1` must retain default-deny after implementation and must not set `PRODUCTION_ISOLATION_EVIDENCE_REVISION` or any equivalent production activation marker.
- No live account action is authorized by this precheck. After all automated gates are green, janus-executioner must stop and request separate explicit user authority before device-code login, restart, refresh, logout, revocation, or two-account evidence actions.
- The existing isolated Janus Account-B credential and its cleanup are outside this task and must not be inspected, imported, copied, mutated, or removed.
Affected Files:
- backend/llm_providers/codex_app_server.py
- backend/tests/test_codex_app_server.py
- tests/electron/codex-runtime-boundary.test.cjs
- documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md (create only from an actually authorized and executed controlled evidence run)
Evidence Focus:
- Replace the managed browser login request type with official `chatgptDeviceCode`; expose only the non-sensitive lifecycle data required by later Settings work.
- Preserve the absolute Janus-only `CODEX_HOME`, forced `cli_auth_credentials_store="keyring"`, stripped API-key environment, strict configuration, and redacted public state.
- Prove with fakes that secure-store unavailability blocks login, credential-bearing account reads, and refresh before process or network effects; no plaintext, `auto`, file, ephemeral, API-key, shared-session, or credential-import fallback is allowed.
- Prove that cancel, restart persistence, refresh, and logout address only the Janus-owned App Server lifecycle and never read or mutate Codex Desktop, Codex CLI, IDE, browser-cookie, or API-key-provider credentials.
- Device codes, verification values, tokens, credentials, auth URLs containing secrets, private account identifiers, and keyring contents must not appear in logs, generic errors, snapshots, or evidence artifacts.
Scope-Regel:
- Implement only the bound target task. No Settings UX, provider/model dropdown, model discovery, chat transport, privacy acknowledgement, atomic UI account switch, API-key-provider change, production activation, release, or multi-account support.
- Do not add private OAuth clients, direct token exchange, undocumented auth/backend endpoints, Hermes credential logic, existing-Codex credential import, or a second product module to work around the bound lifecycle.
- If the official App Server contract cannot satisfy the task inside the listed product/test boundary, stop with BLOCKED and return to janus-task-breakdown instead of widening scope.
Automated Evidence Gate:
- python -m pytest backend/tests/test_codex_app_server.py -q
- node --test tests/electron/codex-runtime-boundary.test.cjs
- python -m py_compile backend/llm_providers/codex_app_server.py
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/codex-connection-settings.spec.js --headed --workers=1 --reporter=list
- git diff --check -- backend/llm_providers/codex_app_server.py backend/tests/test_codex_app_server.py tests/electron/codex-runtime-boundary.test.cjs documentation/test-results/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_isolation_evidence.md
Artifact Identity Check:
- PASS: Spec, compiled task, Task `.1` breakdown, target identifier, file boundary, evidence path, and parked Tasks `.2` through `.5` match.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan or TestResult artifacts. The named isolation evidence file may be created only from the actually executed controlled evidence required by the approved Spec; route any TestSpec/TestPlan change through janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OFFICIAL_DEVICE_CODE_PROVIDER_REDESIGN_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-DEVICE-CODE-PROVIDER.1_task_breakdown.md
- pinned Codex `rust-v0.144.4` App Server device-code and auth-storage source
- affected file cluster and automated evidence commands
Drop Context:
- prior browser-callback implementation assumptions
- Hermes direct OAuth details
- unrelated provider, Settings, model, chat, release, backlog, and historical debug context
Completion Rule:
- End Task `.1` implementation with PASS, BLOCKED, NEEDS_INFO, or HANDOFF plus concrete evidence paths. Production activation remains disabled. Live account actions require a new explicit user gate after green automated validation.
Expected Output:
- Bounded implementation result, executed automated checks, changed files, redaction confirmation, and either the separate controlled-evidence authorization gate or a concrete blocker.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Sol
Recommended Intelligence: high
User Action: Approve implementation of Task `.1` only. Do not log in, log out, retry, switch accounts, refresh, revoke, inspect, or clean up credentials until Codex reaches the separately announced controlled-evidence gate.
