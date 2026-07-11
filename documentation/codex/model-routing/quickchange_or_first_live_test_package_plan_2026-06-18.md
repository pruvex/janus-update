# Quickchange OR First Live Test Package Plan - 2026-06-18

Status: PLANNING ONLY / NO LIVE OR CALLS / NO PRODUCTION ROUTING / NO CANONICAL ROUTING-TABLE UPDATE

## Purpose

Prepare the first real bounded OpenRouter live test package for:

- skill: `janus-quickchange`
- bounded class: `quickchange_patch_review`

This step does not run the live call yet.

## Confirmed Execution Shape

The current quickchange path already supports delegated OpenRouter-style model selection through the bounded sidecar runner path:

- `codex_bounded_delegation_dispatcher.py`
- `quickchange_sidecar_write_pilot_runner.py`
- `codex_sidecar_skill_runner.ps1`

Important confirmed behavior:

- operator aliases already accept `2`, `or`, and `openrouter`
- delegated quickchange patch-review runs under `workspace-write`
- exact editable-path allowlists are already enforced
- touched-file caps are already enforced
- delete/rename/move tripwires are already enforced
- Codex remains final reviewer and acceptance owner

## First Live Test Goal

Prove that one tiny real `janus-quickchange` patch-review task can be sent through the bounded OpenRouter path with:

- explicit operator choice
- explicit selected OR model
- explicit estimated cost
- explicit confidence display
- exact file allowlist
- exact touched-file cap
- clean Codex-owned accept/reject outcome

## First Fixed-Model Order

Use the fixed shortlist from:

- `documentation/codex/model-routing/quickchange_or_fixed_candidate_shortlist_2026-06-18.md`

Run order for the first real quickchange evidence corridor:

1. `openai/gpt-oss-20b`
2. `openai/gpt-oss-120b`
3. `qwen/qwen3-30b-a3b-instruct-2507`

Second-wave backups only if needed later:

4. `qwen/qwen3.5-flash-02-23`
5. `deepseek/deepseek-v4-flash`

## Recommended First Task Shape

The first live test should be a real tiny quickchange with all of these properties:

- one user-visible copy or label change only
- one file only if possible
- frontend-only or documentation-only cluster
- no backend/provider/persistence/API/auth/security/privacy impact
- no package/version file
- no delete/rename/move

Best first live target profile:

- one small copy change in `frontend/index.html` or a comparable single frontend file
- max touched files: `1`
- diff size: tiny text-only diff

Fallback if no suitable real UI quickchange is available immediately:

- use the next genuine tiny copy/label quickchange that naturally appears in everyday work
- do not invent a broader synthetic coding task just to force the first OR run

## Required Operator Gate

The first prompt gate should show:

- `1 = Codex`
- `2 = OpenRouter`
- selected OR model
- estimated OR cost
- confidence percent
- exact editable path
- max touched files
- validation path

The displayed user question should stay aligned with the bounded worker gate wording:

`Willst du 1 Codex das machen lassen oder 2 das mit OpenRouter machen lassen (voraussichtliche Kosten X, Genauigkeit Y%)?`

## Required Inputs Before The First Live Run

Before the first live run, prepare:

### Quickchange brief

```text
QUICKCHANGE BRIEF
- Request:
- Scope:
- Expected Files:
- Acceptance:
- Why Quickchange:
- Reroute Trigger:
```

### Mini test plan

```text
MINI TEST PLAN
- Scope:
- Files Expected:
- Checks:
- Visual Check:
- N/A Reason:
```

### Bounded prompt package

At minimum:

- `prompt.md`
- exact request text
- explicit allowlist path
- explicit file cap
- explicit reject rules

## Recommended First Dispatcher Command Shape

Prompt gate first:

```powershell
python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py ^
  --task-class quickchange_patch_review ^
  --task-label "<tiny quickchange label>" ^
  --normal-target-model "5.4/medium" ^
  --operator-choice prompt ^
  --workflow-id <WORKFLOW-ID> ^
  --editable-path <relative-file-path> ^
  --max-touched-files 1 ^
  --selected-or-model openai/gpt-oss-20b ^
  --estimated-or-cost <estimated_cost> ^
  --cost-estimate-confidence-percent <confidence_percent>
```

If the operator chooses `2`, the corresponding delegated run should use:

- `--operator-choice delegated`
- `--prompt-path <bounded prompt path>`

## First Cost Guardrails

For the first quickchange evidence run:

- per-call soft target: as low as reasonably possible
- hard per-call stop rule: do not run if the estimate is unexpectedly high for a tiny one-file quickchange

Practical rule for the first run:

- if `openai/gpt-oss-20b` estimate looks normal for a tiny one-file prompt, test it first
- if the estimate is anomalous, stop and inspect prompt/package size before making the call

## Acceptance Criteria For The First Live Run

The first quickchange OR live run counts as accepted evidence only if all are true:

- response artifacts are captured
- changed file stays inside allowlist
- touched-file count stays within cap
- delete/rename/move tripwire stays clean
- Codex review says the patch is in-scope and acceptable
- local validation completes
- final outcome stays Codex-owned

## Reject / Fallback Conditions

Reject or fall back immediately if any of these happen:

- changed file outside allowlist
- more files than declared
- delete/rename/move appears
- output drifts outside quickchange scope
- patch quality is weak enough that Codex would need broad rewrite
- validation fails
- run artifacts are incomplete

## Auto Router Boundary

Do not use Auto Router for this first quickchange live test.

Reason:

- we need first clean fixed-model evidence
- we want cost and quality attribution per exact model
- Auto Router would make the first quickchange evidence harder to interpret

## Next Safe Step

Prepare the first real bounded quickchange request package for:

- `quickchange_patch_review`
- model `openai/gpt-oss-20b`
- one exact editable file
- touched-file cap `1`

Only after that package is ready should the user be asked to approve the first live OpenRouter quickchange run.
