# TEST-RUN-2026-05-21-008 Telemetry Sink Inventory

## Evidence Policy

Raw secrets, cookies, bearer tokens, private prompts, file payloads and provider headers are never written to this inventory or test evidence.

## Sinks

| Sink | Source | Owner | Default Privacy Posture | Retention |
|---|---|---|---|---|
| Local AppData backend log | `%APPDATA%/Janus Projekt/logs/janus_backend.log` | Janus maintainer / local beta user | Shared `SensitiveRedactionFilter` redacts secrets plus prompt/content/file payload keys | Local user controlled; deletion by removing local log directory |
| Backend Sentry | `backend/main.py` | Janus maintainer | `send_default_pii=False`; `before_send` applies shared redaction | Provider console setting; owner must keep beta retention minimal |
| Frontend Sentry | `frontend/js/app.js` | Janus maintainer | `sendDefaultPii=false`; request/user stripped; breadcrumbs scrubbed; replay disabled and masked | Provider console setting; owner must keep beta retention minimal |
| Supabase logging | `backend/services/logging/logger_core.py` | Janus maintainer | Payload is redacted before `logs_raw` upload | Provider console setting; delete beta rows by session/trace/date |
| Feedback webhook | `backend/services/telemetry_service.py` | Janus maintainer | No default webhook; feedback description/log snippet redacted before send | Destination owner controlled; disabled unless explicitly configured |
| Chroma/PostHog library telemetry | dependency runtime | Third-party dependency / Janus maintainer | No Janus prompt payload is intentionally sent; captured as dependency watchpoint | Dependency/provider controlled |

## Scope Decision

This gate certifies the packaged-local Electron beta observability model. Hosted SaaS tenant telemetry must be revalidated if Janus later adds centralized accounts.
