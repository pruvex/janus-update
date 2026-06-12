# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Run the local Codex mini baselines for TMR-001 through TMR-005 only, starting with `5.4 mini` low reasoning and recording compact local evidence notes.

## Active Phase
Dev-environment Codex model-routing and local mini-baseline evidence capture. No production routing.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive public or sanitized benchmark prompts from a curated corpus or reviewed mini-task fixture.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, runtime state, dirty worktree content, or unredacted Janus project history.
- OpenRouter must not write repo files, patch code, run commands, approve Git actions, approve final audits, make release-readiness or publish decisions, or decide Janus product scope/backlog priority/user-facing behavior.
- Production routing remains `UNKNOWN`/disabled until local Codex mini baselines exist, OpenRouter prompt/schema fixes are reviewed, benchmark evidence is reviewed, and the user explicitly approves activation.

## Last Codex Work
Confirmed no healthcheck reminder was due.
Read the bound routing artifacts:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/task_model_matrix.md`

Read the Janus routing skill:

- `C:\Users\pruve\.codex\skills\janus-skill-router\SKILL.md`

Validated the first local mini baseline result for `TMR-001 / MINI-001` with `5.4 mini` low reasoning only.
The append-only local evidence note already contains the clean baseline record:

- `documentation/codex/model-routing/local_mini_baseline_results.md`

The recorded baseline is a clean `ALLOW` classification for the sanitized/mechanical excerpt fixture, with required flags present, forbidden flags absent, schema/shape pass, and no escalation needed.
Validated the second local mini baseline result for `TMR-002 / MINI-002` with `5.4 mini` low reasoning only.
Validated the third local mini baseline result for `TMR-003 / MINI-003` with `5.4 mini` low reasoning only.
Validated the fourth local mini baseline result for `TMR-004 / MINI-004` with `5.4 mini` low reasoning only.
Validated the fifth local mini baseline result for `TMR-005 / MINI-005` with `5.4 mini` low reasoning only.
The append-only local evidence note now contains all five clean baseline records.

The recorded baselines are:

- `TMR-001 / MINI-001`: clean `ALLOW` classification for the sanitized/mechanical excerpt fixture, with required flags present, forbidden flags absent, schema/shape pass, and no escalation needed.
- `TMR-002 / MINI-002`: exact four-label extraction with correct meanings, all labels present, forbidden authority absent, schema/shape pass, and no escalation needed.
- `TMR-003 / MINI-003`: advisory-only benchmark interpretation with all three models set to `HOLD`, schema-vs-mode distinction preserved, risk-flag caveat preserved, timeout caveat preserved, and no escalation needed.
- `TMR-004 / MINI-004`: advisory cost/latency ranking with Model A highest practical candidate, Model C strong latency fallback, Model B secondary, Model D HOLD/UNKNOWN, and no escalation needed.
- `TMR-005 / MINI-005`: clarified advisory wording preserving the no-test-yet restriction, schema/risk-flag prerequisite, and Codex/User policy authority, with no escalation needed.
No OpenRouter live calls were run.
No broad benchmark sweep was run.
No Git staging, commit, push, tag, merge, release, or backlog update was performed.

## Changed Files
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/local_mini_baseline_results.md`

## Remote Sync Evidence
- Latest synchronized commit noted in prior state: `378a1c72c` (`docs(ai): reconcile openrouter run feedback sync state`) on `backup/develop`.
- Branch context: `develop` / `backup/develop` workflow.
- This CURRENT_STATE update is local until a later explicit `janus-git-governance` commit/push.
- GitHub or other remote readers may not contain the latest CURRENT_STATE.

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- Focused source reads of required routing artifacts and skill instructions -> PASS
- Existing evidence note verified: TMR-001 low result already present and clean -> PASS
- No broad diff or OpenRouter validation run.

## Open Risks
- The baselines are only for TMR-001 / MINI-001, TMR-002 / MINI-002, TMR-003 / MINI-003, TMR-004 / MINI-004, and TMR-005 / MINI-005; the rest of the matrix remains untested.
- The local evidence note is not a routing policy and should not be treated as production approval.
- The existing worktree contains many unrelated pre-existing Janus product/test/documentation changes; do not stage broadly.
- GitHub or other remotes will not see this local CURRENT_STATE until a later explicit `janus-git-governance` commit/push.

## Next Recommended Step for ChatGPT
Review the recorded TMR-001 through TMR-005 results and decide whether to summarize the first-batch local baselines or prepare harness fixes before any OpenRouter comparison.

## Next Recommended Step for Codex
If the user wants to continue, summarize the first-batch local baselines or prepare the harness fixes separately. Do not expand to OpenRouter live calls.

## Last Updated
2026-06-12 02:34 local time
