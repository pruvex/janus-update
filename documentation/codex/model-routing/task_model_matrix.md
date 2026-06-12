# Janus Codex Task-To-Model Matrix

Status: PROPOSED / REVIEW REQUIRED

Date: 2026-06-12

Scope: Codex development-environment and skill-orchestration only. This document does not approve production routing, Git actions, final-audit outcomes, release decisions, repo writes, command execution, or external delegation for private Janus data.

## Sources

- `AGENTS.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/CODEX_PROJECT_PROFILE.md`
- `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`
- `documentation/pipeline/PIPELINE_CONTRACT.md`
- `documentation/codex/SKILL_USAGE_LOG.md`
- `documentation/codex/openrouter-delegation/README.md`
- `documentation/codex/openrouter-delegation/benchmark_corpus.json`
- `documentation/codex/openrouter-delegation/model_scoring_report.md`
- Installed Janus skill working copies under `C:\Users\pruve\.codex\skills\janus-*`

## Current OpenRouter Evidence

This evidence is local development evidence only. It must not be read as production approval and the generated benchmark JSON files must not be committed unless a later governance pass explicitly approves a safe artifact set.

| Model | Current read | Status |
| --- | --- | --- |
| `inclusionai/ring-2.6-1t` | Promising schema-valid `ALLOW` cases, but missed risk flags, had one timeout, and classified an `ASSIST` case as `ALLOW`. | HOLD |
| `stepfun/step-3.7-flash` | Best schema-valid candidate so far; correct `DENY`/`ASSIST` behavior, but one `ALLOW` schema-extraction case was `UNKNOWN`; risk flags often missing. | HOLD |
| `minimax/minimax-m3` | Provider/schema incompatible. OpenRouter returned HTTP 200 top-level error payloads with MiniMax invalid-params schema mismatch. | HOLD until schema projection fix |
| `qwen/qwen3.7-plus` | Strongest mode classifier so far; selected the correct delegation mode for all external cases, but omitted required fields and failed local schema validation. | HOLD until prompt/schema compliance improves |
| Free Gemma 26B | Rate-limited and inconclusive. | HOLD |
| Free Gemma 31B | Unreliable after retries; repeated truncated/invalid JSON and long response times. | HOLD |
| Nemotron Nano free | Incompatible with current benchmark path. | EXCLUDED |

## Hard Boundaries

OpenRouter is `DENY` for:

- Git staging, commit, push, tag, merge, reset, release, or GitHub publication authority.
- Final audit `PASS`, `PASS WITH FIXES`, `BLOCKED`, release-readiness, publish, or production routing decisions.
- Repo writes, code patching, command execution, test execution, or local process control.
- Secrets, credentials, private local files, private logs, local databases, personal runtime state, broad source trees, or unredacted chat/worktree history.
- Janus product scope, backlog priority, release scope, user-facing behavior decisions, or anything that bypasses the Janus skill pipeline.

## Matrix

| task_id | task_name | source_artifact | task_class | risk_class | data_class | current_codex_candidate | codex_reasoning_candidates | openrouter_allowed | required_output_shape | minimum_quality_gate | minimal_local_test | openrouter_candidate_models | fallback_model | decision_owner | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TMR-001 | Sanitized skill/governance excerpt classification | `README.md`; `benchmark_corpus.json`; `janus-skill-router` | MINI_CANDIDATE | low | sanitized governance excerpt | `5.4 mini` | low, medium, high | ALLOW | `DelegatedTaskResult` with `delegation_mode`, summary, risk flags, `no_write_assertion` | Schema-valid; exact mode; includes `sanitized_input` or equivalent; no authority expansion | Classify one 2-sentence sanitized router excerpt as `ALLOW`; score exact mode and required flags | `qwen/qwen3.7-plus`; `stepfun/step-3.7-flash`; `inclusionai/ring-2.6-1t` | `5.4` low | Codex review, user approves policy changes | PROPOSED MINI |
| TMR-002 | Public or sanitized schema-bound extraction | `benchmark_corpus.json`; `README.md` | MINI_CANDIDATE | low | public or sanitized text only | `5.4 mini` | low, medium, high | ALLOW | Strict JSON or `DelegatedTaskResult`, depending on harness case | All required fields present; exact labels; no private-data assumptions | Extract `ALLOW`, `ASSIST`, `DENY`, `UNKNOWN` meanings from a public snippet | `qwen/qwen3.7-plus`; `stepfun/step-3.7-flash`; `inclusionai/ring-2.6-1t` | `5.4` low | Codex review, user approves policy changes | PROPOSED MINI |
| TMR-003 | Non-binding benchmark result interpretation | `model_scoring_report.md`; local sanitized result summaries | MINI_CANDIDATE | low-medium | sanitized benchmark summary, no raw private prompt/content | `5.4 mini` | low, medium, high | ASSIST_ONLY | Short recommendation plus explicit `HOLD`/`NO_PRODUCTION_APPROVAL` caveat | Does not approve routing; identifies schema vs mode failures separately; names Codex checks | Interpret a 3-row sanitized model-score table and recommend `HOLD` vs `CONTINUE TESTING` | `qwen/qwen3.7-plus`; `stepfun/step-3.7-flash`; `inclusionai/ring-2.6-1t` | `5.4` medium | Codex review, user decides next tests | PROPOSED MINI |
| TMR-004 | Non-binding model cost/latency comparison | `model_scoring_report.md`; public OpenRouter metadata summaries | MINI_CANDIDATE | low | public model metadata or sanitized table | `5.4 mini` | low, medium, high | ASSIST_ONLY | Ranked advisory table with confidence and missing-data notes | No production approval; no live calls; every candidate has fallback; flags missing metadata | Rank 4 fake/public candidates from cost/latency/schema-support columns | `qwen/qwen3.7-plus`; `stepfun/step-3.7-flash`; `inclusionai/ring-2.6-1t`; future deepseek candidate | `5.4` low | Codex review, user decides next tests | PROPOSED MINI |
| TMR-005 | Documentation wording suggestion | `CODEX_WORKFLOW_PLAYBOOK.md`; `README.md`; sanitized excerpt | MINI_CANDIDATE | low | public or sanitized excerpt only | `5.4 mini` | low, medium, high | ASSIST_ONLY | Suggested wording plus rationale and "Codex must edit" statement | No direct repo write; no policy authority; preserves hard deny rules | Rewrite one sanitized "do not test yet" paragraph to be clearer without changing policy | `qwen/qwen3.7-plus`; `stepfun/step-3.7-flash`; `inclusionai/ring-2.6-1t` | `5.4` low | Codex writes after review; user owns policy | PROPOSED MINI |
| TMR-006 | Skill routing and model gate selection | `AGENTS.md`; `janus-skill-router`; `CODEX_WORKFLOW_PLAYBOOK.md` | GPT_5_4_CANDIDATE | medium | local governance docs and active user request | `5.4` | medium, high | DENY | `MODEL SWITCH GATE` plus next skill and context strategy | Must respect current artifacts and stop on model/chat switch | Local-only route a sanitized Janus request from supplied docs | N/A | `5.5` medium/high for risky routing | Codex | LOCAL ONLY |
| TMR-007 | Backlog intake for user bug/change | `janus-backlog-intake`; `BACKLOG.md` | GPT_5_4_CANDIDATE | medium | user request, project backlog | `5.4` | medium | DENY | Backlog item or NEEDS_INFO/QUICKCHANGE candidate | No direct `IN PROGRESS`/`DONE`; no invented requirements | Local-only validate one synthetic intake against required fields | N/A | `5.4` medium | Codex, user for missing decisions | LOCAL ONLY |
| TMR-008 | Backlog prioritization and recommendation | `janus-backlog-prioritization`; `BACKLOG.md` | HUMAN_ONLY | medium-high | local backlog priorities and product context | `5.4` | medium, high | DENY | Backlog review with recommendation and handoff target | User/Codex retain priority authority; no broad unrelated history | Local-only classify one existing open item when explicitly bound | N/A | `5.5` high for high-risk ambiguity | User/Codex | LOCAL ONLY |
| TMR-009 | Dashboard-ready backlog handoff | `janus-backlog-handoff`; dashboard snapshot | GPT_5_4_CANDIDATE | medium | local backlog and dashboard data | `5.4` | medium | DENY | Handoff artifact and dashboard metadata | Single selected item; correct entry point; validator pass if available | Local-only prepare handoff from one bound READY item | N/A | `5.4` medium | Codex | LOCAL ONLY |
| TMR-010 | Feature design / product behavior decisions | `janus-feature-design`; `AGENTS.md` | HUMAN_ONLY | medium-high | user goals and Janus product behavior | `5.4` | medium, high | DENY | `LATEST DECISION SUMMARY` or blocking questions | User decisions locked; no implementation/task creation | Local-only decision checklist on synthetic feature prompt | N/A | `5.5` high for security/privacy-heavy design | User owns decisions, Codex structures | LOCAL ONLY |
| TMR-011 | Spec generation | `janus-spec-generator`; `documentation/SPEC/` | GPT_5_4_CANDIDATE | medium-high | approved decision summary, product requirements | `5.4` | medium, high | DENY | Diamond Feature Spec v4.4.3 | No TBD/maybe/optional core decisions; exact section order | Local-only generate from one approved synthetic decision summary | N/A | `5.5` high for architecture/security risk | Codex, user approves decisions | LOCAL ONLY |
| TMR-012 | Spec normalization | `janus-spec-normalizer`; `documentation/SPEC/` | GPT_5_4_CANDIDATE | low-medium | local spec draft | `5.4` or `5.4 mini` if isolated | low, medium | DENY | Parser-safe normalized spec | Validator pass; no requirement changes | Local-only normalize one bound synthetic malformed spec | N/A | `5.4` medium | Codex | LOCAL ONLY |
| TMR-013 | Spec review / approval gate | `janus-spec-review`; `PIPELINE_CONTRACT.md` | HIGH_LOCAL_ONLY | high | product requirements and risk assessment | `5.5` for high-risk review, otherwise `5.4` high | high | DENY | Review decision and metadata block | Must not approve ambiguous security/privacy/persistence scope | Local-only review one bound spec excerpt; no external authority | N/A | `5.5` high | Codex, user for scope choices | LOCAL ONLY |
| TMR-014 | Spec-to-task compilation | `janus-spec-to-task`; task artifacts | GPT_5_4_CANDIDATE | medium | approved spec and task structure | `5.4` | medium, high | DENY | Deterministic task file | Tasks map to spec only; no implementation; validator pass | Local-only compile one approved synthetic spec section into task outline | N/A | `5.5` high for ambiguous decomposition | Codex | LOCAL ONLY |
| TMR-015 | Task breakdown and precheck release | `janus-task-breakdown`; `janus-preimplementation-check` | GPT_5_4_CANDIDATE | medium-high | local spec/task/test artifacts | `5.4` | medium, high | DENY | One target task and precheck handoff | Exactly one target; evidence plan present; no scope escape | Local-only validate one bound task handoff | N/A | `5.5` high for high-risk ambiguity | Codex | LOCAL ONLY |
| TMR-016 | Code execution / patching | `janus-executioner`; bound task/precheck | HIGH_LOCAL_ONLY | high | source code, tests, local runtime | `5.4` | medium, high | DENY | Patch plus execution result and evidence | Valid precheck; command-first test plan; executed validation | Local-only, never OpenRouter; targeted tests only | N/A | `5.5` high only for risk analysis, not patch authority | Codex | LOCAL ONLY |
| TMR-017 | Debug failed implementation/test/runtime behavior | `janus-debug`; `WHAT_I_LEARNED` targeted search | HIGH_LOCAL_ONLY | high | local failures, logs, code, runtime state | `5.4` or `5.5` for complex/security/provider risk | high | DENY | Debug result with root cause, fix/evidence or blocker | Bounded iterations; secret redaction; no private logs externalized | Local-only debug package review from sanitized excerpt if needed | N/A | `5.5` high | Codex | LOCAL ONLY |
| TMR-018 | TestSpec/TestRun pipeline | `janus-test-pipeline`; `documentation/TEST_SPEC/`; test-runs/results | GPT_5_4_CANDIDATE | medium-high | local test artifacts, generated runners/results | `5.4` | medium, high | DENY | TestPlan/TestRun/result/triage/retest audit output | Generated artifacts validated; no raw transient logs unless governed | Local-only validate one synthetic test plan schema | N/A | `5.5` high for release-critical ambiguity | Codex | LOCAL ONLY |
| TMR-019 | Final audit decision | `janus-final-audit`; audit package | HIGH_LOCAL_ONLY | high | bound diff/evidence/audit package | `5.5` | high, very high | DENY | Final audit result mapped to canonical state | Bound artifacts only; no chat-history authority; no debug package PASS | Local-only audit, never delegated externally | N/A | `5.5` very high | Codex final-audit gate, user for next action | LOCAL ONLY |
| TMR-020 | Documentation update / state sync | `janus-documentation-update`; `CURRENT_STATE`; docs registry | GPT_5_4_CANDIDATE | medium | local docs, validation evidence | `5.4` or isolated `5.4 mini` | low, medium | DENY | Updated docs plus completion checklist | No hidden failed validation; CURRENT_STATE updated for substantive blocks | Local-only update one bound doc package | N/A | `5.4` medium | Codex | LOCAL ONLY |
| TMR-021 | Git governance / commit-push-tag-merge decisions | `janus-git-governance`; `AGENTS.md` | HUMAN_ONLY | high | dirty worktree, Git state, remotes | `5.4` or `5.5` for risky release Git | medium, high | DENY | Git governance check and explicit path list | Explicit user approval; no `git add .`; no destructive action without approval | Local-only status/diff-check; no external delegation | N/A | `5.5` high for release Git risk | User approves, Codex executes after gate | LOCAL ONLY |
| TMR-022 | Build, package, release, publish | `janus-build-release`; release artifacts | HIGH_LOCAL_ONLY | high | local build outputs, release metadata, GitHub assets | `5.5` for release gates, `5.4` for rehearsal fixes | high, very high | DENY | Release result and artifact verification | Version sync, installer/manifest/hash/assets verified; publish needs `Publish: YES` | Local-only rehearsal/validation; no production approval externalized | N/A | `5.5` very high | User/Codex release gate | LOCAL ONLY |
| TMR-023 | Health check and drift review | `janus-health-check`; bounded repo hygiene scripts | GPT_5_4_CANDIDATE | low-medium | local repo metadata and docs | `5.4 mini` for isolated checks or `5.4` low warm cache | low, medium | DENY | DAILY/WEEKLY/MONTHLY health report | Read-only; bounded scan; no large fixes | Local-only run health snapshot/checklist | N/A | `5.4` medium | Codex | LOCAL ONLY |
| TMR-024 | Security/privacy/attack-path review | `AGENTS.md`; Codex Security skills; final-audit gates | HIGH_LOCAL_ONLY | high | source, diffs, sensitive boundaries | `5.5` | high, very high | DENY | Security findings or validation report | Source-to-sink reasoning; no private data externalization | Local-only security scan/diff review | N/A | `5.5` very high | Codex Security/Codex, user for risk acceptance | LOCAL ONLY |

## First Mini-Candidate Tasks

Keep the first baseline set to these five tasks only:

| mini_task | why it is eligible | first local baseline |
| --- | --- | --- |
| TMR-001 sanitized excerpt classification | Short sanitized governance input; mechanical classification; no authority. | `5.4 mini` low -> medium -> high; require 100% exact mode and required risk flags before considering OpenRouter. |
| TMR-002 public/sanitized schema-bound extraction | Public or sanitized snippet; deterministic field extraction. | `5.4 mini` low -> medium -> high; require complete schema output and exact labels. |
| TMR-003 non-binding benchmark interpretation | Advisory-only; uses sanitized result summaries; Codex remains decision-maker. | `5.4 mini` low -> medium -> high; require correct HOLD/continue-test recommendation and no production approval language. |
| TMR-004 non-binding cost/latency comparison | Public metadata or sanitized table; cheap ranking task; no live calls. | `5.4 mini` low -> medium -> high; require explicit missing-data caveats and Codex fallback. |
| TMR-005 documentation wording suggestion | Sanitized excerpt only; advisory wording; Codex performs any repo edit. | `5.4 mini` low -> medium -> high; require no policy changes and no direct-write claim. |

## Minimal Mini-Task Benchmark Plan

Do not run this benchmark yet. This section defines the smallest useful plan for later review.

### Local Codex Baseline Sequence

For each mini-task:

1. Run `5.4 mini` with low reasoning on one sanitized deterministic case.
2. If the output is not 100% clean, rerun the same case with `5.4 mini` medium reasoning.
3. If still not clean, rerun with `5.4 mini` high reasoning.
4. Escalate to `5.4` only when `5.4 mini` cannot solve the task cleanly.
5. Record score as local evidence, not routing policy.

### Minimal Deterministic Cases

| case_id | linked_task | prompt fixture | expected result | scoring |
| --- | --- | --- | --- | --- |
| MINI-001 | TMR-001 | "Classify this sanitized excerpt: route first, pick one next skill, load only bound artifacts, compact handoff." | `ALLOW`; flags include sanitized/mechanical; no Git/final-audit/repo-write flags. | Pass/fail on exact mode, required flags, forbidden flags, no authority expansion. |
| MINI-002 | TMR-002 | "ALLOW means sanitized mechanical work; ASSIST means advisory; DENY means no external delegation; UNKNOWN means hold local." | Four labels with one short meaning each; no private-data assumptions. | Pass/fail on all labels, all meanings, schema completion. |
| MINI-003 | TMR-003 | Sanitized table: Model A schema fail/mode correct; Model B schema valid but missed risk flags; Model C timeout. | Recommend `HOLD` for all; separate schema compliance from mode correctness; no production approval. | Pass/fail on decision, caveats, distinction quality. |
| MINI-004 | TMR-004 | Sanitized/public table with model, prompt cost, completion cost, p95 latency, schema support, missing fields. | Advisory ranking with missing-data caveat and Codex fallback. | Pass/fail on rank explanation, missing-data caveat, no live-call claim. |
| MINI-005 | TMR-005 | Sanitized paragraph: "Do not test OpenRouter until schema and risk flag prompt fixes exist." | Clearer wording preserving policy; marks suggestion non-binding. | Pass/fail on semantic preservation and no policy expansion. |

### OpenRouter Comparison Plan

Run only after local mini baselines exist and harness prompt/schema improvements are planned.

Candidate order after harness fixes:

1. `qwen/qwen3.7-plus`
2. `stepfun/step-3.7-flash`
3. `inclusionai/ring-2.6-1t`
4. DeepSeek candidate selected after checking current OpenRouter metadata.
5. `minimax/minimax-m3` only after provider-compatible schema projection fixes the MiniMax schema mismatch.

Comparison rules:

- No parallel OpenRouter tests.
- No private files, logs, local databases, broad source trees, or runtime state in prompts.
- Use only curated public/sanitized fixtures.
- Treat schema failure as benchmark failure.
- Score mode correctness separately from schema validity.
- Record every external candidate with a Codex fallback.
- Keep production routing `UNKNOWN` until explicit user approval after review.

## Do Not Test Yet

- Do not test `5.4`-level tasks before the mini-task matrix and local baselines exist.
- Do not test OpenRouter again before schema/risk-flag prompt improvements are planned.
- Do not run parallel OpenRouter tests.
- Do not run large Codex model sweeps.
- Do not run OpenRouter live calls from this task.
- Do not approve production routing from this document.

## Harness Fixes To Recommend Separately

These are recommended follow-up tasks, not part of this matrix task unless separately routed:

- Stronger prompt requiring complete `DelegatedTaskResult`.
- Explicit required-field checklist inside the benchmark prompt.
- Explicit risk-flag taxonomy handling with required and forbidden flags.
- Provider-compatible schema projection for Boolean enum incompatibility and provider-specific schema limits.
- Scoring split between mode-correct, schema-valid, risk-flag-complete, and production-safe.

## Next Artifacts Before Testing 5.4-Level Tasks

Before any `GPT_5_4_CANDIDATE`, `HIGH_LOCAL_ONLY`, or `HUMAN_ONLY` benchmark/testing work, read only the artifacts relevant to the selected task:

- For routing/model-gate tests: `AGENTS.md`, `documentation/codex/CODEX_WORKFLOW_PLAYBOOK.md`, `documentation/pipeline/PIPELINE_CONTRACT.md`, and `C:\Users\pruve\.codex\skills\janus-skill-router\SKILL.md`.
- For Backlog tasks: `documentation/backlog/BACKLOG.md` plus the relevant `janus-backlog-*` skill and one selected Backlog item.
- For Spec/task tasks: the single bound Feature Spec or task file plus the matching `janus-spec-*`, `janus-task-breakdown`, or `janus-preimplementation-check` skill.
- For execution/debug/test tasks: the bound precheck, execution result, TestSpec/TestRun/TestResult, and only directly affected code/test files.
- For final audit: a compact audit package such as `AUDIT_PACKAGE.md`, plus the bound Spec/Task/Test evidence and `janus-final-audit`.
- For Git/release tasks: `janus-git-governance`, `janus-build-release`, version files, release artifact paths, and explicit user approval.
- For security/privacy tasks: the bound diff or scoped paths, relevant Codex Security skill, and only source needed for source-to-sink validation.

## Review Questions

- Are the five mini-candidates small enough for the first local baseline?
- Should `documentation wording suggestion` remain `ASSIST_ONLY`, or be held local until schema compliance improves?
- Should any `5.4 mini` local-only documentation tasks be split out from the broader `5.4` documentation update task before benchmarking?
