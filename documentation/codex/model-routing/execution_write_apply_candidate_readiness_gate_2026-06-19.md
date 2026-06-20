# Execution Write Apply Candidate Readiness Gate - 2026-06-19

Status: READINESS CHECK / NO LIVE WRITE ACTIVATION / NO PRODUCTION ROUTING

## Purpose

This note answers one concrete workflow question:

- what is still missing before the first real bounded `execution_write_apply_candidate` live pilot should be allowed?

It is intentionally narrower than the original class plan.
It does not redesign the class.
It turns the current evidence into a concrete go / not-yet-go gate.

## Current Position

The bounded OR worker stack is now split into three relevant layers:

1. `quickchange_write_apply`
2. `execution_patch_candidate`
3. `execution_write_apply_candidate`

Current working position:

- `quickchange_write_apply` already has accepted bounded live write evidence
- `execution_patch_candidate` now has a preferred OR proposal worker:
  - `deepseek/deepseek-v4-flash`
- `execution_write_apply_candidate` has a validated local foundation, but it is not yet live-ready

## What Already Exists

### Planning Layer

Binding plan:

- `documentation/codex/model-routing/codex_execution_write_apply_candidate_plan_2026-06-14.md`

That plan already defines:

- bounded scope
- workspace-write only
- explicit allowlist
- touched-file cap
- diff capture
- changed-files capture
- validation capture
- Codex-owned accept or reject authority

### Local Helper Layer

Validated helper path:

- `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
- `documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py`
- `documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py`
- `documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py`

This means the class is no longer only abstract.
It already has:

- prompt-mode operator gate support
- local choice support
- delegated candidate-source validation
- artifact-presence validation
- Codex-owned acceptance wording

### Dispatcher Layer

Shared bounded dispatcher already knows this class:

- `documentation/codex/model-routing/config/bounded_or_worker_eligibility_2026-06-17.json`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-EXECUTION-WRITE-APPLY-DISPATCH-LIVE-001/dispatcher_result.json`

Current dispatcher-facing state:

- eligibility result: `OR_ALLOWED`
- evidence status: `BOUNDED_AUDITED_FOUNDATION`
- delegated outcome: `EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_LATER_LIVE_PILOT`

This is important:

- the class is entry-validated
- the class is not yet live-approved

## What Is Missing Before A First Live Pilot

### Gate 1: Repeated Accepted Proposal-First Evidence

The class plan requires repeated accepted proposal-first execution evidence before live writes.

For the OR-worker-oriented path, the current direct OR larger-class preferred evidence is:

- accepted:
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002`
  - `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006`
- not accepted:
  - `DIRECT-OR-QWEN-EXECUTION-LIVE-001`

Working interpretation:

- direct OR accepted larger-class proposal evidence count for the preferred worker is now effectively `2`
- the second accepted point now includes one real compact-contract success on another prechecked slice using the same preferred worker family

Result:

- Gate 1 = SATISFIED

### Gate 2: Exact Pilot Slice Selection

No first live `execution_write_apply_candidate` pilot slice is currently bound.

Still missing:

- one exact prechecked task slice
- one exact file cluster
- touched-file cap declared before execution
- local validation bundle declared before execution

Result:

- Gate 2 = NOT YET SATISFIED

### Gate 3: OR Worker Choice Lock

For the larger proposal-first class we now have a clear preferred worker:

- `deepseek/deepseek-v4-flash`

That removes the previous model ambiguity for the next readiness step.

Result:

- Gate 3 = SATISFIED

### Gate 4: Codex-Owned Acceptance Chain

The class still preserves:

- Codex diff review
- Codex validation review
- Codex accept or reject authority
- no delegated final task completion claim

Result:

- Gate 4 = SATISFIED

## Readiness Summary

| Gate | Status | Note |
| --- | --- | --- |
| planning artifact exists | PASS | class definition already exists |
| helper / runner foundation exists | PASS | local helper path and tests exist |
| dispatcher entry exists | PASS | bounded dispatcher already recognizes the class |
| preferred OR worker for larger proposal-first class is clear | PASS | DeepSeek is the current preferred candidate |
| second accepted direct OR larger-class proposal run exists | PASS | `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-002` plus `DIRECT-OR-DEEPSEEK-EXECUTION-LIVE-006` are now both bound |
| first live write pilot slice is explicitly bound | FAIL | no exact live pilot slice selected yet |
| live write activation approved | FAIL | no approval and not enough upstream evidence yet |

## Working Decision

Do not start a live `execution_write_apply_candidate` pilot yet.

The next safe step is:

1. bind one exact prechecked pilot slice for `execution_write_apply_candidate`
2. declare the exact file cluster, touched-file cap, and validation bundle up front
3. open the first write-capable live pilot plan only inside those bounded gates

## What This Does Not Mean

- no production routing
- no canonical routing-table update
- no global DeepSeek approval
- no live write authority yet
- no broad repo write delegation
