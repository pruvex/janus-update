# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
OpenRouter delegation harness robustness patch is synchronized to `backup/develop`.

## Active Phase
Dev-environment OpenRouter benchmark tooling ready for the next free-only candidate benchmark gate.

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

## Last Codex Work
Confirmed no healthcheck reminder was due.
Reviewed the Nemotron free-model benchmark result showing `missing string content` for all external cases while the local forbidden privacy-tier block passed.
Added optional `--debug-response-shape` support to the benchmark harness.
Added explicit handling for OpenRouter payloads that return HTTP 200 with top-level `error` and no chat completion content.
The harness now reports `OpenRouter error payload returned with HTTP 200` instead of generic `missing string content` for that shape.
The debug mode records safe response shape metadata only: task/model ids, HTTP status, payload/choice/message key names, finish reason, content type/shape, presence booleans for `reasoning`, `refusal`, `tool_calls`, and `parsed`, plus sanitized optional `error.code`, `error.provider_name`, and short redacted `error.message`.
Updated README, model scoring report, and benchmark-result schema to document the debug mode, the HTTP 200 error-payload classification, and the no-content/no-secret logging boundary.
Marked `nvidia/nemotron-nano-9b-v2:free` as incompatible/pending in the model scoring report until provider behavior changes.
Committed and pushed the scoped OpenRouter harness robustness patch as `ba9458c0d`.
No production routing was approved.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md

## Remote Sync Evidence
- Prototype commit: `6281fe59f` (`docs(codex): add openrouter delegation prototype`)
- State reconciliation commit: `0d07d24fc` (`docs(ai): reconcile openrouter delegation state`)
- Harness robustness commit: `ba9458c0d` (`docs(codex): harden openrouter benchmark error handling`)
- Branch: `develop`
- Remote: `backup/develop`
- Verified after push: `HEAD`, `refs/remotes/backup/develop`, and `.git/FETCH_HEAD` resolved to `ba9458c0d1a9d8d0e6bfc445c6b1f3da4c94eae7`
- Generated benchmark JSON files were not staged or pushed.

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- `codex --version` -> `codex-cli 0.139.0`
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --models nvidia/nemotron-nano-9b-v2:free` -> PASS, no external prompts sent
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- JSON parse check for both OpenRouter schemas -> PASS
- Local smoke test for `response_shape_metadata` with simulated `message.content: null` -> PASS
- Local smoke test for HTTP 200 top-level `error` payload handling -> PASS; error text became `OpenRouter error payload returned with HTTP 200` and sensitive-looking message fragments were redacted
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --debug-response-shape --models nvidia/nemotron-nano-9b-v2:free` -> blocked as expected because `--allow-external` is missing
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --models nvidia/nemotron-nano-9b-v2:free` -> blocked as expected because `OPENROUTER_API_KEY` is missing
- `git diff --check -- documentation/codex/openrouter-delegation` -> PASS
- `janus-git-governance` staged-only guard for the harness robustness patch -> PASS
- `git push backup develop` for `ba9458c0d` -> PASS
- Remote sync verification for `ba9458c0d` -> PASS

## Open Risks
- `nvidia/nemotron-nano-9b-v2:free` remains excluded/incompatible pending a future provider response change; current debug evidence indicates HTTP 200 top-level OpenRouter error payloads, not hidden structured content.
- Production routing remains `UNKNOWN`/disabled.
- The existing worktree contains many pre-existing Janus product/test/documentation changes unrelated to this prototype; do not stage broadly.
- This CURRENT_STATE reconciliation is local until committed/pushed through `janus-git-governance`.

## Next Recommended Step for ChatGPT
Use `backup/develop` commit `ba9458c0d` as the shared state for the OpenRouter harness robustness patch.

## Next Recommended Step for Codex
Next optional benchmark gate: with explicit user approval and process-local `OPENROUTER_API_KEY`, run the curated-corpus-only free-model benchmark for `qwen/qwen3-next-80b-a3b-instruct:free` using `--run-live --allow-external --debug-response-shape`. Do not run live calls, approve production routing, or delegate Git/final-audit/release decisions without separate explicit approval.

## Last Updated
2026-06-11 21:43 local time
