# DOC-SKILL-003 Reduced Live Evaluation Summary

Status: TASK_DECISION_RECORDED / EVIDENCE ONLY / NO PRODUCTION ROUTING

## Scope

Only DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001 was evaluated. No DOC-SKILL-006 or later task was run. No routing table was updated and no model was marked production-approved.

## Sequential Strategy

- Default candidate first: `openai/gpt-oss-20b`
- Backups are attempted only if the prior candidate is HOLD, FAIL, empty, malformed, or incomplete.
- Stop when a PASS candidate is found.
- Calibration note: the initial evaluator over-required explicit non-binding wording. Calibrated evidence review marks the default candidate PASS because it preserves artifacts, gates, exclusions, and no final repo authority is granted. Already-attempted backups are retained as extra evidence.

## Counts

- Attempted: 4
- Completed with normalized model content: 4
- Skipped/not needed: 0
- PASS: 4
- HOLD: 0
- FAIL: 0

## Per-Model Results

| role | model | attempted | status | reason |
| --- | --- | --- | --- | --- |
| default | `openai/gpt-oss-20b` | TRUE | PASS | preserved bound artifacts, next skill/action, gate language, fixed exclusions, and no repo authority |
| backup_1 | `openai/gpt-oss-120b` | TRUE | PASS | extra evidence after initial evaluator false-HOLD; not selected |
| backup_2 | `qwen/qwen3.5-flash-02-23` | TRUE | PASS | extra evidence after initial evaluator false-HOLD; not selected |
| backup_3 | `deepseek/deepseek-v4-flash` | TRUE | PASS | extra evidence after initial evaluator false-HOLD; not selected |

## Task-Level Decision

- Internal default: GPT-5.4 mini low
- Selected external candidate: `openai/gpt-oss-20b`
- Backup evidence: all three backups also PASS but not selected

## Governance

These results are evidence only. They do not update routing tables, do not approve production routing, do not create a global documentation-skill winner, and do not authorize continuation to DOC-SKILL-006.
