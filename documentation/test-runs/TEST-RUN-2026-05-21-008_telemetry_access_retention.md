# TEST-RUN-2026-05-21-008 Telemetry Access and Retention Notes

## Access Control

- Local logs are stored under the current OS user profile and are not bundled into the application package.
- Provider telemetry access is limited to Janus maintainers with owner-approved Sentry/Supabase/webhook access.
- Feedback webhook telemetry is disabled by default because no webhook URL is embedded in code.
- Debug endpoints remain disabled unless `JANUS_ENABLE_DEBUG_ENDPOINTS=1` is explicitly set in a development-safe environment.

## Retention and Deletion

- Local beta tester logs can be deleted by removing `%APPDATA%/Janus Projekt/logs`.
- Supabase beta telemetry can be deleted by `session_id`, `trace_id` or date range without requiring raw prompt content.
- Sentry beta events should use the shortest practical provider-side retention window and should not enable session replay for beta.
- Feedback webhook destinations must be cleared by the destination owner if beta feedback is enabled.

## Incident Audit Shape

Security-relevant telemetry should keep event type, status, provider/model, skill, trace ID, latency and sanitized summaries. It must not keep raw prompt text, file payloads, cookies, bearer tokens, provider headers or raw tool payloads.
