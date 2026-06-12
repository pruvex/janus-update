# DOC-SKILL-001 Request Payload Manifest

Status: NOT RUN / NO OPENROUTER INFERENCE / NO RESULT JSON

## Scope

These request payloads are for DOC-SKILL-001 only. They prepare future request bodies for the 12 A1 candidates without sending OpenRouter requests, generating benchmark JSON, making routing decisions, or changing production status.

## Source Files

- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/input.sanitized.json`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/prompt.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/expected_reference.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001/live_eval_gate.md`
- `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`

## Generated Payload Files

| candidate | payload_file | status |
| --- | --- | --- |
| `deepseek/deepseek-v4-flash` | `DOC-SKILL-001__deepseek-deepseek-v4-flash__request_payload.json` | NOT RUN |
| `minimax/minimax-m3` | `DOC-SKILL-001__minimax-minimax-m3__request_payload.json` | NOT RUN |
| `nvidia/nemotron-3-nano-30b-a3b` | `DOC-SKILL-001__nvidia-nemotron-3-nano-30b-a3b__request_payload.json` | NOT RUN |
| `openai/gpt-5-mini` | `DOC-SKILL-001__openai-gpt-5-mini__request_payload.json` | NOT RUN |
| `openai/gpt-5-nano` | `DOC-SKILL-001__openai-gpt-5-nano__request_payload.json` | NOT RUN |
| `openai/gpt-5.1-codex-mini` | `DOC-SKILL-001__openai-gpt-5.1-codex-mini__request_payload.json` | NOT RUN |
| `openai/gpt-5.4-nano` | `DOC-SKILL-001__openai-gpt-5.4-nano__request_payload.json` | NOT RUN |
| `openai/gpt-oss-120b` | `DOC-SKILL-001__openai-gpt-oss-120b__request_payload.json` | NOT RUN |
| `openai/gpt-oss-20b` | `DOC-SKILL-001__openai-gpt-oss-20b__request_payload.json` | NOT RUN |
| `qwen/qwen3-235b-a22b-thinking-2507` | `DOC-SKILL-001__qwen-qwen3-235b-a22b-thinking-2507__request_payload.json` | NOT RUN |
| `qwen/qwen3.5-flash-02-23` | `DOC-SKILL-001__qwen-qwen3.5-flash-02-23__request_payload.json` | NOT RUN |
| `stepfun/step-3.7-flash` | `DOC-SKILL-001__stepfun-step-3.7-flash__request_payload.json` | NOT RUN |

## Governance

- No OpenRouter inference/model calls were run.
- No benchmark JSON was generated.
- No routing decision was made.
- No model is production-approved.
- Status remains NOT RUN.
- Stop after DOC-SKILL-001; do not batch DOC-SKILL-002 or later tasks.
