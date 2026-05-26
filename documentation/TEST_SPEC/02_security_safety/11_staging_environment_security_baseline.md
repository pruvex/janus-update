# JANUS PACKAGED LOCAL BETA ENVIRONMENT SECURITY BASELINE - DIAMANTSTANDARD v1.1

## TEST EXECUTION ROUTING

target_skill: TEST_SKILL_SECURITY
execution_mode: SWE_1_6
complexity_score: 88
confidence: HIGH
dashboard_hint: BETA_PRODUCTION_HARDENING
security_hint: PACKAGED_LOCAL_BETA_GATE
reason: Validate Janus' real beta deployment model: a packaged local Electron desktop app with local backend, local AppData state, protected secrets, reproducible build artifacts and rollback/update metadata.

## TEST IDENTITY

- TestSpec Name: 11 Packaged Local Beta Environment Security Baseline
- Security Domain: Packaged Local Desktop Beta Readiness
- Source Input: Category 2 follow-up after local Security ReviewSpec Suite
- Primary Test Goal: Prove that Janus can be shipped to beta testers as a packaged local Electron app without relying on dev-only Vite state, embedded `.env` secrets, hidden repo state, real user data, or missing update/rollback metadata.
- Launch Risk: A desktop beta can pass local source tests while the packaged app ships stale frontend assets, embeds local `.env`, lacks a backend health path, mixes repo state with AppData state, exposes dev tools, or has unverifiable installer/update artifacts.
- Required Precondition: Security TestSpecs 01-10 PASS or PASS WITH WATCHPOINTS.
- Required Result Markdown: documentation/test-results/<test_run_id>_results.md
- Required Result JSON: documentation/test-results/<test_run_id>_results.json

## TEST OBJECTIVE

Validate Janus as a packaged local beta, not as hosted SaaS staging. The target environment is the local Electron application bundle plus local backend health endpoint, AppData configuration, Keyring/AppData credential model, release/update artifacts, provider cost mode and reproducible build metadata.

## TEST MATRIX

| Test-ID | Category | Scenario | Expected Safe Behavior | Evidence |
|---|---|---|---|---|
| STG-001 | Packaging model | Inspect Electron/package config | App is packaged as local Electron desktop app with backend executable resource | package/build evidence |
| STG-002 | Frontend artifact | Build and verify frontend dist | `frontend/dist` exists and passes production bundle verification | build output |
| STG-003 | Backend artifact | Inspect PyInstaller spec and backend exe | Backend executable exists; package includes resources but never embeds `.env` | artifact/spec evidence |
| STG-004 | Local health | Start local backend health endpoint | `127.0.0.1:8001/api/health` responds from local backend path | health response |
| STG-005 | State isolation | Inspect AppData/resource separation | Runtime mutable config lives in AppData; packaged resources are read-only inputs | code references |
| STG-006 | Secret source | Inspect credential and config handling | Secrets are read from Keyring/AppData/env at runtime; no local `.env` bundled | code/spec evidence |
| STG-007 | Dev surface | Inspect packaged Electron behavior | Packaged app loads local backend origin and dev tools open only under `NODE_ENV=development` | code references |
| STG-008 | Update/rollback metadata | Verify release/update artifacts | Installer metadata, latest.yml and update manifest are internally consistent | verification output |
| STG-009 | Evidence hygiene | Scan generated evidence/build metadata | Evidence contains no raw secrets, cookies or provider keys | privacy scan |
| STG-010 | Gate decision | Consolidate packaged-local beta findings | PASS / PASS WITH WATCHPOINTS / FAIL with owner and rationale | final audit |

## ACCEPTANCE CRITERIA

- Janus beta target is explicitly a packaged local Electron app.
- Current frontend production bundle is built and verified.
- Backend packaging config includes required resources and excludes local `.env`.
- Local backend health endpoint is reachable during the test.
- AppData/resource boundary is documented and enforced by code paths.
- Keyring/AppData/runtime secret model is documented; no packaged raw secrets.
- DevTools/dev-only behavior is gated by `NODE_ENV=development`.
- Release/update metadata is verifiable or a current-build rollback note is documented.
- No open Critical or unaccepted High findings remain.

## BLOCKING CONDITIONS

- Packaged config can embed local `.env` secrets.
- Frontend production bundle is missing or stale.
- Local backend health endpoint cannot be started.
- Runtime config/secrets require repo-local hidden state.
- Packaged app exposes dev-only surfaces without a development guard.
- Release/update artifact integrity cannot be verified or explicitly documented.

## REQUIRED ARTIFACTS

- Packaged local beta environment map.
- Frontend build/verification evidence.
- Backend package/resource evidence.
- Local health response evidence.
- Secret-source and AppData isolation evidence.
- Update/rollback verification evidence.
- Final packaged-local beta gate audit.
