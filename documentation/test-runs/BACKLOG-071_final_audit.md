# BACKLOG-071 Final Audit - MCP Isolated Browser Auth Preflight

Date: 2026-05-21
Status: PASS

## Scope

Implement a safe local MCP/Playwright debug auth preflight for isolated browser contexts. The fix must avoid real browser profiles, avoid exporting Janus internal API secrets and stay limited to local development/debug mode.

## Changes

- Added `POST /api/debug/mcp/auth-preflight` in `backend/main.py`.
- Added short-lived MCP debug-session token helpers and local-origin checks in `backend/dependencies.py`.
- Allowed `X-Janus-MCP-Debug-Session` in backend CORS.
- Extended the frontend global fetch wrapper in `frontend/js/app.js` to use `janus_mcp_debug_session` only when no Electron internal-key bridge is available.
- Added `tools/mcp-debug-auth-preflight.mjs` as an automated local helper.
- Added backend and Playwright coverage for the preflight flow.

## Security Decision

PASS. The implementation does not expose the internal Janus API key. The debug session is JWT-signed, short-lived, local-origin guarded and only active when debug endpoints are enabled. External origins are rejected, and packaged/beta mode keeps the endpoint disabled unless an explicit debug flag is present.

## Evidence

- `python -m pytest backend\tests\test_mcp_debug_auth_preflight.py -q` -> PASS, 3 passed.
- `python -m py_compile backend\dependencies.py backend\main.py backend\tests\test_mcp_debug_auth_preflight.py` -> PASS.
- `node --check frontend\js\app.js` -> PASS.
- `node --check tools\mcp-debug-auth-preflight.mjs` -> PASS.
- `node --check tests\e2e\mcp-debug-auth-preflight.spec.js` -> PASS.
- `npx playwright test tests/e2e/mcp-debug-auth-preflight.spec.js --workers=1 --reporter=list` -> PASS, 1 passed. Evidence shows `/api/personalities` and `/api/personalities/active` return 200 after preflight.
- `PYTHONIOENCODING=UTF-8 npm run build` -> PASS, including `verify-frontend-dist`.

## Verdict

PASS. BACKLOG-071 is complete and ready to mark DONE. Remaining initial 401s before preflight are expected because the isolated browser starts without an Electron bridge; after the explicit preflight, protected personality calls succeed without exporting real internal secrets.
