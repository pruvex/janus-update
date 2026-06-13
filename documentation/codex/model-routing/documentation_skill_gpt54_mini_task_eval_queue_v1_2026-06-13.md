# Documentation Skill GPT-5.4 Mini Task Eval Queue v1 - 2026-06-13

Status: PLANNING + LIVE-EVAL CLOSEOUT / DOC-SKILL-010 TASK_DECISION_RECORDED / NO OPENROUTER INFERENCE

## Purpose

Prepare the per-task live-evaluation queue for documentation-skill tasks whose current routing allows `5.4 mini`.

This artifact does not run model calls, fetch live pricing, generate benchmark JSON, activate OpenRouter routing, enable production routing, or approve any external model. Each task must be evaluated separately before moving to the next task.

## Shared References

- Routing table: `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`
- Evaluation plan: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md`
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`

## Eligible Task Count

7

## DOC-SKILL-001 - Summarize benchmark JSON

- Task id: DOC-SKILL-001
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized benchmark-result summaries that preserve HOLD/PASS and `production_approved=false`; blocked for routing decisions, production approval, raw private prompts, and repo-write action.
- Required model/reasoning: `5.4 mini` low; script-first when possible.
- Proposed single-task fixture name: `DOC-SKILL-001-GPT54-MINI-LIVE-EVAL-001`
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-002 - Summarize model scoring report

- Task id: DOC-SKILL-002
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized scoring-evidence summaries that preserve HOLD, UNKNOWN, and disabled states; blocked for routing approval, policy override, production activation, and private evidence interpretation.
- Required model/reasoning: `5.4 mini` low; `5.4` medium if policy nuance rises.
- Proposed single-task fixture name: `DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Reduced live-evaluation result: selected external candidate `openai/gpt-oss-20b`; `openai/gpt-oss-120b` retained as PASS backup evidence; remaining backups NOT RUN / not needed.
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-003 - Draft Codex handoff

- Task id: DOC-SKILL-003
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized copy-safe handoff wording with fixed exclusions and gate language; blocked for skipping gates, broad context expansion, implementation authority, Git authority, and release authority.
- Required model/reasoning: `5.4 mini` low.
- Proposed single-task fixture name: `DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-003-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Reduced live-evaluation result: selected external candidate `openai/gpt-oss-20b`; all three backups retained as PASS backup evidence.
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-006 - Format Markdown Documentation

- Task id: DOC-SKILL-006
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized mechanical Markdown cleanup that preserves meaning and authority boundaries; blocked for repo-write delegation and semantic rewrites that change policy or product meaning.
- Required model/reasoning: `5.4 mini` low for sanitized text; `5.4` low or medium for repo docs.
- Proposed single-task fixture name: `DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Reduced live-evaluation result: selected external candidate `openai/gpt-oss-120b`; default candidate retained as HOLD; later backups NOT RUN / not needed.
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-008 - Write Changelog-Style Summary

- Task id: DOC-SKILL-008
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized changelog bullets from validated facts without implying release readiness; blocked for release approval, invented behavior, and product-scope expansion.
- Required model/reasoning: `5.4 mini` low for sanitized draft; `5.4` medium for real changelog work.
- Proposed single-task fixture name: `DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Reduced live-evaluation result: selected external candidate `qwen/qwen3.5-flash-02-23`; `openai/gpt-oss-20b` and `openai/gpt-oss-120b` were HOLD; `deepseek/deepseek-v4-flash` was not needed after prior PASS.
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-009 - Update SKILL_USAGE_LOG Summary

- Task id: DOC-SKILL-009
- Routing-table summary: `SCRIPT_ONLY`; sanitized summary review may use `5.4 mini`, while real append remains local script plus Codex review; blocked for external append operations and repo-local raw log delegation.
- Required model/reasoning: Script-first; `5.4 mini` low for sanitized summary review.
- Proposed single-task fixture name: `DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001`
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-009-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Reduced live-evaluation result: selected external candidate `qwen/qwen3.5-flash-02-23`; `openai/gpt-oss-20b` and `openai/gpt-oss-120b` were HOLD; `deepseek/deepseek-v4-flash` was not needed after prior PASS.
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.

## DOC-SKILL-010 - Prepare Non-Binding Review Notes

- Task id: DOC-SKILL-010
- Routing-table summary: `OR_ASSIST_CANDIDATE` for sanitized advisory wording notes with no authority language; blocked for task creation, approval language, repo-write claims, and policy decisions.
- Required model/reasoning: `5.4 mini` low.
- Proposed single-task fixture name: `DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001`
- Prepared fixture path: `documentation/codex/model-routing/live-eval/DOC-SKILL-010-GPT54-MINI-LIVE-EVAL-001/`
- Candidate strategy: default `openai/gpt-oss-20b`; backups `openai/gpt-oss-120b`, `qwen/qwen3.5-flash-02-23`, `deepseek/deepseek-v4-flash`.
- Expected pass/fail rubric reference: `documentation/codex/model-routing/documentation_skill_or_candidate_evaluation_plan_v1_2026-06-12.md#passfail-rubric`
- A1 candidate set reference: `documentation/codex/model-routing/openrouter_doc_skill_a1_shortlist_2026-06-12.csv`
- Reduced live-evaluation result: selected external candidate `qwen/qwen3.5-flash-02-23`; `openai/gpt-oss-20b` and `openai/gpt-oss-120b` were HOLD; `deepseek/deepseek-v4-flash` was NOT RUN / not needed after first PASS.
- Status: TASK_DECISION_RECORDED
- Note: Evaluate this task separately before moving to the next task.
