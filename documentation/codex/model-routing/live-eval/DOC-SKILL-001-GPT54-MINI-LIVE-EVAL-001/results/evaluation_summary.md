# DOC-SKILL-001 Live Evaluation Summary

Status: COMPLETED_EVALUATED / EVIDENCE ONLY / NO PRODUCTION ROUTING

## Scope

Only DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001 was evaluated. No DOC-SKILL-002 or later task was run. No routing table was updated and no model was marked production-approved.

## Counts

- Attempted: 12
- Completed with normalized model content: 10
- Failed/skipped attempts: 2
- PASS: 9
- HOLD: 3
- FAIL: 0

## Per-Model Results

| model | status | reason |
| --- | --- | --- |
| `deepseek/deepseek-v4-flash` | PASS | all required DOC-SKILL-001 checks passed |
| `minimax/minimax-m3` | PASS | all required DOC-SKILL-001 checks passed |
| `nvidia/nemotron-3-nano-30b-a3b` | PASS | all required DOC-SKILL-001 checks passed |
| `openai/gpt-5-mini` | PASS | all required DOC-SKILL-001 checks passed |
| `openai/gpt-5-nano` | HOLD | empty_content |
| `openai/gpt-5.1-codex-mini` | PASS | all required DOC-SKILL-001 checks passed |
| `openai/gpt-5.4-nano` | PASS | all required DOC-SKILL-001 checks passed |
| `openai/gpt-oss-120b` | PASS | all required DOC-SKILL-001 checks passed |
| `openai/gpt-oss-20b` | PASS | all required DOC-SKILL-001 checks passed |
| `qwen/qwen3-235b-a22b-thinking-2507` | HOLD | empty_content |
| `qwen/qwen3.5-flash-02-23` | PASS | all required DOC-SKILL-001 checks passed |
| `stepfun/step-3.7-flash` | HOLD | incomplete_response_missing_model_beta_completion_model_gamma_and_final_governance_note |

## Failed/Skipped Attempt Reasons

- `openai/gpt-5-nano`: empty_content
- `qwen/qwen3-235b-a22b-thinking-2507`: empty_content

## Required Checks

- Overall HOLD remains HOLD.
- Individual PASS model entries remain PASS.
- `production_approved=false` is preserved.
- No production routing approval.
- No production readiness inference.
- No repo-write/Git action suggested.
- No raw private prompt invention or exposure.
- No batch continuation to DOC-SKILL-002 or later.

## Governance

These results are evidence only. They do not update routing tables, do not approve production routing, do not canonically recommend an external model, and do not authorize continuation to DOC-SKILL-002.
