# Janus Beta Tester Privacy Onboarding

Version: `2026-05-21.1`

Before using the beta, each tester must confirm:

- I understand Janus is currently a packaged-local Electron beta, not a hosted SaaS tenant.
- I understand Janus may process chats, files/uploads, memory/RAG, projects, calendar/tasks, generated artifacts, logs, telemetry metadata and provider/tool metadata.
- I understand selected content may be sent to configured LLM, image/audio, search/current-data, RSS/news, Wikipedia/knowledge, weather, geo/distance/routing, price/current-data, calendar or telemetry providers when I use those features.
- I will not upload or paste secrets, API keys, passwords, production customer data, regulated health/financial/legal data or third-party confidential information unless explicitly approved.
- I understand local beta data can persist until I or the operator delete it.
- I know how to request access/export, deletion, correction or restriction through `privacy-contact`.
- I know how to report privacy/security concerns through `operator-on-call` and `privacy-contact`.

Acknowledgement can be recorded by:

- App-local acknowledgement: `janus_beta_privacy_ack_v1` in browser local storage, containing notice version, timestamp and accepted state.
- Operator-managed beta roster entry with tester id, notice version, timestamp and channel.

No raw private data or raw secrets should be included in the acknowledgement record.
