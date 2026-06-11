# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
OpenRouter delegation harness progress, timeout, and finish-reason classification patch is local and validated.

## Active Phase
Dev-environment OpenRouter benchmark tooling robustness patch; no production routing.

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
The post-projection state reconciliation commit `9c1a750de` was pushed to `backup/develop`.

## Last Codex Work
Confirmed no healthcheck reminder was due.
Reviewed Gemma 31B retry evidence after the schema projection patch: the prior `uniqueItems` grammar error no longer appeared; `OR-DELEGATE-005` local forbidden privacy-tier block passed; two external cases returned schema-valid partial scores; three external cases returned invalid JSON with `finish_reason` values `error` or `length`.
Added safe progress output for live benchmark cases on stderr. Progress lines include only event, task id, model id, coarse status, and elapsed milliseconds.
Local forbidden privacy-tier deny cases now report progress as `local_deny` and do not call OpenRouter.
Added `--request-timeout-seconds` with default `120`; it applies only to external OpenRouter HTTP requests and records `request_timeout` on timeout.
Added finish-reason-based invalid JSON classification: `length` -> `truncated_json`, `error` -> `provider_generation_error`, otherwise `invalid_json`.
Preserved HTTP 429 classification as `rate_limited / HTTP 429` and preserved HTTP 200 top-level OpenRouter error-payload classification.
Updated README and model scoring report for progress output, timeout behavior, and failure classification.
No live OpenRouter calls were run during this patch.
No production routing was approved.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/codex/openrouter-delegation/README.md
- documentation/codex/openrouter-delegation/model_scoring_report.md
- documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py

## Remote Sync Evidence
- Latest synchronized commit: `9c1a750de` (`docs(ai): reconcile openrouter schema projection sync state`)
- Branch: `develop`
- Remote: `backup/develop`
- Generated benchmark JSON files remain untracked local evidence and were not staged or pushed.
- This progress/timeout/classification patch is local until committed/pushed through `janus-git-governance`.

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --models google/gemma-4-31b-it:free` -> PASS, no external prompts sent
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- JSON parse check for both OpenRouter schemas -> PASS
- Progress output smoke test -> PASS; stderr progress contains task id/model id/status/elapsed only and excludes prompts/API-key test marker
- Timeout classification smoke test -> PASS; external timeout records `request_timeout`
- Timeout report-structure smoke test -> PASS; benchmark result keeps `schema_version`, `corpus_version`, cases, and `production_approved: false`
- Finish-reason smoke test -> PASS; `length` maps to `truncated_json`, `error` maps to `provider_generation_error`, no signal maps to `invalid_json`
- HTTP 429 smoke test -> PASS; classification is `rate_limited / HTTP 429`
- HTTP 200 top-level error payload smoke test -> PASS; classification remains `OpenRouter error payload returned with HTTP 200`
- Live gate without `--allow-external` -> blocked as expected before API-key use
- Live gate with `--allow-external` but without `OPENROUTER_API_KEY` -> blocked as expected

## Open Risks
- No live OpenRouter call has been run after this progress/timeout/classification patch.
- Gemma 31B still needs a retry to determine whether invalid JSON rates improve with operator feedback and timeout controls.
- `nvidia/nemotron-nano-9b-v2:free` remains excluded/incompatible pending a future provider response change.
- Production routing remains `UNKNOWN`/disabled.
- The existing worktree contains many pre-existing Janus product/test/documentation changes unrelated to this prototype; do not stage broadly.
- GitHub or other remote readers will not see this local CURRENT_STATE until a later explicit `janus-git-governance` commit/push.

## Next Recommended Step for ChatGPT
Review the local progress/timeout/classification patch and confirm that the read-only, curated-corpus-only, non-production boundaries still hold.

## Next Recommended Step for Codex
After explicit user approval and a process-local `OPENROUTER_API_KEY`, the next optional live gate is a curated-corpus-only retry for `google/gemma-4-31b-it:free` using `--run-live --allow-external --debug-response-shape --request-timeout-seconds 120`. Do not run live calls, approve production routing, or delegate Git/final-audit/release decisions without separate explicit approval.

## Last Updated
2026-06-11 22:27 local time
