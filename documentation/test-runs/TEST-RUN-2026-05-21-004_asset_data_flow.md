# TEST-RUN-2026-05-21-004 Asset and Data Flow Review

## Protected assets

- User conversation content, chat metadata, model context, memory snippets and summaries.
- Contacts, tasks, calendar entries, projects, media uploads, generated images, RAG documents and file-derived context.
- Provider credentials, internal API key, JWT signing secret, local config, keyring-backed OpenAI/Gemini keys.
- Tool results, source attributions, RSS/web/wiki/weather/geo/price evidence, audit records and test-result artifacts.
- Backend logs under `%APPDATA%/Janus Projekt/logs` and generated frontend build artifacts.

## Trust boundaries

| Boundary | Trusted side | Untrusted side | Controls reviewed |
|---|---|---|---|
| Browser to backend API | FastAPI routes and server-side dependencies | Browser UI, user input, local renderer state | `X-Janus-Internal-Key`, JWT scope checks, CORS/header baseline, API privacy tests |
| Backend to model provider | Orchestrator policy, tool dispatcher, prompt registry | Model output and tool-call suggestions | Tool allowlists, injection detector, destructive/path gates, evidence-honesty tests |
| Backend to local tools/files | Tool executor and configured app paths | Natural-language requests and retrieved content | Argument validation, source labels, path/out-of-sandbox controls, tool truth tests |
| Backend to external data | Weather, websearch, RSS, wiki, geo, price wrappers | External source text, missing/partial evidence | Fallback honesty, source attribution, no fabrication on unavailable sources |
| Logs/telemetry/result artifacts | Redaction filters and result schema | Secrets, cookies, provider headers, private prompt text | Redaction helpers, observability privacy tests, Sentry PII disabled |

## Data flow

1. User input enters the browser and is sent to backend API routes.
2. Protected routes require `api_key_auth`; settings mutations also require JWT scope checks where applicable.
3. The orchestrator builds model context from user input, selected memory/RAG context, system prompts and allowed tool metadata.
4. Model responses may request tools; the tool executor resolves canonical tools, validates arguments and returns structured tool results.
5. External-current-data tools must either return sourced evidence or an explicit unavailable/no-source result.
6. Final responses append source/tool attribution where relevant and must not claim hidden evidence.
7. Logs and result artifacts pass through redaction routines before they become review evidence.

## Persistence and retention assumptions

Local review scope covers persisted local app config, SQLite/Supabase-backed app data where configured, frontend build output, test-result JSON/Markdown and backend logs. Production retention, backup and incident-response windows remain deployment-specific watchpoints and are tracked in the risk register.
