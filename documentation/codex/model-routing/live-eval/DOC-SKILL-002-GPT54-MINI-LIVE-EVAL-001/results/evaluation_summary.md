# DOC-SKILL-002 Reduced Live Evaluation Summary

Status: TASK_DECISION_RECORDED / EVIDENCE ONLY / NO PRODUCTION ROUTING

## Scope

Only DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001 was evaluated. No DOC-SKILL-003 or later task was run. No routing table was updated and no model was marked production-approved.

## Sequential Strategy

- Default candidate first: `openai/gpt-oss-20b`
- Backups are attempted only if the prior candidate is HOLD, FAIL, empty, malformed, or incomplete.
- Stop when a PASS candidate is found.
- Calibration note: the initial automated scorer over-flagged the default candidate's `Disabled: Yes` / `not scored as PASS` wording. Calibrated evidence review marks the default candidate PASS and retains the already-attempted backup_1 call as extra evidence.

## Counts

- Attempted: 2
- Completed with normalized model content: 2
- Skipped/not needed: 2
- PASS: 2
- HOLD: 0
- FAIL: 0

## Per-Model Results

| role | model | attempted | status | reason |
| --- | --- | --- | --- | --- |
| default | `openai/gpt-oss-20b` | TRUE | PASS | preserved HOLD, UNKNOWN, disabled state, `production_approved=false`, and no routing/production approval |
| backup_1 | `openai/gpt-oss-120b` | TRUE | PASS | extra evidence after initial scorer false-negative; not selected |
| backup_2 | `qwen/qwen3.5-flash-02-23` | FALSE | NOT RUN | not_needed_after_default_PASS_after_calibrated_review |
| backup_3 | `deepseek/deepseek-v4-flash` | FALSE | NOT RUN | not_needed_after_default_PASS_after_calibrated_review |

## Task-Level Decision

- Internal default: GPT-5.4 mini low
- Selected external candidate: `openai/gpt-oss-20b`
- Backup evidence: `openai/gpt-oss-120b` also PASS but not selected
- Remaining backups: NOT RUN / not needed

## Governance

These results are evidence only. They do not update routing tables, do not approve production routing, do not create a global documentation-skill winner, and do not authorize continuation to DOC-SKILL-003.
