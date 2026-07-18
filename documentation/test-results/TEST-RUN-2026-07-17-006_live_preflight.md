# TEST-RUN-2026-07-17-006 - OpenRouter Live Preflight

Mode: `LIVE_PREFLIGHT_ONLY`

Decision: `PASS`

Preflight Status: `READY`

## Bound Artifacts

- TestSpec: `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- Candidate Manifest: `backend/services/conformance/fixtures/openrouter/candidates_v1.json`
- Public Metadata Snapshot: `documentation/test-runs/TEST-RUN-2026-07-17-006_public_metadata.json`
- Masked Credential State: `documentation/test-runs/TEST-RUN-2026-07-17-006_credential_public_state.json`
- Operator Attestation: `documentation/test-runs/TEST-RUN-2026-07-17-006_operator_attestation.json`
- Result JSON: `documentation/test-results/TEST-RUN-2026-07-17-006_live_preflight.json`

## Evidence

- The public endpoint `https://openrouter.ai/api/v1/models` returned all four exact approved model IDs and canonical version slugs.
- Every candidate has no expiration marker and still supports `tools` plus `tool_choice`.
- Current public-price bounded maximum: `USD 0.455057408`.
- Price-drift limit: `USD 0.50`.
- Dedicated key credit limit: `USD 1.00`.
- Janus public key state: `present=true`, `masked=********`, `state=VALID`.
- Maximum input tokens per transmission: `8192`.
- Maximum completion tokens per transmission: `1024`.
- Maximum total transmissions: `40`.
- Credential reads: `0`.
- Model transmissions: `0`.
- Runtime registry SHA256 remains `7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F`.

## Authority Boundary

- This result authorizes no model transmission.
- No live TestPlan or generated live runner was executed.
- The exact approval literal `OK START LIVE TEST` was not supplied.
- Runtime registry population, final certification, release, and production activation remain forbidden.

## Next Step

- Next skill: `janus-test-pipeline`
- Next mode: `TEST_RUN_PRECHECK`
- Required before any live call: one runner-generated and validated dedicated TestPlan, one bound generated runner, this `TEST_RUN_ID`, explicit evidence paths, and then the separate exact user approval `OK START LIVE TEST`.
- Recommended model: `5.6 Sol`
- Recommended intelligence: high
- Keep context: Task `.6` TestSpec, dedicated conformance runner/manifests, this preflight bundle, empty runtime registry.
- Drop context: Task `.5`, earlier headed-runner debug traces, unrelated backlog/release history, all development/delegation credential paths.
