# OpenRouter Task .6 Retest Preflight — TEST-RUN-2026-07-17-007

Canonical State: `PASS`

Mode: `LIVE_PREFLIGHT_ONLY`

## Bound Retest Artifacts

- Plan: `documentation/test-runs/TEST-RUN-2026-07-17-007_plan.json`
- Generated runner: `documentation/test-runs/TEST-RUN-2026-07-17-007_generated.py`
- Plan SHA256: `2E5B18BA328CF9F6E77C276438B14A3D4D944610DBCCBAFDC7362FFA8F8CC42E`
- Fresh preflight result: `documentation/test-results/TEST-RUN-2026-07-17-007_live_preflight.json`

## Checks

- Public OpenRouter metadata: PASS for the same four approved candidates and required tool parameters.
- Public Janus credential state: PASS, `present=true`, masked, `VALID`; no credential value was read or retained.
- Bounded-cost gate: PASS, maximum `USD 0.45473792 <= USD 0.50`.
- Certification-key attestation: PASS; conservative remaining-credit floor `USD 0.544942592` is above the bounded maximum.
- New retest result paths: PASS; the historical `TEST-RUN-2026-07-17-006` result and registry-candidate evidence cannot be overwritten by this run.
- Focused dedicated conformance suite: PASS, `79 passed`.
- Model transmissions: `0`.
- Runtime registry: unchanged empty state, SHA256 `7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F`.

## Live Gate

The exact fresh literal `OK START LIVE TEST` is required before the generated runner can access the Janus-secure runtime credential authority or transmit to a model. The prior authorization applied only to historical `TEST-RUN-2026-07-17-006` and is not reused.

Next Skill: `janus-test-pipeline / LIVE_TEST_EXECUTION`
