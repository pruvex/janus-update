# TESTSPEC CREDENTIAL PROTOCOL REVIEW - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6

## Bound Artifact

- TestSpec: `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`
- Mode: `TESTSPEC_REVIEW`
- Review Delta: `DEDICATED_CERTIFICATION_CREDENTIAL_PROTOCOL`
- Review Date: `2026-07-17`

## Decision

TESTSPEC DELTA PASS

The credential protocol is bounded, fail-closed, and suitable for the next
single-task preimplementation check. This decision does not authorize key
installation, keyring access, model calls, live execution, registry population,
release, or production activation.

## Approved Credential Boundary

- Profile: `OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0`
- Label: `janus-task6-cert-2026-07`
- Type: normal OpenRouter inference key
- Storage: real Janus Settings path `Janus-Projekt/openrouter`
- Credit limit: exactly `USD 1.00`
- Limit reset: none
- Expiry: no later than `2026-07-31T23:59:59Z`
- Installation timing: only after `KEY_INSTALLATION_GATE: READY`
- Revocation: immediately after live evidence capture and deletion through
  Janus Settings before closeout

Dev, Codex/OpenRouter delegation, environment, `.env`, CLI, fixture-secret,
management-key, and caller-supplied credential sources are forbidden. There is
no fallback.

## Approved Cost And Transmission Boundary

- Maximum external transmissions: 10 per candidate, 40 overall
- Maximum per transmission: 8192 input tokens and 1024 completion tokens
- Public-price snapshot worst case: `USD 0.455696384`
- Preflight price-drift ceiling: `USD 0.50`
- Automatic key-limit increase: forbidden
- Retry, duplicate transmission, model switch, and provider fallback: forbidden

The public-price snapshot used no credential and invoked no model. The no-call
preflight must recompute prices and block on missing/ambiguous pricing, a total
above `USD 0.50`, unenforceable token ceilings, or insufficient remaining key
credit.

## Evidence

- Dedicated profile, exact label, real Janus Settings path, no-fallback sources,
  installation gate, and revocation rule are explicit.
- Numeric credit, expiry, token, transmission, and price-drift limits are
  explicit.
- Key Installation Status remains `NOT REQUESTED`.
- Live Execution Status remains `NOT AUTHORIZED`.
- Production Activation Status remains `FORBIDDEN`.
- Runtime registry remains empty and unchanged.
- Known generic compiler blocker `GENERATOR_PLAN_INVALID` remains isolated; no
  misleading GPT/Gemini plan was generated for this review.

## Next Gate

Route exactly Task `.6` to `janus-preimplementation-check`. The precheck must
bind this review, the approved TestSpec, the revised task breakdown, and the
existing compiler debug result. The operator must not open Janus for key
installation until later execution evidence emits:

`KEY_INSTALLATION_GATE: READY`
