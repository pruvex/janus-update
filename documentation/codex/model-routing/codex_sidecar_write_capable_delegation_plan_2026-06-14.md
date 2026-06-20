# Codex Sidecar Write-Capable Delegation Plan - 2026-06-14

Status: PLANNING ONLY / NO WRITE-CAPABLE SIDECAR ACTIVATION YET

## Goal

Move beyond the validated read-only Sidecar draft path and define how a Sidecar agent may later perform bounded repo writes while Codex App remains the operator, reviewer, and governance authority.

This plan exists because the real target is not only draft delegation. The real target is:

- saving Codex App quota on workhorse loops
- letting the operator choose between local Codex and delegated worker execution
- allowing the delegated worker to edit files where that is safe and reviewable
- keeping final acceptance, tests, and Git governance with Codex App

## Current Baseline

Already validated:

- file-first Sidecar runner
- timeout-bounded execution
- accepted read-only documentation draft flow
- integrated operator gate for `janus-documentation-update`

Not yet validated:

- write-capable Sidecar runs
- bounded repo diff acceptance
- delete/rename safeguards
- write-capable validation loop
- post-write skill-specific acceptance path

## Core Rule

Write-capable Sidecar delegation is only allowed when all of the following are true:

- a Janus skill has already routed the task
- the task is bounded to one explicit artifact or one explicit file cluster
- the editable path set is declared before execution
- Codex App can validate the result locally after the run
- Codex App can reject the diff without ambiguity
- no Git, release, routing, backlog-state, or final-audit authority is delegated

## Non-Delegable Authority

The Sidecar must not receive authority for:

- `CURRENT_STATE.md`
- Backlog status moves
- central registry completion markers
- final changelog acceptance
- Git add/commit/push/tag/merge
- release/build/publish steps
- final audit decisions
- routing-table changes or production-routing claims

Those remain Codex App only.

## Write-Capable Delegation Levels

| level | meaning |
| --- | --- |
| `WRITE_NONE` | read-only only |
| `WRITE_PATCH_CANDIDATE` | Sidecar may prepare a bounded patch in scoped files; Codex App reviews and may keep or discard it |
| `WRITE_LOCAL_APPLY_CANDIDATE` | Sidecar may write directly into an approved file cluster under `workspace-write`; Codex App must inspect diff and run checks |
| `WRITE_BLOCKED` | keep local to Codex App |

## Recommended Rollout Order

### Phase 1: `janus-quickchange`

Reason:

- smallest real file-write class
- one local intent
- easiest diff review
- easiest rollback

Allowed examples:

- copy replacement
- label rename
- local percentage display
- tiny view-only polish

Required gates:

- max 1 to 3 files
- no persistence, auth, provider, schema, or API contract change
- mandatory before/after validation step
- no deletes or moves

Result:

- best first write-capable Sidecar pilot

### Phase 2: bounded `janus-test-pipeline` artifact writing

Reason:

- useful worker labor
- often mechanical
- lower product risk than direct app logic

Allowed examples:

- draft TestPlan file
- draft test-case block in a bound artifact
- bounded test helper draft in an isolated test file cluster

Required gates:

- explicit artifact target path
- no production code edits in same run
- Codex App reruns validation locally

### Phase 3: bounded `janus-debug` write assistance

Reason:

- debug loops consume heavy quota
- worker can prepare targeted low-risk edits

Allowed examples:

- add temporary instrumentation in a declared file cluster
- adjust test assertions in a bound failing test area
- apply one contained fix attempt from an already approved debug scope

Required gates:

- failure already reproduced locally
- file cluster predeclared
- no broad search-and-edit behavior
- Codex App owns rerun, evidence review, and blocker classification

### Phase 4: bounded `janus-executioner` worker mode

Reason:

- highest potential savings
- highest risk

Allowed examples:

- one prechecked task
- one bounded implementation slice
- one declared file cluster

Required gates:

- valid preimplementation artifact exists
- editable file allowlist declared before run
- diff size cap declared before run
- mandatory local tests after run
- mandatory Codex App acceptance before any documentation closeout

## First Write-Capable Pilot Recommendation

The best first write-capable pilot is:

- skill: `janus-quickchange`
- sandbox: `workspace-write`
- scope: one tiny UI or text correction
- file count target: 1 to 3 files
- forbidden: delete, move, rename, Git commands, package/version changes

This is safer than starting with `janus-executioner` directly and still proves real file-writing under operator control.

## Required Operator Gate For Write-Capable Runs

Future user-facing gate:

```text
CODEX SIDECAR WRITE GATE
- Skill:
- Task:
- 1 = Codex
- 2 = Sidecar
- Sidecar model/provider:
- Sandbox: workspace-write
- Editable paths:
- Diff size cap:
- Validation after run:
- Abort rules:
- User action:
- Boundaries:
```

## Mandatory Abort Rules

Abort or discard the Sidecar result when any of the following happens:

- edit touches a non-allowed path
- file delete/move/rename appears without explicit approval
- diff exceeds declared cap
- the Sidecar claims completion without a reviewable diff
- required validation fails locally
- the output attempts Git, release, backlog-state, or routing authority

## Required Artifacts For Every Write-Capable Run

The runner path should preserve at minimum:

- `prompt.md`
- `command.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `last_message.md`
- `event_stream.jsonl`
- `summary.json`
- `git_diff.patch`
- `changed_files.txt`
- `validation_summary.json`

## Acceptance Flow

1. Codex App routes the task.
2. Codex App shows the write-capable operator gate.
3. User chooses `1` or `2`.
4. If `2`, Sidecar runs in `workspace-write` only within approved scope.
5. Codex App inspects changed files and diff size.
6. Codex App runs required local validation.
7. Codex App either:
   - accepts the result,
   - revises locally,
   - or rejects and rolls forward with Codex-only handling.

## What This Is Not

- not production routing
- not global OpenRouter approval
- not automatic multi-agent execution
- not unsupervised repo editing
- not a Git automation bypass

## Next Safe Build Step

Prepare a `workspace-write` Sidecar runner extension plus a `janus-quickchange` pilot plan with:

- editable path allowlist
- diff capture
- delete/rename detection
- validation command capture
- explicit reject/discard flow
