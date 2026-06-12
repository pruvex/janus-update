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
- A free-only run for `nvidia/nemotron-nano-9b-v2:free` produced no chat completion content for all external cases while the forbidden privacy-tier block passed locally.
- Follow-up debug evidence showed HTTP 200 responses with top-level `error` payloads, no `choices`, no `message`, and no `content`.
- The harness now classifies this edge case as `OpenRouter error payload returned with HTTP 200` and can record safe response metadata when `--debug-response-shape` is enabled.
- A debug run for `google/gemma-4-31b-it:free` produced HTTP 200 top-level `error` payloads for external cases, with no `choices`, no `message`, no `content`, and no `parsed`/`reasoning`/`refusal`/`tool_calls`.
- The sanitized provider message was `Upstream error from OpenInference: Grammar error: Unimplemented keys: ["uniqueItems"]`; local forbidden privacy-tier blocking still passed.
- The harness now projects the local schema before sending it to OpenRouter by stripping `$schema`, `$id`, and `uniqueItems`. Local schema validation remains stricter.
- Gemma 31B retry evidence after the schema projection patch showed the prior `uniqueItems` grammar error was resolved, local forbidden privacy-tier blocking still passed, two external cases returned schema-valid partial scores, and three external cases returned invalid JSON with finish reasons `error` or `length`.
- The harness now reports safe per-case progress, supports configurable OpenRouter request timeouts, and maps invalid JSON with `finish_reason: length` to `truncated_json` and `finish_reason: error` to `provider_generation_error`.
- A feedback-timeout retry for `google/gemma-4-31b-it:free` showed finish-reason classification working (`length` -> `truncated_json`, `stop` without parseable JSON -> `invalid_json`) and local privacy-tier `DENY` still passing with score 100.
- The same retry produced only one schema-valid external case (`OR-DELEGATE-002`, `DENY`, score 80), three truncated JSON cases (`OR-DELEGATE-001`, `003`, `006`), one invalid JSON case (`OR-DELEGATE-004`), and several external elapsed times around 197-211 seconds despite `--request-timeout-seconds 120`.
- Timeout investigation found the previous `urllib` timeout was a socket-operation timeout, not a reliable total request deadline. The harness now wraps the external request/read/decode in an explicit wall-clock guard that returns `request_timeout`.

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
| `google/gemma-4-31b-it:free` | prompt `0`, completion `0` | UNRELIABLE / HOLD: schema projection fixed `uniqueItems`, but repeated truncated/invalid JSON, only partial external validity, and long response times |
| `mistralai/magistral-medium-2509` | prompt `0`, completion `0` | Reported response-format support; verify live behavior |
| `nvidia/nemotron-nano-9b-v2:free` | prompt `0`, completion `0` | Incompatible/pending: returned HTTP 200 top-level OpenRouter error payload instead of chat completion content |
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

The harness now also records diagnostic components for every model-case pair:

| Component | Meaning |
| --- | --- |
| `mode_correct` | Actual `delegation_mode` matches the expected mode, even if the output is otherwise schema-invalid. |
| `schema_valid` | Output validates as a complete `DelegatedTaskResult`. |
| `risk_flags_complete` | Required risk flags are present. |
| `forbidden_flags_absent` | Forbidden risk flags are absent. |
| `production_safe` | Output does not claim production approval, repo-write authority, Git authority, release authority, final-audit authority, or policy-decision authority. |
| `failure_type` | Separates `model_output`, `local_policy_deny`, `request_timeout`, and `provider_or_transport_error`. |

Schema-invalid model outputs receive score `0` even when `mode_correct` is true, so Qwen-style mode-correct but schema-invalid behavior stays visible without being rewarded as a passing result.

## Focused Harness-Fix Plan Before OpenRouter Retry

Status: IMPLEMENTED LOCALLY / DO NOT RUN LIVE YET

The first local Codex mini baseline batch is complete: `TMR-001` through `TMR-005` passed with `5.4 mini` low reasoning and no escalation. Future OpenRouter candidates should be compared against that exact local baseline, not against a generic mini-model expectation.

Before retrying Qwen, Step, Ring, DeepSeek, MiniMax, or any other OpenRouter candidate, the harness has been repaired locally in these areas:

1. Prompt repair task
   Implemented. The benchmark prompt requires a complete `DelegatedTaskResult`, rejects mode-only/partial output, and includes an explicit required-field checklist.

2. Risk-flag taxonomy task
   Implemented. The local delegated-result schema and harness validator define a canonical risk-flag taxonomy. Prompts show required and forbidden flags per case.

3. Scoring split task
   Implemented. Result cases now expose `mode_correct`, `schema_valid`, `risk_flags_complete`, `forbidden_flags_absent`, `production_safe`, and `failure_type` alongside the total score.

4. Schema projection task
   Implemented locally without weakening local validation. Known provider issues now have explicit projection behavior:

   | Provider issue | Required handling |
   | --- | --- |
   | MiniMax Boolean enum `[true]` incompatibility | Outbound provider schema drops Boolean enum constraints while local validation still requires `no_write_assertion` to be `true`. |
   | Previous `uniqueItems` incompatibility | Outbound provider schema continues stripping `uniqueItems`; local schemas remain stricter. |

5. OpenRouter retry task
   Still pending. Retry only after this local harness patch is reviewed. Use the five first-batch mini fixtures first; do not test `TMR-006` or higher-level tasks yet.

No-live retry fixture plan:

- `documentation/codex/openrouter-delegation/mini_retry_fixture_plan.md`
- Candidate models for the first retry handoff: `qwen/qwen3.7-plus`, then `stepfun/step-3.7-flash`
- Excluded for this pass: Ring, MiniMax, DeepSeek, Gemma, and Nemotron

Keep these current findings visible in the next scoring pass:

| Model | Finding to preserve |
| --- | --- |
| `qwen/qwen3.7-plus` | Mode-correct so far, but schema-invalid because required fields were missing. |
| `stepfun/step-3.7-flash` | Best schema-valid candidate so far, but one `ALLOW` schema-extraction case was classified `UNKNOWN`. |
| `inclusionai/ring-2.6-1t` | Misclassified an `ASSIST` case as `ALLOW`, had one timeout, and missed risk flags. |
| `minimax/minimax-m3` | Provider/schema incompatible until schema projection handles MiniMax-specific limits. |

Do not run OpenRouter from this plan. Do not treat this section as production routing approval.

Local validation after implementation:

- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --validate-only` -> PASS
- `python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --dry-run --models qwen/qwen3.7-plus` -> PASS
- `python -m py_compile documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py` -> PASS
- JSON/schema parse and provider schema projection smoke checks -> PASS
- Scoring smoke checks for complete output, missing required flags, forbidden flags, and schema-invalid mode-correct output -> PASS

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

For provider-shape debugging after explicit approval:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --models "nvidia/nemotron-nano-9b-v2:free" --output documentation\codex\openrouter-delegation\benchmark_result_free_nemotron_nano_debug_2026-06-11.json
```

The debug output must contain response shape metadata only, not prompts, content, headers, API keys, environment variables, private files, or raw repo data.

After the outbound schema projection patch, Gemma 31B may be retried with the same safety gates:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --models "google/gemma-4-31b-it:free" --output documentation\codex\openrouter-delegation\benchmark_result_free_gemma_31b_retry_2026-06-11.json
```

For long-running free-model retries, keep progress visible and bound each external request:

```powershell
python documentation\codex\openrouter-delegation\scripts\openrouter_delegation_benchmark.py --run-live --allow-external --debug-response-shape --request-timeout-seconds 120 --models "google/gemma-4-31b-it:free" --output documentation\codex\openrouter-delegation\benchmark_result_free_gemma_31b_retry_progress_2026-06-11.json
```

## Routing Recommendation

Prototype policy:

- `ALLOW`: sanitized mechanical extraction/classification only
- `ASSIST`: advisory scoring or wording suggestions only
- `DENY`: Git, final audit, release, repo writes, secrets, private files, broad source
- `UNKNOWN`: keep local and review policy

Current routing status:

`UNKNOWN` for all production delegation.
