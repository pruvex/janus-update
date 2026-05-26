# Janus Beta Data Rights Process

Version: `2026-05-21.1`

## Owners

| Area | Owner alias | Responsibility |
|---|---|---|
| Data rights intake | `privacy-contact` | Owns access/export/deletion/correction request tracking and response. |
| Technical execution | `operator-on-call` | Runs local/remote dry-runs, validates deletion/export scope and records evidence safely. |
| Release follow-up | `janus-release-owner` | Ensures product/docs changes after privacy findings. |

## Request Types

- Access/export: provide a copy or inventory of beta data in scope.
- Deletion: remove beta data in scope where technically possible.
- Correction: update inaccurate local beta profile/memory data.
- Restriction: disable specific processing routes, e.g. provider access, telemetry or memory/RAG.

## Scope Inventory

The operator must check these locations without writing raw private content into evidence:

- Local AppData Janus database and config.
- Chat history, memory rows and context summaries.
- RAG indexes, uploaded PDFs and document metadata.
- Generated files, images, audio and exports.
- Projects, tasks, calendar/contact data where enabled.
- Local logs and diagnostic files.
- Optional remote sinks: Sentry, Supabase logging, feedback webhook and configured external providers.

## Access/Export Dry-run

1. Confirm requester identity/profile label.
2. Record request id, date, scope and owner aliases.
3. Produce an inventory with counts, object ids, timestamps, feature names and canary labels.
4. Redact secrets, cookies, bearer tokens, provider headers, prompt content and file payloads.
5. For remote sinks, record provider/system name, query handle and deletion/export status only.
6. Return the export through an operator-approved private channel.

## Deletion Dry-run

1. Confirm exact deletion scope and restore/snapshot posture.
2. Build a non-destructive deletion plan first.
3. Include local database rows, file paths, indexes, logs and remote telemetry/provider destinations.
4. Execute deletion only after owner approval.
5. Verify absence by identifier/canary, not by reproducing raw content in evidence.
6. Record completed, partially completed or not-applicable status per data location.

## Incident Reporting

Privacy incidents go to `operator-on-call` and `privacy-contact`. The report must include:

- Incident timestamp and affected feature.
- Active kill switches, if any.
- Whether provider, telemetry or file upload paths were involved.
- Containment and restoration steps.
- Evidence links with no raw secrets or private payloads.

## Retention Assumptions

- Packaged-local beta data remains local until the tester/operator deletes it.
- Remote diagnostics are disabled or minimized by beta telemetry mode unless explicitly configured.
- Remote provider retention depends on the provider/account settings and must be reviewed before broad beta.
