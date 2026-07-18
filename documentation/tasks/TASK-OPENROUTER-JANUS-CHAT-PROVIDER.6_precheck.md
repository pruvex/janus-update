# PREIMPLEMENTATION CHECK - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6

PRE-CHECK RESULT
PRE-CHECK PASSED

## Artifact Identity

- Target Task: `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`
- Target Subtask: N/A
- Task: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_task_breakdown.md`
- Spec: `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- TestSpec: `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- Credential Review: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_testspec_credential_protocol_review.md`
- Compiler Debug: `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_debug_result_testspec_compiler_provider_matrix.md`
- Backlog Item: N/A WITH REASON - compiled Feature Spec task
- Mode: `SINGLE_TASK_PRECHECK`
- Assigned Model: `5.6 Sol`
- Risk: HIGH

## Gate Assessment

| Gate | Result | Evidence |
| --- | --- | --- |
| Artifact identity | PASS | One source Spec, one approved TestSpec, one revised Task `.6`, and one target identity |
| Atomic scope | PASS | Dedicated conformance runner/manifests/schemas/tests only; generic compiler and product surfaces excluded |
| Source of truth | PASS | Battery `OPENROUTER-JANUS-CONFORMANCE/1.0.0`, 30 mandatory cases, 8 live mappings, and binary fail-closed oracles are bound in the TestSpec |
| Candidate identity | PASS | Exact approved Claude, GLM, DeepSeek, and Qwen model/version pairs are immutable for this candidate set |
| Compiler blocker isolation | PASS | `GENERATOR_PLAN_INVALID` is reproduced; generic GPT/Gemini compiler/schema/runner are forbidden and unchanged |
| Dedicated credential profile | PASS | Only `OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0` through `Janus-Projekt/openrouter` is permitted |
| Credential-source isolation | PASS | Dev, Codex/OpenRouter delegation, environment, `.env`, CLI, fixture-secret, management-key, caller-supplied, and fallback credentials are forbidden |
| Operator installation timing | PASS | Key Installation Status is `NOT REQUESTED`; installation is forbidden until execution emits `KEY_INSTALLATION_GATE: READY` |
| Cost and transmission boundary | PASS | Exact `USD 1.00` non-resetting key limit, expiry by `2026-07-31T23:59:59Z`, 8192/1024 token ceilings, 10 transmissions per candidate, 40 overall, and `USD 0.50` price-drift block |
| Current public-price calculation | PASS | Worst-case bounded token cost is `USD 0.455696384`; lookup used no credential and no model invocation |
| Live authority | PASS CLOSED | No live call during execution; later live matrix still requires exact `OK START LIVE TEST` in `janus-test-pipeline` |
| Evidence ownership | PASS | Runner-generated plan/result only; no manual TestPlan/TestResult patching |
| Tool safety | PASS | Only inert test doubles; productive tool side effects forbidden |
| Production default-deny | PASS | Runtime registry remains `models: []` with SHA256 `7712D5B2775F5BDED03EF1C2DAE4228F9FCC8B7441140FC4F1AB8F56210EC46F` |
| Model assignment | PASS | `5.6 Sol/high` matches provider, credential, privacy, prompt-injection, cost, and premature-activation risk |

## Resolved Prior Blockers

- `TESTSPEC_SOURCE_OF_TRUTH_MISSING`: resolved by the approved OpenRouter TestSpec.
- Exact four-candidate identity: resolved by operator-approved immutable model/version pairs.
- Non-numeric credential budget: resolved by the reviewed exact credit, expiry, token, transmission, and price-drift limits.
- Generic TestSpec compiler mismatch: contained as an explicit tripwire and replaced in scope by the dedicated Task `.6` conformance path.

## Scope And Stop Gates

- Implement only the dedicated Task `.6` conformance package, manifests, schemas, focused tests, offline/static/mocked execution, and no-call preflight mechanics.
- Do not modify the generic GPT/Gemini compiler, generic plan schema, generic generated runner, provider gateway, key lifecycle, chat UI, selection behavior, telemetry implementation, release files, or deployment state.
- Do not access a real credential during implementation or offline evidence.
- When offline implementation and validation pass, emit exactly
  `KEY_INSTALLATION_GATE: READY` and stop for the operator.
- Do not ask the operator to open Janus before that gate.
- After the operator installs the dedicated key through Janus Settings, run only
  `LIVE_PREFLIGHT_ONLY`; it must make zero model transmissions.
- Do not run the live matrix without a validated TestPipeline plan/preflight and
  exact `OK START LIVE TEST`.
- Do not populate `backend/config/openrouter_certified_models.json`; generated
  candidates remain non-runtime and at most `TEST_PASS_AUDIT_PENDING`.

## Required Evidence

- Focused Python suite:
  `python -m pytest backend/tests/test_openrouter_conformance.py backend/tests/test_openrouter_certification_registry.py -q`
- Python compilation for the dedicated runner and test module.
- Deterministic manifest/plan/result schema validation and TestSpec mutation
  tripwires.
- Credential-source tripwires proving no real key read before the installation
  gate and no dev/delegation/environment/CLI/fixture/caller fallback.
- Cost tests proving `USD 0.455696384`, the `USD 0.50` drift block, exact
  `USD 1.00` key limit, 8192/1024 token ceilings, and 40-transmission ceiling.
- Registry content/hash invariant and normal-catalog zero-OpenRouter check.
- Scoped secret/redaction scan and `git diff --check`.
- Required headed non-activation regression:
  `npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list`

## Execution Handoff

```text
legacy handoff start
NEXT: janus-executioner
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6
Target Subtask: N/A
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_task_breakdown.md
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Backlog Item: N/A WITH REASON - compiled Feature Spec task
Assigned Model: 5.6 Sol
Mode: SINGLE_TASK_EXECUTION
Pre-Check: PRE-CHECK PASSED
Pre-Check Context:
- Implement the dedicated deterministic OpenRouter conformance runner/manifests/schemas/tests bound to the approved TestSpec and exact four candidates.
- Keep every real credential, live model call, runtime registry write, release, and production activation closed.
- Stop after offline evidence at KEY_INSTALLATION_GATE: READY so the operator can create and save the dedicated USD 1.00 certification key through Janus Settings.
Affected Files:
- backend/services/conformance/__init__.py
- backend/services/conformance/openrouter_conformance_runner.py
- backend/services/conformance/fixtures/openrouter/battery_v1.json
- backend/services/conformance/fixtures/openrouter/candidates_v1.json
- backend/services/conformance/fixtures/openrouter/conformance_plan.schema.json
- backend/services/conformance/fixtures/openrouter/conformance_result.schema.json
- backend/tests/test_openrouter_conformance.py
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_execution_result.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- backend/config/openrouter_certified_models.json (read-only invariant)
- documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md (read-only source of truth)
Evidence Focus:
- python -m pytest backend/tests/test_openrouter_conformance.py backend/tests/test_openrouter_certification_registry.py -q
- python -m py_compile backend/services/conformance/openrouter_conformance_runner.py backend/tests/test_openrouter_conformance.py
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
- deterministic TestSpec/manifests/schemas/cost/credential-source/registry/redaction assertions
- scoped git diff --check
Scope-Regel:
- Implement only the bound target task. No architecture drift, no provider fallback, no scope expansion.
- No key installation or real credential read before KEY_INSTALLATION_GATE: READY; no live model call in execution.
Automated Evidence Gate:
- python -m pytest backend/tests/test_openrouter_conformance.py backend/tests/test_openrouter_certification_registry.py -q
- npx playwright test <runner> --headed --workers=1 --reporter=list
- npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list
Artifact Identity Check:
- Task, Target Task, Backlog Item, Spec, TestSpec, credential review, compiler debug result, and Handoff path verified.
Oracle-/TestPlan-Regel:
- Do not manually patch generated TestPlan/TestResult artifacts. Route TestSpec changes to janus-test-pipeline.
- Reject any generic plan with GPT/Gemini-only output, zero OpenRouter tests, unapproved candidates, or changed battery/oracle bindings as GENERATOR_PLAN_INVALID.
Keep Context:
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_task_breakdown.md
- documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_testspec_credential_protocol_review.md
- documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_debug_result_testspec_compiler_provider_matrix.md
- backend/config/openrouter_certified_models.json
Drop Context:
- Task .5 implementation/browser details
- prior missing-TestSpec blocker narrative
- unrelated backlog, audit, release, and dirty-worktree history
- development and Codex/OpenRouter delegation credential paths
Completion Rule:
- End with PASS/BLOCKED/HANDOFF and concrete evidence paths.
- PASS must stop at KEY_INSTALLATION_GATE: READY before any operator key installation.
Expected Output:
- Offline implementation result, executed checks, changed files, exact key-installation gate state, and janus-test-pipeline handoff.
legacy handoff end
```

## NEXT STEP

- Recommended Skill: janus-executioner
- Recommended Model: 5.6 Sol
- Recommended Intelligence: high
- User Action: none now; do not open Janus or save a key until execution emits `KEY_INSTALLATION_GATE: READY`
