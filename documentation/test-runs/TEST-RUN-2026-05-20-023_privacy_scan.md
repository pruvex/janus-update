# TEST-RUN-2026-05-20-023 Privacy Scan

## Scope

- Final result artifacts: `documentation/test-results/TEST-RUN-2026-05-20-023_results.json`, `documentation/test-results/TEST-RUN-2026-05-20-023_results.md`, and `documentation/test-results/TEST-RUN-2026-05-20-023/*.json`
- Final generated run artifacts: `documentation/test-runs/TEST-RUN-2026-05-20-023_plan.json`, `documentation/test-runs/TEST-RUN-2026-05-20-023_generated.spec.js`, and `tests/e2e/generated/TEST-RUN-2026-05-20-023.live.spec.js`
- Runtime backend log: `%APPDATA%\Janus Projekt\logs\janus_backend.log`

## Strict Leak Patterns

The scan checked for raw secret canaries, provider keys, bearer/header leaks, provider debug payload markers, hidden prompt markers, Discord webhook URLs, OpenAI/Gemini/Supabase key shapes, cookie headers, and known historical raw tool-output indicators.

## Results

- Final result artifacts: PASS. Strict scan returned no matches.
- Runtime backend log: PASS after remediation. Strict scan returned no matches after sanitizing historical unsafe lines.
- Generated TestPlan/runner artifacts: PASS with expected canary-oracle content. The remaining `SECRET-*`, `sk-`, `AIza`, webhook, cookie/header strings are stored as `mustNotContain` assertions in the generated tests, not as runtime evidence or model output.

## Remediation Performed During Audit

- Removed a hardcoded default Discord webhook from telemetry configuration.
- Added global logging redaction for message text, structured arguments, binary header tuples, and recursive mappings.
- Redacted telemetry log attachments and Discord embed descriptions.
- Redacted invalid logging payload warnings and dead-letter queue writes.
- Redacted debug-log fetcher output for Supabase rows and local fallback logs.
- Suppressed noisy third-party debug loggers that exposed HTTP/provider payloads or headers.
- Sanitized the local AppData backend log after historical findings:
  - First pass replaced `12855` lines containing provider keys, provider request/debug payloads, headers, webhook URLs, raw tool output, or local sensitive file path references.
  - Second pass replaced `503` older canary/secret-file prompt lines.

## Residual Risk

External rotated logs, external SIEM/export stores, and production telemetry destinations were not available in this local test environment. This run validates the local Janus runtime, generated test artifacts, AppData backend log, and in-repo telemetry/logging code paths covered by the test harness.
