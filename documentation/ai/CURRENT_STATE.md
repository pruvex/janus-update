# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Goal
Move from one-shot OpenRouter response testing toward a Codex CLI sidecar-agent strategy, so the Codex App can remain the operator while selected Janus skill work is delegated to a cheaper local agent run when the user chooses that option.

## Active Phase
Codex sidecar-agent runner hardening plus integrated normal-skill operator choice for bounded read-only documentation drafts. The prior documentation-skill OR evidence remains available, but the current focus has shifted to a broader delegation architecture where a separate `codex exec` run can act as a bounded workhorse and the Codex App reviews the result.

## Last Decision
The user clarified the target architecture: the goal is not primarily to replace tiny documentation outputs with one-shot OpenRouter calls. The goal is a sidecar-agent workflow:

- Codex App remains the main operator, reviewer, and Janus governance holder.
- A separate Codex CLI sidecar may run selected skill work with a cheaper model/provider.
- The user chooses at a gate whether to spend Codex App quota or delegate a bounded unit to the sidecar.
- Codex App accepts, rejects, or reruns based on local evidence.

The prior `5.4` documentation-skill classifications remain:

- `DOC-SKILL-002`: `KEEP_CODEX`
- `DOC-SKILL-006`: `KEEP_CODEX`
- `DOC-SKILL-008`: `FURTHER_TEST_CANDIDATE`

New sidecar evidence:

- local `codex exec --help` confirms sidecar-relevant flags: `--model`, `--oss`, `--local-provider`, `--cd`, `--sandbox`, `--output-last-message`, and `--json`; the installed CLI does not support the earlier assumed `--ask-for-approval` flag
- local `config.toml` does not show an obvious OpenRouter provider entry yet
- a dry-run Sidecar runner successfully produced command and evidence artifacts without launching an agent
- initial live sidecar attempts exposed Windows runner issues: PowerShell shim invocation, unsupported CLI flag, and unbounded child processes after interrupted Codex App tool calls
- the sidecar runner is now file-first and timeout-bounded; `SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002` returned controlled `TIMEOUT` after 20 seconds and left no matching child process
- `SIDECAR-LIVE-PILOT-READONLY-180-001` produced a completed read-only sidecar recommendation in both `stdout.log` and `last_message.md`
- the accepted sidecar recommendation selects `janus-documentation-update` as the first real read-only pilot class
- one runner bug remained after the accepted pilot: Windows returned a null exit-code path, so `summary.json` still said `FAILED`; the runner was patched to normalize artifact-backed success in that case
- `SIDECAR-LIVE-PILOT-READONLY-180-002` then returned clean `PASS` with `artifact_success=true`, `last_message_present=true`, and no matching lingering sidecar process
- `SIDECAR-DOC-DRAFT-001` then completed a real bounded read-only `janus-documentation-update` draft task with `status=PASS` and a non-binding milestone draft in `last_message.md`
- `doc_skill_sidecar_draft_runner.py` now provides the normal operator choice path for `janus-documentation-update` draft tasks with `prompt`, `local`, and `sidecar` modes
- `SIDECAR-DOC-FLOW-20260614-023725` validated the integrated helper in real `sidecar` mode and returned `SIDECAR_DRAFT_ACCEPTED_FOR_REVIEW`

## Last Codex Work
Hardened the Codex CLI sidecar runner after the first live pilot attempts hung under the Codex App, then completed the first accepted read-only live sidecar pilot, a clean confirmation rerun, the first real workflow-like documentation draft task, and finally integrated the sidecar operator choice into the normal `janus-documentation-update` flow. The runner now resolves the Windows `codex.ps1` shim to direct `node.exe ...\codex.js`, removes the unsupported live CLI approval flag from invocation, writes file-first artifacts, supports `TimeoutSeconds`, kills the child process tree on timeout, and treats completed runs with non-empty final artifacts as success when Windows leaves the exit code unset. A new helper, `doc_skill_sidecar_draft_runner.py`, now exposes the normal operator path with `prompt`, `local`, and `sidecar` modes, and its real sidecar validation run returned `SIDECAR_DRAFT_ACCEPTED_FOR_REVIEW`.

- eligibility matrix for `5.4`/`5.4 medium` documentation-skill rows
- price-based OR candidate shortlist using the existing OpenRouter catalog inventory
- staged evaluation plan from boundary review to fixture prep, local baseline, bounded OR fixture tests, and later replacement/assist matrix
- `DOC-SKILL-002-GPT54-LIVE-EVAL-001`
- `DOC-SKILL-006-GPT54-LIVE-EVAL-001`
- `DOC-SKILL-008-GPT54-LIVE-EVAL-001`
- one local baseline result note per fixture with pass-criteria review and explicit unverified-model caveat
- one comparison-plan artifact defining candidate order, stop rules, cost/capture gates, and explicit future approval phrasing
- one accepted telemetry JSONL batch file
- one technical-failure JSONL batch file
- one healthcheck summary from accepted telemetry ingestion
- one batch result note and one classification note
- one revised family-based `5.4` candidate shortlist
- one revised family-based `5.4` eval queue
- one accepted telemetry JSONL family-follow-up file for `DOC-SKILL-002`
- one failure JSONL family-follow-up file for `DOC-SKILL-002`
- one family-follow-up result note updated with cost split and evaluator caveat
- one versioned local evaluator for saved `5.4` documentation-skill OR responses
- one versioned local batch postcheck helper for saved `5.4` wrapper artifacts
- one family-follow-up result note updated with scripted re-evaluation findings
- one explicit next-run prep artifact for `DOC-SKILL-002` plus `openai/gpt-oss-120b`
- one rerun telemetry JSONL file for `DOC-SKILL-002` plus `openai/gpt-oss-120b`
- one rerun result note for `DOC-SKILL-002` plus `openai/gpt-oss-120b`
- one five-model batch plan artifact for the broadened `5.4` sweep
- one resume-safe multi-model batch runner for current `5.4` documentation fixtures
- one completed five-model batch telemetry JSONL file
- one five-model batch result note
- one five-model batch classification note
- one narrow retest plan for `DOC-SKILL-002` and `DOC-SKILL-006`
- one runner-level skill-override hook for retest prompts and `max_tokens`
- one retest manifest JSON for `DOC-SKILL-002` and `DOC-SKILL-006`
- one exact retest prep note with the executable batch command
- one retest telemetry JSONL file
- one retest result note
- one Codex CLI sidecar-agent execution plan
- one sidecar skill delegation matrix
- one dry-run-first sidecar runner script
- one sidecar dry-run prompt fixture
- one sidecar dry-run artifact package
- one sidecar dry-run result note
- one sidecar live-pilot debug/result note
- one timeout-guarded sidecar live probe package
- one accepted read-only sidecar live pilot package
- one accepted read-only sidecar documentation draft package
- one integrated documentation-skill sidecar operator-choice helper
- one integrated helper validation run package

No production routing, canonical routing-table update, Auto Router continuation, Git action, or sidecar write action occurred. One accepted read-only sidecar content result now exists for a non-binding recommendation only.

## Changed Files
- `documentation/codex/model-routing/gpt54_doc_skill_eligibility_matrix_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_or_candidate_price_shortlist_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_eval_plan_2026-06-14.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/*`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-LIVE-EVAL-001/*`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-008-GPT54-LIVE-EVAL-001/*`
- `documentation/codex/model-routing/gpt54_doc_skill_fixed_or_comparison_plan_2026-06-13.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_fixed_or_comparison_batch_2026-06-13.jsonl`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_fixed_or_comparison_batch_failures_2026-06-13.jsonl`
- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-FIXED-OR-COMPARISON-BATCH-001/*`
- `documentation/codex/model-routing/gpt54_doc_skill_fixed_or_comparison_batch_result_2026-06-13.md`
- `documentation/codex/model-routing/gpt54_doc_skill_fixed_or_comparison_classification_2026-06-13.md`
- `documentation/codex/model-routing/gpt54_or_candidate_family_shortlist_v2_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_family_eval_queue_v2_2026-06-14.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_family_followup_2026-06-14.jsonl`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_family_followup_failures_2026-06-14.jsonl`
- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/*`
- `documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py`
- `documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py`
- `documentation/codex/model-routing/gpt54_doc_skill_002_family_followup_result_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_002_openai_gpt_oss_120b_run_prep_2026-06-14.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_openai_gpt_oss_120b_rerun_2026-06-14.jsonl`
- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-OPENAI-GPT-OSS-120B-RERUN-001/*`
- `documentation/codex/model-routing/gpt54_doc_skill_002_openai_gpt_oss_120b_rerun_result_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_5model_batch_plan_2026-06-14.md`
- `documentation/codex/model-routing/scripts/gpt54_doc_skill_multi_model_batch_runner.py`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_5model_batch_2026-06-14.jsonl`
- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-5MODEL-BATCH-001/*`
- `documentation/codex/model-routing/gpt54_doc_skill_5model_batch_result_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_5model_batch_classification_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_plan_2026-06-14.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-002-GPT54-LIVE-EVAL-001/prompt_retest_v2_2026-06-14.md`
- `documentation/codex/model-routing/live-eval/DOC-SKILL-006-GPT54-LIVE-EVAL-001/prompt_retest_v2_2026-06-14.md`
- `documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_manifest_2026-06-14.json`
- `documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_prep_2026-06-14.md`
- `documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_006_retest_2026-06-14.jsonl`
- `documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-006-RETEST-001/*`
- `documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_agent_execution_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_skill_delegation_matrix_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1`
- `documentation/codex/model-routing/sidecar-fixtures/documentation_draft_pilot_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DRY-RUN-001/*`
- `documentation/codex/model-routing/codex_sidecar_agent_dry_run_result_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-fixtures/sidecar_live_pilot_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DRY-RUN-TIMEOUT-CHECK/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-TIMEOUT-GUARD-002/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-LIVE-PILOT-READONLY-180-002/*`
- `documentation/codex/model-routing/sidecar-fixtures/sidecar_documentation_update_draft_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-DRAFT-001/*`
- `documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-FLOW-20260614-023725/*`
- `documentation/codex/model-routing/codex_sidecar_agent_live_pilot_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_documentation_update_draft_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_agent_execution_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_skill_delegation_matrix_2026-06-14.md`
- `documentation/codex/skills/janus-documentation-update/SKILL.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Tests / Validation Performed
- Read `documentation/codex/model-routing/documentation_skill_routing_table_v1_2026-06-12.md`: PASS.
- Read `documentation/codex/openrouter-delegation/model_price_inventory_2026-06-12.md`: PASS.
- Reused existing catalog inventory only; no model inference endpoint used: PASS.
- `5.4` candidate artifacts created without touching the canonical routing table: PASS.
- Fixture package files for `DOC-SKILL-002`, `DOC-SKILL-006`, and `DOC-SKILL-008` exist: PASS.
- `input.sanitized.json` parses for all three fixture packages: PASS.
- local baseline result artifacts exist for `DOC-SKILL-002`, `DOC-SKILL-006`, and `DOC-SKILL-008`: PASS.
- pass-criteria review was recorded for all three baseline artifacts: PASS.
- bounded fixed-model comparison plan exists for the three-skill `5.4` scope: PASS.
- approved live comparison batch executed: PASS.
- accepted telemetry rows captured with `generation_id` and usage: PASS.
- healthcheck ingestion of the accepted telemetry file: PASS.
- technical provider failures captured separately: PASS.
- local inventory confirms presence of `Qwen`, `Kimi`, `GPT/Codex`, `GLM`, and `DeepSeek` family candidates: PASS.
- external comparison sources reviewed for broader family coverage: PASS.
- approved narrow family follow-up for `DOC-SKILL-002` executed with file-first capture: PASS.
- accepted telemetry for `ibm-granite/granite-4.1-8b` and `qwen/qwen3.5-flash-02-23` parsed and ingested by `health_snapshot.py`: PASS.
- `moonshotai/kimi-k2.6` failure capture preserved `generation_id`, usage, and actual cost despite telemetry exclusion: PASS.
- manual review of the saved `qwen/qwen3.5-flash-02-23` response body shows preserved non-production boundaries and indicates a validator false positive on negated authority wording: PASS.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py --skill-id DOC-SKILL-002 --response-body documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/qwen-qwen3.5-flash-02-23/response_body.json`: PASS.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py --skill-id DOC-SKILL-002 --response-body documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/ibm-granite-granite-4.1-8b/response_body.json`: PASS, with evaluation result `FAIL` as expected under stricter local rules.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py --skill-id DOC-SKILL-002 --response-body documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/qwen-qwen3.5-flash-02-23/response_body.json --response-summary documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/qwen-qwen3.5-flash-02-23/response_summary.json`: PASS, local batch acceptance `true`.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py --skill-id DOC-SKILL-002 --response-body documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/ibm-granite-granite-4.1-8b/response_body.json --response-summary documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-FAMILY-FOLLOWUP-001/ibm-granite-granite-4.1-8b/response_summary.json`: PASS, local batch acceptance `false`.
- historical `openai/gpt-oss-120b` `DOC-SKILL-002` telemetry row extracted and incorporated into the next-run prep artifact: PASS.
- approved live rerun for `DOC-SKILL-002` with `openai/gpt-oss-120b` executed with file-first capture: PASS.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py --skill-id DOC-SKILL-002 --response-body documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-OPENAI-GPT-OSS-120B-RERUN-001/openai-gpt-oss-120b/response_body.json --response-summary documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-OPENAI-GPT-OSS-120B-RERUN-001/openai-gpt-oss-120b/response_summary.json`: PASS, with local batch acceptance `false`.
- `python documentation/codex/skills/janus-health-check/scripts/health_snapshot.py --repo . --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_openai_gpt_oss_120b_rerun_2026-06-14.jsonl`: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/gpt54_doc_skill_multi_model_batch_runner.py documentation/codex/model-routing/scripts/gpt54_doc_skill_batch_postcheck.py documentation/codex/model-routing/scripts/gpt54_doc_skill_response_evaluator.py`: PASS.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_multi_model_batch_runner.py --workflow-id GPT54-DOC-SKILL-5MODEL-BATCH-001 --telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_5model_batch_2026-06-14.jsonl --run-root documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-5MODEL-BATCH-001 --skills DOC-SKILL-002 DOC-SKILL-006 DOC-SKILL-008 --models qwen/qwen3.5-flash-02-23 deepseek/deepseek-v4-flash z-ai/glm-5-turbo moonshotai/kimi-k2.6 openai/gpt-5.3-codex`: PASS, with batch resume and full completion.
- `health_snapshot.py --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_5model_batch_2026-06-14.jsonl`: PASS through the batch runner wrapper, `record_count=15`.
- narrow retest plan for `DOC-SKILL-002` and `DOC-SKILL-006` created and checked for scope consistency against the latest batch result and classification: PASS.
- batch runner override extension for skill-specific prompt files and `max_tokens`: PASS by local compile and request-body build validation.
- retest manifest JSON parse and prepared command review: PASS.
- `python documentation/codex/model-routing/scripts/gpt54_doc_skill_multi_model_batch_runner.py --workflow-id GPT54-DOC-SKILL-002-006-RETEST-001 --telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_006_retest_2026-06-14.jsonl --run-root documentation/codex/model-routing/fixed-or-live-runs/GPT54-DOC-SKILL-002-006-RETEST-001 --skills DOC-SKILL-002 DOC-SKILL-006 --models deepseek/deepseek-v4-flash qwen/qwen3.5-flash-02-23 --skill-overrides-json documentation/codex/model-routing/gpt54_doc_skill_002_006_retest_manifest_2026-06-14.json --per-call-cap 0.01 --total-cap 0.04`: PASS.
- `health_snapshot.py --or-telemetry-jsonl documentation/codex/model-routing/or_healthcheck_telemetry_gpt54_doc_skill_002_006_retest_2026-06-14.jsonl`: PASS through the retest runner wrapper, `record_count=4`.
- `codex exec --help`: PASS, sidecar-relevant CLI flags available.
- `codex debug models`: PASS, local catalog rendered.
- `powershell -NoProfile -ExecutionPolicy Bypass -File documentation/codex/model-routing/scripts/codex_sidecar_skill_runner.ps1 -RunDirectory documentation/codex/model-routing/sidecar-runs/SIDECAR-DRY-RUN-001 -PromptPath documentation/codex/model-routing/sidecar-fixtures/documentation_draft_pilot_prompt_2026-06-14.md -Model gpt-5.4 -Sandbox read-only -ApprovalPolicy never`: PASS, dry-run artifacts created and no sidecar agent executed.
- `git diff --check` for tracked files in this block: PASS.
- trailing-whitespace check for new fixture and baseline files: PASS.
- trailing-whitespace check for the comparison plan file: PASS.

## Open Risks
- The repository worktree still contains many unrelated modified and untracked files; staging must remain path-specific.
- Price inventory is from `2026-06-12`; future live eval planning should refresh or explicitly accept that price snapshot before cost gates.
- `DOC-SKILL-012` and `DOC-SKILL-017` still need safe upstream-bound maintenance fixtures before any OR comparison.
- `DOC-SKILL-004`, `DOC-SKILL-005`, `DOC-SKILL-014`, `DOC-SKILL-015`, final-output `DOC-SKILL-016`, and policy `DOC-SKILL-018` remain local-only.
- Runtime model identity is still not directly verifiable from this workspace turn, so the baseline artifacts remain review references rather than verified execution records.
- `inclusionai/ling-2.6-flash` was not meaningfully evaluated in the earlier batch because all three attempts hit upstream `429`.
- Runtime model identity for the local baseline references remains unverified even though the OR live batch is real.
- The broadened shortlist now has real family evidence, but only `DOC-SKILL-008` produced any passing replacement-style rows; broad family inclusion is still not the same as model approval.
- `moonshotai/kimi-k2.6` remains expensive for this `5.4` work and still produced one `finish_reason=length` capture-only row.
- `DOC-SKILL-002` is still highly sensitive to exact governance phrasing, so a prompt-contract revision may be required before any later retest.
- `DOC-SKILL-006` continues to drift on blocked-scope and operator-reminder wording even when capture and cost gates are fine.
- The new batch runner is now resume-safe, but it is still an adjacent experiment helper rather than a production workflow path.
- `DOC-SKILL-002` still appears highly sensitive to one exact governance line, especially `No global OpenRouter approval exists.`
- `DOC-SKILL-006` still fails even after the higher completion budget, so further retesting there is unlikely to pay off without changing the task contract itself.
- The retest weakens the budget-cap explanation, but it does not prove that no future prompt redesign could ever recover `DOC-SKILL-002`.
- OpenRouter-as-Codex-agent-backend is not yet verified in this local Codex CLI configuration.
- Local OSS sidecar support is visible in CLI flags, but no Ollama/LM Studio model readiness was tested in this block.
- Parallel sidecar execution is intentionally not enabled yet; the single-sidecar capture/review path must prove reliable first.

## Next Recommended Step for ChatGPT
Review the new sidecar-agent execution plan and decide whether the next pilot should be a harmless read-only `janus-documentation-update` draft or a read-only `janus-test-pipeline` test-plan draft.

## Next Recommended Step for Codex
Run one explicitly approved real sidecar pilot with `codex_sidecar_skill_runner.ps1 -Execute` in `read-only` mode, using a non-binding documentation or test-plan prompt. Keep Codex App as reviewer and do not allow parallel sidecars until the single-sidecar run is validated.

## Last Updated
2026-06-14 15:16 local time
