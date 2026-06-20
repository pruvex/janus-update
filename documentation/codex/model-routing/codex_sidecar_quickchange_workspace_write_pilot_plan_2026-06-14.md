# Codex Sidecar Quickchange Workspace-Write Pilot Plan - 2026-06-14

Status: PLANNING ONLY / NO LIVE WRITE-CAPABLE SIDECAR RUN YET

## Purpose

Define the first real write-capable Sidecar pilot using `janus-quickchange`.

This pilot is the bridge between:

- validated read-only Sidecar draft delegation
- future bounded repo-writing worker delegation

The goal is to prove that a delegated worker can make one tiny local file change under explicit operator choice while Codex App still owns:

- routing
- scope control
- diff review
- validation
- acceptance or rejection

## Why `janus-quickchange`

`janus-quickchange` is the safest first write-capable pilot because:

- the task is tiny by contract
- the change surface is limited to one intent
- expected files are usually 1 to 3
- validation can be cheap and explicit
- reroute conditions are already well-defined

## Pilot Scope

Allowed first-pilot change types:

- copy replacement
- label rename
- tooltip wording change
- tiny presentation-only UI text or percentage fix

First pilot constraints:

- one user-visible intent only
- one file cluster only
- expected file count declared up front
- max 3 touched files
- no delete, move, or rename
- no package/version files
- no backend/provider/persistence/API/auth/security/privacy files

## Required Pre-Run Brief

Before any future live Sidecar write attempt, Codex App must produce:

```text
QUICKCHANGE BRIEF
- Request:
- Scope:
- Expected Files:
- Acceptance:
- Why Quickchange:
- Reroute Trigger:
```

And:

```text
MINI TEST PLAN
- Scope:
- Files Expected:
- Checks:
- Visual Check:
- N/A Reason:
```

If either cannot be stated cleanly, the pilot must not run.

## Required Operator Gate

Future live gate:

```text
CODEX SIDECAR WRITE GATE
- Skill: janus-quickchange
- Task:
- 1 = Codex
- 2 = Sidecar
- Sidecar model/provider:
- Sandbox: workspace-write
- Editable paths:
- Max touched files:
- Diff size cap:
- Validation after run:
- Abort rules:
- User action:
- Boundaries:
```

## Editable Path Allowlist

The live pilot must declare an explicit allowlist before execution.

Recommended first format:

- exact file paths, or
- one exact directory plus named file list

Not allowed:

- broad repo-wide globs
- mixed frontend and backend clusters
- generated artifacts
- docs + code mixed unless the quickchange intent explicitly requires both

## Diff Capture Requirements

A future write-capable runner path must capture:

- `git_diff.patch`
- `changed_files.txt`
- `pre_run_status.txt`
- `post_run_status.txt`

Codex App acceptance must compare:

- actual changed files vs allowlist
- actual file count vs declared cap
- actual diff size vs declared cap

## Delete / Rename Tripwire

The future live pilot must fail immediately if the diff contains:

- deleted files
- renamed files
- moved files

unless the user explicitly approved that exact behavior beforehand.

Default first-pilot rule:

- delete = forbidden
- rename = forbidden
- move = forbidden

## Validation Capture

Every live pilot must preserve:

- validation command list
- validation stdout/stderr
- validation return codes
- `validation_summary.json`

Allowed validation for first pilot:

- exact diff review only, if the change is pure text and runtime validation is genuinely unnecessary
- one focused UI/manual validation note for a presentation-only change
- one narrow command if the touched surface already has a cheap focused check

## Reject / Discard Flow

Codex App must reject the Sidecar result when any of the following occurs:

- changed file outside allowlist
- touched file count exceeds cap
- diff size exceeds cap
- delete/rename/move appears
- validation fails
- Sidecar drifts outside quickchange scope
- Sidecar output makes governance, Git, release, routing, or backlog claims

Reject behavior:

- keep artifacts
- do not accept the edit as final
- either reroute to Codex-only quickchange or to the proper upstream Janus skill

## Proposed Artifact Set For First Live Pilot

- `prompt.md`
- `command.json`
- `stdout.log`
- `stderr.log`
- `exit_code.txt`
- `last_message.md`
- `event_stream.jsonl`
- `summary.json`
- `pre_run_status.txt`
- `post_run_status.txt`
- `git_diff.patch`
- `changed_files.txt`
- `validation_stdout.log`
- `validation_stderr.log`
- `validation_summary.json`
- `pilot_result.md`

## Live Pilot Sequence

1. Route a real tiny request into `janus-quickchange`.
2. Bind exact scope and expected files.
3. Show `CODEX SIDECAR WRITE GATE`.
4. If the user selects `2`, run the Sidecar under `workspace-write`.
5. Capture diff and changed-file list.
6. Enforce delete/rename/touched-file caps.
7. Run declared validation locally in Codex App.
8. Accept or reject locally.
9. Update `CURRENT_STATE.md` with truthful pilot outcome.

## Explicit Non-Goals

- no live write-capable Sidecar run in this planning step
- no production routing
- no OpenRouter global approval
- no Git automation delegation
- no automatic scaling to debug/executioner yet

## Next Safe Implementation Step

Build a runner/helper extension for `janus-quickchange` that can:

- invoke `workspace-write`
- take an editable-path allowlist
- save pre/post git status
- save a patch file
- fail on delete/rename/move
- write a machine-readable validation summary
