# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
OpenRouter delegation harness handles HTTP 200 top-level OpenRouter error payloads and is selected for `backup/develop` synchronization.

## Active Phase
Dev-environment harness robustness patch complete; Git governance commit/push authorized for the scoped OpenRouter files only.

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

## Last Codex Work
Confirmed no healthcheck reminder was due.
Reviewed the Nemotron free-model benchmark result showing `missing string content` for all external cases while the local forbidden privacy-tier block passed.
Added optional `--debug-response-shape` support to the benchmark harness.
Added explicit handling for OpenRouter payloads that return HTTP 200 with top-level `error` and no chat completion content.
The harness now reports `OpenRouter error payload returned with HTTP 200` instead of generic `missing string content` for that shape.
The debug mode records safe response shape metadata only: task/model ids, HTTP status, payload/choice/message key names, finish reason, content type/shape, presence booleans for `reasoning`, `refusal`, `tool_calls`, and `parsed`, plus sanitized optional `error.code`, `error.provider_name`, and short redacted `error.message`.
Updated README, model scoring report, and benchmark-result schema to document the debug mode, the HTTP 200 error-payload classification, and the no-content/no-secret logging boundary.
Marked `nvidia/nemotron-nano-9b-v2:free` as incompatible/pending in the model scoring report until provider behavior changes.
No live OpenRouter debug run was executed.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/openrouter-delegation/README.md
- documentation/codex/openrouter-delegation/model_scoring_report.md
- documentation/codex/openrouter-delegation/schemas/benchmark_result.schema.json
- documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py

## Remote Sync Evidence
- Prototype commit: `6281fe59f` (`docs(codex): add openrouter delegation prototype`)
- State reconciliation commit: `0d07d24fc` (`docs(ai): reconcile openrouter delegation state`)
- Branch: `develop`
- Remote: `backup/develop`
- Verified after reconciliation: `HEAD` and `backup/develop` resolved to `0d07d24fc`
- The new debug-response-shape patch is local and not yet committed/pushed.

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

## Open Risks
- `nvidia/nemotron-nano-9b-v2:free` remains excluded/incompatible pending a future provider response change; current debug evidence indicates HTTP 200 top-level OpenRouter error payloads, not hidden structured content.
- Production routing remains `UNKNOWN`/disabled.
- The existing worktree contains many pre-existing Janus product/test/documentation changes unrelated to this prototype; do not stage broadly.
- This harness robustness patch is in the current Git governance commit/push scope; after push, verify `HEAD`, `backup/develop`, and `FETCH_HEAD` before treating the remote as current.

## Next Recommended Step for ChatGPT
Use the scoped OpenRouter harness robustness patch as the next shared state after Git verification. The latest previously pushed shared state was `backup/develop` commit `0d07d24fc`.

## Next Recommended Step for Codex
Complete `janus-git-governance` by committing/pushing only the OpenRouter harness/report/schema/README, CURRENT_STATE, and SKILL_USAGE_LOG changes. Do not run further live OpenRouter calls unless explicitly approved with a process-local key.

## Last Updated
2026-06-11 21:30 local time
