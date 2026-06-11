# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
OpenRouter delegation design/prototype for the Codex development workflow is complete locally.

## Active Phase
Dev-environment delegation prototype complete; live OpenRouter benchmark pending explicit key/approval.

## Last Decision
This work is a Codex development-environment and skill-orchestration improvement, not a Janus application backlog item.
Do not add it to `documentation/backlog/BACKLOG.md` unless the user explicitly changes scope.

OpenRouter delegation remains read-only and non-production:

- OpenRouter may only receive sanitized benchmark prompts from the curated corpus.
- OpenRouter must not read private local files, secrets, local databases, private logs, broad source trees, or runtime state.
- OpenRouter must not write repo files, run commands, approve Git actions, approve final audits, or make release decisions.
- Production routing remains `UNKNOWN`/disabled until benchmark evidence is reviewed and the user approves activation.

The prototype lives under `documentation/codex/openrouter-delegation/` and separates design, corpus, schemas, scoring, and harness code.

## Last Codex Work
Routed the request through `codex-start-of-work-check` and `janus-skill-router`.
Confirmed no healthcheck reminder was due.
Fetched current Codex manual context through the `openai-docs` skill helper.
Consulted OpenRouter primary docs for chat completions, model metadata, structured outputs, authentication, and limits.
Created a read-only OpenRouter delegation design and benchmark prototype.
Validated the local corpus, schemas, script syntax, dry-run behavior, public OpenRouter model metadata listing, and live-call safety gates.

## Changed Files
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/codex/openrouter-delegation/README.md
- documentation/codex/openrouter-delegation/benchmark_corpus.json
- documentation/codex/openrouter-delegation/model_scoring_report.md
- documentation/codex/openrouter-delegation/schemas/delegated_task_result.schema.json
- documentation/codex/openrouter-delegation/schemas/benchmark_result.schema.json
- documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py

## Tests / Validation
- `python C:\Users\pruve\.codex\skills\codex-start-of-work-check\scripts\due_healthchecks.py` -> CLEAR
- `codex --version` -> `codex-cli 0.139.0`
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --models google/gemma-4-26b-a4b-it:free` -> PASS, no external prompts sent
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- JSON parse check for corpus and both schemas -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --list-models --require-response-format --limit 5` -> PASS, public metadata only
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --models google/gemma-4-26b-a4b-it:free` -> blocked as expected because `--allow-external` is missing
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --models google/gemma-4-26b-a4b-it:free` -> blocked as expected because `OPENROUTER_API_KEY` is not set

## Open Risks
- No live OpenRouter benchmark scoring has been run because `OPENROUTER_API_KEY` is not present in the current shell.
- Free-model limits and actual structured-output quality remain unverified until a live benchmark is explicitly approved.
- The existing worktree contains many pre-existing Janus product/test/documentation changes unrelated to this prototype; do not stage broadly.
- Commit and push have not been user-approved.
- A remote such as GitHub may not contain this latest `CURRENT_STATE` or prototype until a later `janus-git-governance` step is explicitly approved and completed.

## Next Recommended Step for ChatGPT
Review `documentation/codex/openrouter-delegation/README.md` and `model_scoring_report.md` for policy correctness, especially ALLOW/ASSIST/DENY/UNKNOWN boundaries and privacy language.

## Next Recommended Step for Codex
If the user approves live benchmarking, set `OPENROUTER_API_KEY` only for the current process and run the read-only benchmark against two to four response-format-capable low-cost/free models. Otherwise route to `janus-git-governance` only after explicit commit/push approval.

## Last Updated
2026-06-11 20:30 local time
