# GPT-5.4 Documentation Skill 5-Model Batch Plan - 2026-06-14

Status: APPROVED BOUNDED LIVE BATCH / NON-PRODUCTION / NO CANONICAL ROUTING-TABLE UPDATE

## Scoped Skills

- `DOC-SKILL-002`
- `DOC-SKILL-006`
- `DOC-SKILL-008`

Reason:

- these three currently have approved sanitized fixture packages and local baseline references
- `DOC-SKILL-012` and `DOC-SKILL-017` remain excluded because no approved safe maintenance fixtures exist yet

## Selected OR Models

- `qwen/qwen3.5-flash-02-23`
- `deepseek/deepseek-v4-flash`
- `z-ai/glm-5-turbo`
- `moonshotai/kimi-k2.6`
- `openai/gpt-5.3-codex`

Reason:

- covers the strongest currently interesting families discussed in the running `5.4` candidate phase
- preserves explicit user interest in `Qwen`, `Kimi`, `GPT/Codex`, `GLM`, and `DeepSeek`
- all five are present in the local OpenRouter inventory

## Batch Shape

- total planned calls: `15`
- comparison shape: `3 skills x 5 models`
- execution mode: file-first capture only
- local acceptance mode: hardened saved-artifact postcheck

## Estimated Cost Snapshot

Using the local `docs_summary` estimate from `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.json`:

- `qwen/qwen3.5-flash-02-23`: `0.00091000`
- `deepseek/deepseek-v4-flash`: `0.00107800`
- `z-ai/glm-5-turbo`: `0.01560000`
- `moonshotai/kimi-k2.6`: `0.01044500`
- `openai/gpt-5.3-codex`: `0.03500000`

Estimated total across `3` skills:

- `0.18909900`

## Hard Gates

- no production routing
- no canonical routing-table update
- no global OR approval
- no Auto Router
- file-first wrapper only
- save `request_body.json`, `response_body.json`, `response_headers.txt`, `response_summary.json`, `stdout.log`, `stderr.log`, `exit_code.txt` for every call
- every row must pass `gpt54_doc_skill_batch_postcheck.py` to count as locally accepted
- if raw capture and local postcheck disagree, the local postcheck wins for candidate interpretation

## Expected Outputs

- one batch telemetry JSONL file
- one batch result note
- one batch classification note
