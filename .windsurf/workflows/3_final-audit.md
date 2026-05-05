---
description: GPT 5.5 finale Abnahme und fix vor /post-impl
---

# Final Audit Workflow (JANUS – PRE-POST-IMPL QUALITY GATE)

Use this workflow after all tasks from a generated implementation task file have been completed and before running `/post-impl`.

Goal:
- Verify that the implementation matches the Feature Spec and task file.
- Detect missed tasks, contract mismatches, unsafe regressions, stale code, selector/IPC/API mismatches, and missing validation.
- Apply only small, deterministic, low-risk fixes when the root cause is clear.
- Produce a final decision: `PASS`, `PASS WITH FIXES`, or `BLOCKED`.

This workflow is an audit-and-fix gate, not a redesign phase.

---

## Hard Rules

- Do not redesign architecture.
- Do not add new product behavior.
- Do not expand the original feature scope.
- Do not rewrite large modules.
- Do not infer missing product decisions.
- Do not hide failed validations.
- Do not run destructive commands.
- Do not proceed to `/post-impl` recommendation if acceptance criteria are not verifiably met.
- Do not bump versions before the audit status is `PASS` or `PASS WITH FIXES`.
- Do not choose a target version automatically. Version changes require an explicit user decision.
- Prefer minimal, precise fixes over broad refactors.
- If a fix would require architectural changes or unclear product decisions, stop and report `BLOCKED`.

Allowed safe fixes:
- Missing import/export.
- Incorrect file path.
- Selector/class/id mismatch.
- Wrong IPC/API method name against an already defined contract.
- Missing initialization call.
- Obvious test race condition.
- Missing package script required by the task.
- Syntax error.
- Broken test fixture/mock that contradicts the implemented contract.
- Dead old code that the task explicitly required to remove.
- Version bump after successful audit, but only after explicit user approval.

Forbidden fixes:
- New feature behavior not present in the task file.
- New persistence schema unless explicitly required.
- New security model.
- Major UI redesign.
- Replacing the implementation with a different architecture.
- Changing acceptance criteria to make tests pass.
- Bumping versions while audit status is `BLOCKED`.
- Bumping versions without showing current version, target options, and recommendation first.

---

## Required Inputs

Before starting, identify or ask for:

1. Feature Spec file or source description.
2. Generated task file, usually under `documentation/tasks/`.
3. Implemented task range, e.g. `T1-T8`.
4. Expected validation commands, if provided.

If the user does not provide paths, search the repository for the most likely task file and feature spec.

---

## Phase 0: WHAT_I_LEARNED Lookup Light (LOW-COST)

Purpose: audit against known Janus/Diamond-OS tripwires without paying for a full knowledge-base read.

Rules:
- Do not read `WHAT_I_LEARNED.md` fully by default.
- Extract targeted audit keys from the task file, changed files, feature domain, validation failures, and risky contracts.
- Search `WHAT_I_LEARNED.md` only for those keys/tags.
- Read only directly matching pattern blocks.
- Use matched learnings as explicit audit tripwires.
- If no relevant match exists, continue without loading the file.
- Do not let weakly related learnings expand audit scope.

Recommended lookup key categories:
- **Files/modules:** exact filenames, package names, router/service names.
- **Contract type:** IPC, API, persistence, UI, security, versioning, release, test.
- **Failure type:** race, false-positive test, import/export, schema mismatch, context bleed, tool-name mismatch.
- **Task/domain tags:** e.g. `TASK068`, `AutoUpdate`, `Playwright`, `ElectronIPC`.

Audit output:

```markdown
## Prior Learnings Applied
- **#[PatternName]:** [tripwire checked] → PASS | FINDING
- None found.
```

---

## Phase 1: Scope Reconstruction

Read the task file and extract:

- Feature name.
- All tasks and task IDs.
- `EXECUTION TARGET` for each task.
- Files to modify/create.
- Acceptance criteria.
- Test instructions.
- Explicit out-of-scope items.
- Security, IPC, API, persistence, and UI contracts.

Output an internal audit map:

```text
Task ID -> Required files -> Required behavior -> Required tests -> Status unknown
```

Do not modify code in this phase.

---

## Phase 2: Implementation Inventory

Identify actual changes and relevant files.

Use available tools to inspect:

- `git status`
- `git diff --name-only`
- `git diff`
- Files explicitly named in the task file
- Existing tests related to the feature

Map actual implementation to expected tasks:

```text
Task ID -> Expected files -> Found files -> Missing/extra files -> Initial status
```

If a task has no visible implementation, mark it as `BLOCKED` unless the user confirms it was intentionally skipped.

---

## Phase 3: Contract Audit

For each task, verify the implementation against the task contract.

Check especially:

### State and Persistence
- Valid states are used exactly as defined.
- State entry/exit conditions are implemented.
- Persistence path matches the spec.
- Recovery/default behavior is deterministic.

### IPC/API Contracts
- Channel names match exactly.
- Renderer calls match preload exposure.
- Main-process handlers match preload methods.
- No old/insecure channels remain if removal was required.

### UI Contracts
- UI appears for the correct states/triggers.
- Text and buttons match the task requirements.
- Critical/blocking behavior is enforced when required.
- Cancel/dismiss behavior matches the spec.
- Selectors used by tests match the implementation.

### Security Contracts
- Hash/signature/validation requirements match the spec.
- No secret/API key is exposed in frontend code.
- No unrestricted IPC bridge is introduced.

### Test Contracts
- Tests map to observable behavior.
- Tests do not only test mocks unless the task explicitly calls for isolated tests.
- At least one real E2E flow exists if mandated by the task file.

For each mismatch:

```text
Finding: [short name]
Severity: LOW / MEDIUM / HIGH / BLOCKING
Task: [task id]
File: [path]
Expected: [contract]
Actual: [observed]
Recommended action: FIX / REPORT BLOCKED
```

---

## Phase 4: Static Quality Audit

Check for:

- Syntax errors.
- Missing imports.
- Unused critical imports caused by removed code.
- Duplicate initialization.
- Race conditions in initialization/listeners.
- Old code paths that conflict with the new implementation.
- Inconsistent file extensions under the package module type.
- Missing npm scripts required by task instructions.
- Test files excluded by config patterns.

Apply safe fixes only when the fix is obvious and scoped.

---

## Phase 5: Validation Execution

Run validation commands from the task file where safe and relevant.

Typical commands:

```powershell
node -c path/to/file.cjs
node --test path/to/test.cjs
npx playwright test path/to/spec.js
npm test -- --specific-if-available
```

Rules:

- Do not run destructive commands.
- Do not install dependencies unless the user explicitly approves.
- If a command starts long-running servers, prefer existing project test scripts/config.
- If validation is canceled or times out, report the exact state and whether code changes were already made.

Record:

```text
Command -> Result -> Evidence -> Follow-up needed
```

---

## Phase 6: Safe Fix Loop

If validation fails:

1. Identify the root cause.
2. Check whether it is an allowed safe fix.
3. Apply the smallest possible change.
4. Re-run the failing validation only.
5. Repeat until:
   - validation passes, or
   - a non-safe fix would be required, or
   - product clarification is needed.

Stop and report `BLOCKED` if:

- The implementation contradicts the spec.
- The spec is incomplete.
- A required behavior is missing and cannot be added safely.
- Tests require a real product decision not present in the task file.
- A fix would alter architecture.

---

## Phase 7: Version Bump Gate

This phase runs only if the audit result is `PASS` or `PASS WITH FIXES`.

If the audit result is `BLOCKED`, skip version bump and proceed directly to the final report with recommendation: `Do not run /post-impl yet`.

Purpose:

- Ensure the release skill/build pipeline uses the final audited version.
- Ensure `/post-impl` can document the final version.
- Avoid consuming a version number before audit fixes are complete.

### Version Discovery

Inspect:

- Root `package.json`
- `frontend/package.json`, if present
- Any other version files explicitly referenced by the release workflow or task file

Determine:

```text
Current root version: [x.y.z]
Current frontend version: [x.y.z or NOT PRESENT]
Version files that must remain synchronized: [list]
Release scripts using version: [list]
```

If version files are inconsistent, report this as a finding and ask whether to synchronize them.

### Decision Requirement

Do not modify any version file until the user answers the version decision.

When a version bump is needed, return exactly:

```markdown
# VERSION BUMP REQUIRED

## Current Version
- **Root package.json:** [current]
- **Frontend package.json:** [current or NOT PRESENT]

## Why This Belongs Here
- The implementation audit is complete.
- Any safe fixes have already been applied.
- The next steps (`/post-impl` and `/release-production`) need the final version.

## Options

### Option A: Patch prerelease bump
- **Target:** [computed target, e.g. 0.4.17-beta.2]
- **Use when:** Same feature/release line, follow-up fixes, beta continuation.

### Option B: Patch release bump
- **Target:** [computed target, e.g. 0.4.18]
- **Use when:** Production-ready patch release.

### Option C: Minor prerelease bump
- **Target:** [computed target, e.g. 0.5.0-beta.1]
- **Use when:** Larger feature milestone or new capability bundle.

## Recommendation
- **Recommended option:** [A/B/C]
- **Reason:** [short reason based on release scope and current version]

## Required Answer Format
- `Decision: Option [A/B/C]`
- `Parameters: [optional exact version override or NONE]`
```

Then stop and wait for the user.

### Applying the Version Bump

After the user chooses a version:

1. Update root `package.json`.
2. Update `frontend/package.json` only if it exists and is part of the release/version contract.
3. Update lockfiles only if the package manager requires it and the command is safe/approved.
4. Re-read changed files and confirm the version was written correctly.
5. Run a lightweight JSON parse/syntax validation.

Do not run the production release command in this workflow.

### Version Bump Report Fragment

Add this to the final report:

```markdown
## Version Bump
- **Decision:** [Option A/B/C or skipped]
- **Old version:** [old]
- **New version:** [new]
- **Files changed:** [list]
```

If the user declines or defers the version bump, use:

```markdown
## Version Bump
- **Decision:** Deferred by user
- **Old version:** [old]
- **New version:** unchanged
- **Impact:** `/post-impl` can run, but `/release-production` may need version bump first.
```

---

## Phase 8: Final Report

Return exactly one of these statuses:

- `PASS`
- `PASS WITH FIXES`
- `BLOCKED`

Report format:

```markdown
# Final Audit Result: PASS | PASS WITH FIXES | BLOCKED

## Scope
- Feature/task file: [path]
- Audited tasks: [T1-Tx]
- Main files checked: [list]

## Findings
- **[severity] [title]:** [summary]

## Fixes Applied
- **[file]:** [what changed]

## Validation
- **[command]:** [passed/failed/canceled] — [evidence]

## Version Bump
- **Decision:** [Option A/B/C/skipped/deferred]
- **Old version:** [old]
- **New version:** [new or unchanged]
- **Files changed:** [list or None]

## Remaining Risks
- **[risk]:** [impact or NONE]

## Recommendation
- **Next step:** Run `/post-impl` | Decide version bump first | Do not run `/post-impl` yet
- **Reason:** [short reason]
```

If no fixes were required, use:

```markdown
## Fixes Applied
- None
```

If no remaining risks exist, use:

```markdown
## Remaining Risks
- None
```

---

## Output Contract

The workflow is complete only when:

- Every implemented task is audited against its acceptance criteria.
- Every relevant validation command is executed or explicitly justified as skipped.
- All safe fixes are either applied or explicitly rejected with reason.
- If audit passes, version bump readiness is checked.
- If a version bump is required, the workflow stops for explicit user decision before modifying versions.
- The final report gives a clear `/post-impl` recommendation.
