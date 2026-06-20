# GPT-5.4 Nano Non-Production Routing Proposal - 2026-06-12

Status: REVIEW-ONLY PROPOSAL / NO ROUTING ACTIVATION

This document proposes a strictly non-production pilot boundary for `openai/gpt-5.4-nano` after its clean five-fixture mini retry. It does not activate routing, does not approve production use, and does not authorize OpenRouter to make Git, audit, release, product, backlog, or policy decisions.

Any routing change requires explicit user approval after Codex/ChatGPT review.

## Evidence Summary

`openai/gpt-5.4-nano` is the first clean `MINI_REPLACEMENT_CANDIDATE` for the first-batch mini fixtures.

Evidence file:

- `documentation/codex/openrouter-delegation/benchmark_result_gpt54_nano_mini_retry_2026-06-12.json`

Reviewed result:

| diagnostic | result |
| --- | --- |
| `run_status` | `complete` |
| `completed_cases / expected_cases` | `5/5` |
| `schema_valid` | `5/5` |
| `mode_correct` | `5/5` |
| `risk_flags_complete` | `5/5` |
| `forbidden_flags_absent` | `5/5` |
| `production_safe` | `5/5` |
| `production_approved` | `false` |

Local baseline to match:

- `5.4 mini low` passed `TMR-001` through `TMR-005` cleanly.

Prior candidates remain `HOLD`:

- `qwen/qwen3.7-plus`: schema-invalid on `5/5` mini retry cases.
- `stepfun/step-3.7-flash`: one mode failure and one production-safety failure on retry 2.
- `minimax/minimax-m3`: provider/schema compatibility history.
- `inclusionai/ring-2.6-1t`: timeout, missing risk flags, and `ASSIST`/`ALLOW` issue.
- Free and zero-price models: `HOLD` / inconclusive for stable routing.

## Candidate Task Class

Allowed only for non-production evaluation with public or sanitized inputs:

- short public/sanitized governance classification
- strict JSON extraction from public/sanitized docs
- advisory-only mini model-routing interpretation
- advisory-only wording or compact summary suggestions for Codex review
- curated mini fixtures or reviewed public/sanitized mini tasks

Explicitly out of scope:

- code patching
- repo writes
- command execution
- Git staging, commit, push, tag, merge, or release
- final audit decisions
- release readiness or publish decisions
- production routing decisions
- Janus product scope, backlog priority, or user-facing behavior decisions
- private data, secrets, private local files, private logs, local databases, broad source trees, dirty worktree content, or unredacted Janus history

## Proposed Non-Production Pilot Scope

The safest pilot shape, if approved later:

- Use only curated mini fixtures or individually reviewed public/sanitized mini tasks.
- Use single-model runs only: `openai/gpt-5.4-nano`.
- Do not run parallel OpenRouter model tests in the same pilot step.
- Treat output as advisory evidence for Codex/ChatGPT review.
- Require complete `DelegatedTaskResult` output.
- Require the existing diagnostic components: `mode_correct`, `schema_valid`, `risk_flags_complete`, `forbidden_flags_absent`, `production_safe`, and `failure_type`.
- Keep the local `5.4 mini low` baseline as fallback and comparison target.
- Store any generated benchmark JSON as local evidence only unless separately reviewed and explicitly accepted.

This pilot would still be non-production. It would not change Janus routing policy by itself.

## Fallback Policy

For any future non-production pilot or reviewed mini task, immediately fall back to local `5.4 mini low` if any of these occurs:

- schema failure
- wrong `delegation_mode`
- missing required risk flags
- forbidden risk flags present
- production-safety failure
- provider timeout
- provider or transport error
- ambiguous, non-scoreable, truncated, or invalid output
- implied production approval
- implied Git, repo-write, command-execution, final-audit, release, product, backlog, or routing-policy authority

Fallback means Codex keeps the task local and treats the OpenRouter output as failed evidence, not as a partial pass.

## Open Questions

1. Is one clean five-fixture pass enough for a non-production pilot?
2. Should a second `openai/gpt-5.4-nano` confirmation run be required before any pilot?
3. Should `openai/gpt-5-mini` be tested as a comparison before any pilot?
4. Should larger-task cost reduction be handled separately from mini replacement?
5. Should the pilot include only harness fixtures first, or also one reviewed real sanitized mini task?

## Recommendation Options

| option | decision | tradeoff |
| --- | --- | --- |
| A | Hold and run a second Nano confirmation. | Best confidence before pilot; spends another live run. |
| B | Hold and test `openai/gpt-5-mini` next. | Gives a same-family comparison; delays Nano pilot decision. |
| C | Prepare a strictly non-production Nano pilot with fallback. | Uses current clean evidence; must keep strong fallback and no-production boundaries. |
| D | Stop here and keep `5.4 mini low`. | Lowest external-delegation risk; forgoes Nano cost advantage for now. |

## Review Recommendation

Preferred next decision: choose between option A and option C.

- Choose A if confidence should require repeatability before any pilot.
- Choose C if one clean five-fixture pass is enough to draft a narrowly bounded, non-production pilot plan with automatic fallback to local `5.4 mini low`.

Do not choose any option as production activation. Production routing remains `UNKNOWN`/disabled.

## Non-Approval Statement

`openai/gpt-5.4-nano` is the first clean `MINI_REPLACEMENT_CANDIDATE`, not an approved production router.

This proposal does not activate routing. Any routing change requires explicit user approval, and any production use requires a separate governance decision after review.
