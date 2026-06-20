# Codex Bounded Delegation Plan - execution_patch_candidate - 2026-06-14

Status: LOCAL VALIDATION PLAN

## Purpose

This artifact defines the first bounded `execution_patch_candidate` class for `janus-executioner`.

The class is deliberately proposal-first:

- no delegated final apply
- no delegated test execution
- no delegated task completion claim
- no delegated audit or release authority

Its goal is to let the operator choose whether one prechecked execution slice stays fully in Codex or uses a bounded delegated patch-candidate review path that still ends in Codex-owned diff review, validation ownership, and final acceptance or rejection.

## Owning Skill

- `janus-executioner`

## Recommended Bounded Mode

- `SIDECAR_ASSIST_ONLY`

This first slice does not create broad write authority.
It creates a bounded patch-candidate contract that can later become the evidence base for a much smaller write pilot.

## Input Contract

The delegated input package must be fully bound to one prechecked task slice and must include:

- `workflow_id`
- `bound_skill_context`
- `target_task`
- `spec_path`
- `precheck_status`
- `allowed_files`
- `max_touched_files`
- `mini_test_plan`
- `manual_validation_gate`
- `delegation_question`

Hard gates:

- `precheck_status` must be exactly `PRE-CHECK PASSED`
- `allowed_files` must be non-empty
- `max_touched_files` must be a positive integer
- `manual_validation_gate` must stay present even though delegated flow cannot satisfy it

## Delegated Output Contract

The delegated result must stay proposal-only and include:

- `status`
- `target_task`
- `patch_text`
- `changed_files`
- `risk_list`
- `suggested_validation_steps`
- `manual_validation_note`
- `codex_acceptance_rule`
- `notes`

Hard result gates:

- `status` must be `PASS`, `WEAK_SIGNAL`, or `BLOCKED`
- `patch_text` must be unified diff text
- every changed file in the diff must stay inside `allowed_files`
- changed file count must be `<= max_touched_files`
- `manual_validation_note` must explicitly keep manual Janus validation with Codex
- `codex_acceptance_rule` must explicitly state that Codex decides whether to apply or reject

## Operator Gate

Prompt mode must stay identical to the shared operator model:

- `1 = Codex`
- `2 = Delegated`

Meaning:

- `1` keeps the execution slice fully local in Codex.
- `2` uses the bounded `execution_patch_candidate` review path.

## Codex-Owned Acceptance

Even on delegated success, Codex still owns:

- artifact binding review
- patch review
- local validation ownership
- apply or reject decision
- manual Janus validation gate
- final `janus-executioner` completion state

The delegated path may suggest a bounded patch, but it may not claim:

- `TASK COMPLETE`
- `PASS` for product validation
- final audit readiness
- Git or release readiness

## Fallback Rules

Fallback to Codex-only immediately when:

- precheck binding is incomplete
- diff escapes the allowed file cluster
- changed file count exceeds the cap
- patch text is malformed
- risk list is missing
- suggested validation steps are weak or absent
- manual validation ownership is not preserved

## Evidence Needed In This First Slice

For local workflow-ready validation:

- prompt gate `PASS`
- local path `PASS`
- delegated fixture validation `PASS`
- dispatcher delegated validation `PASS`

Before any future live write pilot:

- at least 2 accepted proposal-only runs on real prechecked task slices
- then only 1 tiny bounded write pilot under a stricter derivative class

## Explicit Non-Goals

- no production routing
- no canonical routing-table update
- no broad repo write authority
- no delegated test execution
- no delegated final apply
- no delegated task completion claim
- no Git, release, or audit authority

## Recommended Next Step

Implement a bounded local-validation helper plus dispatcher slice using fixture-backed input/result packages, then wire the class into the repo and installed `janus-executioner` skill guidance only after validation passes.
