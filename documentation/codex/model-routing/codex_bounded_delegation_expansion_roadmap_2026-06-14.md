# Codex Bounded Delegation Expansion Roadmap - 2026-06-14

Status: PRIORITIZED ROADMAP AFTER THE FIRST WORKFLOW-READY BOUNDED PACKAGE

## Purpose

This roadmap defines the next bounded delegation classes to build after the currently validated workflow-ready package:

- `documentation_draft`
- `quickchange_patch_review`
- `generator_review`

The goal is not broad sidecar authority. The goal is to expand only into bounded classes where Codex App keeps routing, review, validation, and acceptance authority.

## Prioritization Logic

A class moves earlier when it has most of these properties:

- high Codex-contingent savings in normal work
- small and reviewable diff surface
- deterministic local validation path
- low blast radius on failure
- clear reject-and-fallback path back to Codex

A class moves later when it depends on any of these:

- broad repo writes
- ambiguous product decisions
- release, Git, or acceptance authority
- non-deterministic execution steps without local verifier

## Current Accepted Baseline

| class | current status | reason |
| --- | --- | --- |
| `documentation_draft` | `WORKFLOW_READY` | accepted bounded draft plus Codex review flow |
| `quickchange_patch_review` | `WORKFLOW_READY` | tiny bounded patch proposal/review flow validated |
| `generator_review` | `WORKFLOW_READY` | delegated intent plus deterministic local builder/executor/validator |

## Next Expansion Order

### Priority 1 - `debug_hypothesis_review`

Recommended owning skill:

- `janus-debug`

Recommended bounded mode:

- `SIDECAR_ASSIST_ONLY`

Recommended output:

- redacted root-cause summary
- top 1 to 3 hypotheses
- suggested local validation checks
- optional bounded instrumentation proposal as review-only patch

Why first:

- high everyday value
- no immediate write authority required
- strong Codex savings on repetitive investigation framing
- easy fallback to Codex if the hypotheses are weak

Required gates before everyday use:

- redaction rule for logs and secrets
- fixed output schema for hypotheses and evidence quality
- explicit `no local execution` default
- Codex-owned reproduction and acceptance step

Evidence needed:

- 3 accepted bounded assist runs across distinct debug situations
- at least 1 rejection example with clean fallback to Codex

### Priority 2 - `test_result_triage_review`

Recommended owning skill:

- `janus-test-pipeline`

Recommended bounded mode:

- `SIDECAR_ASSIST_ONLY`

Recommended output:

- failure clustering
- likely root-cause bucket
- suggested next local verifier or rerun target
- bounded draft for a `TestResult` note only after Codex review

Why second:

- strong savings on repetitive failure interpretation
- safer than delegated test-artifact writes
- can reuse existing generator-review and validator patterns

Required gates before everyday use:

- bind inputs to saved local test outputs only
- forbid delegated command execution
- require a structured triage summary format
- Codex-owned PASS/FAIL and rerun decision

Evidence needed:

- 3 accepted triage-review runs
- at least 1 case with mixed or noisy failures

### Priority 3 - `quickchange_write_apply`

Recommended owning skill:

- `janus-quickchange`

Recommended bounded mode:

- `SIDECAR_WRITE_CANDIDATE`

Recommended output:

- one tiny live write in a predeclared file allowlist
- exact diff capture
- validation summary
- Codex review before acceptance

Why not earlier:

- the review path is proven, but broader operator comfort still benefits from one more assist-only class first
- write authority should expand only after the shared operator model is routine

Required gates before everyday use:

- exact editable-path allowlist
- touched-file cap
- delete/rename/move tripwire
- local validation command capture
- forced Codex reject flow when validation is incomplete

Evidence needed:

- 3 accepted live write runs in separate tiny quickchange situations
- 0 silent path escapes

### Priority 4 - `execution_patch_candidate`

Recommended owning skill:

- `janus-executioner`

Recommended bounded mode:

- `SIDECAR_ASSIST_ONLY` first, later `SIDECAR_WRITE_CANDIDATE`

Recommended output:

- bounded patch proposal for one prechecked task slice
- optional local structured patch package
- explicit risk list and expected validation steps

Why here:

- large potential Codex savings
- but materially higher authority and failure surface than quickchange
- should only begin after the write discipline is routine on smaller scopes

Required gates before everyday use:

- preimplementation artifact binding
- file-cluster allowlist
- touched-file budget
- mandatory local test/validation plan
- Codex-owned final apply decision

Evidence needed:

- 2 accepted proposal-only runs
- then 1 bounded write pilot on a tiny prechecked task slice

### Priority 5 - `test_artifact_write_runner_level`

Recommended owning skill:

- `janus-test-pipeline`

Recommended bounded mode:

- `SIDECAR_WRITE_CANDIDATE`

Recommended output:

- generated runner/spec artifacts through runner-level execution support, not prompt-only command steering

Why later:

- this class already has three bounded live failures
- the blocker is execution reliability, not just prompt quality
- it should return only when runner-level command support is intentionally added

Required gates before everyday use:

- runner-owned command templates
- exact output-path allowlist
- post-generation validator pass
- complete reject flow on missing artifacts

Evidence needed:

- 1 dry-run with runner-level execution
- 2 accepted live writes with validator PASS

## Explicit Deferrals

These stay out of the next wave:

- `janus-final-audit`
- `janus-git-governance`
- `janus-build-release`
- `janus-skill-router`

Reason:

- authority too high
- reject cost too high
- sidecar value too low relative to governance risk

## Recommended Build Sequence

1. Add `debug_hypothesis_review`.
2. Add `test_result_triage_review`.
3. Expand `quickchange` from review to routine tiny write evidence.
4. Pilot `execution_patch_candidate` on a single prechecked slice.
5. Revisit `test_artifact_write_runner_level` only after runner-owned execution support exists.

## Operator Outcome

If this roadmap succeeds, the operator will gradually get the same simple bounded choice across more Janus work:

- `1 = Codex`
- `2 = Delegated`

But each class keeps separate gates, separate evidence, and separate fallback rules. No global sidecar approval should be inferred from this roadmap.
