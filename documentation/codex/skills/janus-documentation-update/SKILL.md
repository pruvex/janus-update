---
name: janus-documentation-update
description: Synchronize Janus documentation after a passed final audit, resolved debug gate, completed Backlog item, completed Spec implementation, or green TestSpec/TestRun validation. Use when the user asks to close work, update docs, record evidence, mark Backlog DONE, update dashboard, changelog, project state, central registry, WHAT_I_LEARNED, or prepare for build/release after validation.
---

# Janus Documentation Update

## Overview

Use this skill after validation passed. Persist the result into Janus documentation and prepare the repository for `janus-build-release`. Do not implement product code, change architecture, hide failed validation, or run release commands.

## Source References

Read only when exact legacy wording is needed:

- `C:\KI\Janus-Projekt\.windsurf\workflows\SKILL 7 – DOKUMENTATIONSUPDATE.md`
- `C:\KI\Janus-Projekt\documentation\pipeline\PIPELINE_CONTRACT.md`
- `C:\KI\Janus-Projekt\AGENTS.md`

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

## Normal Completion Flow

1. Verify final audit/manual/debug gates.
2. Resolve task file, Spec path, Backlog ID, TestRun/TestSpec artifacts, version, and validation evidence.
3. Update task/Spec implementation metadata.
4. Update central registry and project state.
5. Update changelog or report exact skip reason.
6. Update `WHAT_I_LEARNED.md` if a reusable pattern exists.
7. Move Backlog item to DONE when applicable.
8. Sync dashboard snapshot if Backlog changed.
9. Validate Backlog with:

```powershell
python C:\Users\pruve\.codex\skills\janus-backlog-handoff\scripts\validate_backlog.py C:\KI\Janus-Projekt\documentation\backlog\BACKLOG.md
```

10. Run documentation completion validator when applicable:

```powershell
python C:\Users\pruve\.codex\skills\janus-documentation-update\scripts\validate_doc_update.py --repo C:\KI\Janus-Projekt --marker <BACKLOG-XXX-or-TEST-RUN-id>
```

11. Recommend `janus-git-governance` for a checkpoint commit.

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

