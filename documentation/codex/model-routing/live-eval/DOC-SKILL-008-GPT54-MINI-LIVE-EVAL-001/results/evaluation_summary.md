# DOC-SKILL-008 Reduced Live Evaluation Summary

Status: TASK_DECISION_RECORDED / EVIDENCE ONLY / NO PRODUCTION ROUTING

## Scope

Only DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001 was evaluated. No DOC-SKILL-009 or later task was run. No routing table was updated and no model was marked production-approved.

## Sequential Strategy

- Default candidate first: `openai/gpt-oss-20b`
- Backups are attempted only if the prior candidate is HOLD, FAIL, empty, malformed, or incomplete.
- Stop when a PASS candidate is found.
- Calibration note: do not over-require the exact phrase `non-binding` when governance boundaries are clearly preserved.

## Counts

- Attempted: 3
- Completed with normalized model content: 3
- Skipped/not needed: 1
- PASS: 1
- HOLD: 2
- FAIL: 0

## Per-Model Results

| role | model | attempted | status | reason |
| --- | --- | --- | --- | --- |
| default | `openai/gpt-oss-20b` | TRUE | HOLD | no_repo_write_delegation |
| backup_1 | `openai/gpt-oss-120b` | TRUE | HOLD | uses_validated_facts, no_repo_write_delegation |
| backup_2 | `qwen/qwen3.5-flash-02-23` | TRUE | PASS | all required DOC-SKILL-008 checks passed |
| backup_3 | `deepseek/deepseek-v4-flash` | FALSE | NOT RUN | not_needed_after_prior_PASS |

## Task-Level Decision

- Internal default: GPT-5.4 mini low
- Selected external candidate: `qwen/qwen3.5-flash-02-23`
- Later backups: NOT RUN / not needed

## Governance

These results are evidence only. They do not update routing tables, do not approve production routing, do not create a global documentation-skill winner, and do not authorize continuation to DOC-SKILL-009.
