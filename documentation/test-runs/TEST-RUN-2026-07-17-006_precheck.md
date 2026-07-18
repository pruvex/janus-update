# TEST_RUN_PRECHECK — TEST-RUN-2026-07-17-006

Canonical state: **PASS**

Mode: `janus-test-pipeline / TEST_RUN_PRECHECK`

No live provider call was made. Live execution is authorized only after the operator supplies the separate exact literal `OK START LIVE TEST`.

## TEST_SCOPE

- TEST_RUN_ID: `TEST-RUN-2026-07-17-006`
- TestSpec: `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- Plan: `documentation/test-runs/TEST-RUN-2026-07-17-006_plan.json`
- Runner: `documentation/test-runs/TEST-RUN-2026-07-17-006_generated.py`
- Preflight: `documentation/test-results/TEST-RUN-2026-07-17-006_live_preflight.json`
- Result JSON: `documentation/test-results/TEST-RUN-2026-07-17-006_results.json`
- Result Markdown: `documentation/test-results/TEST-RUN-2026-07-17-006_results.md`
- Per-case evidence: `documentation/test-results/TEST-RUN-2026-07-17-006/`

## Evidence

- Dedicated plan schema and immutable TestSpec bindings: PASS
- Canonical plan SHA256: `7C5AD398D15E7FC21A8AE70597881DC85F39764966C06DF6B753C51C544DC34F`
- Provider binding: PASS, exactly `openrouter`
- Candidate binding: PASS, exactly four approved model/version pairs
- Battery binding: PASS, 30 cases and 8 live scenarios
- Dedicated generated runner identity: PASS
- Generated runner SHA256: `4E4C106801050A34B580D2A6CABB890CF986137E3F0342E94AAD61A6E7DCA071`
- Runner plan-hash and manual-patch tripwire: PASS
- Exact live-approval short circuit: PASS; wrong literal returns `LIVE_APPROVAL_MISSING` before runtime access
- Dedicated conformance suite: PASS, `78 passed`
- Python compilation: PASS
- Zero-call live preflight: `READY`
- Current worst-case estimate: PASS, `USD 0.455057408 <= USD 0.50`
- Public credential state: PASS, masked and `VALID`
- Runtime registry: PASS, empty; SHA256 `7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F`
- Generic GPT/Gemini compiler/schema/runner: unchanged and not used
- Model transmissions during generation/precheck: `0`
- Credential-value reads during generation/precheck: `0`

## Prerequisites

- Dedicated Janus OpenRouter certification key public state: `VALID`
- Key source: existing Janus secure credential authority only at live runtime
- Environment, CLI, development, and delegation key fallback: forbidden
- App/Playwright startup: not required; the dedicated Python runner uses the existing Janus OpenRouter gateway directly
- Candidate execution: serial
- Completion-token ceiling: `1024` per transmission
- Conservative input ceiling: `8192` UTF-8 bytes per transmission, bounded within the approved `8192` token maximum
- Transmission ceiling: `10` per candidate and `40` total
- Retry and provider/model fallback: forbidden
- Productive tools: unavailable; only allowlisted `janus_inert_*` fixtures are present
- Runtime registry activation: forbidden

## Decision

`TEST_RUN_PRECHECK: PASS`

One validated dedicated TestPlan, one deterministic generated executable runner, one TestRun ID, explicit prerequisites, and explicit evidence paths are bound. `GENERATOR_RUNNER_FAILED` / `DEDICATED_LIVE_RUNNER_MISSING` is resolved.

The next gate is the operator's exact literal:

`OK START LIVE TEST`

Any other acknowledgement, including `ok`, does not authorize live execution.

