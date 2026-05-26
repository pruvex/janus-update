# TEST-RUN-2026-05-21-011 Ops Recovery Runbook

Spec: `documentation/TEST_SPEC/02_security_safety/17_ops_recovery_kill_switches.md`

## Scope

This runbook validates packaged-local Janus beta recovery controls through safe dry-runs. It covers provider access, external/current-data tools, write/destructive tools, local beta user lock, memory/RAG features, telemetry level, rollback/restore, beta export/delete dry-run and incident reporting.

## Kill Switches

| Control | Switch | Expected dry-run behavior | Restore |
|---|---|---|---|
| Cloud provider access | `JANUS_DISABLE_CLOUD_PROVIDERS=1` or `JANUS_DISABLE_PROVIDER_ACCESS=1` | OpenAI/Gemini/Google style providers return safe disabled responses before provider clients are used. Local Ollama remains recoverable. | Unset switch and restart backend. |
| External/current-data tools | `JANUS_DISABLE_EXTERNAL_TOOLS=1` or `JANUS_DISABLE_CURRENT_DATA_TOOLS=1` | Websearch, weather, RSS/news, Wikipedia, geo/routing and price/current-data tools return a safe disabled tool error. | Unset switch and restart backend. |
| Write/destructive tools | `JANUS_DISABLE_WRITE_TOOLS=1` or `JANUS_DISABLE_DESTRUCTIVE_TOOLS=1` | Filesystem writes, calendar mutations, memory writes and RAG upload/index routes are blocked with HTTP 423 or tool error. | Unset switch and restart backend. |
| Memory/RAG | `JANUS_DISABLE_MEMORY_RAG=1`, `JANUS_DISABLE_RAG=1` or `JANUS_DISABLE_MEMORY=1` | Memory and knowledge/RAG reads/writes are blocked. | Unset switch and restart backend. |
| Local beta user/account | `JANUS_LOCK_LOCAL_BETA_USER=1` or `JANUS_DISABLE_USER_ACCOUNTS=1` | Protected user routes are blocked while `/api/system/ops/kill-switches` stays available for recovery verification. | Unset switch and restart backend. |
| Telemetry level | `JANUS_TELEMETRY_MODE=off|minimal|normal|debug` | Effective mode is bounded to the allow-list. `off` drops telemetry events and remote upload. `minimal` allows only security/ops/abuse event ingest and disables remote telemetry upload. Startup also sets dependency telemetry opt-out flags for Chroma-style anonymous telemetry. | Set `JANUS_TELEMETRY_MODE=normal` and restart backend. |

## Rotation Dry-run

1. Identify beta-facing provider/API secrets by source system: local config, keyring, provider console, telemetry provider and any hosted integration.
2. Create replacement credential in the source system, but do not paste raw values into issues, logs or evidence.
3. Record only: source system, credential name/alias, rotation status, created-at/rotated-at timestamp and operator initials.
4. Validate Janus can start with replacement aliases.
5. Revoke old credential after smoke test.

Evidence rule: No raw secret values, bearer tokens, cookies, provider headers or API keys may be written to this repository.

## Rollback/Restore

1. Verify `/api/health`.
2. Call `/api/system/ops/kill-switches` with the internal API key and confirm active switches.
3. Unset the relevant environment variable(s).
4. Restart packaged-local backend.
5. Re-check `/api/health`.
6. Re-call `/api/system/ops/kill-switches` and confirm switch state is restored.
7. Run a minimal no-user-data smoke test for the affected feature.

## Beta Export/Delete Dry-run

Use canary-only staging/beta data. The dry-run is non-destructive:

1. Resolve beta account identifier from the operator console or local beta account registry.
2. Export metadata inventory only: counts, object ids, timestamps and canary labels.
3. Simulate delete plan by listing affected chats, memory rows, files/uploads, projects, calendar/tasks and generated artifacts.
4. Do not delete real data during this spec.
5. Confirm restore point/snapshot exists before any future destructive execution.

## Incident Reporting

Primary aliases:

| Role | Alias | Responsibility |
|---|---|---|
| Operator | `operator-on-call` | Activates kill switches, records timeline, validates restore. |
| Privacy | `privacy-contact` | Assesses personal-data exposure and user notification requirements. |
| Engineering | `janus-release-owner` | Owns fix, rollback, deployment and post-incident follow-up. |

Incident report must include the test run id, affected feature, active switches, time enabled, time restored, evidence links and a no-raw-secret confirmation.
