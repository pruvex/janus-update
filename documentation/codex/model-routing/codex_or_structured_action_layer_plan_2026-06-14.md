# Codex OR Structured Action Layer Plan - 2026-06-14

Status: DESIGN PLAN / NO PRODUCTION ROUTING / NO LIVE OR WRITE ENABLEMENT

## Goal

Create a safer delegation architecture so cheaper OpenRouter or Sidecar models can take over meaningful Janus work without being trusted to improvise shell commands, Git actions, release actions, or unrestricted repo writes.

This plan keeps the original economic goal intact:

- save Codex quota on repetitive work
- let cheaper external or sidecar models act as workhorses
- keep Codex App as operator, reviewer, validator, and authority

## Problem Confirmed By Current Evidence

The recent bounded `janus-test-pipeline` write pilots did not fail because the generator logic was wrong.

They failed because delegated free-form Windows command composition is too fragile.

Observed pattern:

- bounded prompts were understood
- file-scope tripwires held
- no out-of-scope writes happened
- command execution inside the delegated shell remained unreliable

Conclusion:

- delegation should not depend on a model inventing shell syntax correctly
- execution must move into a deterministic local action layer

## Core Architecture

Target control split:

```text
Codex App
  -> routes the Janus skill
  -> shows local vs OR/sidecar choice
  -> prepares bounded context package
  -> chooses allowed action set

OR or Sidecar Model
  -> analyzes
  -> drafts
  -> proposes patch
  -> selects from predeclared action intents
  -> never improvises unrestricted shell execution

Local Structured Executor
  -> validates action request
  -> runs deterministic local action
  -> enforces allowlist and caps
  -> captures artifacts, diff, stdout/stderr, exit code

Codex App
  -> reviews output
  -> validates
  -> accepts, rejects, reruns, or escalates
```

## Design Principle

Delegated models should express intent, not operating-system ceremony.

Bad pattern:

- model writes raw Windows shell commands
- model guesses quoting, PATH, invocation style, environment assumptions

Good pattern:

- model returns a structured action request or a bounded patch
- local executor translates that into the real deterministic command or file write

## Action Families

### 1. Draft Actions

Purpose:

- produce non-binding text output only

Examples:

- documentation draft
- changelog draft
- debug summary
- test triage summary

Model output:

- markdown or structured text

Executor need:

- none beyond artifact capture

Current status:

- already proven for bounded read-only documentation sidecar work

### 2. Patch Actions

Purpose:

- let delegated models write or propose bounded code/file edits

Examples:

- quickchange text update
- small refactor in declared files
- instrumentation patch
- test file patch

Model output:

- unified diff
- exact file replacement payload
- structured write-set

Executor need:

- file allowlist
- touched-file cap
- delete/rename/move tripwire
- diff capture
- validation hooks

Current status:

- tiny quickchange path proven
- broader code/test patch path not yet proven

### 3. Deterministic Generator Actions

Purpose:

- run known local generators or validators without asking the model to compose shell commands

Examples:

- compile TestSpec to TestPlan
- generate live runner from plan
- validate plan
- validate runner

Model output:

- structured action request such as:
  - `run_generator`
  - `generator_id`
  - `input_artifacts`
  - `declared_output_artifacts`

Executor need:

- static mapping from `generator_id` to approved executable plus arguments
- fixed environment rules
- declared output allowlist
- artifact capture

Current status:

- this is the missing layer exposed by the failed `janus-test-pipeline` pilots

### 4. Analysis Actions

Purpose:

- offload reasoning-heavy but non-authoritative work

Examples:

- debug hypothesis set
- failing test triage
- patch review summary
- compare fixed baseline vs OR candidate

Model output:

- structured analysis JSON or markdown

Executor need:

- none beyond capture and schema validation

Current status:

- highly viable

## First Structured Action Types

Recommended first minimal action contract:

| action_type | purpose | write allowed | executor role |
| --- | --- | --- | --- |
| `draft_markdown` | produce non-binding text | no | capture only |
| `propose_patch` | produce bounded diff for declared files | yes, after review | apply or reject locally |
| `run_generator` | request one approved deterministic generator | yes, executor-owned | local runner executes mapped command |
| `run_validator` | request one approved validator | no direct writes except validator outputs if predeclared | local runner executes mapped command |
| `summarize_results` | explain existing artifacts | no | capture only |

## Example Deterministic Generator Mapping

The delegated model should never emit the raw command directly.

Instead:

```json
{
  "action_type": "run_generator",
  "generator_id": "testspec_to_testplan_v1",
  "inputs": {
    "testspec_path": "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md",
    "test_run_id": "TEST-RUN-2026-06-14-901"
  }
}
```

Then the local executor owns the real command mapping, for example:

- `testspec_to_testplan_v1`
  - executable: approved local Node binary
  - script: `tests/e2e/generator/compile-testspec-to-testplan.mjs`
  - argument template: fixed and versioned

This eliminates shell improvisation from the delegated model path.

## Skill Rollout Strategy

### Phase 1

Keep or expand:

- `janus-documentation-update` draft delegation
- read-only analysis and summary tasks
- bounded quickchange patch proposals

### Phase 2

Add structured patch delegation for:

- `janus-quickchange`
- narrow `janus-debug` instrumentation
- narrow `janus-executioner` predeclared file clusters

### Phase 3

Add deterministic executor-backed generator delegation for:

- `janus-test-pipeline`
- selected codegen or validation helpers

### Phase 4

Add richer OR worker routing by task class:

- fixed model per stable task family where evidence is strong
- small curated Auto Router pools only where task variance is real

## What OR Should Eventually Do Well

High-confidence future workhorse candidates:

- documentation drafting
- structured summaries
- debug hypothesis generation
- failing log triage
- bounded patch proposals
- mechanical refactors
- test-case wording and expected assertions
- code skeleton drafting

Lower-confidence or delayed candidates:

- unrestricted generator execution
- free-form shell tasks
- release/build authority
- Git governance
- final audits

## Non-Goals

- no production routing activation
- no canonical routing-table update
- no global OR approval
- no Git/release delegation
- no final-audit delegation
- no unrestricted repo-write delegation

## Recommended Next Build Item

Build a minimal structured action contract plus local executor plan.

The first concrete implementation target should be:

- one versioned JSON schema for delegated action requests
- one local executor that supports:
  - `draft_markdown`
  - `propose_patch`
  - `run_generator`
  - `run_validator`
- one deterministic mapping for the first `janus-test-pipeline` generator action

## Decision

The original idea remains valid:

- OR can still become the cheap workhorse
- but it must operate through structured bounded actions, not raw shell improvisation

That is the architecture path most likely to unlock large Codex quota savings without breaking Janus governance.
