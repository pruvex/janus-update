PRE-CHECK RESULT
PRE-CHECK PASSED

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-CHATGPT-CODEX.1
Target Subtask: N/A
Task: documentation/tasks/TASK-CHATGPT-CODEX.1_task_breakdown.md
Spec: documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A
Assigned Model: 5.6 Terra
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Exactly one high-risk slice is released: the Janus-owned lifecycle boundary around the official Codex App Server managed ChatGPT-account surface.
- Official App Server documentation confirms that managed `chatgpt` login owns the browser OAuth flow, credential persistence, automatic refresh, account read, login cancel, and logout; Janus must consume only this surface and never handle tokens directly.
- Official configuration documentation exposes `cli_auth_credentials_store = "keyring"`; unlike `auto`, the current official storage implementation fails when the OS keyring is unavailable and does not fall back to an auth file.
- The current official storage implementation derives the keyring account key from the canonical `CODEX_HOME`. A Janus-specific immutable home therefore creates a credential entry distinct from other Codex clients; Janus logout targets only its owned App Server process and that isolated home.
- `@openai/codex@0.144.4-win32-x64` is an official Apache-2.0 npm distribution whose dry-run manifest contains `vendor/x86_64-pc-windows-msvc/bin/codex.exe`. It may be pinned and copied as an Electron resource without using `PATH`.
- OpenRouter counter-review reported three missing-proof blockers. Codex resolved all three against current official documentation, official source, npm package metadata, and the inspected Janus lifecycle/packaging seams; delegated output remains review material only.
- No product test, live login, build, or code edit was performed during precheck.
Affected Files:
- backend/llm_providers/codex_app_server.py
- backend/main.py
- main.electron.cjs
- scripts/run-backend-dev.cjs
- package.json
- package-lock.json
- backend/utils/redaction.py
- licenses/openai-codex/LICENSE.txt
- backend/tests/test_codex_app_server.py
- tests/electron/codex-runtime-boundary.test.cjs
Evidence Focus:
- Official contracts: https://developers.openai.com/codex/app-server/ and https://developers.openai.com/codex/config-reference/
- Official source: https://github.com/openai/codex/blob/main/codex-rs/core/src/auth/storage.rs and https://github.com/openai/codex/blob/main/LICENSE
- Distribution proof: `npm view @openai/codex@0.144.4 bin optionalDependencies --json`; `npm view @openai/codex@0.144.4-win32-x64 version license dist.tarball --json`; `npm pack @openai/codex@0.144.4-win32-x64 --dry-run --json`
- `python -m pytest backend/tests/test_codex_app_server.py -q`
- `node --test tests/electron/codex-runtime-boundary.test.cjs`
- `python -m pytest backend/tests/test_runtime_llm.py -q`
- `npm run build`
- `npx electron-builder --dir --publish never`
- Verify the unpacked Electron resource contains the pinned `codex.exe` and Apache-2.0 license copy at the exact paths asserted by `tests/electron/codex-runtime-boundary.test.cjs`.
Scope-Regel:
- Implement only `TASK-CHATGPT-CODEX.1`. No direct OAuth, token parsing, token refresh, credential-file storage, shared `CODEX_HOME`, system/PATH runtime discovery, API-key fallback, provider/model fallback, UI, API router, model discovery, provider transport, chat behavior, or scope expansion.
- Pin the official runtime to exact version `0.144.4` and use only the Windows x64 package resource `vendor/x86_64-pc-windows-msvc/bin/codex.exe`; do not silently select another architecture or installation.
- Force `CODEX_HOME` to a deterministic Janus-only application-data directory and force `cli_auth_credentials_store = "keyring"`; unavailable protected storage is a fail-closed provider-unavailable state.
- Extend `backend/utils/redaction.py` only for credential-container keys and OAuth URL/query shapes such as authorization codes, state, and callback parameters that the current helper does not fully cover.
- Add only the official Apache-2.0 license text under `licenses/openai-codex/LICENSE.txt` and package it with the runtime. No broader licensing refactor is authorized.
- `janus_backend.spec`, `backend/llm_providers/runtime_llm.py`, all frontend files, all routers, and every existing API-key provider remain unchanged.
Automated Evidence Gate:
- `python -m pytest backend/tests/test_codex_app_server.py -q`
- `node --test tests/electron/codex-runtime-boundary.test.cjs`
- `python -m pytest backend/tests/test_runtime_llm.py -q`
- `npm run build`
- `npx electron-builder --dir --publish never`
- npx playwright test <runner> --headed --workers=1 --reporter=list
- `npx playwright test tests/e2e/capability-overview.spec.js --headed --workers=1 --reporter=list`
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, parent task, and task-breakdown handoff path verified. Historical `TASK-CHATGPT-OAUTH*` artifacts are stale and forbidden as execution inputs.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route later TestSpec, packaged live-login, provider/model, or UI evidence to janus-test-pipeline.
Keep Context:
- documentation/SPEC/CHATGPT_OAUTH_PROVIDER_FEATURE_SPEC.md
- documentation/tasks/TASK-CHATGPT-CODEX-PROVIDER.md
- documentation/tasks/TASK-CHATGPT-CODEX.1_task_breakdown.md
- documentation/tasks/TASK-CHATGPT-CODEX.1_precheck.md
- current official Codex App Server, configuration, storage-source, license, and pinned npm distribution evidence
Drop Context:
- all historical TASK-CHATGPT-OAUTH task/precheck artifacts
- unrelated provider, UI, model-catalog, chat, audit, release, and backlog history
Completion Rule:
- End with PASS, BLOCKED, or HANDOFF and concrete evidence paths. Stop immediately if keyring-only isolation, pinned-resource resolution, protocol compatibility, redaction, or license packaging cannot be proven without widening scope.
Expected Output:
- Implementation result, executed checks, affected files, residual risks, and the next-skill handoff.
legacy handoff end
```

NEXT STEP
Recommended Skill: janus-executioner
Recommended Model: 5.6 Terra
Recommended Intelligence: high
User Action: Approve implementation of exactly TASK-CHATGPT-CODEX.1 in this bounded context. If 5.6 Sol becomes executable for the current ChatGPT Codex account, it may be used; otherwise retain the documented `SOL_UNAVAILABLE_FOR_CHATGPT_CODEX_ACCOUNT` fallback to 5.6 Terra/high.
