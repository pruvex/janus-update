# Debug Result - Task .6 OpenRouter TestSpec Compiler Provider Matrix

SKILL 5 DEBUG RESULT: BLOCKED

Iteration: 1

Progress-Validierung: Failure Code `GENERATOR_PLAN_INVALID`; Evidence geaendert ggü. N-1: N/A; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

## Bound Debug Package

- **Task:** `TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6`
- **Feature Spec:** `documentation/SPEC/OPENROUTER_JANUS_CHAT_PROVIDER_FEATURE_SPEC.md`
- **TestSpec:** `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- **Blocked Precheck:** `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_precheck.md`
- **Expected:** A deterministic plan preserves exactly the approved OpenRouter provider and four model/version bindings.
- **Actual:** The existing compiler reports a valid plan but emits only GPT/Gemini tests and zero OpenRouter tests.
- **Logs:** The compiler and generated-plan summary are the direct reproduction evidence; no provider or credential logs were required.

## Root Cause

The generic TestSpec compiler is structurally unable to represent the approved
Task `.6` certification matrix:

1. `compile-testspec-to-testplan.mjs` fixes the provider expansion to
   `['GPT', 'Gemini']`.
2. `modelForProvider()` maps only Gemini explicitly and maps every other provider
   to the GPT default model.
3. `test-plan.schema.json` allows only `GPT`, `Gemini`, and `Any`.
4. `generate-live-runner.mjs` maps only GPT to `openai` and Gemini to `gemini`;
   every unknown provider falls back to `openai`.
5. The compiler does not preserve the TestSpec's exact `model_version`,
   execution class (`STATIC`, `MOCKED_RUNTIME`, `LIVE_PROVIDER`), applicability,
   candidate-set version, battery version, or certification evidence contract.

This is a silent semantic miscompile, not a normal validation rejection. The
generated plan passes the current validator even though it has lost the complete
OpenRouter identity and oracle contract.

## Reproduction Evidence

Command:

```powershell
node tests/e2e/generator/compile-testspec-to-testplan.mjs `
  --spec documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md `
  --test-run-id TEST-RUN-2026-07-17-998 `
  --output-dir $env:TEMP/janus-openrouter-testspec-compile-debug-20260717 `
  --skip-skill2-handover
```

Observed:

- compiler exit: `0`
- validator result: `TESTPLAN VALID`
- generated tests: `68`
- generated providers: `GPT`, `Gemini`
- generated models: `gpt-5.4-nano`, `gemini-3-flash-preview`
- generated OpenRouter tests: `0`
- repository TestRun artifacts created: none
- live/provider calls: none

## Candidate Approval State

The operator approved exactly:

- `anthropic/claude-sonnet-5` /
  `anthropic/claude-sonnet-5-20260630`
- `z-ai/glm-5.2` /
  `z-ai/glm-5.2-20260616`
- `deepseek/deepseek-v4-pro` /
  `deepseek/deepseek-v4-pro-20260423`
- `qwen/qwen3.7-plus` /
  `qwen/qwen3.7-plus-20260602`

Approval covers candidate identity only. Live execution and production
activation remain unauthorized.

## Fix Summary

No fix was applied in `janus-debug`.

The source-aligned repair is to revise the Task `.6` execution design so its
already-required dedicated conformance runner has a deterministic
TestSpec-to-battery/candidate validation path and emits TestPipeline-compatible,
schema-validated results. The generic GPT/Gemini compiler must not be used as
Task `.6` evidence unless a separately bound infrastructure task fully adds and
validates OpenRouter provider/model/version/execution-class support.

The revised task breakdown must bind:

- the approved TestSpec as oracle source of truth
- the exact four approved model/version rows
- deterministic extraction or validation of battery and candidate manifests
- a schema for battery version, candidate-set version, execution class, exact
  model identity, transmission/retry/fallback counters, redaction assertions,
  and audit-pending certification state
- result generation under `documentation/test-results/` without manual edits
- an explicit no-live-call boundary until `OK START LIVE TEST`
- an unchanged empty runtime registry

## Auto-Verification

- Status: PASS
- Evidence:
  - isolated temp compilation reproduced the silent provider substitution
  - generated plan inspection confirmed `68` GPT/Gemini tests and `0`
    OpenRouter tests
  - source inspection confirmed compiler, schema, and runner provider limits
  - runtime certification registry hash/content remained unchanged

Artifact Identity Check: PASS

Final Feature Suite: N/A WITH REASON - this iteration diagnosed a test
infrastructure planning blocker only; it changed no product or test-pipeline
implementation and ran no live provider suite.

Changed Files:

- `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`
- `documentation/tasks/TASK-OPENROUTER-JANUS-CHAT-PROVIDER.6_debug_result_testspec_compiler_provider_matrix.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## NEXT_STEP

- **Target Skill:** `janus-task-breakdown`
- **Canonical State:** `BLOCKED`
- **Required Artifacts:** approved OpenRouter TestSpec, Task `.6` breakdown, blocked precheck, this debug result
- **Evidence Paths:** `documentation/TEST_SPEC/02_security_safety/20_openrouter_model_conformance_certification.md`; `%TEMP%/janus-openrouter-testspec-compile-debug-20260717/TEST-RUN-2026-07-17-998_plan.json`; compiler/schema/runner files under `tests/e2e/generator/`
- **Failure Code:** `GENERATOR_PLAN_INVALID`
- **Changed Files:** TestSpec approval metadata and this debug result; no product or compiler code
- **Decision:** revise exactly Task `.6` to bind a deterministic dedicated conformance-plan/result path before rerunning precheck
- **Reason:** the generic compiler silently replaces the approved OpenRouter matrix with GPT/Gemini and cannot be accepted as evidence
- **Recommended Model:** `5.6 Sol`
- **Recommended Intelligence:** high
- **Next User Action:** reply `ok` to run `janus-task-breakdown` on this compiler-blocker delta; this does not authorize live tests
