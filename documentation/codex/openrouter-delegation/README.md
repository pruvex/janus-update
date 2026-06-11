# OpenRouter Delegation For Codex Development Workflow

Canonical state: DESIGN PROTOTYPE

Scope: Codex development-environment and skill-orchestration improvement. This is not a Janus application backlog item, not a production routing change, and not a Git governance path.

## Primary Sources Consulted

- Codex manual fetched by `openai-docs` on 2026-06-11: skills are available in Codex CLI, IDE extension, and Codex app; MCP configuration is shared by CLI and IDE extension; `codex exec` supports non-interactive runs and `--output-schema`.
- OpenRouter docs fetched on 2026-06-11:
  - `https://openrouter.ai/docs/quickstart`
  - `https://openrouter.ai/docs/api/reference/authentication`
  - `https://openrouter.ai/docs/guides/features/structured-outputs`
  - `https://openrouter.ai/docs/api/reference/overview`
  - `https://openrouter.ai/docs/guides/overview/models`
  - `https://openrouter.ai/docs/api/reference/limits`

## Goal

Create a diamond-standard way for Codex to delegate bounded, low-risk sub-tasks to OpenRouter models so Codex can save usage without weakening Janus governance.

The first version is read-only:

- no repo writes by delegated models
- no Git action delegation
- no release or final-audit PASS delegation
- no secrets or private local files sent externally
- no production routing until benchmark evidence exists

## Task Taxonomy

### ALLOW

OpenRouter may run these tasks when the prompt is fully sanitized and input is intentionally provided by Codex:

- summarize or classify short skill/governance excerpts
- extract fields into a strict JSON schema
- compare candidate routing options from already-redacted snippets
- score benchmark outputs against expected labels
- draft non-binding policy text for Codex review
- list current OpenRouter model metadata from the public models API

### ASSIST

OpenRouter may provide advisory output, but Codex must make the final decision:

- model comparison and cost/latency tradeoff summaries
- rough routing suggestions for low-risk workflow tasks
- benchmark result interpretation
- schema-shape suggestions
- documentation wording suggestions for governance docs

### DENY

OpenRouter must not perform these tasks:

- write files, patch code, run commands, or modify the repo
- stage, commit, push, tag, merge, release, or approve any Git action
- make final-audit PASS/PASS WITH FIXES/BLOCKED decisions
- make release-readiness or publish decisions
- inspect secrets, tokens, credentials, local databases, private logs, or private user data
- receive broad Janus source files, private runtime files, or unsanitized local history
- decide Janus product scope, backlog priority, release scope, or user-facing behavior
- bypass Janus skills, `AGENTS.md`, or `CURRENT_STATE`

### UNKNOWN

If a task is not clearly ALLOW or ASSIST, Codex must classify it as UNKNOWN and keep it local until the policy is updated by a human-reviewed Codex governance pass.

## Minimal Benchmark Corpus

The starter corpus lives in `benchmark_corpus.json`. It uses short sanitized governance snippets based on existing Codex/Janus skill patterns, not raw private project files.

Each case has:

- a task id
- a task type
- an input prompt
- privacy tier
- expected routing decision
- required risk flags
- scoring notes

The corpus is intentionally small. It validates whether candidate models can obey schema, preserve delegation boundaries, and deny tempting governance tasks.

## Gateway Design

The gateway is a local script:

`python documentation/codex/openrouter-delegation/scripts/openrouter_delegation_benchmark.py`

Default behavior is offline:

- `--dry-run`: show what would be sent
- `--validate-only`: validate local corpus and schemas
- `--list-models`: fetch public OpenRouter model metadata without sending task prompts

Live benchmark calls require all of these:

- `--run-live`
- `--allow-external`
- `--models <comma-separated model ids>`
- `OPENROUTER_API_KEY` in the current process environment

The script never reads arbitrary repo files for prompts. It only reads the curated benchmark corpus. That keeps data exfiltration boring in the best possible way.

Before sending a JSON Schema to OpenRouter, the harness projects the local schema into a provider-compatible request schema. It strips local or provider-incompatible schema keywords currently known to break providers: `$schema`, `$id`, and `uniqueItems`. The checked-in local schemas remain stricter and continue to be used for local validation.

Live benchmark operator feedback is intentionally narrow. The harness prints progress lines to stderr with task id, model id, coarse status, and elapsed milliseconds only. It does not print prompts, generated content, raw responses, headers, API keys, user ids, environment variables, private files, arbitrary repo files, or secrets.

External request timeouts are bounded by `--request-timeout-seconds`, defaulting to `120`. The timeout applies only to OpenRouter HTTP calls, not to dry-run, validate-only, or local privacy-tier deny behavior. Timeout results are recorded as `request_timeout` while preserving the benchmark-result JSON structure.

Optional debug mode:

- `--debug-response-shape` may be combined with live benchmark mode to diagnose provider response-shape mismatches.
- It records only safe response metadata for missing or invalid content: task id, model id, HTTP status, payload/choice/message key names, finish reason, content type/shape, and booleans for `reasoning`, `refusal`, `tool_calls`, and `parsed`.
- It must not record API keys, request headers, full prompts, full message content, raw private files, arbitrary repo files, secrets, or environment variables.

## Delegated Output Schema

Delegated model outputs must match `schemas/delegated_task_result.schema.json`.

Core fields:

- `schema_version`
- `task_id`
- `model_id`
- `delegation_mode`: `ALLOW`, `ASSIST`, `DENY`, or `UNKNOWN`
- `confidence`
- `summary`
- `findings`
- `required_codex_checks`
- `refusal_reason`
- `privacy_notes`
- `no_write_assertion`
- `risk_flags`

Codex treats schema failure as a benchmark failure, not as something to repair silently. Response-healing can be tested later as a separate model capability, but the baseline should measure native compliance first.

Invalid JSON failures are classified by safe response metadata when available:

- `finish_reason: length` -> `truncated_json`
- `finish_reason: error` -> `provider_generation_error`
- no finish-reason signal -> `invalid_json`
- HTTP 429 -> `rate_limited / HTTP 429`
- HTTP 200 top-level OpenRouter error payload -> `OpenRouter error payload returned with HTTP 200`

## Routing Policy

Decision order:

1. If input may contain secrets, private local files, personal data, credentials, local DB state, or broad source code, return `DENY`.
2. If the task asks for Git/release/final-audit authority, return `DENY`.
3. If the task asks for repo writes or command execution by OpenRouter, return `DENY`.
4. If the task is a sanitized mechanical extraction/classification, return `ALLOW`.
5. If the task is advisory and Codex remains the decision-maker, return `ASSIST`.
6. Otherwise return `UNKNOWN`.

Production delegation remains `DENY` until:

- at least two candidate models pass the benchmark corpus
- Codex reviews the scoring report
- privacy allowlists are explicit
- routing policy is versioned and documented
- the user explicitly approves moving from prototype to active use

## Model Scoring

The report lives in `model_scoring_report.md`.

Scoring dimensions:

- schema compliance
- correct route label
- risk flag recall
- concise evidence quality
- refusal quality for DENY cases
- cost and latency metadata when available

No model is production-approved by this prototype alone.

## Codex App Integration

Recommended first integration:

- Keep this as a local docs-plus-script workflow invoked by Codex from the app terminal.
- Add a future personal skill only after the benchmark harness is stable.
- Keep implicit invocation disabled for any future OpenRouter skill, because external delegation must be deliberate.
- Store the API key outside the repo as `OPENROUTER_API_KEY`, set only for the benchmark invocation.

Why this fits the app:

- Codex app can use skills and local scripts.
- The user remains in the same workspace and can inspect every artifact.
- The external boundary is visible at the command line.
- No app plugin or MCP server is required for the first read-only benchmark.

## Codex CLI Integration

Recommended CLI path:

- Use the same Python harness for model benchmarking.
- Use `codex exec --output-schema` only for local Codex-side evaluation or report generation, not for OpenRouter calls.
- If this grows into a service, implement a local MCP server with a narrow `benchmark_sanitized_case` tool and disabled-by-default external calls.

Avoid:

- passing `OPENROUTER_API_KEY` through broad shell environments
- storing benchmark prompts that include private project content
- letting an MCP server expose file-read or write tools

## Security And Privacy Constraints

- No secrets in docs, schemas, reports, logs, or `CURRENT_STATE`.
- No raw private files in prompts.
- No model outputs are trusted as authority.
- No delegated result may create a task, update backlog, update skills, or approve a gate without Codex review.
- Live benchmark logs should record model id, task id, route label, elapsed time, and cost if returned, not full private prompts beyond the sanitized corpus.

## Prototype Status

Implemented artifacts:

- task taxonomy and routing policy
- minimal benchmark corpus
- delegated output JSON Schema
- benchmark result JSON Schema
- read-only benchmark harness
- initial scoring report shell

Blocked for live scoring:

- `OPENROUTER_API_KEY` is not present in this shell.
- No user approval has been given for live external benchmark calls.

Known debug path:

- `nvidia/nemotron-nano-9b-v2:free` produced no chat completion content for all external cases in one free-model benchmark.
- Follow-up debug evidence showed HTTP 200 responses with top-level `error` payloads and no `choices` or `message`.
- The harness classifies that shape as `OpenRouter error payload returned with HTTP 200`.
- Treat the model as incompatible/pending until a future provider response changes.
- `google/gemma-4-31b-it:free` produced HTTP 200 top-level `error` payloads with a sanitized OpenInference grammar error: `Unimplemented keys: ["uniqueItems"]`.
- Retry Gemma 31B only after the outbound schema projection strips `uniqueItems`, using `--debug-response-shape`.
