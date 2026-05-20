# Skill 7 Documentation Update - TEST-RUN-2026-05-20-023

## Capability

Janus Observability Privacy Boundary

## Documentation Delta

- Redaction is now a shared backend utility rather than isolated string handling.
- Logging privacy is enforced at the global logging handler layer, at telemetry export boundaries, and at logging persistence/debug-read boundaries.
- Spec 08 is serial-only in generated live runs because log and telemetry evidence share mutable runtime state.
- Generated result artifacts may contain canary terms only as planned `mustNotContain` assertions; runtime evidence and logs must not contain those terms raw.

## Operator Notes

- Configure feedback delivery with `FEEDBACK_WEBHOOK_URL`; Janus no longer ships with an embedded fallback webhook.
- Keep `openai`, `openai._base_client`, `hpack`, `h2`, `httpx`, and `httpcore` out of DEBUG in normal operation.
- After adding new logging or telemetry sinks, run the observability redaction regression tests and a strict artifact/log scan.
- Add every newly discovered secret shape to `backend/utils/redaction.py` and `backend/tests/test_observability_redaction.py`.

## Audit Artifacts

- Final audit: `documentation/test-runs/TEST-RUN-2026-05-20-023_final_audit.md`
- Privacy scan: `documentation/test-runs/TEST-RUN-2026-05-20-023_privacy_scan.md`
- Result JSON: `documentation/test-results/TEST-RUN-2026-05-20-023_results.json`
