# TEST-RUN-2026-05-21-005 Packaged Local Beta Environment Map

## Verdict

PASS. Janus' beta deployment model is a packaged local Electron desktop app, not hosted SaaS staging. The corrected Spec 11 validates that model directly.

## Environment model

| Area | Evidence | Result |
|---|---|---|
| App shell | `package.json` declares Electron main and `de.pruvex.janus` app id | PASS |
| Packaged frontend | `frontend/dist` rebuilt and verified by `scripts/verify-frontend-dist.cjs` | PASS |
| Packaged backend | `dist/janus_backend.exe` exists and is referenced as Electron extra resource | PASS |
| Local health | `http://127.0.0.1:8001/api/health` returned success during Playwright run | PASS |
| Runtime state | Mutable config resolves to `%APPDATA%/Janus Projekt`; packaged resources resolve via `sys._MEIPASS` | PASS |
| Secret source | Keyring/AppData/runtime config used; PyInstaller no longer appends local `.env` | PASS |
| Dev surface | Packaged app loads `http://127.0.0.1:8001/`; Vite/devtools are development-gated | PASS |
| Update metadata | `release/latest.yml` and `release/janus-update-manifest.json` are internally consistent | PASS |
| Evidence hygiene | Generated evidence scan found no raw secret patterns | PASS |

## Remediation performed

- Removed PyInstaller `.env` bundling behavior from `janus_backend.spec`.
- Reframed Spec 11 from hosted staging to packaged local beta, matching Janus' actual Electron deployment model.
- Replaced the blocked hosted-staging runner with a packaged-local beta runner.

## Watchpoints

- `release/latest.yml` and `janus-update-manifest.json` are internally consistent for the last built installer, but the current source version should be rebuilt into a fresh installer before an actual beta shipment.
- Vite/Sentry source-map upload occurred during the production frontend build. This is acceptable as build evidence here, but source-map exposure policy remains a dedicated follow-up for Specs 14 and 15.
- Startup logs still show the known Supabase `exec_sql` schema-validation noise; it does not block Spec 11 but remains an operations watchpoint.
