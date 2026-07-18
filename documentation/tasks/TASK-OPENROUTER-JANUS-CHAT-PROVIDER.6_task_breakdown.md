# TASK BREAKDOWN - TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6

## Source Identity

- **Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **TestSpec:** `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- **Task File:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.md`
- **Backlog Item:** N/A WITH REASON - compiled Feature Spec task
- **Prior Gate:** Tasks `.1` through `.5` have task-scoped Final Audit PASS or PASS WITH FIXES; Task `.5` explicitly excludes live provider activation and leaves Task `.6` as a separate conformance block
- **Prior Precheck:** `PRE-CHECK BLOCKED: TESTSPEC_SOURCE_OF_TRUTH_MISSING`
- **Resolved Blocker:** Battery `OPENROUTER-JANUS-CONFORMANCE/1.0.0` and the exact four candidates are now decision-locked in the approved TestSpec
- **Credential Decision:** A fresh OpenRouter inference key dedicated to Task `.6`, labeled `janus-task6-cert-2026-07`, limited to exactly `USD 1.00` without reset and expiring no later than `2026-07-31T23:59:59Z`, must later be saved through Janus Settings under credential profile `OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0`; dev, delegation, environment, CLI, fixture-secret, management-key, and caller-supplied credential sources are forbidden
- **Operator Timing:** Do not save the certification key yet. Janus may be opened for key installation only after implementation and offline validation emit `KEY_INSTALLATION_GATE: READY`
- **Open Debug Blocker:** `GENERATOR_PLAN_INVALID` - the generic compiler silently emits GPT/Gemini instead of OpenRouter and is forbidden for Task `.6`
- **Production Invariant:** `backend/config/openrouter_certified_models.json` remains the sole runtime certification authority and is intentionally empty; OpenRouter remains unavailable in production throughout this task

## Selected Target

- **Target Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`
- **Target Subtask:** N/A
- **Mode:** SINGLE_TASK_PRECHECK
- **Goal:** Implement one dedicated deterministic OpenRouter conformance plan/runner/result path bound to the approved TestSpec, produce complete offline/static/mocked evidence and a no-call live preflight for the four approved candidates, then hand live execution to `janus-test-pipeline`. Do not use the generic GPT/Gemini compiler, perform live calls, populate the runtime registry, release, publish, or activate OpenRouter in this execution slice.

## Source Of Truth

- The bound Feature Spec defines the required four model families, full Janus conformance surface, exact model/battery binding, fail-closed behavior, and evidence/privacy constraints.
- The approved TestSpec is the only test-oracle and candidate-identity authority. Generated battery, candidate, plan, runner, or result artifacts may not add, remove, weaken, reinterpret, or replace its cases or bindings.
- The approved TestSpec is also the credential-protocol authority. Live evidence may use only profile `OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0`, stored through the Janus Settings path `Janus-Projekt/openrouter`.
- Battery `OPENROUTER-JANUS-CONFORMANCE/1.0.0` contains 20 functional, 6 security, and 4 prompt-injection cases plus 8 bundled live scenarios.
- Candidate set `OPENROUTER-FOUR-FAMILY-2026-07-17.1` binds exactly:
  - Claude: `anthropic/claude-sonnet-5` / `anthropic/claude-sonnet-5-20260630`
  - GLM: `z-ai/glm-5.2` / `z-ai/glm-5.2-20260616`
  - DeepSeek: `deepseek/deepseek-v4-pro` / `deepseek/deepseek-v4-pro-20260423`
  - Qwen: `qwen/qwen3.7-plus` / `qwen/qwen3.7-plus-20260602`
- The generic `tests/e2e/generator/compile-testspec-to-testplan.mjs`, generic plan schema, and generic generated runner are not Task `.6` authorities. Debug evidence proves they replace this matrix with GPT/Gemini while still reporting `TESTPLAN VALID`.
- Task `.6` must use its already specified dedicated conformance runner to deterministically extract or validate the TestSpec battery/candidate manifests and generate its conformance-plan/result artifacts.
- A generated registry-shaped update candidate is evidence only, must remain outside `backend/config/`, and may use only `TEST_PASS_AUDIT_PENDING`.
- `backend/config/openrouter_certified_models.json` remains the only runtime certification authority and must stay byte-for-byte empty of models in this slice. Passing evidence does not authorize copying entries into it.
- Final Audit remains a later independent gate. This task must not claim final certification or production eligibility before that gate passes.

## Atomic Scope

- Add an isolated package under `backend/services/conformance/` with one dedicated OpenRouter conformance runner, versioned manifests, and dedicated validation schemas.
- Implement a deterministic TestSpec binding check that fails if any battery ID/version, candidate-set ID, exact model/version row, mandatory case ID, execution class, live-scenario mapping, or binary oracle differs from the approved TestSpec.
- Generate or validate exactly one battery manifest and one candidate manifest. Hand editing that creates semantic drift must fail validation.
- Generate a dedicated non-live conformance plan containing:
  - battery and candidate-set identity
  - all mandatory case identities
  - execution class (`STATIC`, `MOCKED_RUNTIME`, `LIVE_PROVIDER`)
  - exact applicability per candidate
  - exact model ID/version
  - expected transmission/retry/fallback contract
  - evidence and redaction requirements
- Keep the dedicated plan/result schemas Task `.6`-local. Do not broaden the generic GPT/Gemini compiler, plan schema, or generated runner in this slice.
- Implement static and mocked-runtime execution for schema/version drift, exact binding, unavailable/alias candidates, auth/provider/model/stream failures, no retry, no duplicate transmission, no fallback, nullable telemetry, inert tools, evidence redaction, and empty production registry.
- Implement the eight TestSpec live-scenario definitions and their maximum ten-transmission-per-candidate budget, but do not invoke them in `janus-executioner`.
- Implement and validate all static/mocked runner and preflight mechanics before
  requesting any real credential installation. When those checks pass, emit
  exactly `KEY_INSTALLATION_GATE: READY` and pause for the operator.
- The operator checkpoint must instruct creation of a fresh normal OpenRouter
  inference key labeled `janus-task6-cert-2026-07`, limited to exactly
  `USD 1.00` with no reset and expiry no later than
  `2026-07-31T23:59:59Z`, followed by storage through the real Janus Settings
  UI and immediate post-evidence revocation.
- Do not read, import, copy, or fall back to a Codex/OpenRouter delegation key,
  development key, environment variable, `.env`, CLI argument, test fixture
  secret, management key, or caller-supplied credential.
- Implement a `LIVE_PREFLIGHT_ONLY` path that performs no model call and verifies:
  - exact official model metadata remains available and matches the approved binding
  - the dedicated certification-key operator attestation is present
  - Janus public credential state is `present=true`, masked, and `VALID`
    without exposing credential data
  - inert tool allowlists and result paths are ready
  - runtime registry hash/content is still empty
  - the maximum remains 10 transmissions per candidate and 40 overall
  - every transmission is capped at 8192 input and 1024 completion tokens
  - current public prices recompute to at most `USD 0.50`
  - the dedicated key has at least the recomputed amount remaining
  - call budget, no-retry rule, and evidence destinations are explicit
- Route the generated plan and preflight result to `janus-test-pipeline`. Only that skill may request `OK START LIVE TEST` and own live execution/result evidence.
- After the real no-call preflight is complete, keep the key installed but
  unusable for normal chat because the production certification registry remains
  empty. After the approved live run and evidence capture, require operator
  revocation and Janus Settings deletion before closeout unless a later
  separately approved production-key workflow replaces it.
- Generate machine-readable evidence through the runner only. Neither `janus-executioner` nor an operator may manually patch a plan, runner, result JSON, or registry candidate to change an outcome.
- Make every missing, skipped, malformed, inconclusive, or failed mandatory applicable case fail closed for that candidate.
- Exercise tool, permission, and confirmation paths with inert test fixtures/test doubles only; no productive Janus tool side effect is allowed.
- Never serialize a key, bearer value, fingerprint, keyring handle, private prompt/response, private conversation content, or unredacted sentinel.
- Prove the packaged runtime registry remains empty and the normal catalog exposes zero OpenRouter models. Positive catalog compatibility may use an injected test fixture only.

## Files

- `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md` (read-only source of truth during execution)
- `backend/services/conformance/__init__.py` (new, only if required for package execution)
- `backend/services/conformance/openrouter_conformance_runner.py` (new)
- `backend/services/conformance/fixtures/openrouter/battery_v1.json` (new; deterministic TestSpec-bound manifest)
- `backend/services/conformance/fixtures/openrouter/candidates_v1.json` (new; exact approved candidate-set manifest)
- `backend/services/conformance/fixtures/openrouter/conformance_plan.schema.json` (new)
- `backend/services/conformance/fixtures/openrouter/conformance_result.schema.json` (new; certification extension over the base TestResult contract)
- `backend/tests/test_openrouter_conformance.py` (new)
- `backend/config/openrouter_certified_models.json` (read-only production-invariant check; no model population)
- `documentation/test-runs/<TEST_RUN_ID>_plan.json` (runner-generated later; dedicated conformance schema; never hand-edited)
- `documentation/test-results/<TEST_RUN_ID>_results.json` (runner-generated later; base TestResult plus validated certification extension)
- `documentation/test-results/<TEST_RUN_ID>_results.md` (runner-generated later)
- `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_certification_evidence.md` (generated after live TestRun, not created manually during execution)
- `documentation/test-results/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_registry_update_candidate.json` (generated after complete evidence, non-runtime and audit-pending)

The three generic files below are evidence-only and must not be changed in this slice:

- `tests/e2e/generator/compile-testspec-to-testplan.mjs`
- `tests/e2e/generator/test-plan.schema.json`
- `tests/e2e/generator/generate-live-runner.mjs`

Any additional production file, runtime registry writer, catalog import path, UI file, provider-selection file, generic TestPlan generator file, release file, or deployment file is out of scope and requires rerouting.

## Explicit Exclusions

- No write that adds a model to `backend/config/openrouter_certified_models.json`.
- No use of a generic plan reporting only GPT/Gemini as Task `.6` evidence.
- No modification of the generic TestSpec compiler, generic TestPlan schema, generic generated runner, or their existing GPT/Gemini behavior.
- No live provider/model call during `janus-executioner`; only no-call preflight is allowed.
- No certification-key installation before `KEY_INSTALLATION_GATE: READY`.
- No reuse of a development, Codex/OpenRouter delegation, environment, CLI,
  fixture, management, or caller-supplied key.
- No release, publish, tag, merge, installer, update-manifest, deployment, production activation, or productive catalog visibility.
- No runtime certification, hot-pull model catalog, full OpenRouter catalog import, automatic candidate replacement, `latest` alias, or model-family expansion.
- No provider, key-lifecycle, chat UI, selection persistence, DeepDive UI, database migration, or Task `.5` telemetry implementation changes.
- No real Janus tool side effects and no use of private user conversations as certification prompts.
- No automatic retry, fallback, or relaxed oracle for a flaky or partially passing candidate.
- No claim that a passed execution result is final certification before independent Final Audit.

## Acceptance Criteria

1. The dedicated validator binds exactly TestSpec battery `OPENROUTER-JANUS-CONFORMANCE/1.0.0`, candidate set `OPENROUTER-FOUR-FAMILY-2026-07-17.1`, all mandatory case IDs/oracles, and the four approved model/version pairs.
2. Any mutation, omission, addition, weakening, alias substitution, version mismatch, execution-class change, live-bundle drift, or candidate-family drift fails validation.
3. The dedicated plan contains OpenRouter and all four exact candidates; a plan containing only GPT/Gemini, zero OpenRouter tests, or any unapproved model is rejected with `GENERATOR_PLAN_INVALID`.
4. Static and mocked-runtime cases produce deterministic binary results bound to battery, candidate set, exact model/version, case ID, execution class, and evidence reference.
5. Missing, skipped, malformed, inconclusive, or failed mandatory evidence makes that candidate ineligible. There is no partial-pass, retry-based promotion, substitution, or manual waiver.
6. The result contract exposes selected/returned model, transmission/retry/fallback counters, tool/permission/confirmation outcomes, telemetry presence/value fields, redaction assertions, runner hash, timestamps, and evidence paths without raw sensitive content.
7. The dedicated result validates both the repository base TestResult requirements and the Task `.6` certification extension.
8. Tool, permission, and confirmation scenarios use inert fixtures/test doubles and cause no productive side effect.
9. Offline implementation and validation complete before the runner emits
   `KEY_INSTALLATION_GATE: READY`; no real credential is required or read before
   that checkpoint.
10. The credential checkpoint accepts only a freshly created normal OpenRouter
    inference key for profile
    `OPENROUTER-JANUS-CERTIFICATION-KEY/1.0.0`, labeled
    `janus-task6-cert-2026-07`, limited to exactly `USD 1.00` without reset,
    expiring no later than `2026-07-31T23:59:59Z`, and saved through Janus
    Settings.
11. Dev/delegation/environment/CLI/fixture/management/caller-supplied key reuse
    and every credential fallback are rejected.
12. `LIVE_PREFLIGHT_ONLY` makes zero model calls and fails closed on metadata
    mismatch, absent operator attestation, missing or non-`VALID` Janus public
    credential state, unsafe tool fixture, missing evidence path, non-empty
    registry, token ceilings above 8192 input or 1024 completion, more than 40
    transmissions, public-price recomputation above `USD 0.50`, insufficient
    remaining key credit, or an ambiguous call budget.
13. `janus-executioner` ends with a `janus-test-pipeline` handoff and does not create final live certification evidence or claim a candidate passed live certification.
14. The actual live matrix remains blocked until `janus-test-pipeline` presents a validated plan/preflight and receives exact `OK START LIVE TEST`.
15. Only candidates with every mandatory applicable result passed may later enter the non-runtime update candidate as `TEST_PASS_AUDIT_PENDING`.
16. After live evidence capture, the dedicated certification key is revoked and
    deleted through Janus Settings before closeout unless a separately approved
    production-key workflow replaces it.
17. `backend/config/openrouter_certified_models.json` still has `models: []`, its initial hash remains unchanged, and the packaged catalog exposes zero OpenRouter models.
18. The generic GPT/Gemini compiler/schema/runner and all product/UI/provider/release files remain unchanged.
19. The eventual complete TestRun result routes to independent `janus-final-audit`; neither implementation nor TestPipeline self-authorizes production activation.

## Tests And Evidence

- Focused unit tests for TestSpec-to-manifest identity, battery/candidate schemas, exact four-family binding, case/oracle completeness, execution classes, live-scenario bundles, and deterministic plan/result generation.
- Mutation matrix for wrong battery/candidate-set version, case omission/addition, weakened oracle, wrong execution class, unknown model, `latest`/alias, duplicate/missing family, and wrong canonical version.
- Tripwire proving the reproduced `68` GPT/Gemini / `0` OpenRouter generic plan is rejected as `GENERATOR_PLAN_INVALID`.
- Mocked runner matrix for all-pass, one-case-fail, skipped/inconclusive case, auth/provider/model mismatch, timeout/stream interruption, no retry, no duplicate transmission, no fallback, and per-candidate independence.
- Focused Janus-boundary tests for redaction, necessary context, canonical skill/tool payloads, permission denial, confirmation-required behavior, inert tool execution, and no productive side effects.
- Telemetry contract tests for exact model identity and individually nullable prompt, completion, total, cache-read, cache-write, reasoning, OpenRouter-credit, and upstream-inference-cost fields without estimation.
- Result-schema tests for the repository base TestResult fields plus the certification extension.
- `LIVE_PREFLIGHT_ONLY` tests proving exact metadata checks, secure credential presence-only handling, call budget, evidence paths, and zero model transmissions.
- Deterministic price-budget tests for the four public rates, worst-case
  `USD 0.455696384`, the `USD 0.50` drift gate, the exact `USD 1.00` key limit,
  8192/1024 per-transmission token ceilings, and 40-transmission global ceiling.
- Credential-source tripwires proving no key is read before
  `KEY_INSTALLATION_GATE: READY`, no dev/delegation/environment/CLI/fixture or
  caller-supplied fallback exists, and only masked public Janus state enters
  evidence.
- Secret/redaction scan over stdout, exceptions, logs, fixtures, generated plan/result JSON, and Markdown summaries.
- Production-invariant test that the packaged registry remains empty and the normal catalog exposes zero OpenRouter models; positive catalog compatibility uses only an injected test registry candidate.
- Required offline command: `python -m pytest backend/tests/test_openrouter_conformance.py backend/tests/test_openrouter_certification_registry.py -q`.
- Required non-activation UI regression: `npx playwright test tests/e2e/openrouter-settings.spec.js --headed --workers=1 --reporter=list`.
- Python compilation for changed Python files, JSON parsing/schema validation for every manifest/plan/result payload, scoped credential/content scan, and scoped `git diff --check`.
- No live TestRun command belongs to this execution slice.

## Risks And Precheck Gates

- **Source drift:** Precheck must verify the approved TestSpec remains the sole oracle/candidate authority and generated manifests cannot weaken it.
- **Silent generic miscompile:** Precheck must prohibit the generic compiler/schema/runner and require the `GENERATOR_PLAN_INVALID` tripwire.
- **Current model volatility:** Precheck must bind the four approved IDs/versions and require official availability recheck in no-call preflight; automatic replacement is forbidden.
- **False certification:** Precheck must verify all 30 mandatory case IDs plus 8 live-scenario mappings remain represented and missing evidence fails closed.
- **Premature activation:** Precheck must capture the initial hash/content of `backend/config/openrouter_certified_models.json`, require `models: []`, and block any execution plan that writes passed entries there.
- **Credential/privacy exposure:** Precheck must bind the dedicated
  certification profile, forbid all dev/delegation/environment fallbacks, keep
  installation closed until `KEY_INSTALLATION_GATE: READY`, and verify that
  only masked public Janus state enters evidence; no credential value or live
  call is allowed.
- **External cost and transmission:** Precheck must verify execution stops before live calls and hands the validated plan/preflight to TestPipeline.
- **Tool side effects:** Precheck must verify inert tool fixtures/test doubles and block any plan that can invoke productive Janus tools.
- **Result ownership:** Precheck must verify plan/results are runner-generated and schema-validated, never manually patched.
- **Audit authority:** The later update candidate must be non-runtime, `TEST_PASS_AUDIT_PENDING`, and independently audited; execution may not edit release or production state.
- Preserve all unrelated dirty and untracked operator files.

## Execution Model

- **Model:** `5.6 Sol`
- **Intelligence:** high
- **Reason:** External model certification crosses security, privacy, prompt-injection, tool-permission, evidence-integrity, and premature-activation boundaries.

## Decision

TASK DESIGN COMPLETE

```text
@janus-preimplementation-check
Spec: documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md
Task: documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_task_breakdown.md
Backlog Item: N/A
Target Task: TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6
Target Subtask: N/A
Mode: SINGLE_TASK_PRECHECK
Execution Model: 5.6 Sol
Rules: VALIDATE_ONE_TARGET_TASK_NO_IMPLEMENTATION_NO_CODE_CHANGES_RELEASE_EXECUTION_HANDOFF_ONLY_IF_SCOPE_FILES_TESTS_RISKS_ARE_CLEAR
Expected Output: PRE_CHECK_PASSED_PLUS_EXECUTION_HANDOFF_OR_PRE_CHECK_BLOCKED
```
