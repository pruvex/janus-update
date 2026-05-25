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

## TestRun Bundle Classification

Initial bundle decision for untracked `TEST-RUN-2026-05-21-*` artifacts:

| Bundle(s) | Reference signal | Classification | Cleanup action |
| --- | --- | --- | --- |
| `014`, `015` | Registry, pipeline log, TestSpec 08; `015` supersedes `014` for dashboard status | keep curated evidence | Commit as Skill Registry Integrity evidence bundle, preserving supersession note |
| `017`, `019`, `021` | Registry, pipeline log, TestSpecs 10-12 | keep curated evidence | Commit by memory-context TestSpec bundle |
| `023`, `025` | Registry, pipeline log, regression TestSpecs 16-17 | keep curated evidence | Commit by regression TestSpec bundle |
| `026`, `027` | Registry/pipeline log notes `026` as generated archive and `027` as final generator certification | keep curated evidence | Commit together with TestSpec 18/generator evidence |
| `028`, `029` | Registry/pipeline log notes `028` as generated archive and `029` as final cost/token certification | keep curated evidence | Commit together with TestSpec 13/cost evidence |
| `030`, `031` | Registry/pipeline log notes `030` as generated archive and `031` as final model-routing certification | keep curated evidence | Commit together with TestSpec 14/model-routing evidence |
| `033`, `034` | Registry/pipeline log notes `033` as generated archive and `034` as final prompt/context certification | keep curated evidence | Commit together with TestSpec 15/context-budget evidence |
| `035` | Dashboard final-green audit says PASS for dashboard overview; separate Websearch result JSON is FAIL with 1/2; no registry/backlog reference found | split bundle | Keep `TEST-RUN-2026-05-21-035_dashboard_final_green_audit.md` as dashboard meta-audit evidence if needed; do not treat `035_results.json`, evidence files, generated runner, or logs as green Websearch evidence |
| `036`, `038`, `039`, `040`, `041` | Websearch retest chain; TestSpec 10 explicitly cites `041` as latest full live-provider run | keep curated evidence with care | Commit only if tied to Websearch Provider Parity work; consider retaining full chain or only cited milestone runs after audit |
| `037` | Plan/runner/handover present, no result JSON found and no registry/backlog reference found | orphan/generated candidate | Do not commit unless a later audit explicitly cites it as generated archive; otherwise leave untracked until archive/delete decision |
| `042` | TestSpec 10 cites as closure run; final audit and documentation update present | keep curated evidence | Commit with Websearch closure evidence |

Do not stage all TestRun artifacts at once. Stage by bundle group after checking each group against its referenced TestSpec/Backlog/final audit.

## Ready Commit Groups

### TEST-RUN-2026-05-21-014 / 015 - Skill Registry Integrity

Decision: ready as first curated evidence commit.

Validation:

- `TEST-RUN-2026-05-21-014_results.json`: PASS, 6/6, 0 failed, 0 blocked.
- `TEST-RUN-2026-05-21-015_results.json`: PASS, 6/6, 0 failed, 0 blocked.
- `validate_test_pipeline_artifacts.py` passed for both `014` and `015`.
- `014` has final audit PASS and Skill 7 documentation update.
- `015` is the dashboard-aligned deterministic static certification and supersedes `014` for dashboard status.

Stage as evidence bundle:

- `documentation/test-runs/TEST-RUN-2026-05-21-014_final_audit.md`
- `documentation/test-runs/TEST-RUN-2026-05-21-014_generated.spec.js`
- `documentation/test-runs/TEST-RUN-2026-05-21-014_plan.json`
- `documentation/test-runs/TEST-RUN-2026-05-21-014_skill2_handover.txt`
- `documentation/test-runs/TEST-RUN-2026-05-21-014_skill7_documentation_update.md`
- `documentation/test-results/TEST-RUN-2026-05-21-014/`
- `documentation/test-results/TEST-RUN-2026-05-21-014_results.json`
- `documentation/test-results/TEST-RUN-2026-05-21-014_results.md`
- `documentation/test-runs/TEST-RUN-2026-05-21-015_plan.json`
- `documentation/test-results/TEST-RUN-2026-05-21-015_results.json`
- `documentation/test-results/TEST-RUN-2026-05-21-015_results.md`

Do not include the broad documentation sync files in this commit yet (`PROJECT_STATE.md`, `WHAT_I_LEARNED.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `documentation/TEST_SPEC/03_tools_skills/08_skill_selector_capability_registry_integrity.md`, `documentation/pipeline/TEST_PIPELINE_RUN_LOG.md`) because their current diffs include additional TestRun bundles beyond `014/015`.

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
