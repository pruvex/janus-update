# TEST-RUN-2026-05-21-005 Staging Environment Map

## Verdict

BLOCKED. No explicit non-local Janus staging environment is configured in this workspace or process environment.

The runner intentionally rejected implicit local development targets. A local Electron/dev server, `localhost`, `127.0.0.1`, `file://` or `janus://` does not satisfy Security TestSpec 11 because it cannot prove beta-production isolation, deployment provenance, real staging secret source or target-environment browser/API behavior.

## Required staging inputs

| Variable | Purpose | Status |
|---|---|---|
| `JANUS_STAGING_FRONTEND_URL` | Stable beta/staging frontend URL | Missing |
| `JANUS_STAGING_HEALTH_URL` | Stable backend health endpoint | Missing |
| `JANUS_STAGING_METADATA_URL` | Version/environment metadata endpoint | Missing |
| `JANUS_STAGING_ENVIRONMENT_NAME` | Must identify staging/beta/preprod | Missing |
| `JANUS_STAGING_DATASTORE_ID` | Redacted staging DB/storage identifier | Missing |
| `JANUS_PRODUCTION_DATASTORE_ID` | Redacted production DB/storage identifier for inequality check | Missing |
| `JANUS_STAGING_SECRET_SOURCE` | Approved secret source, not repo/local `.env`/AppData | Missing |
| `JANUS_STAGING_BACKEND_URL` | Backend base URL for debug-surface probing | Missing |
| `JANUS_STAGING_BUILD_VERSION` | Build/version deployed to staging | Missing |
| `JANUS_STAGING_SOURCEMAP_POLICY` | `disabled`, `private`, or `authenticated` | Missing |
| `JANUS_STAGING_PROVIDER_MODE` | `staging`, `beta`, `capped`, `sandbox`, or `local-only` | Missing |
| `JANUS_STAGING_PROVIDER_COST_CAP` | Explicit provider cost cap | Missing |
| `JANUS_STAGING_DEPLOY_COMMIT` | Commit/build provenance | Missing |
| `JANUS_STAGING_ROLLBACK_TARGET` | Rollback target | Missing |

## Evidence gathered

- Repository search found no committed staging URL or `JANUS_STAGING_*` configuration.
- Current process environment exposed no `JANUS_STAGING_*` variables.
- Generic TestSpec compiler could not derive an executable plan from the staging checklist, so a dedicated runner was added.
- Custom runner produced `TEST-RUN-2026-05-21-005_results.json` with `BLOCKED`, `1/10` pass, `9/10` blocked, `0` failed.

## Next action required

Create or declare a real staging environment, then rerun TestSpec 11 with the required variables above. The next run must not use developer-local URLs unless the TestSpec is explicitly rewritten for a packaged local beta, because the current Spec requires a dedicated staging environment.
