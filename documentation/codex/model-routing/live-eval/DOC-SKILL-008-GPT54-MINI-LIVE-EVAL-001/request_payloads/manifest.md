# DOC-SKILL-008 Request Payload Manifest

Status: NOT RUN / NO OPENROUTER INFERENCE / NO RESULT JSON

## Scope

These request payloads are for DOC-SKILL-008 only. They prepare future request bodies for the reduced candidate strategy without sending OpenRouter requests, generating benchmark JSON, making routing decisions, or changing production status.

## Candidate Strategy

- Default external candidate: `openai/gpt-oss-20b`
- Backups, only if needed:
  1. `openai/gpt-oss-120b`
  2. `qwen/qwen3.5-flash-02-23`
  3. `deepseek/deepseek-v4-flash`

## Source Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`

## Generated Payload Files

| role | candidate | payload_file | status |
| --- | --- | --- | --- |
| default | `openai/gpt-oss-20b` | `DOC-SKILL-008__openai-gpt-oss-20b__request_payload.json` | NOT RUN |
| backup 1 | `openai/gpt-oss-120b` | `DOC-SKILL-008__openai-gpt-oss-120b__request_payload.json` | NOT RUN |
| backup 2 | `qwen/qwen3.5-flash-02-23` | `DOC-SKILL-008__qwen-qwen3.5-flash-02-23__request_payload.json` | NOT RUN |
| backup 3 | `deepseek/deepseek-v4-flash` | `DOC-SKILL-008__deepseek-deepseek-v4-flash__request_payload.json` | NOT RUN |

## Scorer Calibration

- Do not over-require the exact phrase `non-binding` if the response clearly preserves governance boundaries.
- PASS may be recorded when validated facts, no-release-readiness boundaries, exclusions, task boundaries, and no-authority constraints are preserved.
- HOLD or FAIL remains required for genuine omissions, malformed output, empty content, or production/routing authority claims.

## Governance

- No OpenRouter inference/model calls were run.
- No benchmark JSON was generated.
- No routing decision was made.
- No model is production-approved.
- Status remains NOT RUN.
- Stop after DOC-SKILL-008; do not batch DOC-SKILL-009 or later tasks.
