# TEST-RUN-2026-05-21-007 Emergency Rotation Dry Run

## Scope

This runbook covers beta-facing Janus secrets without requiring raw secret values in documentation or evidence.

## Dry-Run Steps

1. Identify impacted secret class by key name and source system only.
2. Revoke or rotate the provider-side credential in the provider console or OS keyring.
3. Update the local beta secret source: OS keyring, AppData config or ignored `.env` file.
4. Restart Janus backend/Electron session.
5. Run health and affected provider smoke checks.
6. Run `TEST-RUN-2026-05-21-007` again.
7. Confirm no raw secret appears in repo, bundle, logs, responses or test artifacts.

## Rules

- Do not paste raw secrets into Git, documentation, screenshots, logs, tickets or test evidence.
- Record only key name, source system, owner, rotation timestamp/status and redacted fingerprint.
- Treat source-map upload credentials as release-only and opt-in only.
- If a raw secret is found in any tracked/public artifact, revoke first, then clean history/artifact, then rerun the scan.

## Owner Actions Required Outside Repo

- Provider consoles: OpenAI, Google/Gemini/YouTube, Supabase, Sentry, GitHub release publishing.
- Cost caps/scopes: verify in the provider console before broad beta.
