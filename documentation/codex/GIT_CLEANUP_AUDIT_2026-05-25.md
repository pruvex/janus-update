# Git Cleanup Audit - 2026-05-25

## Scope

Read-only inventory of the dirty Janus worktree before productive Codex workflow usage.

No files were deleted, reverted, moved, staged, committed, or pushed during this audit.

## Snapshot

- Branch: `develop`
- Staged entries: `0`
- Dirty entries: `256`
- Unstaged tracked entries: `84`
- Untracked entries: `172`
- Large dirty file risk: none detected by `git_guard.py`
- Core artifacts: present
- Backlog visibility: `IN PROGRESS 3`, `READY 43`, `NEEDS INFO 5`, `BLOCKED 13`

## TestRun Evidence Policy

`documentation/test-runs/`, `documentation/test-results/`, and `tests/e2e/generated/` are established evidence locations in this repository, not blanket cleanup targets. At audit time, Git already tracked roughly `508` files under `documentation/test-runs`, roughly `3070` files under `documentation/test-results`, and roughly `150` files under `tests/e2e/generated`.

Retention rule:

- Keep and version curated evidence bundles when referenced by TestSpec, Backlog, final audit, registry, documentation update, release gate, or retest decision.
- Group cleanup decisions by `TEST_RUN_ID`, not by directory alone.
- Treat `documentation/test-results/<TEST_RUN_ID>_results.json` as primary triage evidence.
- Keep generated/live runners only when they are the executed runner for retained evidence.
- Do not retain raw Playwright report folders, trace bundles, transient terminal logs, local databases, or ad-hoc debug output unless explicitly cited by a final audit.
- Do not add broad ignore rules for `documentation/test-runs/`, `documentation/test-results/`, or `tests/e2e/generated/`.

## Main Groups

| Group | Evidence | Count / Shape | Initial Classification | Recommended Next Step |
| --- | --- | ---: | --- | --- |
| TestRun evidence | `documentation/test-runs/`, `documentation/test-results/`, generated E2E specs | `99` test-run entries, `48` test-result entries | likely generated evidence | Review by TestRun batches before committing or archiving |
| Backend feature/code changes | `backend/services/`, `backend/tools/`, `backend/tool_registry.py`, provider gateways | broad tracked diff | likely multiple feature/fix slices | Split by functional area before any commit |
| Websearch v3 | `backend/services/websearch_v3/`, `backend/tests/websearch_v3/`, modified websearch providers/tests | focused untracked + tracked set | likely coherent feature slice | Inspect and validate separately |
| Backlog/dashboard sync | `documentation/backlog/`, `janus-dashboard/`, `documentation/tasks/`, `BACKLOG-*` files | dashboard + backlog artifacts | likely dashboard/backlog state update | Reconcile with current Backlog before commit |
| TestSpec/test generator | `documentation/TEST_SPEC/`, `tests/e2e/generator/`, generated live specs | multiple related testspec updates | likely TestPipeline work | Group by TestSpec/TestRun relation |
| Root docs and release notes | `CHANGELOG.md`, `PROJECT_STATE.md`, `README.md`, `WHAT_I_LEARNED.md`, `release_notes.md` | tracked docs | likely closure documentation | Commit only with matching validated work |
| Root cleanup candidates | deleted `test_backlog_033_verification.py`, deleted `test_config.json`, untracked replacement test under `tests/` | two deletes plus one replacement-looking test | needs confirmation | Verify whether this is an intentional move before staging |
| Local suspicious root artifacts | `chat_history.db`, `costs.db`, `e2e_janus.db`, `main.log` from healthcheck | existing root hygiene findings | do not delete blindly | Decide ignore/archive policy separately |

## ID Signals

Backlog/TestRun identifiers visible in dirty or untracked paths:

- `BACKLOG-001`
- `BACKLOG-007`
- `BACKLOG-022`
- `BACKLOG-070`
- `BACKLOG-071`
- `BACKLOG-086`
- Many `TEST-RUN-2026-05-21-*` artifacts, strongest clusters around `014`, `017`, `019`, `021`, `023`, `025`, `027`, `029`, `031`, `034`, `035`, `036`, `038`, `039`, `040`, `041`, `042`

## Safe Ordering

1. Review and decide TestRun evidence policy.
2. Review focused Websearch v3 slice.
3. Review Backlog/dashboard state sync.
4. Review TestSpec/test generator changes.
5. Review broad backend feature/fix slices.
6. Review root docs only when their matching work is understood.
7. Handle root local artifacts and intentional moves last.

## Stop Rules

- Do not run `git add .`.
- Do not delete root databases/logs without explicit approval.
- Do not commit generated TestRun artifacts until the retention policy is clear.
- Do not mix dashboard/backlog sync with backend feature commits unless they belong to the same validated Backlog item.
- Do not push to `origin` during cleanup.
