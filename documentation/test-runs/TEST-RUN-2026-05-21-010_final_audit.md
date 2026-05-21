# TEST-RUN-2026-05-21-010 Final Audit

## Decision

PASS. `TEST-RUN-2026-05-21-010` validates Janus Beta Abuse Limits and Cost Controls with `10/10` passing checks, `0` failed, `0` blocked and `0` manual gates.

## Implemented Controls

- Added beta abuse middleware for mutating `/api/*` requests with per-user/key and global sliding-window limits.
- Added safe 429 wording with `Retry-After` and no stack traces, raw prompts or raw secrets.
- Added image and PDF upload byte caps with safe 413 wording and allowlisted content types.
- Extended retry/cost abuse detection to cover maximum-cost, tool-flood and broad web/RSS/search crawl prompts.
- Removed raw prompt snippets from retry-storm abuse warning logs; abuse alerts record classification metadata only.
- Added `JANUS_DISABLE_SENTRY` for test/capped-provider runs so security tests do not emit Sentry telemetry.

## Evidence

- TestPlan: `documentation/test-runs/TEST-RUN-2026-05-21-010_plan.json`
- Limit policy map: `documentation/test-runs/TEST-RUN-2026-05-21-010_beta_abuse_limit_policy.md`
- Unit tests: `backend/tests/test_beta_abuse_limits.py`
- Runner: `tests/e2e/generated/TEST-RUN-2026-05-21-010.beta-abuse.spec.js`
- Playwright config: `tests/e2e/generated/TEST-RUN-2026-05-21-010.beta-abuse.playwright.config.js`
- Result JSON: `documentation/test-results/TEST-RUN-2026-05-21-010_results.json`
- Result Markdown: `documentation/test-results/TEST-RUN-2026-05-21-010_results.md`
- Evidence directory: `documentation/test-results/TEST-RUN-2026-05-21-010`

## Verification Commands

- `python -m py_compile backend/main.py backend/api/routers/images.py backend/api/routers/rag.py backend/services/chat_orchestrator.py backend/services/orchestrator/execution_dispatcher.py` -> PASS
- `python -m pytest backend/tests/test_beta_abuse_limits.py -q` -> PASS, `5 passed`
- `npx playwright test --config tests/e2e/generated/TEST-RUN-2026-05-21-010.beta-abuse.playwright.config.js --reporter=list` -> PASS, `10 passed`

## Watchpoints

- The packaged-local in-process limiter is appropriate for the current Electron beta shape. A future hosted multi-process beta must add durable centralized counters and provider-side hard spend caps.
- Startup still initializes existing logging subsystems; this run disables Sentry for capped tests but does not change the broader telemetry posture already covered by Security Spec 14.
