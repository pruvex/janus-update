---
description: SWE 1.6 sorgt dafür, dass nach der technischen Umsetzung alles im Diamond-OS sauber dokumentiert ist
---

# Post-Implementation Workflow (JANUS – AFTER FINAL AUDIT)

Use this workflow only after:

```text
/1_Feature-erstellen
→ implementation of generated tasks
→ /2_final-audit
→ version bump decision if required
→ /post-impl
```

Goal:
- Persist the final audit result into the task documentation.
- Sync project inventory, task registry, changelog, and project state.
- Persist reusable implementation/audit learnings in `WHAT_I_LEARNED.md`.
- Sync the Janus Capability Registry and UX capability view from validated post-implementation results.
- Preserve validation evidence and version bump details.
- Prepare the repository for `/release-production`.

This workflow is a documentation and registry sync step. It is not an implementation phase.

---

## Hard Rules

- Do not run `/post-impl` if `/2_final-audit` returned `BLOCKED`.
- Do not make feature implementation changes.
- Do not redesign architecture.
- Do not silently ignore failed validation.
- Do not overwrite user-authored documentation outside the required sections.
- Do not run production release commands.
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
- Record version bump details from `/2_final-audit`.

---

## Required Inputs

Ask for or infer:

1. Feature task file path, usually `documentation/tasks/task_<NR>_*.md`.
2. Implemented task range, e.g. `T1-T8`.
3. `/2_final-audit` final result block.
4. Version bump decision/result, if any.
5. Validation commands and pass/fail evidence from `/2_final-audit`.
6. Existing capability registry path, default `backend/data/capability_registry.json`.

If the user provides no audit block, search recent conversation/context and task files. If still unavailable, ask for the `/2_final-audit` report before proceeding.

---

## Phase 1: Final Audit Gate

Read or reconstruct the `/2_final-audit` result.

Required accepted statuses:

- `PASS`
- `PASS WITH FIXES`

If status is `BLOCKED`, stop and return:

```markdown
# POST-IMPL BLOCKED

## Reason
- `/2_final-audit` is BLOCKED.

## Required Action
- Resolve audit blockers.
- Re-run `/2_final-audit`.
- Then run `/post-impl`.
```

Do not update registries or changelog when audit is blocked.

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
- **[command]:** PASS | FAIL | SKIPPED — [evidence]

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
→ Modified by [task file / task id]: [short description]
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
- **Lösung:** [deterministic fix or rule]
- **Härtung:** [guardrails, tests, validation]
- **Tripwire:** [symptom that means this pattern was violated]
- **Location:** [files/modules], implementiert [date]
- **Epic:** [task/feature]
- **Confidence:** High | Medium | Low
- **Tags:** [comma-separated tags]
```

If no reusable learning exists, record in the final report:

```markdown
- **WHAT_I_LEARNED:** skipped — no reusable pattern/root cause identified
```

---

## Phase 9: Capability Sync

Run this phase only if `/2_final-audit` is `PASS` or `PASS WITH FIXES`.

Purpose:
- Keep Janus' "Was kannst du?" answer aligned with the latest validated system state.
- Treat the capability list as a derived post-implementation snapshot, not as a manually maintained source of truth.
- Update existing capability data by merge, never by wholesale overwrite.

Inputs:
- Feature task file and post-implementation audit trail.
- `/2_final-audit` result and applied fixes.
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
- **Capability Registry:** skipped — no new or changed user-visible capability identified
```

---

## Phase 10: Validation Handling

Primary validation source is `/2_final-audit`.

Record all audit commands and results.

Only run additional regression if:

- the task file explicitly requires it,
- `/2_final-audit` requested it,
- or the user asks for release-level confidence.

Recommended validation selection:

- Backend-only feature: `python -m pytest backend/tests -q`
- Electron/update feature: Node tests + Playwright tests from audit
- Frontend feature: relevant Playwright/Vitest/UI tests
- Full release: defer to `/release-production`
- Capability sync: validate `backend/data/capability_registry.json` JSON syntax and, if capability entries changed, run focused Help/Capability tests when practical.

Do not automatically run `python -m pytest backend/tests -q` for every feature if it is unrelated or known to be expensive/flaky.

---

## Phase 11: Final Report

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
- **Backward refs:** [updated / none / skipped + reason]

## Version
- **Old version:** [old]
- **New version:** [new or unchanged]

## Validation Recorded
- **[command]:** [PASS/FAIL/SKIPPED]

## Remaining Risks
- **[risk]:** [impact]
- None

## Next Step
- **Recommended:** `/release-production` | additional regression | no release yet
- **Reason:** [short reason]
```
