---
name: janus-documentation-update
description: Synchronize Janus documentation after a passed final audit, resolved debug gate, completed Backlog item, completed Spec implementation, or green TestSpec/TestRun validation. Use when the user asks to close work, update docs, record evidence, mark Backlog DONE, update dashboard, changelog, project state, central registry, WHAT_I_LEARNED, or prepare for build/release after validation.
---

# Janus Documentation Update

## Overview

Use this skill after validation passed. Persist the result into Janus documentation, and when the user is preparing a release or release readiness, include the version bump as part of the same documentation checkpoint. Do not implement product code, change architecture, hide failed validation, or run release commands.

Primary actor is shared:

- ChatGPT uses this skill to review scope, decide which documentation artifacts must change, and prepare compact handoffs.
- Codex uses this skill to perform the actual bounded documentation edits, validations, and closeout sync.

Stay in the same Codex context when the validated marker, evidence bundle, and documentation scope are already bound and no actor change is needed.

If control must move across an actor or chat boundary, emit exactly one compact fenced `text` handoff block. Do not use bare acknowledgements like `ok` as a handoff substitute.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 7 – DOKUMENTATIONSUPDATE.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

## Documentation Skill Model-Switch Gate

The canonical model-routing reference for documentation-skill work is:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\documentation_skill_routing_table_v1_2026-06-12.md`

Before doing documentation-skill work, classify the request against the routing table's `DOC-SKILL-*` rows. Use the table's `minimal_local_model_reasoning`, `safe_scope`, `blocked_scope`, `OR_eligibility`, `required_upstream_skill_path`, and `final_status` columns as the binding reference for documentation-skill model and authority boundaries.

Treat the current Codex model and reasoning level as user-declared, not self-detected. If `DECLARED CODEX MODEL` is missing, stop before deciding sufficiency and ask the user to provide or confirm the selected model and reasoning level.

If the declared Codex model or reasoning level is insufficient for the matching documentation task, stop before editing or validating and tell the user exactly which model and reasoning level to select. Continue only after the user confirms the selection or explicitly instructs Codex to stay in the current setup.

Use this gate format:

```text
DOCUMENTATION SKILL MODEL SWITCH GATE
- Documentation task:
- Declared model/reasoning:
- Required model/reasoning:
- User action:
- Reason:
```

Do not switch models automatically. Do not enable production routing. OpenRouter remains disabled for routing and production decisions except for the bounded fixed-model operator-choice path described below. Auto Router remains disabled.

If the routing table marks any requested scope as blocked or upstream-owned, do not solve it inside this skill. Route to the required upstream Janus skill path first, then return to `janus-documentation-update` only after the upstream decision, audit, validation, or approval evidence exists.

## Bounded Fixed OR Operator Choice

For real-world documentation-skill testing, this skill may offer one bounded `local` versus fixed `or` choice only when all of the following are true:

- the classified row is exactly one of `DOC-SKILL-001`, `DOC-SKILL-002`, `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, `DOC-SKILL-009`, or `DOC-SKILL-010`
- the normal target remains `GPT-5.4 mini`
- the request stays inside documentation-skill safe scope
- the request does not drift into release, git-governance, canonical routing-table, production routing, `DOC-SKILL-011`, `DOC-SKILL-012`, or broader `5.4` candidate work

Binding implementation artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\config\doc_skill_mini_fixed_or_live_enabled_2026-06-13.json`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\doc_skill_mini_fixed_or_live_runner.py`

When the task is eligible, first run the runner in prompt mode and use its output as the operator gate:

```powershell
python documentation/codex/model-routing/scripts/doc_skill_mini_fixed_or_live_runner.py --skill-id <DOC-SKILL-XXX> --normal-target-model "<declared model/reasoning>" --task-intent documentation_skill --operator-choice prompt
```

Then present this exact user-facing gate:

```text
FIXED OR OPERATOR CHOICE
- Documentation task:
- Skill ID:
- 1 = Codex
- 2 = OpenRouter
- Selected OR model:
- Voraussichtliche Kosten:
- Genauigkeit:
- User action:
- Boundaries:
```

Gate rules:

- if the user chooses `1`, `local`, or `codex`, invoke the same runner with `--operator-choice local`
- if the user chooses `2`, `or`, `opr`, or `openrouter`, invoke the same runner with `--operator-choice or`
- if the user already explicitly requested `local` or fixed `or` for an eligible task, you may skip the extra wait and invoke the runner directly
- if prompt mode or the follow-up invocation returns a pre-wrapper abort or Codex-only fallback, do not force OR; continue with local Codex handling or `Manual-review` according to the result
- use `--use-local-fixture` only for bounded validation work, never for live everyday operator choice

Forbidden inside this path:

- Auto Router
- dynamic model substitution outside the fixed config
- any OR use for out-of-scope documentation skills
- any claim that this is production routing or global OR approval

## Bounded Sidecar Draft Operator Choice

For normal documentation-update workflow use, this skill may offer one bounded `Codex` versus `Sidecar` choice only when all of the following are true:

- the request is inside documentation-skill safe scope
- the work is a non-binding draft, summary, milestone note, changelog draft, or handoff draft
- no release, git-governance, final audit, canonical routing-table, production routing, backlog move, registry write, or `CURRENT_STATE` authority is being delegated
- the sidecar can stay `read-only`

Binding implementation artifacts:

- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\codex_sidecar_skill_runner.ps1`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\scripts\doc_skill_sidecar_draft_runner.py`
- `C:\KI\Janus-Projekt\documentation\codex\model-routing\codex_sidecar_agent_live_pilot_result_2026-06-14.md`

When the task is eligible, first run the helper in prompt mode and use its output as the operator gate:

```powershell
python documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py --task-label "<short documentation draft task>" --normal-target-model "<declared model/reasoning>" --operator-choice prompt
```

Then present this exact user-facing gate:

```text
CODEX SIDECAR DELEGATION GATE
- Skill:
- Task:
- 1 = Codex
- 2 = Sidecar
- Sidecar model/provider:
- Sandbox:
- Estimated cost/quota impact:
- Expected delegation value:
- Codex App review after sidecar:
- User action:
- Boundaries:
```

Gate rules:

- if the user chooses `1`, `local`, or `codex`, invoke the same helper with `--operator-choice local`
- if the user chooses `2` or `sidecar`, invoke the same helper with `--operator-choice sidecar --prompt-path <bounded prompt path>`
- keep sidecar runs `read-only` unless a later explicit validation artifact proves a write-capable path is safe
- Codex App must review the returned draft and perform any binding documentation writes locally
- do not treat a sidecar draft as authoritative state

Forbidden inside this path:

- sidecar file writes
- sidecar Git commands
- sidecar release or routing decisions
- sidecar updates to `CURRENT_STATE`, backlog sections, registries, changelog acceptance, or final completion markers

## Required Gate

Proceed only when one is true:

- Final audit result is `PASS` or `PASS WITH FIXES`.
- Test pipeline completion input has `CompletionAction=RECORD_TEST_PIPELINE_PASS_AND_SYNC_DOCUMENTATION` and valid PASS evidence.
- The user provides a green validation package with concrete evidence paths.

Block if:

- final audit is `BLOCKED`, `FAILED`, or missing
- manual Janus test failed and debug gate is unresolved
- Skill 5/debug returned `ESCALATION REQUIRED`, `BLOCKED`, or `OUT OF SCOPE`
- required evidence paths are missing
- version files are inconsistent and cannot be parsed

## Context Budget

Documentation update should be marker-scoped, not history-scoped. Resolve only:

- `documentation/ai/CURRENT_STATE.md` when this is a substantial Janus work block
- final audit result or green validation package
- target marker such as `BACKLOG-XXX`, `SPEC-XX`, or `TEST-RUN-XXX`
- files that must carry that marker
- exact evidence paths needed for validation

Do not reread old specs, execution chatter, or unrelated DONE backlog history when the marker package already identifies the required updates.

Do not treat local installed skills under `C:\Users\pruve\.codex\skills\` as repo skill sources. This skill operates on repo artifacts only unless the user explicitly requests otherwise.

## Allowed Edits

- append audit trail to task or Spec files
- update `documentation/01_CENTRAL_TASK_REGISTRY.md`
- update `PROJECT_STATE.md`
- update `CHANGELOG.md` when product/user-facing/docs behavior changed
- update `WHAT_I_LEARNED.md` for reusable patterns, root causes, tripwires, and fix rules
- update `documentation/pipeline/TEST_PIPELINE_RUN_LOG.md`
- update TestSpec `## Latest Pipeline Validation`
- move completed Spec to `documentation/SPEC/Spec Done/`
- move completed Backlog item to `## DONE` exactly once
- update `documentation/backlog/BACKLOG.md`
- run `npm run sync:backlog` in `C:\KI\Janus-Projekt\janus-dashboard` after Backlog edits
- remove resolved temporary `.windsurf/tmp/skill5_*` or `skill6_*` handoff files only when clearly temporary

## Forbidden Edits

- product implementation changes
- architecture redesign
- provider fallback behavior
- production release commands
- placeholder completion versions like `CURRENT`, `TBD`, `Unreleased`, or `unknown` when a concrete version is parseable
- duplicate Backlog items across active and DONE sections
- silent skips of central registry, project state, changelog, or dashboard sync

## Versioning For Release Prep

Version bumps belong here, not in `janus-build-release`.

When the user asks to prepare a Janus release or Electron auto-update release, update version metadata only after the validated work is documented and the release intent is clear.

Rules:

- Default channel is the existing channel from `package.json` such as `0.4.17-beta.38`.
- For normal beta/update releases, increment the prerelease number only: `0.4.17-beta.38` -> `0.4.17-beta.39`.
- For stable releases, require explicit user approval before dropping `-beta.N` or changing major/minor/patch.
- Keep `package.json`, `package-lock.json`, and `backend/version.py` synchronized before the checkpoint is considered complete.
- Prefer `npm version <version> --no-git-tag-version`, then `npm run write-version`, and verify lock/backend sync.
- If the release-prep version bump is requested or implied, do not leave the docs step without the matching version files and completed release-facing documentation.
- Do not create tags, merge branches, push to `origin`, publish GitHub releases, or build installers in this skill.
- After the version/docs checkpoint is committed and pushed to `backup/develop`, route to `janus-build-release`.

## Release Version Check

If the user asks to move from a validated documentation state into build/release readiness, this skill must:

1. bump the prerelease version in `package.json`
2. run `npm run write-version`
3. sync `package-lock.json` and `backend/version.py`
4. update the release-facing docs for the completed marker to the new version
5. validate the version consistency before handing off to `janus-git-governance`

If any of those steps cannot be completed, the documentation update is not finished yet.

Required version check:

```powershell
node -e "const fs=require('fs'); const pkg=JSON.parse(fs.readFileSync('package.json','utf8')); const lock=JSON.parse(fs.readFileSync('package-lock.json','utf8')); const backend=fs.readFileSync('backend/version.py','utf8'); console.log({root:pkg.version, lock:lock.version, lockRoot:lock.packages[''].version, backend}); if(lock.version!==pkg.version || lock.packages[''].version!==pkg.version || !backend.includes(pkg.version)) process.exit(1);"
```

## Normal Completion Flow

1. Verify final audit/manual/debug gates.
2. Resolve task file, Spec path, Backlog ID, TestRun/TestSpec artifacts, version, and validation evidence.
3. Build a compact documentation scope package in notes or scratch form:

```text
DOC_SCOPE:
- Marker:
- Required Files:
- Optional Files:
- Evidence Paths:
- Exact Skip Reasons:
```

4. Update task/Spec implementation metadata.
5. Update central registry and project state.
6. Update changelog or report exact skip reason.
7. Update `WHAT_I_LEARNED.md` if a reusable pattern exists, using append-only format and avoiding duplicates.
8. Move Backlog item to DONE when applicable.
9. Sync dashboard snapshot if Backlog changed.
10. Validate Backlog with:

```powershell
python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
```

11. Run documentation completion validator when applicable:

```powershell
python C:\Users\pruve\.codex\skills\janus-documentation-update\scripts\validate_doc_update.py --repo C:\KI\Janus-Projekt --marker <BACKLOG-XXX-or-TEST-RUN-id>
```

12. Recommend `janus-git-governance` for a checkpoint commit.
13. For release prep, verify version sync and recommend `janus-build-release` only after the Git checkpoint is clean.

Prefer exact skip reasons over optional rereads. Example: `CHANGELOG skipped: validation-only internal hardening, no user-facing behavior change`.

If another actor should take over after this step, include exactly one compact fenced `text` handoff block with only the marker, the required next skill, the minimum load artifacts, and any exact skip reasons.

## Test Pipeline Completion Mode

Use when input contains:

```text
CompletionAction=RECORD_TEST_PIPELINE_PASS_AND_SYNC_DOCUMENTATION
```

or has `BacklogItem=N_A`, `Task=N_A`, `ResultStatus=PASS`, `Findings=NONE`, and valid `TestSpec`, `TestPlan`, and `TestResultJson`.

Mandatory updates:

- `documentation/pipeline/TEST_PIPELINE_RUN_LOG.md`
- `PROJECT_STATE.md`
- `documentation/01_CENTRAL_TASK_REGISTRY.md`
- `WHAT_I_LEARNED.md` when the run validates reusable pipeline hardening/oracle/routing rules
- TestSpec `## Latest Pipeline Validation`
- capability registry/view validation marker when capability overview/help is validated

Allowed skips:

- Backlog only when `BacklogItem=N_A`
- Task file only when `Task=N_A`
- Changelog only with exact reason: `validation-only TestSpec pass, no product/user-facing change`

Terminal success line:

```text
TEST PIPELINE COMPLETE
```

## Backlog DONE Rule

When closing `BACKLOG-XXX`:

- The item block must appear exactly once.
- Remove it from `READY`, `NEEDS INFO`, `IN PROGRESS`, and `BLOCKED`.
- Place it under `## DONE`.
- Set `- **Status:** DONE`.
- Preserve lifecycle fields.
- Add final audit, validation evidence, completed version, and completed task/spec where available.

After edit:

```powershell
cd C:\KI\Janus-Projekt\janus-dashboard
npm run sync:backlog
```

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

If no push happens or push fails, the documentation-update result or handoff must explicitly say that a remote such as GitHub may not contain the latest CURRENT_STATE yet.

## Output Format

Use:

```markdown
# JANUS DOCUMENTATION UPDATE

## Result
- **Documentation Update:** COMPLETE | BLOCKED
- **Final Audit:** PASS | PASS WITH FIXES | N/A
- **Canonical State:** PASS | BLOCKED | NEEDS_INFO

## Updated Artifacts
- <path>: <UPDATED | VALIDATED | SKIPPED WITH REASON>

## Validation
- <command>: <PASS | FAIL | NOT RUN WITH REASON>

## Scope Package
- **Marker:** <BACKLOG-XXX | SPEC-XX | TEST-RUN-XXX | N/A>
- **Required Files:** <paths>
- **Dropped Context:** <broad docs/history intentionally not reread>

## Completion Checklist
- **Task/Spec marker:** PASS | UPDATED | N/A | MISSING
- **Backlog marker:** PASS | UPDATED | N/A | MISSING
- **Dashboard sync:** PASS | UPDATED | N/A | MISSING
- **Central registry marker:** PASS | UPDATED | MISSING
- **PROJECT_STATE marker:** PASS | UPDATED | MISSING
- **CHANGELOG marker:** PASS | UPDATED | SKIPPED WITH REASON | MISSING
- **WHAT_I_LEARNED marker:** PASS | UPDATED | SKIPPED WITH REASON | MISSING

## Next Skill
`janus-git-governance`
```

Do not report `COMPLETE` if any required checklist item is `MISSING`.

When handing off across an actor or chat boundary, append exactly one compact fenced `text` block after the normal result. Include:

```text
NEXT: <next skill>
MODEL: <model>/<reasoning>
LOAD:
- <minimal artifact path>
ASK: <one-line instruction>
```

If the next step stays in the same warm Codex context, naming `Next Skill` is enough and no extra copy-box is required.

## WHAT_I_LEARNED Rules

Before appending, search for duplicates:

```powershell
python documentation\codex\scripts\search_what_i_learned.py --query "<pattern tags root cause>"
```

Append only when all are true:

- root cause is understood
- solution or rule was validated
- hardening evidence exists
- future tripwire can be stated concretely
- no existing pattern already covers it

Prefer:

```powershell
python documentation\codex\scripts\append_learning_pattern.py --id <PatternId> --title "<title>" --context "<context>" --problem "<problem>" --solution "<solution>" --hardening "<evidence/tests>" --tripwire "<future warning sign>" --location "<files>" --epic "<backlog/spec/test-run>" --tags "<tags>"
```

If skipped, output `WHAT_I_LEARNED marker: SKIPPED WITH REASON`.
