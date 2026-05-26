# Janus Beta Privacy Notice

Version: `2026-05-21.1`

This notice applies to the Janus packaged-local Electron beta. Janus runs a local desktop app with a local backend on loopback (`127.0.0.1` / `localhost`). It is not a hosted multi-tenant SaaS service in the current beta scope.

## What Data Janus May Process

Janus may process these beta data categories:

- Chat prompts, assistant responses and conversation metadata.
- Local memory entries, context summaries and RAG/knowledge snippets.
- Uploaded files, indexed PDFs, generated documents, generated images and other artifacts you create.
- Local workspace paths and file-operation metadata when you grant file access.
- Calendar/task/project/contact data if you enable and use those features.
- Provider/model/tool metadata such as provider name, model id, skill/tool id, status, trace id, latency and cost metadata.
- Local diagnostic logs and optional beta feedback reports.
- Optional telemetry events after redaction, depending on `JANUS_TELEMETRY_MODE` and provider configuration.

## Where Data May Go

By default, Janus stores beta data locally under the Janus AppData/user folders and local project/workspace locations. Some features can send selected request content or metadata outside the device:

- LLM providers such as OpenAI, Gemini/Google or other configured providers receive prompts, context, file/image content or tool results needed for the selected model request.
- Local Ollama requests stay on the local machine unless your Ollama setup is configured otherwise.
- Web/current-data tools may contact search, RSS/news, Wikipedia/knowledge, weather, geo/distance/routing and price/current-data providers.
- Image, audio, calendar or other integration providers may receive the minimum content needed for the requested feature.
- Sentry, Supabase logging or a feedback webhook may receive redacted diagnostics only when configured and not disabled by telemetry mode.

Do not paste or upload secrets, passwords, API keys, private regulated data, production customer data, health/financial/legal records or third-party confidential data unless the Janus operator has explicitly approved that beta scenario in writing.

## Telemetry And Logs

Janus minimizes diagnostics for beta:

- Local logs are stored under the Janus AppData log directory and are controlled by the local tester.
- Redaction removes credential-shaped values, cookies, bearer tokens, provider headers, prompt/content/file payload keys and similar sensitive fields before remote diagnostic upload paths.
- `JANUS_TELEMETRY_MODE=off` drops Janus telemetry events and remote upload.
- `JANUS_TELEMETRY_MODE=minimal` permits only security/ops/abuse event ingest and disables remote telemetry upload.
- Sentry source maps, replay and provider-side retention must remain explicitly controlled for beta.

## Retention

Current packaged-local beta retention is mostly local:

- Chats, memory, RAG indexes, files, generated artifacts and local logs remain until the tester or operator deletes them.
- Remote provider retention is governed by the selected provider and account settings.
- Sentry/Supabase/feedback retention is governed by the operator-controlled destination and should be kept to the shortest practical beta window.
- Beta test evidence must not contain raw secrets, raw private prompts, file payloads, cookies, bearer tokens or provider headers.

## Tester Responsibilities

Beta testers must:

- Use synthetic or low-risk data unless explicitly told otherwise.
- Avoid secrets, regulated data and production customer data.
- Review provider/model/tool choices before sending sensitive context.
- Report privacy or security concerns immediately through the issue route below.
- Delete local beta data before sharing devices, logs or screenshots.

## Data Rights And Requests

For export/access, deletion or correction requests, contact `privacy-contact` and include:

- Your beta tester identifier or local profile label.
- Request type: access/export, deletion, correction or restriction.
- Scope: chats, memory, files/uploads, projects, calendar/tasks, generated artifacts, logs/telemetry or all beta data.
- Date range and any canary labels you used.

The operator will use the Beta Data Rights Process to identify local and remote data locations without recording raw secrets or private content in evidence.

## Incident Reporting

Report suspected privacy/security issues to `operator-on-call` and `privacy-contact`. Include what happened, approximate time, affected feature and whether any secrets/private data may have been involved. Do not include raw secrets in the report.

## Acknowledgement

Before beta use, testers must acknowledge this notice in the app or via the beta onboarding checklist. The app records local acknowledgement as `janus_beta_privacy_ack_v1` with notice version and timestamp in browser local storage.
