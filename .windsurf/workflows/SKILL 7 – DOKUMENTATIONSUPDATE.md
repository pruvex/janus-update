---
description: Skill 7 â€“ SWE 1.6 synchronisiert Dokumentation nach Skill-6-Audit und abgeschlossenem Skill-5-Debug-Gate
---

# Skill 7 â€“ Dokumentationsupdate (JANUS â€“ AFTER FINAL AUDIT AND DEBUG GATE)

Use this workflow only after:

```text
/1_Feature-erstellen
â†’ implementation of generated tasks
â†’ /2_final-audit or Skill 6 â€“ Diamantstandard Final Audit
â†’ manual Janus test evidence from Skill 4 / Skill 6 passed or explicitly deferred with reason
â†’ /SKILL 5 â€“ FEATURE DEBUG completed if Skill 4, Skill 6, or manual Janus test found a failure
â†’ Skill 7 automatic version bump
â†’ /SKILL 7 â€“ DOKUMENTATIONSUPDATE
```

Goal:
- Persist the final audit result into the task documentation.
- Sync project inventory, task registry, changelog, and project state.
- Persist reusable implementation/audit learnings in `WHAT_I_LEARNED.md`.
- Sync the Janus Capability Registry and UX capability view from validated post-implementation results.
- Preserve validation evidence and version bump details.
- Clean up temporary Skill-5 GPT-5.5 escalation handover files after the debug gate is resolved.
- Prepare the repository for `/SKILL 8 – BUILD RELEASE`.
- Trigger `/save` after successful documentation sync before release.

This workflow is a documentation and registry sync step. It is not an implementation phase.

---

## Hard Rules

- Do not run Skill 7 if `/2_final-audit` or Skill 6 returned `BLOCKED`.
- Do not run Skill 7 if the manual Janus test failed and Skill 5 has not resolved it.
- Do not run Skill 7 if Skill 6 requested re-run of Skill 4.
- Do not run Skill 7 if Skill 5 returned `ESCALATION REQUIRED`, `BLOCKED`, or `OUT OF SCOPE`.
- Do not make feature implementation changes.
- Do not redesign architecture.
- Do not silently ignore failed validation.
- Do not overwrite user-authored documentation outside the required sections.
- Do not run production release commands.
- Do not ask the user to manually choose a version unless version files are inconsistent or not parseable.
- Do not leave release-relevant version files unsynchronized.
- Prefer appending structured audit sections over rewriting existing task content.
- If required documentation files are missing, create a clear `BLOCKED` report instead of guessing.

Allowed safe edits:
- Append post-implementation audit trail to the task file.
- Update existing registry/status rows.
- Add changelog entry.
- Add or update `WHAT_I_LEARNED.md` with reusable patterns, root causes, tripwires, and fix rules.
- Add or update derived capability entries in `backend/data/capability_registry.json`.
- Add project state session log row.
- Add or update inventory entry.
- Add backward-reference notes.
- Compute and apply the Skill-7 automatic version bump.
- Record Skill-7 version bump details.
- Verify and, if necessary, repair the completed Spec dashboard marker after successful Skill-6 audit.
- Move completed Spec files to `documentation/SPEC/Spec Done/` if Skill 6 did not already move them.
- Move completed Backlog items from `IN PROGRESS` to `DONE` when the implementation originated from `BACKLOG-XXX`, preserving dashboard-readable lifecycle fields.
- Keep Backlog status sections canonical when moving items: one `## NEEDS INFO`, one `## READY`, one `## IN PROGRESS`, one `## DONE`, one `## BLOCKED`; item section must match its `Status` field.
- Delete resolved temporary Skill-5 escalation handover files matching `.windsurf/tmp/skill5_escalation_*.md`.

---

## Required Inputs

Ask for or infer:

1. Feature task file path, usually `documentation/tasks/task_<NR>_*.md`.
2. Implemented task range, e.g. `T1-T8`.
3. `/2_final-audit` or Skill 6 final result block.
4. Manual Janus test status from Skill 4 / Skill 6: `PASS`, `FAIL`, `N/A`, or `DEFERRED WITH REASON`.
5. Skill 5 result, if Skill 4/Skill 6/manual Janus test found a failure.
6. Current release/version state from root `package.json`.
7. Validation commands and pass/fail evidence from `/2_final-audit` or Skill 6.
8. Existing capability registry path, default `backend/data/capability_registry.json`.
9. Optional Backlog ID, e.g. `BACKLOG-004`, if the task originated from `BACKLOG SKILL 3 – SELECTED_HANDOFF` or references a `BACKLOG-XXX` item.
10. Optional temporary Skill-5 escalation handover file path, default pattern `.windsurf/tmp/skill5_escalation_*.md`, if Skill 5 escalated to GPT-5.5.
11. Optional Spec file path, including already moved paths under `documentation/SPEC/Spec Done/`, if the implementation originated from a Spec pipeline.

If the user provides no audit block, search recent conversation/context and task files. If still unavailable, ask for the `/2_final-audit` or Skill 6 report before proceeding.

If the task file contains a `BACKLOG-XXX` reference, treat `documentation/backlog/BACKLOG.md` as a required sync artifact for Phase 9.5.

If Skill 5 produced a temporary GPT-5.5 escalation handover file, treat it as a cleanup artifact, not as documentation source of truth. Use the Skill-5/GPT-5.5 final result and retest evidence as the source of truth.

---

## Phase 1: Final Audit Gate

Read or reconstruct the `/2_final-audit` or Skill 6 result.

Required accepted statuses:

- `PASS`
- `PASS WITH FIXES`

If status is `BLOCKED`, stop and return:

```markdown
# POST-IMPL BLOCKED

## Reason
- `/2_final-audit` or Skill 6 is BLOCKED.

## Required Action
- Resolve audit blockers.
- Re-run `/2_final-audit` or Skill 6.
- Then run `/SKILL 7 â€“ DOKUMENTATIONSUPDATE`.
```

Do not update registries or changelog when audit is blocked.

Validate the manual Janus test gate:

- `PASS`: continue.
- `N/A`: continue only if Skill 6 explicitly explained why no product-level test is meaningful and provided a smoke-test alternative.
- `DEFERRED WITH REASON`: continue only if the reason is explicit and non-blocking.
- `FAIL`: stop unless Skill 5 returned `SKILL 5 DEBUG RESULT: FIXED` and the user retest passed.

If manual test or debug gate is not satisfied, stop and return:

```markdown
# POST-IMPL BLOCKED

## Reason
- Manual Janus test or Skill 5 gate is not satisfied.

## Required Action
- Run `/SKILL 5 â€“ FEATURE DEBUG` with the actual output, expected result, and backend log.
- Re-run the manual Janus test after any Skill-5 fix.
- Then run `/SKILL 7 â€“ DOKUMENTATIONSUPDATE` again.
```

---

## Phase 1.2: Spec Dashboard Completion Sync Gate

Run this phase when the implementation originated from a Spec file under `documentation/SPEC` or when the Skill-6 package contains a `Spec:` path.

Purpose:
- Ensure Spec cards reliably move to Dashboard History even if Skill 6 wrote a non-canonical completion block.
- Ensure completed Specs live under `documentation/SPEC/Spec Done/`.

Required behavior after Skill 6 `PASS` or `PASS WITH FIXES`:

1. Resolve the Spec file path:
   - Prefer the `Spec:` path from the Skill-6 final audit package.
   - If that path no longer exists, check `documentation/SPEC/Spec Done/<original-filename>.md`.
   - If neither exists, stop with `SKILL 7 BLOCKED – SPEC FILE NOT FOUND`.

2. Ensure the Spec file contains the canonical dashboard marker:

```markdown
## SPEC IMPLEMENTATION METADATA

- **Implementation Status:** DONE
- **Final Audit:** <PASS | PASS WITH FIXES>
- **Completed At:** <YYYY-MM-DD>
- **Completed By:** SKILL 6 – DIAMANTSTANDARD FINAL AUDIT
- **Validation Evidence:** <Skill 6 validation/manual retest evidence>
```

3. If the Spec contains legacy or non-canonical fields, normalize them:
   - `Implementation Status: COMPLETE` -> `- **Implementation Status:** DONE`
   - `Audit Result: PASS` -> `- **Final Audit:** PASS`
   - `Audit Date` or `Implementation Date` -> `- **Completed At:** <date>`

4. Ensure the Spec file is located under:

```text
documentation/SPEC/Spec Done/<original-filename>.md
```

5. If the Spec file is still directly under `documentation/SPEC/`, move it to `documentation/SPEC/Spec Done/`.

6. If the target file already exists, stop with:

```text
SKILL 7 BLOCKED – SPEC DONE TARGET EXISTS
```

and do not overwrite either file.

7. In the final Skill-7 report, include:

```markdown
## Spec Dashboard Completion Sync
- **Spec file:** <old path>
- **Final Spec path:** documentation/SPEC/Spec Done/<file>.md
- **Metadata normalized:** YES | NO
- **Moved to Spec Done:** YES | NO
- **Dashboard History marker:** PASS | FAIL
```

Do not continue to release preparation if this phase fails for a Spec-originated implementation.

---

## Phase 1.5: Automatic Version Bump Gate

Skill 7 owns the final release-relevant version bump.

Purpose:
- Ensure `/SKILL 8 – BUILD RELEASE` never has to bump versions.
- Keep root package, lockfile, backend version, changelog, and task audit trail consistent.
- Avoid manual version decisions during the normal feature pipeline.

Required version files:
- `package.json`
- `package-lock.json`
- `backend/version.py`

Optional version file:
- `frontend/package.json` only if it is explicitly part of the release/version contract or already matches the root version.

Deterministic default:

```text
Patch prerelease bump
```

Computation rules:

1. If root version is `X.Y.Z-beta.N`, bump to `X.Y.Z-beta.(N+1)`.
2. If root version is stable `X.Y.Z`, bump to `X.Y.(Z+1)-beta.1`.
3. If root version has another semver prerelease suffix, stop and report `VERSION BUMP BLOCKED â€“ UNSUPPORTED VERSION FORMAT`.
4. If `package-lock.json` is inconsistent before the bump, stop and report `VERSION BUMP BLOCKED â€“ VERSION FILES INCONSISTENT`.
5. If `backend/version.py` is inconsistent before the bump, stop and report `VERSION BUMP BLOCKED â€“ VERSION FILES INCONSISTENT`.

Apply the new version to:

- root `package.json`
- root `package-lock.json` top-level `version`
- root `package-lock.json.packages[""].version`
- `backend/version.py`
- `frontend/package.json` only if it matched the old root version or project convention explicitly requires sync

Validation:

- Parse both JSON files after writing.
- Re-read all changed version files.
- Confirm every synchronized file contains the new version.

If blocked:

```markdown
# SKILL 7 BLOCKED

## Reason
- VERSION BUMP BLOCKED â€“ [specific reason]

## Required Action
- Fix version file inconsistency or provide an explicit version override.
- Re-run Skill 7.
```

Record in task audit trail and final report:

```markdown
## Skill 7 Version Bump
- **Old version:** [old]
- **New version:** [new]
- **Mode:** automatic patch prerelease bump
- **Files changed:** [list]
- **Validation:** PASS | FAIL
```

---

## Phase 2: Task File Audit Trail

Open the feature task file.

If the task file contains sections named:

- `Section 6 (Ergebnis & Audit-Trail)`
- `Section 7 (Debugging-Log)`

fill those sections.

If those sections do not exist, append:

```markdown
---

## POST-IMPLEMENTATION AUDIT TRAIL

### Implementation Scope
- **Implemented tasks:** [T1-Tx]
- **Feature status:** DONE
- **Final audit status:** PASS | PASS WITH FIXES

### Files Changed
- **[path]:** [brief description]

### What Was Done
[1-3 sentence summary]

### Validation Evidence
- **[command]:** PASS | FAIL | SKIPPED â€” [evidence]
- **Manual Janus test:** PASS | FAIL | N/A | DEFERRED â€” [evidence/reason]
- **Skill 5:** FIXED | NEEDS RETEST | ESCALATION REQUIRED | BLOCKED | OUT OF SCOPE | N/A â€” [evidence]

### Final Audit Fixes
- **[path]:** [fix summary]
- None, if no fixes were applied.

### Version Bump
- **Old version:** [old]
- **New version:** [new or unchanged]
- **Files changed:** [list or None]

### Remaining Risks
- **[risk]:** [impact]
- None, if no risks remain.
```

Then append:

```markdown
## DEBUGGING LOG

- **[issue]:** [cause and fix]
- Keine Probleme., if implementation was clean.
```

---

## Phase 3: Backward References

Read the task file for dependency/reference sections such as:

- `Beeinflusst`
- `Dependencies`
- `Must be completed after`
- explicit referenced task files

For each referenced task file:

1. Open the referenced task file.
2. Add a short note under its reference/dependency section:

```markdown
â†’ Modified by [task file / task id]: [short description]
```

If no referenced tasks exist, record:

```markdown
Backward references: None
```

---

## Phase 4: Inventory Sync

Read `documentation/04_PROJECT_INVENTORY_AND_STATUS.md`.

Add or update the component entry affected by the feature:

- Component / Skill / Module name
- Domain
- Status: `DONE`
- Capabilities added/changed
- Important files
- Test evidence
- Version, if release-relevant

If the file is missing, report it as a non-blocking documentation risk unless the task explicitly requires it.

---

## Phase 5: PROJECT_STATE Sync

Read `PROJECT_STATE.md`.

Add a row to `SECTION 2 (SESSION_LOG)` or the current session log equivalent:

- Timestamp
- Task file / feature ID
- Editor/model used
- Result: `DONE`
- Final audit status
- Version bump
- Validation summary
- Short notes

If the exact section is not found, append a clearly marked session log entry without restructuring the file.

---

## Phase 6: Central Task Registry Sync

Read `documentation/01_CENTRAL_TASK_REGISTRY.md`.

Update the matching task/feature row:

- Status: `DONE`
- Result column: concise summary
- Audit status: `PASS` or `PASS WITH FIXES`, if such a column exists
- Version: new version, if applicable
- Epic progress, if the feature completion changes it

If the registry file is missing or no matching row exists, report a documentation risk and do not invent a fake row unless the existing file format is obvious.

---

## Phase 7: CHANGELOG Sync

Read `CHANGELOG.md`.

Add an entry under `[Unreleased]`.

Use categories:

- `Added`
- `Changed`
- `Fixed`
- `Security`
- `Removed`
- `Deprecated`

Include:

- Feature/task reference
- User-visible summary
- Important internal/security/test note if relevant
- Version bump note if relevant

Example:

```markdown
### Added
- Implemented deterministic Auto Update System state machine, secure IPC bridge, SHA256 manifest validation, state-driven update UI, and test coverage (`task_068`, T1-T8).
```

---

## Phase 8: WHAT_I_LEARNED Sync

Read `WHAT_I_LEARNED.md`.

Cost rule:
- Do not read `WHAT_I_LEARNED.md` fully by default.
- First derive a proposed `PatternName`, tags, task id, feature domain, and root-cause keywords.
- Search `WHAT_I_LEARNED.md` for those exact terms.
- Read only matching sections to avoid duplicates.
- Append a new learning only if no existing learning already covers the same root cause/tripwire.

Add a learning only if the implementation or `/2_final-audit` produced reusable knowledge, such as:

- root cause that should not be rediscovered
- false-positive test pattern
- race condition or lifecycle pattern
- security/IPC/validation invariant
- versioning/release invariant
- recurring failure mode and tripwire

Do not add generic summaries. Each learning must be actionable and future-facing.

Use this format:

```markdown
## [PATTERN] #[PatternName] "[short title]"
- **Kontext:** [feature/task and why this matters]
- **Problem:** [what failed or could fail]
- **LÃ¶sung:** [deterministic fix or rule]
- **HÃ¤rtung:** [guardrails, tests, validation]
- **Tripwire:** [symptom that means this pattern was violated]
- **Location:** [files/modules], implementiert [date]
- **Epic:** [task/feature]
- **Confidence:** High | Medium | Low
- **Tags:** [comma-separated tags]
```

If no reusable learning exists, record in the final report:

```markdown
- **WHAT_I_LEARNED:** skipped â€” no reusable pattern/root cause identified
```

---

## Phase 9: Capability Sync

Run this phase only if `/2_final-audit` or Skill 6 is `PASS` or `PASS WITH FIXES`.

Purpose:
- Keep Janus' "Was kannst du?" answer aligned with the latest validated system state.
- Treat the capability list as a derived post-implementation snapshot, not as a manually maintained source of truth.
- Update existing capability data by merge, never by wholesale overwrite.

Inputs:
- Feature task file and post-implementation audit trail.
- `/2_final-audit` or Skill 6 result and applied fixes.
- CHANGELOG entry for the implemented feature.
- Existing `backend/data/capability_registry.json`.

Hard rules:
- Do not run this phase if the audit status is `BLOCKED`.
- Do not add planned, partial, speculative, or failed capabilities.
- Do not let capability generation influence feature decisions or acceptance criteria.
- Do not expose internal module names, task IDs, source files, IPC channels, test names, or implementation details in user-facing capability text.
- Do not overwrite the full registry. Merge only directly affected categories and abilities.
- Do not create a separate manually maintained capability source of truth.

Derivation rules:
1. Extract user-visible capabilities from the implemented feature result.
2. Translate technical implementation facts into product-language abilities.
3. Group each ability into the closest product category.
4. Consolidate duplicates with existing ability entries.
5. Remove or mark obsolete entries only when the current task explicitly replaced or removed that user-visible capability.
6. Preserve existing `skill_refs`, `ui_locations`, provider/model metadata, and unrelated categories.

Canonical grouping for derived capabilities:

```json
{
  "planning": [],
  "automation": [],
  "ai": [],
  "release": [],
  "system": []
}
```

Mapping guidance:
- **planning:** planning, task creation, audits, documentation workflows, implementation guidance.
- **automation:** scheduled flows, background jobs, self-healing, state machines, repeatable system actions.
- **ai:** model usage, memory, retrieval, agent behavior, tool use, reasoning, multimodal capabilities.
- **release:** builds, installers, updates, manifests, deployment, production publishing.
- **system:** settings, diagnostics, security, state persistence, IPC/user actions, local runtime behavior.

Registry merge target:
- Use `backend/data/capability_registry.json` as the machine-readable registry.
- Existing registry schema with `categories -> abilities` remains authoritative for the Help Skill.
- If canonical categories already exist, append/merge there.
- If the existing registry uses more specific categories, either merge into the closest existing category or create one canonical category with:

```json
{
  "display_name": {"de": "[Endnutzer-Kategorie]", "en": "[category]"},
  "icon": "[icon]",
  "description": {"de": "[short product-level description]", "en": "[short product-level description]"},
  "abilities": [],
  "ui_locations": {}
}
```

Each new or changed ability must use product language:

```json
{
  "id": "[stable.dot.separated.id]",
  "label": {
    "de": "[what the user can do]",
    "en": "[what the user can do]"
  },
  "skill_refs": [],
  "how_to": {
    "de": "[short user instruction, no internal filenames/tasks]",
    "en": "[short user instruction, no internal filenames/tasks]"
  }
}
```

UX capability view rules:
- The UX view is generated from the same registry data used by `HelpSkill.get_overview`.
- It must be cleanly grouped, stable, and understandable to end users.
- It must not mention modules, task IDs, code files, tests, IPC, manifests, package names, or audit internals.
- It should answer "Was kannst du?" with product capabilities only.

Final report must include:

```markdown
- **Capability Registry:** [updated / skipped + reason]
- **Capability UX View:** [validated / skipped + reason]
- **Derived capabilities:** [list of user-visible abilities added/merged]
```

If no user-visible capability changed, record:

```markdown
- **Capability Registry:** skipped â€” no new or changed user-visible capability identified
```

---

## Phase 9.5: Backlog Sync

Run this phase only if the implemented task or spec references a `BACKLOG-XXX` item.

Purpose:
- Keep `documentation/backlog/BACKLOG.md` current after successful implementation.
- Remove completed work from the active backlog view without losing audit history.
- Link the completed Backlog item to the task file, changelog entry, validation evidence, and version.

Rules:
- Only run after Skill 6 final audit is `PASS` or `PASS WITH FIXES` and the manual Janus test gate is `PASS`, `N/A`, or `DEFERRED WITH REASON`.
- Do not mark Backlog items as `DONE` if Skill 5 debug is still open, blocked, or awaiting retest.
- Do not delete Backlog items permanently.
- Move completed items from `IN PROGRESS` to `DONE`.
- If the item is still in `READY` but the task was completed, move it to `DONE` and record that the `IN PROGRESS` transition was skipped.
- If the Backlog item cannot be found, record `Backlog Sync: skipped — item not found` in the final report.
- Preserve existing `Entry Point`, `Routing reason`, `Routing confidence`, `Handoff`, and `Recommended next skill` fields for dashboard history.
- Do not delete completed items or remove their handoff references.
- When marking an item `DONE`, move the complete `### BACKLOG-XXX` block under the single canonical `## DONE` heading; do not only edit the `Status` field.
- After Backlog Sync, verify there are no duplicate status headings and no section/status mismatch for any `BACKLOG-XXX` item.

Update the item with:

```markdown
- **Completed in version:** <new version>
- **Completed by task:** <task file path>
- **Completed at:** YYYY-MM-DD
- **Final audit:** PASS | PASS WITH FIXES
- **Validation evidence:** <commands/results>
- **Changelog:** <entry or section>
```

Final report must include:

```markdown
- **Backlog:** updated | skipped + reason
- **Backlog ID:** BACKLOG-XXX | none
- **Backlog section consistency:** PASS | FAIL | skipped + reason
```

---

## Phase 10: Validation Handling

Primary validation source is `/2_final-audit` or Skill 5.

Record all audit commands and results.

Only run additional regression if:

- the task file explicitly requires it,
- `/2_final-audit` or Skill 5 requested it,
- or the user asks for release-level confidence.

Recommended validation selection:

- Backend-only feature: `python -m pytest backend/tests -q`
- Electron/update feature: Node tests + Playwright tests from audit
- Frontend feature: relevant Playwright/Vitest/UI tests
- Full release: defer to `/SKILL 8 – BUILD RELEASE`
- Capability sync: validate `backend/data/capability_registry.json` JSON syntax and, if capability entries changed, run focused Help/Capability tests when practical.

Do not automatically run `python -m pytest backend/tests -q` for every feature if it is unrelated or known to be expensive/flaky.

---

## Phase 11: Temporary Skill-6 Escalation File Cleanup

Run this phase after:

- Final audit gate is satisfied.
- Manual Janus test gate is `PASS`, `N/A`, or `DEFERRED WITH REASON`.
- If Skill 6 was needed, Skill 6/GPT-5.5 returned `FIXED` and the user retest passed.

Purpose:
- Keep the project clean after token-saving GPT-5.5 escalation.
- Remove temporary handover files that only exist to avoid sending long backend logs.

Target files:

```text
.windsurf/tmp/skill5_escalation_*.md
```

Rules:
- Delete only files that clearly match the Skill-6 temporary escalation naming pattern.
- If the user provided an explicit temporary file path, delete only that file unless other matching files clearly belong to the same resolved feature/task.
- Do not delete arbitrary files in `.windsurf/tmp`.
- Do not delete the temporary file if Skill 6 is still `ESCALATION REQUIRED`, `NEEDS RETEST`, `BLOCKED`, or `OUT OF SCOPE`.
- If deletion fails, report it as a cleanup warning, not as a feature failure, unless the file contains sensitive log data.

Final report must include:

```markdown
- **Skill 6 temp cleanup:** deleted | skipped | warning
- **Deleted files:** [list or none]
- **Cleanup reason:** [resolved debug gate / no temp file found / blocked because debug gate unresolved / deletion failed]
```

---

## Phase 12: Final Report

Return:

```markdown
# POST-IMPL COMPLETE

## Task
- **Task file:** [path]
- **Implemented tasks:** [T1-Tx]
- **Final audit status:** PASS | PASS WITH FIXES

## Documentation Updated
- **Task file:** [updated / skipped + reason]
- **Inventory:** [updated / skipped + reason]
- **PROJECT_STATE:** [updated / skipped + reason]
- **Central registry:** [updated / skipped + reason]
- **CHANGELOG:** [updated / skipped + reason]
- **WHAT_I_LEARNED:** [updated / skipped + reason]
- **Capability Registry:** [updated / skipped + reason]
- **Capability UX View:** [validated / skipped + reason]
- **Derived capabilities:** [user-visible abilities added/merged or none]
- **Spec Dashboard Completion Sync:** [updated / normalized / already valid / skipped + reason]
- **Backlog:** [updated / skipped + reason]
- **Backward refs:** [updated / none / skipped + reason]
- **Skill 6:** [not needed / fixed + retest pass / skipped + reason]
- **Skill 6 temp cleanup:** [deleted / skipped / warning + reason]

## Version
- **Old version:** [old]
- **New version:** [new or unchanged]

## Validation Recorded
- **[command]:** [PASS/FAIL/SKIPPED]

## Remaining Risks
- **[risk]:** [impact]
- None

## Next Step
- **Recommended:** `/save` before `/SKILL 8 – BUILD RELEASE` | additional regression | no release yet
- **Reason:** [short reason]
```

---

## Phase 13: Atomic Save Handoff

If Skill 7 completed successfully, instruct the user to run:

```text
/save
```

Rules:
- `/save` is mandatory before `/SKILL 8 – BUILD RELEASE`.
- `/save` commits the documented final state to `backup develop`.
- Do not proceed to release if `/save` fails.

