# Codex OR Structured Executor Plan - 2026-06-14

Status: DESIGN PLAN / FIRST EXECUTOR SLICE ONLY / NO LIVE ENABLEMENT

## Purpose

Translate delegated action requests into deterministic local execution so OR or Sidecar models do not need to compose shell commands directly.

This plan is the execution companion to:

- `documentation/codex/model-routing/codex_or_structured_action_layer_plan_2026-06-14.md`
- `documentation/codex/model-routing/schemas/codex_delegated_action_request.schema.json`

## First Executor Scope

The first executor version should support exactly these action types:

- `draft_markdown`
- `propose_patch`
- `run_generator`
- `run_validator`

It should reject:

- unknown action types
- undeclared generators or validators
- write requests outside allowlists
- delete/rename/move intent
- any action that lacks the required Codex review flag

## Executor Responsibilities

### Common

- load one delegated action request JSON
- validate it against `codex_delegated_action_request.schema.json`
- create one run directory with:
  - request copy
  - validation result
  - stdout/stderr
  - exit code
  - changed-files snapshot when relevant
  - final executor summary

### `draft_markdown`

- persist the draft payload into an artifact file only
- no repo write outside the run directory

### `propose_patch`

- validate patch scope against `allowed_files`
- store the patch for Codex review
- optionally support local dry-run patch validation later
- do not auto-apply in v1 unless separately approved

### `run_generator`

- map `generator_id` to one pre-approved executable and argument template
- inject only declared inputs
- enforce declared output artifact allowlist
- capture stdout/stderr and resulting artifact existence

### `run_validator`

- map `validator_id` to one pre-approved executable and argument template
- inject only declared inputs
- capture stdout/stderr and pass/fail

## First Approved Generator IDs

Recommended first deterministic mappings:

| generator_id | purpose | local mapping |
| --- | --- | --- |
| `testspec_to_testplan_v1` | compile TestSpec to TestPlan | local approved Node binary + `tests/e2e/generator/compile-testspec-to-testplan.mjs` |
| `generate_live_runner_v1` | create live runner from plan | local approved Node binary + `tests/e2e/generator/generate-live-runner.mjs` |

## First Approved Validator IDs

| validator_id | purpose | local mapping |
| --- | --- | --- |
| `validate_test_plan_v1` | validate generated plan | local approved Node binary + `tests/e2e/generator/validate-test-plan.mjs` |
| `validate_runner_v1` | validate generated runner against plan | local approved Node binary + `tests/e2e/generator/validate-runner.mjs` |
| `node_check_script_v1` | syntax-check generated runner | local approved Node binary + `node --check` |

## Execution Mapping Principle

The delegated model never supplies:

- raw shell pipelines
- quoting rules
- executable discovery logic
- PATH assumptions

The executor owns all of that.

Inputs from the model are limited to:

- generator or validator ID
- declared input values
- declared output artifact list when relevant

## Suggested Executor Output

The executor should emit one structured summary with:

- `workflow_id`
- `action_type`
- `executor_status`
- `schema_validation`
- `mapping_resolution`
- `allowlist_status`
- `output_artifact_status`
- `stdout_path`
- `stderr_path`
- `exit_code`
- `codex_review_required`

## Why This Unlocks OR Workhorse Value

This executor lets us offload the expensive cognitive part:

- patch drafting
- analysis
- test-shaping
- generator selection intent

while keeping the brittle part local:

- command invocation
- file boundaries
- output validation

## Recommended Build Order

1. build schema validation loader
2. build run-directory artifact capture
3. implement `draft_markdown`
4. implement `propose_patch` capture-only mode
5. implement `run_generator` for `testspec_to_testplan_v1`
6. implement `run_validator` for plan plus runner checks
7. add one dry-run fixture and one dummy accepted example per action type

## Non-Goals

- no production routing
- no Git authority
- no unrestricted executor shell
- no direct final-audit or release execution
- no automatic patch apply without Codex review

## Next Concrete Step

If implementation is approved, the first code slice should be a local executor skeleton that:

- reads one JSON request
- validates against the v1 schema
- supports `draft_markdown` and `run_generator` first
- captures artifacts in a deterministic run directory
