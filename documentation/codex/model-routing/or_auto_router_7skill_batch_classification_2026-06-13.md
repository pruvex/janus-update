# OpenRouter Auto Router 7-Skill Batch Classification - 2026-06-13

Status: PARTIAL CLASSIFICATION / EXPERIMENT-ONLY / FIXED-MODEL AUTO-SPARSAM REMAINS CANONICAL

## Classification Table

| skill_id | classification | rationale |
| --- | --- | --- |
| `DOC-SKILL-001` | `KEEP_FIXED` | Auto Router selected openai/gpt-oss-120b and passed capture, but actual cost was much higher than the fixed openai/gpt-oss-20b baseline. |
| `DOC-SKILL-002` | `MANUAL_REVIEW` | Auto Router selected openai/gpt-oss-120b but stopped with finish_reason=length, so the batch aborted before accepting telemetry for this skill. |
| `DOC-SKILL-003` | `MANUAL_REVIEW` | This batch aborted at DOC-SKILL-002 before the skill was attempted, so there is no new 7-skill batch evidence for this skill and the fixed baseline remains canonical. |
| `DOC-SKILL-006` | `MANUAL_REVIEW` | This batch aborted at DOC-SKILL-002 before the skill was attempted, so there is no new 7-skill batch evidence for this skill and the fixed baseline remains canonical. |
| `DOC-SKILL-008` | `MANUAL_REVIEW` | This batch aborted at DOC-SKILL-002 before the skill was attempted, so there is no new 7-skill batch evidence for this skill and the fixed baseline remains canonical. |
| `DOC-SKILL-009` | `MANUAL_REVIEW` | This batch aborted at DOC-SKILL-002 before the skill was attempted, so there is no new 7-skill batch evidence for this skill and the fixed baseline remains canonical. |
| `DOC-SKILL-010` | `FURTHER_TEST_CANDIDATE` | The prior explicit DOC-SKILL-010 Auto Router classification remains in force because this batch aborted before reaching DOC-SKILL-010 and did not replace the existing bounded evidence. |

## Interpretation

- `DOC-SKILL-001`: `KEEP_FIXED` because the Auto Router route was materially more expensive than the accepted fixed baseline while delivering no routing-governance advantage.
- `DOC-SKILL-002`: `MANUAL_REVIEW` because the Auto Router route still hit `finish_reason=length`, which is not acceptable as clean bounded replacement evidence.
- `DOC-SKILL-010`: `FURTHER_TEST_CANDIDATE` remains the active Auto Router classification from the prior explicit DOC-SKILL-010 review. This batch did not supersede it because the batch aborted before the skill was reached.
- `DOC-SKILL-003`, `DOC-SKILL-006`, `DOC-SKILL-008`, and `DOC-SKILL-009`: `MANUAL_REVIEW` for this batch only because the batch did not reach those skills, so there is no new broad-batch evidence to classify as stable or baseline-replacing.

## Aggregate Result

- broad 7-skill Auto Router usefulness is not confirmed by this batch
- the only accepted row favored the fixed baseline (`CODEX_PREFERRED`)
- the second attempted row failed the completion adequacy gate and stopped the run early
- fixed-model Auto-sparsam remains canonical for all seven mini skills
- any future Auto Router follow-up would require explicit approval and should likely focus on completion-control before breadth expansion

## Boundary Reminder

- this classification note does not activate production routing
- this classification note does not update the canonical routing table
- this classification note does not create a global OR approval
- this classification note does not continue the separate `5.4` candidate phase
