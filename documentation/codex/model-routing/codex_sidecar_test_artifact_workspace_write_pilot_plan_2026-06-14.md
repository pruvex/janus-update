# Codex Sidecar Test-Artifact Workspace-Write Pilot Plan - 2026-06-14

Status: PLANNING PLUS DRY-RUN INFRA ONLY / NO LIVE TEST-ARTIFACT WRITE YET

## Purpose

Define the next bounded write-capable Sidecar class after the successful quickchange pilot.

This pilot targets test artifacts, not product code.

## Why This Is The Next Sensible Step

Compared with normal implementation work, test artifact generation is:

- more mechanical
- easier to validate structurally
- less risky than direct product edits
- still useful for saving Codex App quota on workhorse tasks

It also respects the `janus-test-pipeline` rule to prefer repository generators over handwritten artifacts.

## Selected Pilot Slice

First bounded slice:

- skill: `janus-test-pipeline`
- mode: `TESTSPEC_TO_TEST_PLAN`
- sidecar write type: generated test artifacts only

Allowed write targets for one run:

- `documentation/test-runs/<TEST_RUN_ID>_plan.json`
- `documentation/test-runs/<TEST_RUN_ID>_generated.spec.js`
- `documentation/test-runs/<TEST_RUN_ID>_skill2_handover.txt`

Reason for the extra file:

- the repository compiler `compile-testspec-to-testplan.mjs` deterministically writes the Skill-2 handover as part of the same bounded generation chain
- allowing this exact side-effect is safer than bypassing the compiler or hand-authoring a plan

Not allowed despite this extension:

- any other `documentation/test-runs/<TEST_RUN_ID>_skill*.{txt,md,json}` output
- any `documentation/test-results/*` write
- any product-code change

Not included in the first pilot:

- live Playwright execution
- `documentation/test-results/*.json`
- `documentation/test-results/*.md`
- product code changes
- backlog, registry, or final-audit writes

## Bound Read Inputs

The future live pilot must bind exactly:

- one TestSpec path
- one declared `TEST_RUN_ID`
- generator scripts under `tests/e2e/generator/`

No broad test history should be loaded into the sidecar prompt.

## Required Operator Gate

Future live gate:

```text
CODEX SIDECAR TEST-ARTIFACT WRITE GATE
- Skill: janus-test-pipeline
- Mode: TESTSPEC_TO_TEST_PLAN
- TestSpec:
- TEST_RUN_ID:
- 1 = Codex
- 2 = Sidecar
- Sidecar model/provider:
- Sandbox: workspace-write
- Editable paths:
- Validation after run:
- Abort rules:
- User action:
- Boundaries:
```

## Editable Path Allowlist

The live pilot must declare exact output files before execution.

Recommended first allowlist:

- `documentation/test-runs/<TEST_RUN_ID>_plan.json`
- `documentation/test-runs/<TEST_RUN_ID>_generated.spec.js`
- `documentation/test-runs/<TEST_RUN_ID>_skill2_handover.txt`

Read-only helper/generator inputs may include:

- one TestSpec file
- `tests/e2e/generator/compile-testspec-to-testplan.mjs`
- `tests/e2e/generator/generate-live-runner.mjs`
- `tests/e2e/generator/validate-test-plan.mjs`

## Mandatory Abort Rules

Abort or reject the result when any of the following happens:

- any file outside the exact output allowlist is changed
- product code is touched
- any file in `documentation/test-results/` is created or modified
- generated artifact does not parse or validate
- `TEST_RUN_ID` drift appears
- sidecar handwrites fake results instead of using generator paths

## Validation Requirements

The future live pilot must capture and preserve:

- compile command
- validate command
- stdout/stderr for both
- return codes
- `validation_summary.json`

Minimum local acceptance checks:

- `node tests/e2e/generator/validate-test-plan.mjs --plan <plan>`
- `node --check <generated runner>`
- optional `node tests/e2e/generator/validate-runner.mjs --plan <plan> --runner <runner>`

## Proposed Artifact Set

- `prompt.md`
- `command.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `last_message.md`
- `event_stream.jsonl`
- `summary.json`
- `editable_paths.txt`
- `pre_run_status.txt`
- `post_run_status.txt`
- `changed_files.txt`
- `git_diff.patch`
- `validation_stdout.log`
- `validation_stderr.log`
- `validation_summary.json`
- `pilot_result.md`

## Why This Pilot Is Safer Than Debug/Executioner

- the file targets are generated artifacts
- the outputs are structure-checkable
- there is no direct runtime behavior change yet
- failure can be rejected without product rollback concerns

## Non-Goals

- no live provider execution
- no fake result JSON generation
- no direct product fix
- no final PASS/BLOCKED release decision
- no production routing

## Next Safe Implementation Step

Build a test-artifact pilot helper that:

- exposes prompt/local/dry-run modes
- binds exact output allowlist paths
- reuses the Sidecar runner `workspace-write` artifact capture
- validates the dry-run path locally before any live write attempt
