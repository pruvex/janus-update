# TEST-RUN-2026-05-21-013 Final Risk Register

## Gate Summary

Decision: PASS WITH WATCHPOINTS.

No open Critical findings remain for the reviewed packaged-local beta scope.
No open High findings remain for the reviewed packaged-local beta scope.

This register consolidates the launch-relevant security risks after Security 01-18. It does not certify a hosted SaaS, multi-tenant web deployment, or public/commercial production release.

## Closed Critical/High Findings

| ID | Severity | Status | Source | Resolution | Retest Evidence |
|---|---|---|---|---|---|
| RSV-008-FIX-001 | High | Fixed | Security 10 telemetry review | Sentry defaults were hardened: PII disabled, DSN env-configurable, production traces capped, profiles disabled by default. | `documentation/test-results/TEST-RUN-2026-05-21-004_results.json`, `backend/main.py` compile/review evidence |

## Open Watchpoints

| ID | Severity | Status | Owner | Watchpoint | Required Follow-up |
|---|---|---|---|---|---|
| BLG-W-001 | Medium | Accepted/Tracked | janus-release-owner | Current launch gate is for packaged-local Electron beta, not hosted SaaS or multi-tenant browser beta. | Before hosted beta, rerun Security 11, 12, 15 and 19 against the real hosted URL, identity provider, database/storage isolation and deployment metadata. |
| BLG-W-002 | Medium | Accepted/Tracked | privacy-contact | Beta privacy documents are product-accurate for current data flows but are not a substitute for formal legal review. | Complete formal legal/privacy review before public/commercial release or materially broader beta distribution. |
| BLG-W-003 | Medium | Accepted/Tracked | operator-on-call | Provider-side retention, spend caps and account console settings are operated outside this repo. Evidence records source systems without raw secrets. | Verify provider consoles immediately before distributing each external beta build. |
| BLG-W-004 | Low | Accepted/Tracked | janus-release-owner | Future hosted or multi-process beta should move env-driven kill switches and counters into durable operator-controlled configuration. | Design durable ops configuration before hosted/multi-instance deployment. |
| BLG-W-005 | Low | Accepted/Tracked | janus-release-owner | Desktop beta build distribution still requires a fresh installer artifact built from the signed launch commit. | Build, smoke-test and archive installer hash before sending to testers. |
| BLG-W-006 | Low | Accepted/Tracked | janus-release-owner | CSP still permits legacy inline compatibility in the local Electron/browser surface. | Remove inline compatibility before public web deployment, then rerun Security 15. |

## Launch Blocking Policy

- Any new Critical finding blocks beta until fixed and retested.
- Any new High finding blocks beta unless fixed or explicitly accepted by the release owner and security reviewer with a documented expiry.
- Medium and Low watchpoints may remain only when accepted, owned and scoped to follow-up milestones.
- Raw secrets, provider tokens, cookies, tester content and file payloads must not be copied into evidence.

Final state: 0 open Critical, 0 open High, 6 accepted/tracked Medium/Low watchpoints.
