# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
OpenRouter delegation harness schema projection patch is synchronized to `backup/develop`.

## Active Phase
Dev-environment OpenRouter benchmark tooling ready for Gemma 31B retry gate; no production routing.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive sanitized benchmark prompts from the curated corpus.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, or runtime state.
- OpenRouter must not write repo files, run commands, approve Git actions, approve final audits, or make release decisions.
- Production routing remains `UNKNOWN`/disabled until benchmark evidence is reviewed and the user approves activation.

The prototype lives under `documentation/codex/openrouter-delegation/` and separates design, corpus, schemas, scoring, and harness code.
The prototype commit `6281fe59f` was pushed to `backup/develop`.
The state reconciliation commit `0d07d24fc` was pushed to `backup/develop`.
The harness robustness commit `ba9458c0d` was pushed to `backup/develop`.
The post-robustness state reconciliation commit `218ed5fd9` was pushed to `backup/develop`.
The outbound schema projection commit `f235819be` was pushed to `backup/develop`.

## Last Codex Work
Confirmed no healthcheck reminder was due.
Reviewed Gemma 31B debug evidence: `google/gemma-4-31b-it:free` returned HTTP 200 top-level `error` payloads for external cases, with no `choices`, no `message`, no `content`, and no `parsed`/`reasoning`/`refusal`/`tool_calls`.
The sanitized provider message was `Upstream error from OpenInference: Grammar error: Unimplemented keys: ["uniqueItems"]`.
The local forbidden privacy-tier safety block still passed.
Updated `schema_for_openrouter()` so the outbound OpenRouter request schema strips `$schema`, `$id`, and `uniqueItems` recursively.
Kept checked-in local schema files unchanged so local validation can remain stricter than provider-compatible request projection.
Updated README and model scoring report to document the outbound schema projection and mark `google/gemma-4-31b-it:free` as schema-incompatible pending retry after the projection patch.
Committed and pushed the scoped outbound schema projection patch as `f235819be`.
No live OpenRouter calls were run after this patch.
No production routing was approved.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/codex/openrouter-delegation/README.md
- documentation/codex/openrouter-delegation/model_scoring_report.md
- documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py

## Remote Sync Evidence
- Latest synchronized commit: `218ed5fd9` (`docs(ai): reconcile openrouter harness sync state`)
- Outbound schema projection commit: `f235819be` (`docs(codex): strip unsupported schema keys for openrouter`)
- Branch: `develop`
- Remote: `backup/develop`
- Verified after push: `HEAD`, `refs/remotes/backup/develop`, and `.git/FETCH_HEAD` resolved to `f235819beccf741ea7ca410047ac486994960d44`
- Generated benchmark JSON files remain untracked local evidence and were not staged or pushed.

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --models google/gemma-4-31b-it:free` -> PASS, no external prompts sent
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- JSON parse check for both OpenRouter schemas -> PASS
- Local smoke test for `schema_for_openrouter()` -> PASS; `$schema`, `$id`, and `uniqueItems` are stripped recursively from the outbound request schema projection
- Local schema retention smoke test -> PASS; `schemas/delegated_task_result.schema.json` still contains `"uniqueItems": true`
- `git diff --check -- documentation/codex/openrouter-delegation documentation/ai/CURRENT_STATE.md documentation/codex/SKILL_USAGE_LOG.md` -> PASS after SKILL_USAGE_LOG append
- `python C:\Users\pruve\.codex\skills\janus-git-governance\scripts\git_guard.py C:\KI\Janus-Projekt` -> BLOCKED for full-worktree mixed dirty state; expected because unrelated backend/dashboard/test/skill-rule changes pre-exist outside this scoped patch
- Staged-only `janus-git-governance` guard for the outbound schema projection patch -> PASS
- `git push backup develop` for `f235819be` -> PASS
- Remote sync verification for `f235819be` -> PASS

## Open Risks
- `google/gemma-4-31b-it:free` has not been retried live after the schema projection patch.
- `nvidia/nemotron-nano-9b-v2:free` remains excluded/incompatible pending a future provider response change.
- Production routing remains `UNKNOWN`/disabled.
- The existing worktree contains many pre-existing Janus product/test/documentation changes unrelated to this prototype; full-worktree Git guard blocks broad staging, so only explicit path staging is safe after a separate user approval.
- This rolling snapshot records the synchronized `f235819be` patch state; the closeout response records the follow-up CURRENT_STATE reconciliation commit.

## Next Recommended Step for ChatGPT
Use `backup/develop` commit `f235819be` as the shared state for the OpenRouter outbound schema projection patch.

## Next Recommended Step for Codex
After explicit user approval and a process-local `OPENROUTER_API_KEY`, the next optional live gate is a curated-corpus-only retry for `google/gemma-4-31b-it:free` using `--run-live --allow-external --debug-response-shape`. Do not run live calls, approve production routing, or delegate Git/final-audit/release decisions without separate explicit approval.

## Last Updated
2026-06-11 22:05 local time
