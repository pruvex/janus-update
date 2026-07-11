---
name: janus-quickchange
description: Execute a trivial low-risk Janus quick change such as copy replacement, label rename, percentage display, or tightly bounded local polish without sending the request through the full Backlog-to-Spec pipeline. Use only when scope is tiny, acceptance is obvious, and a Mini-TestPlan plus validation evidence can be produced before and after the edit.
---

# Janus Quickchange

## Overview

Use this skill for one tiny bounded change on an existing Janus surface. It is a guarded express lane for edits that would be wasteful in the full pipeline, not a loophole for skipping scope control, evidence, or rerouting.

Default execution model is `5.6 Terra`, low/medium. Stay on warm `5.6 Terra` when possible. Escalate to `janus-backlog-intake`, `janus-feature-design`, or `janus-preimplementation-check` as soon as the change stops being trivial.
This is primarily a Codex execution skill. ChatGPT normally uses its result only when scope grows, risk becomes unclear, or Codex returns a blocked or reroute state.

## Allowed Scope

Typical fits:

- copy replacement, German/English wording cleanup, tooltip or label rename
- percentage, unit, icon, spacing, or small presentation fix
- tiny local UI polish in one component cluster
- deterministic docs or config touch tied to the same bounded intent

All of these must stay true:

- one user-visible intent
- likely one to three touched files in one file cluster
- no new product decision
- no persistence, routing, API, provider, auth, security, privacy, migration, or release-boundary change
- targeted validation is known before editing

## Do Not Use

Stop and reroute when any of these apply:

- a Backlog item should exist for visibility, prioritization, or follow-up tracking
- multiple plausible implementations or product decisions exist
- the change may affect saved state, data shape, backend contracts, or several surfaces
- verification needs a broad test matrix, unclear manual exploration, or a normal precheck
- the user asked for a feature, refactor, test expansion, or architecture change

If two or more reroute signals appear, stop immediately instead of trying to rescue the change as a quickchange.

## Required Input

Start only when you can state this brief up front:

```text
QUICKCHANGE BRIEF
- Request:
- Scope:
- Expected Files:
- Acceptance:
- Why Quickchange:
- Reroute Trigger:
```

If any line is unclear, do not guess broadly. Route out.

## Workflow

1. Read only the directly affected files and the smallest binding context.
2. Emit `QUICKCHANGE BRIEF`.
3. Emit a command-first `MINI TEST PLAN` before edits.
4. Make the smallest possible change set.
5. Run the targeted checks from the plan.
6. If checks fail, fix only inside the brief. Make at most two focused attempts.
7. If scope expands, stop and reroute instead of growing the quickchange.
8. End in exactly one canonical state from the pipeline contract.

If the change remains valid and the same warm Codex context can continue, route directly to `janus-documentation-update` with a compact same-context `NEXT`.
If control must move to ChatGPT, emit exactly one compact fenced `text` handoff block.

## Bounded Delegation Gate

Global delegation vocabulary across Janus is now:

- `1 = Codex`
- `2 = OpenRouter`
- `3 = Cursor Composer`
- `4 = Cursor API`

This skill's bounded `quickchange_patch_review` slice is now wired through the shared manifest-backed `documentation/codex/model-routing/scripts/janus_delegate.py` entry. The visible gate for this lane is currently `1 = Codex` / `2 = OpenRouter` / `4 = Cursor API`; there is not yet a validated Cursor Composer quickchange backend here, so option `3` stays unavailable for this specific slice.

Only this approved bounded quickchange lane should surface a normal delegated choice at the everyday skill entry. Other quickchange helper paths below are separate bounded helpers and must not be read as a generic shared-gate expansion.

Current preferred OR candidate for the bounded `quickchange_patch_review` lane: `qwen/qwen3-coder-30b-a3b-instruct`.

Binding artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\janus_delegate.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_bounded_delegation_dispatcher.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\quickchange_sidecar_write_pilot_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_bounded_delegation_dispatcher_canonical_entry_2026-06-14.md`

Use the shared delegate entry first for review-first quickchanges:

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py --lane quickchange_patch_review --task-id TASK-QC-001 --workflow-id <WORKFLOW-ID> --operator-choice prompt --prompt-path documentation/codex/model-routing/fixtures/examples/quickchange_patch_review_prompt_example.md --editable-path <relative-path> --max-touched-files <N> --estimated-codex-saved-tokens 8000 --estimated-delegation-overhead-tokens 4000
```

Current visible operator gate for this lane:

- `1 = Codex`
- `2 = OpenRouter`
- `4 = Cursor API`

Meaning here:

- `1` keeps the quickchange fully local in Codex.
- `2` routes through the existing bounded OpenRouter quickchange dispatcher path.
- `4` routes through the shared Cursor API bounded review path.

Boundaries stay strict:

- no production routing
- no canonical routing-table update
- no Git or release authority by delegated path
- no auto-apply of delegated patches
- Codex App remains final reviewer and acceptance owner

If the user chooses the OpenRouter path:

- if the user chooses `1`, `local`, or `codex`, stay local in Codex
- if the user chooses `2`, `or`, `opr`, or `openrouter`, the shared delegate currently plans the bounded dispatcher path and hands off to the existing helper chain
- if the user chooses `4`, `cursor-api`, `cursor_api`, or `api`, the shared delegate currently plans the bounded Cursor API review path
- pass the exact `--prompt-path`, `--editable-path` allowlist, and `--max-touched-files` cap that belong to the quickchange brief

Important:

- this OpenRouter quickchange path is still bounded and review-first
- it is not broad write authority
- it is not a general code-generation mode
- it should be used only when the quickchange still satisfies this skill's tiny-scope rules

For tiny file-write quickchanges that already have an accepted bounded source package and must stay inside an exact file allowlist, use the separate `quickchange_write_apply` class:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class quickchange_write_apply --task-label "<short quickchange task>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt --workflow-id <WORKFLOW-ID> --accepted-source-run-dir <accepted-sidecar-run-dir>
```

Meaning there:

- `1` keeps the quickchange fully local in Codex.
- `2` uses the bounded OpenRouter quickchange write-apply acceptance path.

Extra write-apply boundaries:

- delegated write evidence must come from an accepted bounded source run
- Codex still owns diff review, validation review, and final acceptance
- no delete, rename, or move authority is granted by this class
- no fresh broad write delegation starts from this gate alone

Use `quickchange_write_apply` only when:

- the quickchange remains tiny and deterministic
- the accepted source package already proves allowlist, touched-file cap, and delete/rename/move tripwires
- Codex is explicitly acting as final acceptance owner

## Mini Test Plan

Before edits, state:

```text
MINI TEST PLAN
- Scope:
- Files Expected:
- Checks:
- Visual Check:
- N/A Reason:
```

`N/A Reason` is allowed only when the omitted check truly does not apply.

## Validation

Prefer the cheapest real evidence that still proves the change:

- targeted unit test or existing focused test command
- narrow build, lint, or typecheck command
- screenshot, Browser check, or documented manual visual confirmation for local UI-only tweaks
- exact file diff review when the change is pure text/config and runtime validation is genuinely unnecessary

Never claim completion without executed evidence or an explicit documented blocker.

## Reroute Rules

Reroute to:

- `janus-backlog-intake` when the issue deserves tracking or stops being tiny
- `janus-feature-design` when product decisions appear
- `janus-preimplementation-check` when implementation scope is real but still bounded
- `janus-debug` when validation fails for reasons outside the brief

Treat any of these as scope-growth signals:

- more than one user-visible intent
- more than one small file cluster
- hidden backend, persistence, routing, or data-shape impact
- unclear acceptance or unclear validation path
- follow-up work that obviously needs tracking

## CURRENT_STATE Requirement

Before finishing a substantial Janus work block, update `documentation/ai/CURRENT_STATE.md`.

A Janus work block is substantial when at least one of these is true:

- files changed
- validation executed
- a blocker documented
- a formal next-skill handoff produced

Pure routing replies, short status answers, and other mini-interactions do not require a CURRENT_STATE update.

Keep the update concise and include:

- what changed
- which files changed
- which checks ran
- what remains risky or open
- what ChatGPT should review next
- what Codex should do next

CURRENT_STATE does not replace Backlog, Spec, TestSpec, TestRun, TestResult, audit package, or dashboard artifacts.

Commit and push remain gated by `janus-git-governance` and explicit user approval.

If no push happens or push fails, the quickchange result or handoff must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.

## Output Skeleton

```text
QUICKCHANGE RESULT
Canonical State: PASS | BLOCKED | FAILED | HANDOFF | NEEDS_INFO
Request:
Changed Files:
Executed Checks:
Evidence Paths:
Notes:

NEXT_SKILL_HANDOFF
Target Skill: janus-git-governance | janus-backlog-intake | janus-feature-design | janus-preimplementation-check | janus-debug | none
Canonical State: PASS | HANDOFF | BLOCKED | FAILED | NEEDS_INFO
Required Artifacts:
Evidence Paths:
Changed Files:
Decision:
Reason:
Recommended Model:
Recommended Intelligence:
New Chat: yes | no
```

Use `Target Skill: none` only when the quickchange is fully validated and no additional Janus gate is required yet.

If the next step is `janus-documentation-update` in the same warm Codex context, naming `NEXT: janus-documentation-update` is enough.
If control moves to ChatGPT, use exactly one compact fenced `text` block and do not use bare `ok` or prose-only routing as a handoff substitute.
