# Codex Bounded Delegation Plan - execution_write_apply_candidate - 2026-06-14

Status: PLANNING ONLY / NO LIVE WRITE ACTIVATION YET

## Purpose

This artifact defines the next safe follow-up after `execution_patch_candidate`.

The intent is not to skip directly into broad `janus-executioner` write authority.
The intent is to define one derivative bounded write candidate that can exist only after:

- proposal-first execution patch review is routine
- one prechecked slice stays narrow enough for exact file-cluster control
- Codex App still owns validation, apply/reject, and final task completion

## Decision

The next bounded build step after `execution_patch_candidate` should be:

- plan a derivative `execution_write_apply_candidate`

The next bounded build step should **not** be:

- immediate return to `test_artifact_write_runner_level`

## Why This Comes Next

Reasons:

- `execution_patch_candidate` is now locally workflow-ready as a proposal-first class
- it already establishes the needed artifact binding, file allowlist, touched-file cap, and Codex-owned acceptance rule
- the blocked `test_artifact_write_runner_level` class still lacks runner-owned command execution support
- the remaining blocker for test-artifact writing is infrastructure reliability, not operator-model design

## Why Test-Artifact Runner-Level Work Does Not Come Next

Even though test artifacts are lower product risk than direct product code, the next immediate problem there is different:

- three bounded live failures already showed prompt-level command steering is not enough
- the class now needs runner-owned command templates before new bounded live attempts are worthwhile
- that means the next step there is infrastructure hardening, not normal bounded-class expansion

So the clean order is:

1. keep `test_artifact_write_runner_level` paused
2. plan the derivative execution write candidate
3. only revisit the test-artifact path after runner-level execution support is intentionally added

## Proposed Derivative Class

Class name:

- `execution_write_apply_candidate`

Owning skill:

- `janus-executioner`

Recommended bounded mode:

- `SIDECAR_WRITE_CANDIDATE`

## Planned Operator Outcome

The operator should eventually see the normal bounded gate:

- `1 = Codex`
- `2 = Delegated`

Meaning in this derivative class:

- `1` keeps the prechecked execution slice fully local in Codex.
- `2` allows one bounded delegated write attempt inside a predeclared file cluster under `workspace-write`.

This class must remain narrower than normal execution:

- one target task slice only
- one explicit file cluster only
- one explicit validation bundle only
- one Codex acceptance decision only

## Live Entry Contract

Before a live derivative write attempt is even allowed, the bound input package should include:

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
- `codex_apply_rule`

Hard entry rules:

- `precheck_status` must be exactly `PRE-CHECK PASSED`
- `allowed_files` must be non-empty and exact
- `max_touched_files` must be declared before execution
- `mini_test_plan` must already contain real local checks
- `manual_validation_gate` must remain explicitly Codex-owned
- `codex_apply_rule` must preserve Codex final apply or reject authority

## Planned Delegated Output Contract

The delegated live result should be accepted only when all of these exist:

- `summary.json`
- `last_message.md`
- `git_diff.patch`
- `changed_files.txt`
- `validation_summary.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`

The operator-facing summary should normalize at least:

- `status`
- `target_task`
- `selected_path`
- `changed_files`
- `allowlist_ok`
- `touched_file_cap_ok`
- `delete_rename_move_ok`
- `validation_result`
- `final_outcome`
- `operator_message`

## Required Write Gates

Compared with proposal-first mode, this derivative class must satisfy all of these additional live gates:

- exact editable-path allowlist in runner invocation
- exact touched-file cap enforcement
- delete/rename/move tripwire
- diff capture always on
- changed-files capture always on
- local validation capture always on
- forced fallback to Codex-only when any capture artifact is missing

## Planned Abort Rules

Abort or discard the delegated result immediately when any of the following happens:

- a changed file escapes the declared allowlist
- changed file count exceeds the cap
- delete, rename, or move activity appears
- no reviewable diff is captured
- validation artifacts are missing
- validation fails locally
- the sidecar claims task completion, audit readiness, or Git/release authority

## Codex-Owned Acceptance Flow

The derivative class must preserve this sequence:

1. `janus-executioner` binds exactly one prechecked task slice.
2. Codex shows the bounded operator gate.
3. The user chooses `1` or `2`.
4. If `2`, the sidecar runs in `workspace-write` inside the declared allowlist only.
5. Codex inspects `changed_files.txt` and `git_diff.patch`.
6. Codex reads `validation_summary.json`.
7. Codex either:
   - accepts and continues with the normal execution flow,
   - revises locally,
   - or rejects and rolls forward with Codex-only handling.

Even on accepted delegated writes, Codex still owns:

- the Mini-TestPlan
- the local validation interpretation
- the manual Janus validation gate
- the final `janus-executioner` completion state

## First Safe Pilot Shape

The first later live pilot should stay very small:

- 1 to 2 touched files
- UI copy, local presentation logic, or tiny non-architectural backend refinement only
- no schema or migration work
- no provider-routing changes
- no persistence-shape changes
- no security/privacy/auth boundary
- no release-bound files

## Explicit Stop Conditions

Do not move this derivative class to live validation yet when any of these remain true:

- fewer than 2 accepted real proposal-only `execution_patch_candidate` runs exist
- the sidecar runner does not reliably preserve diff and validation artifacts
- the target slice needs more than one file cluster
- the required validation path is broad or unclear
- the work would need a second task or architecture decision

## Relationship To execution_patch_candidate

`execution_patch_candidate` remains the proving ground.

Its purpose now is to generate the evidence needed for this derivative class:

- repeated proposal quality
- repeated allowlist discipline
- repeated Codex-owned acceptance

This means:

- do not skip proposal-first evidence
- do not infer live write approval from local fixture validation alone
- do not silently merge the proposal-first and write-capable classes

## Strict Entry Preconditions

This derivative class should be valid only when all are true:

- one real `janus-preimplementation-check` handoff is bound
- one exact target task slice is bound
- one exact file-cluster allowlist is declared before execution
- touched-file cap is declared before execution
- required local checks are already known before execution
- Codex can reject or roll forward locally without ambiguity

## Required Additional Gates Beyond execution_patch_candidate

Compared with proposal-first mode, the write candidate must add:

- exact editable-path allowlist for live write mode
- exact touched-file cap enforcement at runner level
- delete/rename/move tripwire
- mandatory post-run diff capture
- mandatory validation capture
- explicit Codex reject/discard path when validation is incomplete

## Non-Goals

- no broad repo writes
- no multi-task execution
- no delegated test execution
- no delegated final task completion claim
- no delegated audit package authority
- no Git, release, or routing authority
- no production routing
- no canonical routing-table update

## Evidence Needed Before Any Live Write Attempt

Before a live derivative execution write pilot:

- at least 2 accepted proposal-only `execution_patch_candidate` runs on real prechecked slices
- 0 allowlist escapes
- 0 touched-file-cap escapes
- 0 ambiguity on Codex apply/reject ownership

## First Recommended Live Slice Later

When the derivative class is eventually live-tested, the first slice should be:

- one tiny prechecked UI or narrow backend refinement
- 1 to 2 files
- no schema change
- no provider boundary change
- no persistence migration
- no auth, security, or release boundary

## Relationship To test_artifact_write_runner_level

`test_artifact_write_runner_level` remains important, but it is now an infrastructure track.

That track should resume only after a separate runner-owned command-support step produces:

- deterministic command templates
- exact output-path enforcement
- post-generation validator capture
- at least one dry-run runner-owned success

## Recommended Next Safe Build Step

Create a planning artifact for the derivative execution write candidate only.

Do not start live writes yet.
Do not resume the blocked test-artifact write class yet.
