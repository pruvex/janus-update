# TEST-RUN-2026-05-21-004 Code and Config Review

## Scope

Reviewed critical security boundaries requested by the ReviewSpec: API route protection, auth/session handling, secret management, logging/telemetry, AI/tool dispatcher controls, external-source honesty, OWASP/browser headers, rate/cost controls and deployment assumptions.

## Findings and evidence

| Area | References | Review result |
|---|---|---|
| API privacy boundary | `backend/main.py`, `backend/dependencies.py`, Security 02/03/08 results | Core chat, contacts, context, memory, media, RAG, projects, images, users, tasks, calendar and backlog routers are mounted with `Depends(api_key_auth)`. JWT scope protection exists for settings mutation. Public routes are known local/system endpoints and remain watchpoints for deployment exposure. |
| Auth/AuthZ | `backend/dependencies.py`, Security 03 | Internal API key comparison uses `secrets.compare_digest`; JWT token validation checks subject, expiration and required scopes. Synthetic User A/B evidence is covered by prior auth tests and Mini-Prep fixtures. |
| Secret handling | `backend/utils/redaction.py`, `backend/logger_config.py`, Security 01/08 | Redaction covers authorization, cookies, API keys, tokens, secrets, passwords, provider keys and common provider token shapes. Logging handlers attach `SensitiveRedactionFilter`. |
| Telemetry privacy | `backend/main.py` | Fixed during this review: Sentry now uses `send_default_pii=False`; production traces default to `0.1`, profiling defaults to `0.0`, and values are environment-configurable. |
| AI/tool safety | `backend/services/security/injection_detector.py`, `backend/services/orchestrator/execution_dispatcher.py`, `backend/services/tool_executor.py`, Security 05/06/07, Tool Truth, External Fallback Honesty | Prompt-injection and tool-abuse behavior is covered by live tests. Tool execution has canonical resolution and validation; current-data tools must disclose unavailable/no-source states instead of fabricating. |
| OWASP/browser surface | `backend/main.py`, Security 04/05 | CSP, `X-Frame-Options`, `X-Content-Type-Options`, referrer policy and permissions policy are present. CORS is broad for local/electron development and must be revalidated for target deployment origins. |
| Deployment and operations | `package.json`, `playwright.config.js`, Mini-Prep | Local lifecycle is reproducible through Playwright webServer, backend health and Vite startup. Production/staging HTTPS, HSTS, domain CORS, cookie attributes, external monitoring and real account fixtures remain environment-specific watchpoints. |

## Watchpoints

- Production/staging domain and CORS origin list must be revalidated in the target environment.
- HTTPS/HSTS only applies when the app is actually served over HTTPS; deployment must confirm TLS termination.
- Local Mini-Prep validates disposable fixture identities; true staging multi-account identities need environment owner sign-off.
- Log retention and rotation policy should be operationalized outside this local review.

## Retest notes

The telemetry privacy fix in `backend/main.py` is covered by `RSV-008` in the custom ReviewSpec runner and by `python -m py_compile backend/main.py`.
