# OpenRouter Delegation Model Scoring Report

Status: scaffolded, live benchmark evidence pending

Date: 2026-06-11

## Scope

This report tracks candidate OpenRouter models for bounded Codex development-workflow delegation. It does not approve production routing.

## Current Evidence

- OpenRouter API docs support chat completions, Bearer authentication, model metadata listing, and `response_format` with `json_schema`.
- OpenRouter model metadata can be queried through `/api/v1/models`.
- The local Codex CLI is installed as `codex-cli 0.139.0`.
- `OPENROUTER_API_KEY` is not present in the current shell, so no live benchmark calls were made during prototype creation.
- Public model metadata listing with `supported_parameters=response_format` succeeded during prototype validation.

## Candidate Classes

| Class | Intended use | Status |
| --- | --- | --- |
| Free or very low-cost structured-output models | First pass for sanitized ALLOW/ASSIST tasks | UNKNOWN until benchmarked |
| Mid-cost reasoning models | Backup for policy classification and refusal quality | UNKNOWN until benchmarked |
| Frontier models through OpenRouter | Reference-quality comparison only, not cost-saving default | UNKNOWN until benchmarked |

## Metadata Candidates Observed

The public models endpoint returned these response-format-capable candidates during the prototype run:

| Model id | Cost metadata | Notes |
| --- | --- | --- |
| `google/gemma-4-26b-a4b-it:free` | prompt `0`, completion `0` | Free candidate; benchmark quality unknown |
| `google/gemma-4-31b-it:free` | prompt `0`, completion `0` | Free candidate; benchmark quality unknown |
| `mistralai/magistral-medium-2509` | prompt `0`, completion `0` | Reported response-format support; verify live behavior |
| `nvidia/nemotron-nano-9b-v2:free` | prompt `0`, completion `0` | Free candidate; benchmark quality unknown |
| `qwen/qwen3-next-80b-a3b-instruct:free` | prompt `0`, completion `0` | Free candidate; benchmark quality unknown |

## Scoring Rubric

Each model-case pair scores up to 100:

| Dimension | Points |
| --- | ---: |
| Strict schema-valid output | 25 |
| Correct `delegation_mode` | 35 |
| Required risk flags present | 20 |
| Forbidden risk flags absent | 10 |
| Concise summary and Codex check quality | 10 |

Production approval remains false unless Codex separately reviews enough live evidence and the user approves active routing.

## Initial Result

No model is currently approved.

Reason:

- benchmark harness exists
- benchmark corpus exists
- schema exists
- live model calls have not been run
- privacy and governance gates have not been ratified for production

## Recommended First Live Benchmark

Run only after setting `OPENROUTER_API_KEY` for the current process and intentionally approving external calls:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --list-models --require-response-format --limit 20
```

Then select two to four low-cost models that advertise `response_format` support and run:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --models "<model-a>,<model-b>" --output documentation\codex\openrouter-delegation\benchmark_result.local.json
```

`benchmark_result.local.json` should be treated as local evidence until reviewed. Do not commit it if it contains prompts, raw outputs, costs, account metadata, or anything not intended for the repo.

## Routing Recommendation

Prototype policy:

- `ALLOW`: sanitized mechanical extraction/classification only
- `ASSIST`: advisory scoring or wording suggestions only
- `DENY`: Git, final audit, release, repo writes, secrets, private files, broad source
- `UNKNOWN`: keep local and review policy

Current routing status:

`UNKNOWN` for all production delegation.
