# CURRENT_STATE

## Project
Janus / Pruki Codex Diamond Workflow

## Current Snapshot Update
As of `2026-06-16 01:08 +02:00`, `BACKLOG-112` is fully documentation-closed after final audit `PASS`. The backlog item now sits in `DONE`, the central registry and project state reflect the sealed quickchange delegated live-execute seam, and the dashboard snapshot has been re-synced for the first real bounded OR pilot path.

The active Janus work remains on the OpenRouter or Sidecar implementation track, but one concrete operational blocker has now been retired: the operator-facing `janus-quickchange` delegated path no longer terminates new runs as dry-run-only and now reaches the bounded live-execute seam with focused dispatcher/helper evidence.

The remaining defect has been resolved. The dog fact no longer pollutes the address field, and the address book now keeps the residence in the correct block while pet details are normalized into compact wording.

A subsequent live retest had exposed one more narrow language-coverage gap: `und er besitzt einen Hund` still fell through to the unverifiable-facts response even though `und er hat einen Hund` was already fixed. The local heuristics now also cover the verb form `besitzt` across intent detection, contact-extraction candidate selection, and pet-detail normalization, and the live retest confirmed the follow-up phrasing now behaves sensibly.

The newest local slice isolated one final persistence seam for the same contact chain: pet-name facts such as `Olis hund heißt tasso` were already being extracted into memory, but they did not automatically reach the address-book contact because extractor-created pet memories could carry a valid contact alias in `subject_name` while still missing `subject_role=contact`. The extractor now triggers contact sync for contact-like memory categories whenever a usable subject name exists, and the local `Oliver Schwab` row was repaired so details now include `Olis hund heißt tasso`.

The latest local formatting pass cleans the remaining presentation bug in the contact card itself: named pet facts collapse into one sentence such as `hat einen Hund namens tasso`, owner-prefixed variants such as `Oli hat auch eine katze` normalize down to `hat eine Katze`, and weaker generic duplicates are dropped when a stronger named variant already exists. The live retest confirmed that the cleaned wording now appears automatically in everyday use.

## Current Goal
The live proof target has been met for the contact-debug branch. The active Janus goal is now fully back on the OpenRouter or Sidecar implementation track.

Goal override for the active architecture track: prepare the first structured executor implementation slice for safe implementation by releasing exactly one bounded precheck target, `TASK-SPEC17.1 Structured action request intake and validation skeleton`.

Operational delegation override: with `BACKLOG-112` now sealed, the first real bounded OR pilot path is no longer blocked by a dry-run-only `janus-quickchange` seam.

Stabilize the real Janus runtime for `BACKLOG-110` after the accepted read-only `execution_patch_candidate` proposal and local Codex apply. The immediate target is no longer delegation architecture, but the live contact/address-book workflow: ordinary contact fact statements such as `Oliver Schwab wohnt in Köln-Stammheim` must enter the real tool path and stop returning the earlier `keine verifizierten Fakten` response.

## Active Phase
The contact-debug branch is now operationally closed after live verification and documentation sync.

The active phase has shifted from task compilation to task-refinement completion for the OpenRouter or Sidecar structured executor path. The bounded operator package remains workflow-ready for eight classes, and the new feature spec for the first deterministic `janus-test-pipeline` executor slice is now narrowed to one released precheck target before implementation.

The newest completed phase is `janus-documentation-update` for `BACKLOG-112`, which sealed the quickchange delegated live-execute closeout across backlog, registry, project-state, changelog, dashboard snapshot, skill log, and CURRENT_STATE.

- a validated dry-run helper path
- one attempted live delegated run blocked by missing `node` PATH resolution
- one hardened retry blocked by Windows PowerShell invocation syntax for the explicit `node.exe` path
- one final bounded retry with the PowerShell-safe form still failed to create any target artifacts, confirming that prompt-level command steering is not yet reliable enough for this class

## Last Decision
The user confirmed the next architecture step: do not stop at read-only drafts. Plan for a future mode where delegated worker execution can also write files when that is safe, bounded, reviewable, and still governed by Codex App.

- Codex App remains the main operator, reviewer, and Janus governance holder.
- A separate Codex CLI sidecar may later run selected bounded write-capable work under `workspace-write`.
- The user should still choose at a gate whether Codex or the Sidecar handles the step.
- Codex App must retain final diff review, validation, and acceptance authority.

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
- `SIDECAR-DOC-FLOW-LIVE-TEST-001` completed the first everyday workflow-style documentation skill test after an explicit operator `2 = Sidecar` choice and returned `SIDECAR_DRAFT_ACCEPTED_FOR_REVIEW`
- a new planning artifact now defines the write-capable rollout ladder, with `janus-quickchange` chosen as the safest first true file-write pilot before broader `janus-test-pipeline`, `janus-debug`, or `janus-executioner` delegation
- a dedicated quickchange pilot-plan artifact now defines the exact future write gate, editable-path allowlist rules, diff-capture artifacts, delete/rename tripwire, validation capture, and reject flow for the first live `workspace-write` attempt
- the runner and helper are now extended in dry-run form for the quickchange pilot, and the dry-run path validated the new artifacts plus allowlist/touched-file/delete-rename checks without performing a live delegated write
- `SIDECAR-QUICKCHANGE-LIVE-001` completed the first real delegated write-capable Sidecar pilot against `frontend/index.html`, with exact allowlist compliance, exactly one touched file, accepted diff review, and no delete/rename/move activity
- a new test-artifact pilot plan now binds the next write-capable class to generated `documentation/test-runs/<TEST_RUN_ID>_plan.json`, `_generated.spec.js`, plus the deterministic compiler side-effect file `_skill2_handover.txt`
- `SIDECAR-TEST-ARTIFACT-DRYRUN-001` validated the test-artifact helper path in `workspace-write` dry-run mode with exact output allowlist coverage and no touched-file/reject violations
- `SIDECAR-TEST-ARTIFACT-LIVE-001` attempted the first real delegated test-artifact write pilot, but no artifacts were generated because the Sidecar shell could not resolve `node` and timed out while investigating the local environment
- local operator-shell verification after the failed run confirms the real Node binary exists at `C:\nvm4w\nodejs\node.exe`, so the next retry should use the explicit full path rather than plain `node`
- `SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001` then used the explicit Node path, but the Sidecar still failed before generation because the path was not invoked in PowerShell-safe quoted call syntax
- `SIDECAR-TEST-ARTIFACT-LIVE-FINAL-RETRY-001` then used the PowerShell-safe form, but still produced no target files and ended with the same immediate command-failure outcome in the Sidecar response text

## Last Codex Work
Completed `janus-task-breakdown` for `TASK-SPEC17.1` and released exactly one bounded precheck target:

- `documentation/tasks/TASK-SPEC17.1_task_breakdown.md` now binds the next implementation gate to `TASK-SPEC17.1` only.
- The released target keeps scope on request intake, schema or shape validation, deterministic run-directory artifacts, and explicit rejection of unsupported or forbidden action types.
- Generator mapping, validator mapping, dispatcher fallback integration, and any write or apply authority remain out of scope for this first target and must stay in `TASK-SPEC17.2` or `TASK-SPEC17.3`.
- The existing `codex_structured_action_executor.py` remains implementation context only for the next precheck; it is not a competing requirements source against Spec 17 plus `TASK-SPEC17`.

Backlog prioritization update:

- `BACKLOG-112` is now the top operational blocker for the first real bounded OR pilot class (`janus-quickchange`) and has been marked `HIGH` / `LOW` / `M` / `READY` / `DO NOW` in `documentation/backlog/BACKLOG.md`.
- The item captures the dry-run-only gap in the current delegated quickchange path and keeps the live-execute pilot blocked until the helper can produce a real bounded write attempt.
- The item has now been handed off via `janus-backlog-handoff` into `documentation/tasks/backlog_BACKLOG-112_quickchange_delegationspfad_live_execute_handoff.md` and moved to `IN PROGRESS`.
- `BACKLOG-112` has now passed `janus-preimplementation-check` in `documentation/tasks/backlog_BACKLOG-112_preimplementation_check.md`.
- `BACKLOG-112` has now been implemented in `documentation/tasks/backlog_BACKLOG-112_execution_result.md`.
- The quickchange delegated helper now supports an explicit bounded live execute attempt, and the existing dispatcher path now invokes that mode for `quickchange_patch_review`.
- `BACKLOG-112` now has a compact audit package in `documentation/tasks/BACKLOG-112_AUDIT_PACKAGE.md` and a validated final-audit report in `documentation/tasks/backlog_BACKLOG-112_final_audit.md`.
- A narrow re-audit delta added the missing bounded dispatcher/helper-level operator-path evidence in `documentation/codex/model-routing/tests/test_quickchange_live_operator_path.py` and `documentation/tasks/backlog_BACKLOG-112_reaudit_delta_execution_result.md`.
- Final audit for `BACKLOG-112` is now `PASS`.
- `janus-documentation-update` has now completed the `BACKLOG-112` closeout across `documentation/backlog/BACKLOG.md`, `documentation/01_CENTRAL_TASK_REGISTRY.md`, `PROJECT_STATE.md`, `CHANGELOG.md`, `janus-dashboard/data/backlog.snapshot.json`, and `documentation/codex/SKILL_USAGE_LOG.md`.
- `BACKLOG-112` is now marked `DONE` and no longer blocks the first real bounded OR quickchange pilot on documentation or governance grounds.

Newest local debug slice after the partially improved live retest:

- live logs show the follow-up `und er hat einen Hund` now enters the intended Fact-Telling path, loads `memory.write`, and applies against the existing `Oliver Schwab` contact instead of falling into ambiguity clarification
- the remaining bad behavior came from a second extraction seam: saved evidence text for the dog fact still included quoted context from the earlier residence sentence, and the generic address parser re-read that embedded `wohnt in ...` fragment as if it were a fresh address update
- `backend/services/contact_manager.py` now restricts generic address parsing to explicit `adresse` / `anschrift` wording, adds a direct residence pattern for genuine `wohnt in ...` facts, sanitizes malformed trailing quote/parenthesis artifacts, and maps `Haustier-Details` into structured contact `personal_details`
- `backend/data/crud.py` now applies the same address sanitizer during read/normalization so malformed stored address suffixes are cleaned and persisted on contact load
- focused regression coverage now proves that pet-detail evidence text no longer backfills residence into the address field and that malformed trailing quote/parenthesis suffixes are stripped during normalization
- the local live contact row for `Oliver Schwab` was repaired after the patch: address normalized to `koeln stammheim`, personal details now contain `hat einen Hund`
- `backend/data/crud.py` now also normalizes pet-detail wording into one clean sentence per pet, including `Olis hund heißt tasso` -> `hat einen Hund namens tasso` and `Oli hat auch eine katze` -> `hat eine Katze`
- contact normalization now removes the weaker generic `hat einen Hund` line when the stronger named variant `hat einen Hund namens tasso` already exists
- targeted regression coverage now proves the final normalized contact-card result `["hat einen Hund namens tasso", "hat eine Katze"]`

Ran a bounded `janus-debug` investigation against the live Janus failure reported after the `BACKLOG-110` local apply. The new finding is runtime-tooling, not residence parsing:

- `extract_and_save_contact_from_text` existed and its unit tests were already green, but it was not registered in the normal tool catalog used by the live chat path
- `ToolSelector` did not surface a dedicated contact-extraction candidate for free fact statements such as `Oliver Schwab wohnt in Köln-Stammheim` or `und er hat einen Hund`
- a second runtime seam then appeared immediately after the first fix: the selector candidate originally still used the legacy function name, while the real tool catalog exposed the contact extractor under the skill ID `contacts.extract_from_text`; this meant `select_tools(...)` could still drop the intended tool before LLM execution
- `backend/tool_registry.py` now registers `extract_and_save_contact_from_text` with `ContactExtractionArgs`
- `backend/services/chat/tool_selector.py` now adds the contact-extraction path for simple contact fact statements even without explicit `Kontakt` or `Adressbuch` wording and uses the runtime skill ID `contacts.extract_from_text` consistently
- `backend/skills/contacts/extract_from_text.json` now gives the new path proper skill metadata
- `backend/tests/test_tool_selector_contact_routing.py` now covers candidate detection and final tool selection for residence and pet follow-up statements
- `documentation/test-runs/BACKLOG-110_debug_contact_fact_statement_tool_routing_2026-06-14.md` documents the debug result and validates against the `janus-debug` validator

Validation for this debug slice is green:

- `python -m py_compile backend/tool_registry.py backend/services/chat/tool_selector.py backend/tests/test_tool_selector_contact_routing.py`: PASS
- `python -m pytest backend/tests/test_tool_selector_contact_routing.py -q`: PASS
- `python -m pytest backend/tests/test_contact_manager.py -q`: PASS
- `python -m pytest backend/tests/test_calendar_routing_fix.py -q`: PASS
- `python -m pytest backend/tests/test_contact_manager.py -q -k extract_and_save_contact_stages_private_contact_proposal`: PASS

The earlier bounded delegation and structured-action evidence remains valid; the content below is retained as historical context for that architecture track:

- request loading plus v1 schema-shape validation
- deterministic per-workflow run directories
- `draft_markdown` artifact-only execution
- `propose_patch` capture-only execution with touched-file allowlist validation
- one deterministic `run_generator` mapping: `generate_live_runner_v1`
- deterministic `run_validator` mappings: `validate_test_plan_v1`, `validate_runner_v1`, `node_check_script_v1`
- repeatable fixture requests using `__RUN_DIR__` placeholder expansion
- a bounded request builder that converts saved markdown drafts, unified diffs, generator payload manifests, or validator payload manifests into schema-conformant executor request JSON
- a bounded sidecar-package helper that validates `summary.json`, consumes `last_message.md`, builds a request, and optionally executes it locally
- the documentation sidecar draft runner can now trigger that reviewed structured flow directly after a successful accepted sidecar draft
- a bounded generator-review helper can now chain `run_generator` plus follow-up `run_validator` for `generate_live_runner_v1` without manual handoff between builder and executor steps
- a new bounded delegation dispatcher now routes one operator-facing entry point across three validated classes: documentation drafts, quickchange patch review, and generator-backed structured review
- the documentation skill guidance and delegated draft runner are now aligned with that dispatcher, and the dispatcher-bound documentation draft path has a fresh live `PASS` with structured review enabled
- the installed documentation skill copy under `C:\Users\pruve\.codex\skills\janus-documentation-update\SKILL.md` is now synced to the same dispatcher-first bounded draft guidance as the repo source
- the dispatcher-bound `quickchange_patch_review` path is now also validated in operator style, with prompt-gate `PASS` and delegated dry-run plus structured patch-review `PASS`
- the dispatcher-bound `generator_review` path is now also validated in operator style, with prompt-gate `PASS` and delegated builder/executor/validator flow `PASS`
- a canonical-entry note now records `codex_bounded_delegation_dispatcher.py` as the shared bounded operator entry for `documentation_draft`, `quickchange_patch_review`, and `generator_review`
- a new bounded delegation expansion roadmap now prioritizes the next classes as `debug_hypothesis_review`, `test_result_triage_review`, `quickchange_write_apply`, `execution_patch_candidate`, and only later `test_artifact_write_runner_level`
- a dedicated `debug_hypothesis_review` plan now defines the first next-class input package, redaction gate, delegated output contract, Codex validation flow, fallback rules, and evidence needed before everyday use
- a new bounded `debug_hypothesis_review` helper now exists with prompt/local/delegated fixture modes, normalized assist-only artifacts, and dispatcher integration for local validation runs
- the repo and installed `janus-debug` skill guidance now expose `debug_hypothesis_review` as a skill-near bounded operator gate instead of leaving it as a helper-only path
- a dedicated `test_result_triage_review` plan now defines the second assist-only class for `janus-test-pipeline`, including bounded inputs, supported classifications, Codex validation flow, and fallback rules
- a new bounded `test_result_triage_review` helper now exists with prompt/local/delegated fixture modes, normalized assist-only artifacts, and dispatcher integration for local validation runs
- the repo and installed `janus-test-pipeline` skill guidance now expose `test_result_triage_review` as a skill-near bounded operator gate instead of leaving it as a helper-only path
- a dedicated `quickchange_write_apply` plan now defines the first dispatcher-visible bounded write-acceptance class backed by accepted workspace-write evidence instead of fresh broad write authority
- a new bounded `quickchange_write_apply` helper now exists with prompt/local/delegated validation modes, accepted-source evidence checks, and dispatcher integration for local validation runs
- the repo and installed `janus-quickchange` skill guidance now expose both `quickchange_patch_review` and `quickchange_write_apply` as skill-near bounded operator gates instead of leaving write-acceptance knowledge hidden behind low-level helper details
- a dedicated `execution_patch_candidate` plan now defines the first `janus-executioner` proposal-first delegation class with strict precheck binding, file-cluster allowlist, no delegated apply, and Codex-owned final acceptance
- a new bounded `execution_patch_candidate` helper now exists with prompt/local/delegated fixture validation modes, unified-diff allowlist checks, and dispatcher integration for local validation runs
- the repo and installed `janus-executioner` skill guidance now expose `execution_patch_candidate` as a skill-near bounded operator gate instead of leaving the execution proposal path hidden behind helper-script knowledge only
- a follow-up decision note now records that the next safe bounded expansion should plan a derivative `execution_write_apply_candidate`, while `test_artifact_write_runner_level` stays paused until runner-owned command support exists
- the derivative `execution_write_apply_candidate` plan now includes the actual operator gate, live entry contract, delegated artifact contract, abort rules, stop conditions, and Codex-owned acceptance flow needed before any future live pilot
- a new bounded `execution_write_apply_candidate` helper now exists with prompt/local/delegated accepted-source validation modes, dispatcher integration, and skill-near `janus-executioner` guidance
- the first shared-gate everyday walkthrough for `execution_patch_candidate` now exists, with prompt gate `PASS` and delegated proposal-first validation `PASS` in the same operator-facing pattern as the earlier bounded classes
- the first real prechecked `execution_patch_candidate` candidate package is now prepared for `BACKLOG-110`, using the existing `PRE-CHECK PASSED` artifact and a narrowed backend-first file cluster
- the `execution_patch_candidate` helper now also supports a real read-only Codex CLI sidecar path that auto-builds a bounded patch prompt from the prechecked input package, captures a proposal-only unified diff, and stores a structured review artifact for Codex
- `BACKLOG-110-EXECUTION-PATCH-CANDIDATE-DRYRUN-001` and `BACKLOG-110-EXECUTION-PATCH-DISPATCH-DRYRUN-001` both returned `DRY_RUN_VALIDATED`, proving the first real prechecked execution proposal path is wired end-to-end without making a live delegated model call yet
- `BACKLOG-110-EXECUTION-PATCH-CANDIDATE-LIVE-001` then attempted the first real live read-only proposal run, but the sidecar timed out after bounded repository inspection and produced neither `stdout.log` content nor `last_message.md`; this is blocker evidence only, not accepted proposal evidence
- the live execution prompt for `BACKLOG-110` is now tightened to a compact one-pass diff-only format, and `BACKLOG-110-EXECUTION-PATCH-CANDIDATE-DRYRUN-002` returned `DRY_RUN_VALIDATED` with the shortened prompt artifact
- `BACKLOG-110-EXECUTION-PATCH-CANDIDATE-LIVE-002` then returned `PASS` with a bounded unified diff, exact allowlist compliance, and successful structured patch capture; this is the first accepted real proposal-only `execution_patch_candidate` evidence for `BACKLOG-110`
- Codex then reviewed and locally applied the accepted `BACKLOG-110` proposal with one small refinement: residence extraction from inbound private-contact `notes` now preserves unrelated note lines instead of dropping them wholesale
- local verification for the applied `BACKLOG-110` implementation is green: `py_compile` PASS, `backend/tests/test_contact_manager.py` PASS, and `backend/tests/test_contact_card_normalization.py` PASS

The earlier architecture artifacts still define:

- the versioned delegated action request schema
- the first supported action types: `draft_markdown`, `propose_patch`, `run_generator`, `run_validator`, `summarize_results`
- the first deterministic generator and validator IDs for `janus-test-pipeline`
- the executor responsibilities, mapping rules, and non-goals

The immediately preceding live evidence remains:

- attempt 1 failed on missing `node` PATH resolution inside the Sidecar shell
- retry 2 failed because the explicit `C:\nvm4w\nodejs\node.exe` path was not invoked in PowerShell-safe quoted call syntax
- final retry 3 still failed to generate target files even after prompt hardening to the PowerShell-safe form, so this class is not yet suitable for prompt-only delegated execution

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
- one everyday workflow sidecar live-test prompt
- one everyday workflow sidecar live-test run package
- one local documentation-update result note for the everyday workflow test
- one write-capable Sidecar delegation plan
- one updated Sidecar delegation matrix with `SIDECAR_WRITE_CANDIDATE`
- one concrete quickchange `workspace-write` pilot plan
- one extended Sidecar runner with quickchange write-pilot artifacts
- one quickchange workspace-write pilot helper
- one dry-run fixture for the quickchange write pilot
- two dry-run artifact packages for the quickchange write pilot
- one implementation result note for the runner/helper extension
- one live quickchange write prompt
- one live quickchange write artifact package
- one live quickchange result note
- one test-artifact write pilot plan
- one test-artifact write pilot helper
- one test-artifact dry-run fixture
- one test-artifact live fixture updated with explicit Node path guidance
- one test-artifact dry-run artifact package
- one test-artifact runner result note
- one test-artifact live result note documenting the `node` PATH blocker
- one test-artifact live retry result note documenting the PowerShell invocation blocker
- one test-artifact final retry result note documenting that prompt-level command steering is still not sufficient for accepted live delegation
- one structured OR/Sidecar action-layer architecture plan
- one delegated-action request JSON schema
- one first structured executor plan

No production routing, canonical routing-table update, Auto Router continuation, or Git action occurred. One real write-capable Sidecar pilot exists for a tiny `janus-quickchange` scope. The test-artifact class now has three bounded live blocker records, all infrastructure-only, and still no accepted delegated output.

## Changed Files
- `backend/services/contact_manager.py`
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_contact_card_normalization.py`
- `documentation/test-runs/BACKLOG-110_debug_contact_apply_normalization_addendum_2026-06-14.md`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/chat/tool_selector.py`
- `backend/services/memory_extractor.py`

- `backend/services/orchestrator/intent_engine.py`
- `backend/services/capability_registry.py`
- `backend/services/memory/retrieval_service.py`
- `backend/tests/test_calendar_routing_fix.py`
- `backend/tests/unit/test_skill_selector_filesystem_calendar.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-110_debug_contact_fact_statement_tool_routing_2026-06-14.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/model-routing/backlog_110_execution_patch_candidate_live_result_2026-06-14.md`
- `documentation/codex/model-routing/backlog_110_execution_patch_candidate_live_acceptance_2026-06-14.md`
- `documentation/codex/model-routing/backlog_110_execution_patch_candidate_prompt_tightening_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py`
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/skills/janus-executioner/SKILL.md`
- `C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md`
- `backend/services/contact_manager.py`
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_contact_card_normalization.py`
- `documentation/codex/model-routing/execution-review-runs/BACKLOG-110-EXECUTION-PATCH-CANDIDATE-DRYRUN-001/*`
- `documentation/codex/model-routing/execution-review-runs/BACKLOG-110-EXECUTION-PATCH-CANDIDATE-DRYRUN-002/*`
- `documentation/codex/model-routing/execution-review-runs/BACKLOG-110-EXECUTION-PATCH-DISPATCH-DRYRUN-001/*`
- `documentation/codex/model-routing/execution-review-runs/BACKLOG-110-EXECUTION-PATCH-CANDIDATE-LIVE-001/*`
- `documentation/codex/model-routing/execution-review-runs/BACKLOG-110-EXECUTION-PATCH-CANDIDATE-LIVE-002/*`
- `documentation/codex/model-routing/codex_bounded_delegation_dispatcher_canonical_entry_2026-06-14.md`
- `documentation/codex/model-routing/codex_bounded_delegation_expansion_roadmap_2026-06-14.md`
- `documentation/codex/model-routing/codex_debug_hypothesis_review_plan_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_debug_hypothesis_review_runner.py`
- `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`
- `documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_input_package_2026-06-14.json`
- `documentation/codex/model-routing/debug-review-fixtures/debug_hypothesis_fixture_result_2026-06-14.json`
- `documentation/codex/model-routing/debug-review-runs/DEBUG-HYPOTHESIS-PROMPT-001/*`
- `documentation/codex/model-routing/debug-review-runs/DEBUG-HYPOTHESIS-LOCAL-001/*`
- `documentation/codex/model-routing/debug-review-runs/DEBUG-HYPOTHESIS-DELEGATED-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-DEBUG-DISPATCH-PROMPT-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-DEBUG-DISPATCH-LIVE-001/*`
- `documentation/codex/skills/janus-debug/SKILL.md`
- `C:\Users\pruve\.codex\skills\janus-debug\SKILL.md`
- `documentation/codex/model-routing/codex_test_result_triage_review_plan_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_test_result_triage_review_runner.py`
- `documentation/codex/model-routing/test-triage-fixtures/test_result_triage_input_package_2026-06-14.json`
- `documentation/codex/model-routing/test-triage-fixtures/test_result_triage_fixture_result_2026-06-14.json`
- `documentation/codex/model-routing/test-triage-runs/TEST-TRIAGE-PROMPT-001/*`
- `documentation/codex/model-routing/test-triage-runs/TEST-TRIAGE-LOCAL-001/*`
- `documentation/codex/model-routing/test-triage-runs/TEST-TRIAGE-DELEGATED-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-TEST-TRIAGE-DISPATCH-PROMPT-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-TEST-TRIAGE-DISPATCH-LIVE-001/*`
- `documentation/codex/skills/janus-test-pipeline/SKILL.md`
- `C:\Users\pruve\.codex\skills\janus-test-pipeline\SKILL.md`
- `documentation/codex/model-routing/codex_quickchange_write_apply_plan_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_quickchange_write_apply_runner.py`
- `documentation/codex/model-routing/quickchange-apply-runs/QUICKCHANGE-WRITE-APPLY-PROMPT-001/*`
- `documentation/codex/model-routing/quickchange-apply-runs/QUICKCHANGE-WRITE-APPLY-LOCAL-001/*`
- `documentation/codex/model-routing/quickchange-apply-runs/QUICKCHANGE-WRITE-APPLY-DELEGATED-001/*`
- `documentation/codex/model-routing/quickchange-apply-runs/BOUNDED-QUICKCHANGE-WRITE-APPLY-DISPATCH-LIVE-001/*`
- `documentation/codex/skills/janus-quickchange/SKILL.md`
- `C:\Users\pruve\.codex\skills\janus-quickchange\SKILL.md`
- `documentation/codex/model-routing/codex_execution_patch_candidate_plan_2026-06-14.md`
- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_input_package_2026-06-14.json`
- `documentation/codex/model-routing/execution-review-fixtures/execution_patch_candidate_fixture_result_2026-06-14.json`
- `documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py`
- `documentation/codex/model-routing/execution-review-runs/EXECUTION-PATCH-CANDIDATE-PROMPT-001/*`
- `documentation/codex/model-routing/execution-review-runs/EXECUTION-PATCH-CANDIDATE-LOCAL-001/*`
- `documentation/codex/model-routing/execution-review-runs/EXECUTION-PATCH-CANDIDATE-DELEGATED-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-EXECUTION-PATCH-DISPATCH-PROMPT-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-EXECUTION-PATCH-DISPATCH-LIVE-001/*`
- `documentation/codex/skills/janus-executioner/SKILL.md`
- `C:\Users\pruve\.codex\skills\janus-executioner\SKILL.md`
- `documentation/codex/model-routing/codex_execution_write_apply_candidate_plan_2026-06-14.md`
- `documentation/codex/model-routing/execution-write-apply-fixtures/execution_write_apply_candidate_source_manifest_2026-06-14.md`
- `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`
- `documentation/codex/model-routing/execution-write-apply-runs/EXECUTION-WRITE-APPLY-CANDIDATE-PROMPT-001/*`
- `documentation/codex/model-routing/execution-write-apply-runs/EXECUTION-WRITE-APPLY-CANDIDATE-LOCAL-001/*`
- `documentation/codex/model-routing/execution-write-apply-runs/EXECUTION-WRITE-APPLY-CANDIDATE-DELEGATED-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-EXECUTION-WRITE-APPLY-DISPATCH-PROMPT-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/BOUNDED-EXECUTION-WRITE-APPLY-DISPATCH-LIVE-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/EXECUTION-EVERYDAY-WALKTHROUGH-001/*`
- `documentation/codex/model-routing/bounded-dispatch-runs/EXECUTION-EVERYDAY-WALKTHROUGH-001-DELEGATED/*`
- `documentation/codex/model-routing/execution-review-fixtures/backlog_110_execution_patch_candidate_input_package_2026-06-14.json`
- `documentation/codex/model-routing/backlog_110_execution_patch_candidate_prep_2026-06-14.md`
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
- `documentation/codex/model-routing/sidecar-fixtures/sidecar_documentation_skill_live_test_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-FLOW-LIVE-TEST-001/*`
- `documentation/codex/model-routing/codex_sidecar_documentation_skill_live_test_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_write_capable_delegation_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_quickchange_workspace_write_pilot_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_quickchange_workspace_write_runner_extension_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_quickchange_workspace_write_live_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_test_artifact_workspace_write_pilot_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_test_artifact_workspace_write_runner_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_agent_live_pilot_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_documentation_update_draft_result_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_agent_execution_plan_2026-06-14.md`
- `documentation/codex/model-routing/codex_sidecar_skill_delegation_matrix_2026-06-14.md`
- `documentation/codex/skills/janus-documentation-update/SKILL.md`
- `documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`
- `documentation/codex/model-routing/sidecar-fixtures/quickchange_workspace_write_dry_run_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-fixtures/quickchange_workspace_write_live_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_dry_run_prompt_2026-06-14.md`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-QUICKCHANGE-DRY-RUN-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-QUICKCHANGE-HELPER-DRYRUN-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-QUICKCHANGE-LIVE-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-TEST-ARTIFACT-DRYRUN-001/*`
- `documentation/codex/model-routing/scripts/codex_structured_action_executor.py`
- `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`
- `documentation/codex/model-routing/scripts/codex_structured_action_sidecar_bridge.py`
- `documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py`
- `documentation/codex/model-routing/structured-action-fixtures/delegated_request_draft_markdown_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/delegated_request_generate_live_runner_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/builder_patch_source_2026-06-14.diff`
- `documentation/codex/model-routing/structured-action-fixtures/builder_generator_payload_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/builder_validator_payload_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/built_request_draft_from_sidecar_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/built_request_patch_from_diff_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/built_request_generator_from_manifest_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/built_request_validator_from_manifest_2026-06-14.json`
- `documentation/codex/model-routing/structured-action-fixtures/STRUCTURED-SIDECAR-BRIDGE-001_built_from_sidecar.json`
- `documentation/codex/model-routing/structured-action-fixtures/SIDECAR-DOC-STRUCTURED-FLOW-001-STRUCTURED_built_from_sidecar.json`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-ACTION-DRAFT-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-ACTION-GENERATOR-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-ACTION-VALIDATOR-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-ACTION-PATCH-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-BUILDER-DRAFT-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-BUILDER-PATCH-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-BUILDER-GENERATOR-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-BUILDER-VALIDATOR-001/*`
- `documentation/codex/model-routing/structured-action-runs/STRUCTURED-SIDECAR-BRIDGE-001/*`
- `documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-STRUCTURED-FLOW-001/*`
- `documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md`
- `documentation/tasks/TASK-SPEC17_structured_executor_first_slice_for_or_sidecar_delegation.md`
- `frontend/index.html`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

## Tests / Validation Performed
- Feature spec for the first structured executor slice created at `documentation/SPEC/17_structured_executor_first_slice_for_or_sidecar_delegation.md`: PASS.
- `python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py`: PASS.
- `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS, 5 passed.
- `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`: PASS.
- `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS, 4 passed.
- `python -m pytest backend/tests/test_contact_manager.py -q`: PASS, 31 passed.
- direct live-DB repair verification for contact `Oliver Schwab`: PASS, address normalized and `hat einen Hund` present in `personal_details`.
- `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/chat/tool_selector.py backend/services/contact_manager.py backend/tests/test_calendar_routing_fix.py backend/tests/test_tool_selector_contact_routing.py backend/tests/test_contact_manager.py`: PASS.
- `python -m pytest backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_pronoun_contact_fact_followup_with_besitzt_bypasses_ambiguity_clarification backend/tests/test_tool_selector_contact_routing.py::test_retrieve_candidates_adds_contact_extraction_for_pet_follow_up_with_besitzt backend/tests/test_contact_manager.py::test_pet_detail_memory_with_besitzt_updates_existing_contact_personal_details -q`: PASS.
- `python -m pytest backend/tests/test_contact_manager.py -q -k "pet_detail"`: PASS, 3 passed.
- `python -m py_compile backend/services/memory_extractor.py backend/tests/test_contact_manager.py`: PASS.
- `python -m pytest backend/tests/test_contact_manager.py::test_fact_extractor_syncs_pet_name_detail_even_when_subject_role_is_missing backend/tests/test_contact_manager.py::test_pet_detail_memory_updates_existing_contact_personal_details backend/tests/test_contact_manager.py::test_pet_detail_memory_with_besitzt_updates_existing_contact_personal_details backend/tests/test_contact_manager.py::test_pet_detail_evidence_text_does_not_backfill_residence_address -q`: PASS, 4 passed.
- direct local DB verification after replaying memory `Olis hund heißt tasso`: PASS, contact details now include the pet-name detail.

- `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/capability_registry.py backend/services/memory/retrieval_service.py backend/tests/test_calendar_routing_fix.py backend/tests/unit/test_skill_selector_filesystem_calendar.py backend/tests/test_memory_tools.py`: PASS.
- `python -m pytest backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_pronoun_contact_fact_followup_bypasses_ambiguity_clarification backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_contact_fact_statement_bypasses_ambiguity_clarification -q`: PASS.
- `python -m pytest backend/tests/unit/test_skill_selector_filesystem_calendar.py::TestSkillSelectorFilesystemCalendar::test_registry_fact_telling_loads_memory_and_contact_extraction -q`: PASS.
- `python -m pytest backend/tests/test_memory_tools.py::test_get_last_subject_from_chat_skips_unknown_or_unscoped_recent_memory -q`: PASS.
- `python -m pytest backend/tests/test_tool_selector_contact_routing.py backend/tests/test_contact_manager.py -q`: PASS, 32 passed.
- `python -m pytest backend/tests/unit/test_skill_selector_filesystem_calendar.py backend/tests/test_calendar_routing_fix.py -q`: PASS, 44 passed.
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
- `python documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py --task-label "Everyday documentation skill sidecar workflow test" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/sidecar_documentation_skill_live_test_prompt_2026-06-14.md --workflow-id SIDECAR-DOC-FLOW-LIVE-TEST-001`: PASS.
- `Get-Content documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-FLOW-LIVE-TEST-001/last_message.md`: PASS.
- `Get-Content documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-FLOW-LIVE-TEST-001/summary.json`: PASS.
- `git diff --check`: PASS.
- planning review of `codex_sidecar_skill_runner.ps1` against `workspace-write` expansion needs: PASS.
- `janus-quickchange` skill contract review against Sidecar first-write pilot scope: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`: PASS.
- direct `workspace-write` dry-run of `codex_sidecar_skill_runner.ps1` with allowlist, touched-file cap, and delete/rename gating: PASS.
- helper dry-run of `quickchange_sidecar_write_pilot_runner.py`: PASS.
- dry-run `validation_summary.json` confirms `allowlist_ok=true`, `touched_file_cap_ok=true`, and `delete_rename_move_ok=true`: PASS.
- live `workspace-write` run of `codex_sidecar_skill_runner.ps1` for `SIDECAR-QUICKCHANGE-LIVE-001`: PASS.
- live `validation_summary.json` confirms `allowlist_ok=true`, `touched_file_cap_ok=true`, and `delete_rename_move_ok=true`: PASS.
- live `git_diff.patch` review confirms exactly two placeholder replacements in `frontend/index.html`: PASS.
- `rg -n "Nachricht an Janus (senden|schreiben)\.\.\." frontend/index.html`: PASS, both placeholders now show `schreiben`.
- `python -m py_compile documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py`: PASS.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2099-12-31-001" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_dry_run_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-DRYRUN-001`: PASS.
- test-artifact `validation_summary.json` confirms `allowlist_ok=true`, `touched_file_cap_ok=true`, and `delete_rename_move_ok=true`: PASS.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2026-06-14-901" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_live_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-LIVE-PRECHECK-001`: PASS, dry-run precheck for the real live target.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2026-06-14-901" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_live_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-LIVE-001 --execute-live`: BLOCKED, runner timeout after Sidecar-side Node resolution failure.
- `Get-Command node | Select-Object Name,Source | Format-List`: PASS, local operator shell resolves `C:\nvm4w\nodejs\node.exe`.
- `where.exe node`: PASS, confirms `C:\nvm4w\nodejs\node.exe`.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2026-06-14-901" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_live_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-LIVE-RETRY-PRECHECK-001`: PASS, dry-run precheck after prompt hardening.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2026-06-14-901" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_live_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-LIVE-RETRY-001 --execute-live --timeout-seconds 180`: BLOCKED, wrapper-level run PASS but no target artifacts created and post-validation FAIL.
- `python documentation/codex/model-routing/scripts/test_pipeline_sidecar_write_pilot_runner.py --testspec-path "documentation/TEST_SPEC/07_regression_suite/17_memory_recall_placeholder_regression.md" --test-run-id "TEST-RUN-2026-06-14-901" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/test_artifact_workspace_write_live_prompt_2026-06-14.md --workflow-id SIDECAR-TEST-ARTIFACT-LIVE-FINAL-RETRY-001 --execute-live --timeout-seconds 180`: BLOCKED, wrapper-level run PASS but no target artifacts created and post-validation FAIL.
- structured architecture review against existing sidecar execution plan, delegation matrix, and OpenRouter delegation prototype: PASS.
- delegated action request schema JSON created and parseable: PASS.
- structured executor plan created with first generator/validator mappings: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py`: PASS.
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_draft_markdown_2026-06-14.json`: PASS.
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_generate_live_runner_2026-06-14.json`: PASS.
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_2026-06-14.json`: PASS.
- temporary local `propose_patch` request against `documentation/ai/CURRENT_STATE.md`: PASS, capture-only and no apply.
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`: PASS.
- builder run from `SIDECAR-DOC-DRAFT-001/last_message.md` to `built_request_draft_from_sidecar_2026-06-14.json`: PASS.
- builder run from `builder_patch_source_2026-06-14.diff` to `built_request_patch_from_diff_2026-06-14.json`: PASS.
- built draft request executed through `codex_structured_action_executor.py`: PASS.
- built patch request executed through `codex_structured_action_executor.py`: PASS.
- builder run from `builder_generator_payload_2026-06-14.json` to `built_request_generator_from_manifest_2026-06-14.json`: PASS.
- builder run from `builder_validator_payload_2026-06-14.json` to `built_request_validator_from_manifest_2026-06-14.json`: PASS.
- built generator request executed through `codex_structured_action_executor.py`: PASS.
- built validator request executed through `codex_structured_action_executor.py`: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_sidecar_bridge.py`: PASS.
- `python documentation/codex/model-routing/scripts/codex_structured_action_sidecar_bridge.py --sidecar-run-dir documentation/codex/model-routing/sidecar-runs/SIDECAR-DOC-DRAFT-001 --workflow-id STRUCTURED-SIDECAR-BRIDGE-001 --skill-id janus-documentation-update --summary "Bridge accepted sidecar documentation draft into structured action flow." --non-goal "No direct repo authority update" --non-goal "No production routing activation" --execute`: PASS.
- built sidecar-bridge request file exists and parses: PASS.
- sidecar-bridge executor summary exists and returns `executor_status=PASS`: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py`: PASS.
- `python documentation/codex/model-routing/scripts/doc_skill_sidecar_draft_runner.py --task-label "Structured review flow validation" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/sidecar_documentation_update_draft_prompt_2026-06-14.md --workflow-id SIDECAR-DOC-STRUCTURED-FLOW-001 --structured-review-flow`: PASS locally; the first Codex tool call hit a tool-timeout window, but the run artifacts show final `validation_result=PASS` and `structured_bridge_status=PASS`.
- `operator_summary.json` for `SIDECAR-DOC-STRUCTURED-FLOW-001` exists and records `SIDECAR_DRAFT_ACCEPTED_AND_STRUCTURED_REVIEW_READY`: PASS.
- `python -m py_compile documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py`: PASS.
- `python documentation/codex/model-routing/scripts/codex_structured_action_sidecar_bridge.py --sidecar-run-dir documentation/codex/model-routing/sidecar-runs/SIDECAR-QUICKCHANGE-LIVE-001 --workflow-id STRUCTURED-QUICKCHANGE-BRIDGE-001 --skill-id janus-quickchange --bridge-mode patch --summary "Bridge accepted quickchange patch proposal into structured review flow." --non-goal "No auto apply" --non-goal "No repo authority update" --execute`: PASS.
- `python documentation/codex/model-routing/scripts/quickchange_sidecar_write_pilot_runner.py --task-label "Structured patch review flow validation" --normal-target-model "5.4/medium" --operator-choice sidecar --prompt-path documentation/codex/model-routing/sidecar-fixtures/quickchange_workspace_write_dry_run_prompt_2026-06-14.md --editable-path frontend/index.html --max-touched-files 1 --workflow-id SIDECAR-QUICKCHANGE-STRUCTURED-FLOW-001 --structured-review-flow --structured-review-source-run-dir documentation/codex/model-routing/sidecar-runs/SIDECAR-QUICKCHANGE-LIVE-001`: PASS.
- `operator_summary.json` for `SIDECAR-QUICKCHANGE-STRUCTURED-FLOW-001` records `DRY_RUN_VALIDATED_AND_STRUCTURED_REVIEW_READY`: PASS.

## Open Risks
- the latest pet-detail formatting fix is locally test-green, but one fresh real Janus retest is still needed to prove that the address-book card now renders the final compact wording automatically instead of fragmented lines.
- the newest contact apply/normalization patch is locally test-green and the local contact row was repaired, but the real Janus app still needs one fresh end-to-end retest after restart to prove that the dog fact now persists automatically in normal workflow use.
- older malformed address variants may still exist in other local contacts if they were created before this sanitizer fix; no broad cleanup pass has been run.
- synonym coverage for other possession verbs beyond `hat` and `besitzt` is still heuristic-based; if the next live retest uses a different phrasing, one more narrow vocabulary patch may still be needed.
- the pet-name path is now locally repaired and manually verified against the saved memory row, but one fresh real live retest is still needed to confirm the automatic extractor-to-contact sync end-to-end after restart.

- The latest `BACKLOG-110` contact fact fix is locally test-green but not yet live-verified after app/backend restart.
- If the next real Janus retest still returns `keine verifizierten Fakten`, the remaining bug is likely after SkillSelector/tool availability, in the post-selector tool-call or response-finalization path.
- The first failed live row saved one debug-only unknown pet fact; later cleanup may be needed if it remains in the user's local memory store.
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
- The Sidecar workflow path is validated for bounded read-only documentation drafts, but no write-capable sidecar path is approved.
- Everyday usage still depends on the task staying inside draft-safe scope; authoritative documentation sync remains a Codex-only step.
- Write-capable delegation will need diff capture, allowlist enforcement, and delete/rename tripwires before any live pilot.
- OpenRouter-as-agent-backend is still unverified in the local Codex CLI provider configuration, so the first write-capable pilot should stay provider-neutral and safety-first.
- The runner/helper still lacks the actual `workspace-write` allowlist enforcement and diff-capture implementation; only the pilot contract is ready.
- The runner/helper is now implemented for dry-run and artifact validation, but no live delegated write path has been exercised yet.
- Only one tiny quickchange write pilot has been proven so far; broader code, debug, or test-writing delegation is still unproven.
- This first live pilot used the local Codex CLI sidecar path, not a verified OpenRouter-as-agent backend.
- The first live test-artifact pilot timed out before generation because the Sidecar shell could not resolve `node` by PATH even though the operator shell can.
- The second live test-artifact retry proved that the next fix is not PATH but PowerShell invocation syntax; the explicit binary path must be called as `& "C:\nvm4w\nodejs\node.exe" ...`.
- The final bounded retry still failed despite the PowerShell-safe form being documented in the prompt, which means this class likely needs runner-level execution support instead of more prompt-only retries.
- The first executor slice exists, but it currently supports only one deterministic generator mapping and no automatic patch apply path.
- The new integrated generator-review helper is validated only for `generate_live_runner_v1`; broader generator families still need explicit mappings before reuse.
- The test-artifact write class is not yet accepted; current live evidence is blocker-only, not delegated artifact success.
- The reviewed structured sidecar flow now covers accepted documentation drafts and bounded quickchange patch proposals, and the operator-facing next step is to test the same reviewed pattern in a real day-to-day documentation workflow before widening scope. Broader sidecar package families and write-capable structured acceptance paths are still not yet wired in.
- `SIDECAR-DOC-FLOW-LIVE-TEST-002` and `SIDECAR-DOC-FLOW-LIVE-TEST-003` just validated that the everyday documentation-skill workflow still offers the bounded `Codex` versus `Sidecar` choice, with `PASS` read-only sidecar drafts and artifact-backed review data for both the original prompt and a small prompt variant.
- All three bounded dispatcher classes are now operator-validated.
- `documentation_draft`, `quickchange_patch_review`, and `generator_review` are now all wired through skill-near operator guidance.
- The dispatcher is now documented as the canonical shared bounded entry beneath those skill-facing operator gates.
- a shared operator playbook now explains when to use the bounded documentation, quickchange, and generator gates in everyday Janus workflow
- one real local everyday quickchange walkthrough now exists for the shared gate model: bounded quickchange gate `PASS`, local `1 = Codex` path selected, and `frontend/index.html` placeholder copy updated from `API Key` to `API-Schlüssel`
- one real delegated everyday generator walkthrough now exists for the shared gate model: bounded generator gate `PASS`, `2 = Delegated` selected, and the deterministic builder/executor/validator review flow returned `GENERATOR_REVIEW_AND_VALIDATION_READY`
- one closeout note now marks the bounded operator enablement package as workflow-ready: canonical dispatcher, three skill-near entries, shared playbook, and everyday walkthrough evidence
- the next bounded expansion order is now explicitly documented, so future delegation work can proceed by class priority instead of ad-hoc probing
- the first next-class plan now exists for `debug_hypothesis_review`, including strict assist-only boundaries and a redaction-first validation path
- the first bounded implementation slice for `debug_hypothesis_review` is now locally validated through the shared operator model: prompt gate `PASS`, local path `PASS`, delegated fixture validation `PASS`, and dispatcher-routed delegated validation `PASS`
- `janus-debug` now has skill-near bounded guidance for `debug_hypothesis_review`, so the first new debug delegation class is no longer hidden behind low-level helper knowledge only
- the second assist-only class is now planned as `test_result_triage_review`, giving the `janus-test-pipeline` side of the roadmap a bounded triage target before any renewed write-capable expansion
- the first bounded implementation slice for `test_result_triage_review` is now locally validated through the shared operator model: prompt gate `PASS`, local path `PASS`, delegated fixture validation `PASS`, and dispatcher-routed delegated validation `PASS`
- `janus-test-pipeline` now has skill-near bounded guidance for `test_result_triage_review`, so the second assist-only delegation class is no longer hidden behind low-level helper knowledge only
- `quickchange_write_apply` is now locally validated through the shared operator model: prompt gate `PASS`, local path `PASS`, delegated accepted-source validation `PASS`, and dispatcher-routed delegated validation `PASS`
- `janus-quickchange` now has skill-near bounded guidance for `quickchange_write_apply`, so the first write-acceptance delegation class is no longer hidden behind low-level helper knowledge only
- `execution_patch_candidate` is now locally validated through the shared operator model: prompt gate `PASS`, local path `PASS`, delegated fixture validation `PASS`, and dispatcher-routed delegated validation `PASS`
- `janus-executioner` now has skill-near bounded guidance for `execution_patch_candidate`, so the first execution proposal delegation class is no longer hidden behind low-level helper knowledge only
- the next bounded expansion decision is now explicit: derivative execution write planning comes before any resumed `test_artifact_write_runner_level` work, because the blocked test-artifact path still needs runner-owned command support rather than another normal class slice
- the next bounded execution write track is now specified in enough detail to become a later helper/dispatcher build step without reopening the class-definition question first
- `execution_write_apply_candidate` is now locally validated through the shared operator model: prompt gate `PASS`, local path `PASS`, delegated accepted-source validation `PASS`, and dispatcher-routed delegated validation `PASS`
- `janus-executioner` now has skill-near bounded guidance for both `execution_patch_candidate` and `execution_write_apply_candidate`, so the derivative execution write-readiness class is no longer hidden behind low-level helper knowledge only
- the first everyday operator walkthrough for `execution_patch_candidate` is now validated, but it is still fixture-backed and does not yet count as a real prechecked product-task acceptance run
- `BACKLOG-110` live evidence is now complete and the contact/address-book branch can be treated as operationally closed

## Next Recommended Step for ChatGPT
Ask for the next Janus work block to move back to the OpenRouter implementation track now that the contact-debug branch is closed.

Treat the eight validated bounded delegation classes as still available, but for `BACKLOG-110` switch attention to live Janus retest. Ask for a real app retry of `Oliver Schwab wohnt in Köln-Stammheim` followed by `und er hat einen Hund`, then decide whether the path is now fixed or whether another `janus-debug` iteration is needed.

## Next Recommended Step for Codex
Run `janus-preimplementation-check` on `TASK-SPEC17.1`, then continue into implementation only if the precheck keeps the slice bounded to request intake, validation, run artifacts, and forbidden-action rejection.

## Last Updated
2026-06-15 18:27 local time

## Latest Handoff Override
Timestamp: `2026-06-15 17:18 local time`

Current goal: carry the first structured-executor slice into a bounded precheck without leaking later generator, validator, or dispatcher scope into the first implementation step.

Active phase: `janus-task-breakdown`, canonical state `PASS`. The spec is compiled into `TASK-SPEC17`, and `TASK-SPEC17.1` is now released as the single preimplementation target via `documentation/tasks/TASK-SPEC17.1_task_breakdown.md`.

Next recommended step for ChatGPT: ask for a live app/backend restart and retry `Oliver Schwab wohnt in Köln-Stammheim` followed by `und er hat einen Hund`. If the response stages/confirms the contact update and does not ask for pronoun clarification, classify the debug as live-passed; otherwise continue `janus-debug` on the post-selector runtime path.

Next recommended step for Codex: capture the live retest evidence. If it passes, prepare the next audit/retest handoff; if it still returns `keine verifizierten Fakten`, inspect the post-selector tool-call or response-finalization path.

## Task Breakdown Override
Timestamp: `2026-06-15 17:18 local time`

Current goal override: carry the first structured-executor slice into a bounded precheck without leaking later generator, validator, or dispatcher scope into the first implementation step.

Active phase override: `janus-task-breakdown`, canonical state `PASS`. The spec is compiled into `TASK-SPEC17`, and `TASK-SPEC17.1` is now released as the single preimplementation target via `documentation/tasks/TASK-SPEC17.1_task_breakdown.md`.

Last work override:
- Completed `janus-task-breakdown` for `TASK-SPEC17.1`.
- Bound the next gate to request intake, schema or shape validation, deterministic run artifacts, and unsupported-action rejection only.
- Kept generator mapping, validator mapping, dispatcher fallback integration, and write or apply authority out of scope for this first target.

Next recommended step for ChatGPT override: keep the architecture track on `TASK-SPEC17.1` and do not reopen `BACKLOG-110` unless a fresh live regression is reported.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC17.1` using Spec 17, `TASK-SPEC17`, and the new task-breakdown handoff only.

## Preimplementation Check Override
Timestamp: `2026-06-15 17:24 local time`

Current goal override: move `TASK-SPEC17.1` from task-design readiness to implementation readiness without widening scope into generator mapping, validator mapping, or dispatcher fallback work.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. The precheck output now exists at `documentation/tasks/TASK-SPEC17.1_preimplementation_check.md` and passed the local validator.

Last work override:
- Created `documentation/tasks/TASK-SPEC17.1_preimplementation_check.md`.
- Locked the first execution slice to request load, schema or shape validation, deterministic run artifacts, and forbidden-action rejection only.
- Explicitly marked `documentation/codex/model-routing/tests/test_codex_structured_action_executor.py` as the focused new test module to add during execution.
- Confirmed local precheck format with `validate_precheck.py`.

Validation override:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC17.1_preimplementation_check.md`: PASS
- `git diff --check`: warnings only, no diff-format failures
- staged-only git guard: PASS, nothing staged

Open risks override:
- `CURRENT_STATE.md` still carries older historical architecture text higher up in the file, so the newest task-breakdown and precheck status is intentionally recorded in override sections.
- The focused executor pytest module named in the precheck does not exist yet; it is part of the next execution step, not pre-existing evidence.
- The first slice remains sensitive because `codex_structured_action_executor.py` already contains later-slice generator and validator logic, so Skill 4 must avoid accidental scope expansion while editing it.

Next recommended step for ChatGPT override: keep the work on the architecture track and do not reopen the older contact-debug branch unless a fresh user report proves regression.

Next recommended step for Codex override: start `janus-executioner` for `TASK-SPEC17.1` on `5.4` medium with the bound precheck artifact and no scope expansion.

## Execution Override
Timestamp: `2026-06-15 17:28 local time`

Current goal override: finish `TASK-SPEC17.1` as a strict structured-action intake skeleton and leave all mapping-backed execution for later task slices.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC17.1` is implemented and closed by `documentation/tasks/TASK-SPEC17.1_execution_result.md`.

What changed:
- `codex_structured_action_executor.py` now explicitly limits the TASK-SPEC17.1 slice to artifact-only action types and rejects later-slice action classes such as `run_generator`.
- Added a focused invalid-action fixture to prove deterministic rejection behavior.
- Added a focused executor test module that covers valid artifact-only handling, later-slice rejection, and CLI artifact persistence on failure.

Changed files:
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- documentation/codex/model-routing/structured-action-fixtures/delegated_request_invalid_action_type_2026-06-15.json
- documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
- documentation/tasks/TASK-SPEC17.1_execution_result.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_draft_markdown_2026-06-14.json`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_invalid_action_type_2026-06-15.json`: expected FAIL, rejection artifacts written
- `python -m pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q`: PASS

Open risks:
- The executor file still contains earlier generator and validator helper code deeper in the file; it is currently unreachable for TASK-SPEC17.1 but should be treated carefully when TASK-SPEC17.2 begins.
- `CURRENT_STATE.md` still contains older historical architecture text higher up, so the newest implementation state is intentionally recorded in override sections.

Next recommended step for ChatGPT override: continue on the structured executor track and review whether the next slice should precheck `TASK-SPEC17.2` immediately.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC17.2` if the user wants to continue the multi-slice rollout without pausing for audit.

## Preimplementation Check 17.2 Override
Timestamp: `2026-06-15 17:35 local time`

Current goal override: move the structured executor rollout from the completed intake skeleton into one bounded first generator-mapping slice without pulling validator or dispatcher work forward.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. The next implementation gate now exists at `documentation/tasks/TASK-SPEC17.2_preimplementation_check.md`.

What changed:
- Created the strict precheck handoff for `TASK-SPEC17.2`.
- Bound the next execution slice to exactly one deterministic `run_generator` path with declared output enforcement and reviewable fallback status.
- Documented the visible prototype drift between the task-bound first path `compile-testspec-to-testplan.mjs` and the existing executor prototype `generate_live_runner_v1` as an in-scope reconciliation point rather than leaving it implicit.

Changed files:
- documentation/tasks/TASK-SPEC17.2_preimplementation_check.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC17.2_preimplementation_check.md`: PASS
- `git diff --check`: warnings only, no diff-format failures
- staged-only git guard: PASS, nothing staged

Open risks:
- The first generator route is not yet unified between task artifact and prototype fixtures, so Skill 4 must converge on one explicit path instead of preserving both.
- The executor file still contains deeper validator and fallback logic that belongs to `TASK-SPEC17.3`; keeping that out of the 17.2 edit boundary remains important.

Next recommended step for ChatGPT override: keep the work on the structured executor track and review the implementation result for `TASK-SPEC17.2` before deciding whether `TASK-SPEC17.3` should be immediate or gated.

Next recommended step for Codex override: start `janus-executioner` for `TASK-SPEC17.2` on `5.4` medium using the new precheck artifact only.

## Execution 17.2 Override
Timestamp: `2026-06-15 17:38 local time`

Current goal override: finish the first generator-enabled structured executor slice and keep validator plus dispatcher fallback work out of scope until `TASK-SPEC17.3`.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC17.2` is implemented and closed by `documentation/tasks/TASK-SPEC17.2_execution_result.md`.

What changed:
- `codex_structured_action_executor.py` now enables exactly one `run_generator` route: `compile_testspec_to_testplan_v1`.
- The executor now enforces a deterministic two-artifact output contract for that route: generated TestPlan plus generated runner inside the executor run directory.
- `compile-testspec-to-testplan.mjs` now accepts explicit `--test-run-id` and `--output-dir` arguments plus a bounded `--skip-skill2-handover` mode so the first executor mapping can stay inside run-directory allowlists.
- Added a bound generator request fixture and updated the unknown-generator fixture to match the 17.2 artifact contract.
- Expanded the focused executor test module to cover the allowed generator route and unknown-generator rejection.

Changed files:
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- tests/e2e/generator/compile-testspec-to-testplan.mjs
- documentation/codex/model-routing/structured-action-fixtures/delegated_request_compile_testspec_to_testplan_2026-06-15.json
- documentation/codex/model-routing/structured-action-fixtures/delegated_request_invalid_action_type_2026-06-15.json
- documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
- documentation/tasks/TASK-SPEC17.2_execution_result.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_compile_testspec_to_testplan_2026-06-15.json`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_invalid_action_type_2026-06-15.json`: expected FAIL, rejection artifacts written
- `python -m pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q`: PASS

Open risks:
- The current first generator route intentionally skips Skill-2 handover generation in executor mode to keep outputs bounded to the run directory; if a later slice needs handover artifacts, that should be introduced deliberately rather than implicitly.
- `codex_structured_action_executor.py` still contains deeper validator-path and fallback logic from later planned slices; that code remains out of scope until `TASK-SPEC17.3`.

Next recommended step for ChatGPT override: keep the structured executor rollout moving and review whether the next safe slice is the validator-plus-fallback precheck for `TASK-SPEC17.3`.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC17.3` if the user wants to continue immediately.

## Preimplementation Check 17.3 Override
Timestamp: `2026-06-15 18:07 local time`

Current goal override: move the structured executor rollout from the first generator slice into one bounded validator-plus-fallback slice without reopening request intake, multi-generator work, or broad assist-only review families.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. The next implementation gate now exists at `documentation/tasks/TASK-SPEC17.3_preimplementation_check.md`.

What changed:
- Created the strict precheck handoff for `TASK-SPEC17.3`.
- Bound the next execution slice to exactly one first deterministic `run_validator` path plus one immediate Codex-local fallback classification on the bounded `janus-test-pipeline` delegation path.
- Explicitly called out the prototype seam between the executor's existing latent validator helpers and the older generator-review validation assumptions, so Skill 4 can reconcile one route deliberately instead of widening validator support.

Changed files:
- documentation/tasks/TASK-SPEC17.3_preimplementation_check.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC17.3_preimplementation_check.md`: PASS
- `git diff --check`: warnings only, no diff-format failures
- staged-only git guard: PASS, nothing staged

Open risks:
- The current bounded `janus-test-pipeline` path still contains an older validation assumption tied to `generate_live_runner_v1`; the next execution slice must converge that seam without silently reintroducing multi-route behavior.
- `codex_test_result_triage_review_runner.py` is named in the task context but should remain pattern-reference only unless a very small compatibility change is truly required.

Next recommended step for ChatGPT override: keep the work on the structured executor track and review the implementation result for `TASK-SPEC17.3` before deciding whether a later slice should expand validator coverage further.

Next recommended step for Codex override: start `janus-executioner` for `TASK-SPEC17.3` on `5.4` medium using the new precheck artifact only.

## Execution 17.3 Override
Timestamp: `2026-06-15 18:16 local time`

Current goal override: finish the first validator-enabled structured executor slice and make the bounded `janus-test-pipeline` delegation path fall back reviewably to Codex-local instead of hard-failing when the structured route is unsupported or broken.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC17.3` is implemented and closed by `documentation/tasks/TASK-SPEC17.3_execution_result.md`.

What changed:
- `codex_structured_action_executor.py` now enables exactly one deterministic `run_validator` route: `validate_runner_v1`.
- The executor now records reviewable validator PASS and validator FAIL runs through the same bounded run-artifact model used by earlier slices.
- `codex_structured_action_generator_review_runner.py` now derives validator manifests for both the legacy single-runner shape and the current `compile_testspec_to_testplan_v1` two-artifact shape.
- `codex_bounded_delegation_dispatcher.py` now converts structured generator-review failure into an explicit `CODEX_LOCAL_FALLBACK_REQUIRED` result instead of aborting the operator path.
- Added one broken-runner validator fixture plus one compile-testspec generator manifest fixture for deterministic local validation.

Changed files:
- documentation/codex/model-routing/scripts/codex_structured_action_executor.py
- documentation/codex/model-routing/scripts/codex_structured_action_generator_review_runner.py
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_failure_2026-06-15.json
- documentation/codex/model-routing/structured-action-fixtures/invalid_generated_runner_2026-06-15.spec.js
- documentation/codex/model-routing/structured-action-fixtures/builder_generator_payload_compile_testspec_2026-06-15.json
- documentation/codex/model-routing/tests/test_codex_structured_action_executor.py
- documentation/tasks/TASK-SPEC17.3_execution_result.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_structured_action_executor.py documentation/codex/model-routing/scripts/codex_structured_action_generator_review_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/tests/test_codex_structured_action_executor.py`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_2026-06-14.json`: PASS
- `python documentation/codex/model-routing/scripts/codex_structured_action_executor.py --request-json documentation/codex/model-routing/structured-action-fixtures/delegated_request_validate_runner_failure_2026-06-15.json`: expected FAIL, reviewable artifacts written
- `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class generator_review ...builder_generator_payload_compile_testspec_2026-06-15.json ...`: PASS
- `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class generator_review ...builder_generator_payload_2026-06-14.json ...`: PASS with explicit fallback result
- `python documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py --task-class documentation_draft ... --operator-choice local ...`: PASS
- `python -m pytest documentation/codex/model-routing/tests/test_codex_structured_action_executor.py -q`: PASS (`6 passed`)
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC17.3_execution_result.md`: PASS

Open risks:
- The current validator slice is still intentionally limited to `validate_runner_v1`; broader validator families remain out of scope until a later prechecked slice binds them explicitly.
- The dispatcher fallback currently preserves operator usability by returning structured fallback JSON, but it does not yet emit a separate richer fallback artifact family beyond the normal bounded dispatch result.

Next recommended step for ChatGPT override: decide whether the structured executor rollout should continue into another bounded precheck slice or pause for final audit at the current package boundary.

Next recommended step for Codex override: run `janus-preimplementation-check` for the next explicit structured executor slice on `5.4` medium, or route to `janus-final-audit` if the user wants to audit the package now.

## Final Audit 17 Override
Timestamp: `2026-06-15 18:27 local time`

Current goal override: close the first structured executor slice as an audited bounded package and hand the result to documentation sync without inventing a non-existent `TASK-SPEC17.4`.

Active phase override: `janus-final-audit`, canonical state `PASS`. The final audit report now exists at `documentation/tasks/TASK-SPEC17_final_audit.md`, and the bound spec has been marked done and moved to `documentation/SPEC/Spec Done/17_structured_executor_first_slice_for_or_sidecar_delegation.md`.

What changed:
- Built the compact audit package at `documentation/tasks/TASK-SPEC17_AUDIT_PACKAGE.md`.
- Final-audited the full three-slice package from `TASK-SPEC17.1` through `TASK-SPEC17.3` with artifact-backed validation and explicit internal-slice manual-evidence `N/A WITH REASON`.
- Added `SPEC IMPLEMENTATION METADATA` to the Spec-17 file and moved it into `documentation/SPEC/Spec Done/`.

Changed files:
- documentation/tasks/TASK-SPEC17_AUDIT_PACKAGE.md
- documentation/tasks/TASK-SPEC17_final_audit.md
- documentation/SPEC/Spec Done/17_structured_executor_first_slice_for_or_sidecar_delegation.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python documentation/codex/skills/codex-audit-package-builder/scripts/build_audit_package.py ...`: PASS
- `python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py documentation/tasks/TASK-SPEC17_final_audit.md`: PASS
- targeted `WHAT_I_LEARNED` search for bounded validator/fallback audit tripwires: reviewed
- staged-only git guard: PASS, nothing staged
- `git diff --check`: warnings only, no diff-format failures

Open risks:
- The completed first slice still intentionally supports only `validate_runner_v1`; further validator families require a new bound Spec or Task slice.
- The dispatcher fallback is operationally reviewable but still minimal in artifact richness; this is a future expansion seam, not a blocker for Spec 17 closure.
- No push has happened, so a remote such as GitHub may not yet contain the newest `CURRENT_STATE` or final-audit artifacts.

Next recommended step for ChatGPT override: route the audited package into documentation sync and registry/state updates, not back into implementation.

Next recommended step for Codex override: start `janus-documentation-update` on `5.4` low to close the Spec-17 package in backlog, registry, dashboard-facing docs, and project-state artifacts.

## Documentation Update 17 Override
Timestamp: `2026-06-15 18:31:24 +02:00`

Current goal override: close the audited Spec-17 package in the documentation layer so registry, project-state, changelog, learning memory, and CURRENT_STATE all point to the same sealed structured-executor slice.

Active phase override: `janus-documentation-update`, canonical state `PASS`. The audited `TASK-SPEC17` package is now synced into registry-facing and project-facing documentation without reopening implementation scope.

What changed:
- Added a sealed `TASK-SPEC17` closure entry to `documentation/01_CENTRAL_TASK_REGISTRY.md`.
- Synced `PROJECT_STATE.md` and `CHANGELOG.md` so the first structured executor slice now appears as a completed audited platform hardening item.
- Added one validated `WHAT_I_LEARNED` pattern for reviewable structured fallback instead of hard-abort behavior.
- Kept the canonical completion boundary on the audited three-slice package only; no new Spec-17.4 or rollout expansion was introduced.

Changed files:
- documentation/01_CENTRAL_TASK_REGISTRY.md
- PROJECT_STATE.md
- CHANGELOG.md
- WHAT_I_LEARNED.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/ai/CURRENT_STATE.md
- documentation/codex/SKILL_USAGE_LOG.md

Checks run:
- `python documentation/codex/scripts/search_what_i_learned.py --query "structured executor fallback audit package deterministic generator validator" --limit 5`: PASS
- `python C:\Users\pruve\.codex\skills\janus-documentation-update\scripts\validate_doc_update.py --repo C:\KI\Janus-Projekt --marker TASK-SPEC17 --require documentation/01_CENTRAL_TASK_REGISTRY.md --require PROJECT_STATE.md --require WHAT_I_LEARNED.md --require CHANGELOG.md --require documentation/ai/CURRENT_STATE.md`: PASS
- staged-only git guard: PASS, nothing staged
- `git diff --check`: warnings only, no diff-format failures
- `python documentation/codex/scripts/record_skill_usage.py ...`: PASS

Open risks:
- The first structured executor slice remains intentionally narrow; only the first deterministic generator and validator families are covered by the audited package.
- No push has happened, so a remote such as GitHub may not yet contain this CURRENT_STATE sync or the documentation closure entries.

Next recommended step for ChatGPT override: either checkpoint the sealed Spec-17 documentation state or decide on one fresh bounded follow-up slice for structured delegation.

Next recommended step for Codex override: if the user wants to continue the architecture track, route back through `janus-skill-router` or into one new bounded precheck on `5.4` medium instead of extending Spec 17 informally.

## Spec Generation 18 Override
Timestamp: `2026-06-15 18:45 local time`

Current goal override: define the next bounded OR or Sidecar follow-up after the audited Spec-17 foundation so the architecture track can move toward real delegated write value without skipping Codex-owned acceptance gates.

Active phase override: `janus-spec-generator`, canonical state `PASS`. A new bounded follow-up spec now exists for the first delegated write-apply candidate path, instead of informally extending Spec 17.

What changed:
- Locked the next architecture step to `execution_write_apply_candidate` rather than additional assist-only expansion.
- Generated a fresh follow-up spec at `documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`.
- Preserved the key governance rule that delegated write attempts remain bounded by exact allowlists, touched-file caps, mandatory diff and validation capture, and Codex-owned accept or reject authority.

Changed files:
- documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- reviewed `documentation/codex/model-routing/codex_execution_write_apply_candidate_plan_2026-06-14.md`
- reviewed the sealed Spec-17 outcome and CURRENT_STATE open-risk thread
- spec structure generated in Janus Diamond format: PASS

Open risks:
- The new spec is still unreviewed; no task, precheck, or implementation artifact exists yet for Spec 18.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and this new spec.
- No push has happened, so remotes may not contain the new Spec-18 design state.

Next recommended step for ChatGPT override: review the new bounded write-candidate spec and confirm whether its acceptance and abort rules stay narrow enough for the intended OR workhorse path.

Next recommended step for Codex override: run `janus-spec-review` on `documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md` using `5.4` with medium-high reasoning.

## Spec Review 18 Override
Timestamp: `2026-06-15 18:52 local time`

Current goal override: verify that the new bounded delegated write-apply candidate spec is narrow, deterministic, and ready for task compilation without silently broadening OR or Sidecar authority.

Active phase override: `janus-spec-review`, canonical state `PASS`. Spec 18 is reviewed and ready for task compilation with non-blocking notes only.

What changed:
- Reviewed `documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md` against Janus spec gates for bounded scope, acceptance clarity, and decomposition readiness.
- Wrote the `SPEC REVIEW METADATA` block with `APPROVED_WITH_NOTES`.
- Kept the write candidate bounded to exact allowlists, touched-file caps, mandatory diff plus validation capture, and Codex-owned accept or reject authority.

Changed files:
- documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-spec-review\scripts\validate_spec_review.py --spec documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`: pending
- spec review gate pass on bounded scope, edge cases, non-goals, and decomposition readiness: PASS

Open risks:
- The spec is intentionally strict, but the first implementation slice still needs later task compilation to choose an exact first write-candidate seam instead of leaving that to implementation chat.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and Spec-18 review state.
- No push has happened, so remotes may not contain the new Spec-18 reviewed state.

Next recommended step for ChatGPT override: compile Spec 18 into bounded implementation tasks and keep the first task narrower than full write-capable rollout.

Next recommended step for Codex override: run `janus-spec-to-task` on `documentation/SPEC/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md` using `5.4` with medium-high reasoning.

## Spec To Task 18 Override
Timestamp: `2026-06-15 18:58 local time`

Current goal override: convert the reviewed Spec-18 write-candidate design into bounded implementation tasks so the next execution path can resume through normal task-breakdown and precheck gates.

Active phase override: `janus-spec-to-task`, canonical state `PASS`. Spec 18 is now compiled into one deterministic task artifact with three bounded implementation slices.

What changed:
- Created `documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`.
- Split the work into three bounded slices:
  - entry-contract plus allowlist enforcement
  - reviewable diff plus changed-files capture
  - validation summary plus Codex-owned accept or reject flow
- Kept the first slice narrower than a full write-capable rollout by making entry gating and hard rejects the first implementation target.

Changed files:
- documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- task decomposition reviewed against reviewed Spec 18: PASS
- `python C:\Users\pruve\.codex\skills\janus-spec-to-task\scripts\validate_task_artifact.py --task documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`: PASS

Open risks:
- The generated tasks still depend on later task-breakdown choosing one exact first target seam and file cluster before preimplementation can begin.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and the new Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 task artifact.

Next recommended step for ChatGPT override: release exactly one target task from `TASK-SPEC18`, starting with the entry-contract and allowlist gate rather than jumping to later diff or validation slices.

Next recommended step for Codex override: run `janus-task-breakdown` on `documentation/tasks/TASK-SPEC18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md` with `Target Task: TASK-SPEC18.1`.

## Task Breakdown 18.1 Override
Timestamp: `2026-06-15 19:05 local time`

Current goal override: release exactly one first implementation-ready task from Spec 18 without accidentally widening the delegated write-candidate rollout into later diff or validation phases.

Active phase override: `janus-task-breakdown`, canonical state `PASS`. `TASK-SPEC18.1` is now released as the single preimplementation target for the bounded write-candidate entry gate.

What changed:
- Created `documentation/tasks/TASK-SPEC18.1_task_breakdown.md`.
- Narrowed the first implementation slice to exact entry-contract enforcement only:
  - exact target-task gate
  - exact editable-path allowlist requirement
  - touched-file-cap requirement
  - delete-rename-move tripwire
  - reviewable reject or fallback status
- Kept diff capture, changed-files capture, validation-summary capture, and final accept-reject normalization explicitly out of scope for this first target.

Changed files:
- documentation/tasks/TASK-SPEC18.1_task_breakdown.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-task-breakdown\scripts\validate_task_handoff.py --task documentation/tasks/TASK-SPEC18.1_task_breakdown.md --target TASK-SPEC18.1`: PASS
- task-breakdown gate on scope, files, tests, and first-slice narrowness: PASS

Open risks:
- The first write-candidate task still needs preimplementation to freeze one exact fixture family and one exact test surface before execution starts.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and new Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 task-breakdown state.

Next recommended step for ChatGPT override: run the preimplementation gate only for `TASK-SPEC18.1` and keep later write-candidate phases out of scope until the entry contract is green.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC18.1` on `5.4` with medium reasoning.

## Preimplementation Check 18.1 Override
Timestamp: `2026-06-15 19:12 local time`

Current goal override: freeze the first delegated write-candidate slice as one exact prechecked execution gate before any later diff-capture, changed-files capture, or validation-summary expansion begins.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. `TASK-SPEC18.1` is now implementation-ready as the first bounded delegated write-candidate entry-gate slice.

What changed:
- Created `documentation/tasks/TASK-SPEC18.1_preimplementation_check.md`.
- Confirmed that `TASK-SPEC18.1` stays atomic:
  - one exact target-task contract
  - one exact editable-path allowlist requirement
  - one touched-file-cap requirement
  - one delete-rename-move tripwire family
  - one reviewable reject or fallback output family
- Kept diff capture, changed-files capture, validation-summary capture, and final accept-reject normalization explicitly out of scope for this first implementation target.

Changed files:
- documentation/tasks/TASK-SPEC18.1_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC18.1_preimplementation_check.md`: PASS
- precheck gate on artifact identity, scope boundedness, file cluster, test surface, and model assignment: PASS

Open risks:
- The planned focused pytest target for this slice does not exist yet and must be introduced by the implementation result as part of the bounded evidence bundle.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and new Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 precheck state.

Next recommended step for ChatGPT override: start execution only for `TASK-SPEC18.1` and do not pull later write-candidate phases forward during implementation.

Next recommended step for Codex override: run `janus-executioner` for `TASK-SPEC18.1` on `5.4` with medium reasoning.

## Execution 18.1 Override
Timestamp: `2026-06-15 19:35 local time`

Current goal override: land the first bounded delegated write-candidate entry gate so only exact prechecked target-task packages with explicit allowlists and touched-file caps can enter later delegated execution phases.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC18.1` is complete as the first admissibility gate for delegated execution write candidates.

What changed:
- Hardened `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py` with an explicit `execution_write_apply_candidate` entry-gate path for:
  - exact target-task matching
  - required allowlist
  - required touched-file cap
  - delete-rename-move tripwire rejection
  - reviewable reject or fallback status before later write phases
- Hardened `documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py` so `validate_write_candidate_entry_v1` manifests cannot skip the bounded entry-contract fields.
- Added four focused fixtures plus `documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py` to prove:
  - valid bounded entry acceptance
  - missing allowlist rejection
  - missing touched-file-cap rejection
  - delete-intent rejection
- Created `documentation/tasks/TASK-SPEC18.1_execution_result.md`.

Changed files:
- documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py
- documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py
- documentation/codex/model-routing/structured-action-fixtures/execution_write_candidate_entry_valid_2026-06-15.json
- documentation/codex/model-routing/structured-action-fixtures/execution_write_candidate_entry_missing_allowlist_2026-06-15.json
- documentation/codex/model-routing/structured-action-fixtures/execution_write_candidate_entry_missing_touched_cap_2026-06-15.json
- documentation/codex/model-routing/structured-action-fixtures/execution_write_candidate_entry_delete_intent_2026-06-15.json
- documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py
- documentation/tasks/TASK-SPEC18.1_execution_result.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py documentation/codex/model-routing/scripts/codex_structured_action_request_builder.py`: PASS
- `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py -q`: PASS (`4 passed`)
- `python documentation/codex/model-routing/tests/test_bounded_write_candidate_entry_gate.py`: PASS
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.1_execution_result.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- Later `TASK-SPEC18.2` still has to add actual diff plus changed-files artifact capture for the admitted delegated write-candidate path.
- Later `TASK-SPEC18.3` still has to add validation-summary capture and final Codex-owned accept or reject normalization.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and current Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 execution state.

Next recommended step for ChatGPT override: precheck and execute `TASK-SPEC18.2` next if you want to continue the bounded delegated write-candidate rollout; otherwise final-audit just this first gate slice.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC18.2` on `5.4` with medium reasoning.

## Preimplementation Check 18.2 Override
Timestamp: `2026-06-15 19:46 local time`

Current goal override: freeze the second delegated write-candidate slice as one exact prechecked artifact-capture seam before any later validation-summary or accept-reject normalization begins.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. `TASK-SPEC18.2` is now implementation-ready as the bounded diff-plus-changed-files capture slice.

What changed:
- Created `documentation/tasks/TASK-SPEC18.2_preimplementation_check.md`.
- Confirmed that `TASK-SPEC18.2` stays atomic:
  - required `git_diff.patch`
  - required `changed_files.txt`
  - required `summary.json`, `stdout.log`, `stderr.log`, and `exit_code.txt`
  - reject-capable artifact completeness checks before later validation-summary and accept-reject phases
- Kept validation-summary capture and final Codex-owned accept or reject normalization explicitly out of scope for this second implementation target.

Changed files:
- documentation/tasks/TASK-SPEC18.2_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC18.2_preimplementation_check.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The planned focused pytest target for artifact completeness does not exist yet and must be introduced by the implementation result as part of the bounded evidence bundle.
- `TASK-SPEC18.3` still remains for validation-summary capture and final Codex-owned accept or reject normalization.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and current Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 precheck state.

Next recommended step for ChatGPT override: start execution only for `TASK-SPEC18.2` and do not pull `TASK-SPEC18.3` forward during implementation.

Next recommended step for Codex override: run `janus-executioner` for `TASK-SPEC18.2` on `5.4` with medium reasoning.

## Execution 18.2 Override
Timestamp: `2026-06-15 19:55 local time`

Current goal override: land the second bounded delegated write-candidate slice so an admitted candidate always carries reviewable diff and changed-files artifacts plus the standard run bundle before any later acceptance logic.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC18.2` is complete as the bounded diff-plus-changed-files artifact-capture slice.

What changed:
- Hardened `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py` so accepted-source validation now requires:
  - `summary.json`
  - `stdout.log`
  - `stderr.log`
  - `exit_code.txt`
  - `git_diff.patch`
  - `changed_files.txt`
- Added artifact-quality checks for:
  - empty `git_diff.patch`
  - empty `changed_files.txt`
  - mismatch between `changed_files.txt` and `validation_summary.json`
  - summary pointers that do not reference `git_diff.patch` and `changed_files.txt`
- Added `documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py` with focused coverage for:
  - complete accepted-source bundle
  - missing diff artifact
  - missing changed-files artifact
  - changed-files mismatch
- Created `documentation/tasks/TASK-SPEC18.2_execution_result.md`.

Changed files:
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py
- documentation/tasks/TASK-SPEC18.2_execution_result.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py`: PASS
- `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py -q`: PASS (`4 passed`)
- `python documentation/codex/model-routing/tests/test_bounded_write_candidate_artifact_capture.py`: PASS
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.2_execution_result.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- `TASK-SPEC18.3` still remains for validation-summary capture and final Codex-owned accept or reject normalization.
- This slice validates accepted-source artifact completeness locally but does not yet normalize the final operator-facing accept or reject outcome.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and current Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 execution state.

Next recommended step for ChatGPT override: precheck and execute `TASK-SPEC18.3` next if you want to finish the bounded delegated write-candidate rollout; otherwise final-audit just the first two slices.

Next recommended step for Codex override: run `janus-preimplementation-check` for `TASK-SPEC18.3` on `5.4` with medium reasoning.

## Preimplementation Check 18.3 Override
Timestamp: `2026-06-15 20:03 local time`

Current goal override: freeze the final delegated write-candidate slice as one exact validation-summary and Codex-owned accept-or-reject seam before any broader rollout or audit closeout.

Active phase override: `janus-preimplementation-check`, canonical state `PASS`. `TASK-SPEC18.3` is now implementation-ready as the final validation-summary plus accept-or-reject slice.

What changed:
- Created `documentation/tasks/TASK-SPEC18.3_preimplementation_check.md`.
- Confirmed that `TASK-SPEC18.3` stays atomic:
  - required `validation_summary.json`
  - reject on missing local validation summary
  - reject on failed local validation
  - normalized operator-facing final outcome that keeps Codex as explicit accept-or-reject owner
- Kept broader rollout, new delegation classes, and earlier allowlist or diff-capture work explicitly out of scope for this last implementation target.

Changed files:
- documentation/tasks/TASK-SPEC18.3_preimplementation_check.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-preimplementation-check\scripts\validate_precheck.py documentation/tasks/TASK-SPEC18.3_preimplementation_check.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The planned focused pytest target for validation-summary and normalized final outcomes does not exist yet and must be introduced by the implementation result as part of the bounded evidence bundle.
- After `TASK-SPEC18.3`, the remaining question becomes whether to final-audit the sealed Spec-18 package or continue into a fresh higher-level workflow slice.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and current Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 precheck state.

Next recommended step for ChatGPT override: start execution only for `TASK-SPEC18.3` and keep the final scope on validation-summary enforcement plus Codex-owned accept-or-reject wording.

Next recommended step for Codex override: run `janus-executioner` for `TASK-SPEC18.3` on `5.4` with medium reasoning.

## Execution 18.3 Override
Timestamp: `2026-06-15 20:11 local time`

Current goal override: close the final delegated write-candidate trust boundary so accepted proposal-first evidence must include validation-summary proof and an explicit Codex-owned accept-or-reject operator outcome.

Active phase override: `janus-executioner`, canonical state `PASS`. `TASK-SPEC18.3` is complete as the final validation-summary plus Codex-owned accept-or-reject slice.

What changed:
- Hardened `documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py` so accepted-source validation now:
  - rejects missing `validation_summary.json`
  - rejects non-`PASS` validation status
  - preserves reject behavior when `accepted_for_codex_patch_review` is false
- Normalized the operator-facing PASS outcome to:
  - `EXECUTION_WRITE_APPLY_CANDIDATE_READY_FOR_CODEX_ACCEPT_REJECT`
- Added `main_with_args(...)` for deterministic runner invocation in focused local tests.
- Added `documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py` with focused coverage for:
  - missing `validation_summary.json`
  - failed local validation
  - normalized Codex-owned PASS outcome
- Created `documentation/tasks/TASK-SPEC18.3_execution_result.md`.

Changed files:
- documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py
- documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py
- documentation/tasks/TASK-SPEC18.3_execution_result.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_write_apply_candidate_runner.py documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py`: PASS
- `python -m pytest documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py -q`: PASS (`3 passed`)
- `python documentation/codex/model-routing/tests/test_bounded_write_candidate_validation_acceptance.py`: PASS
- `python C:\Users\pruve\.codex\skills\janus-executioner\scripts\validate_execution_result.py documentation/tasks/TASK-SPEC18.3_execution_result.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- Spec 18 implementation is now complete, but the package has not yet passed `janus-final-audit`.
- No compact audit package exists yet for the Spec-18 slice, so final audit may either work directly from the three execution results or benefit from a task-scoped audit package first.
- The repo still contains many unrelated dirty and untracked changes outside the sealed Spec-17 checkpoint and current Spec-18 path.
- No push has happened, so remotes may not contain the new Spec-18 execution state.

Next recommended step for ChatGPT override: run `janus-final-audit` for the sealed Spec-18 package, optionally after building a compact task-scoped audit package.

Next recommended step for Codex override: run `janus-final-audit` on `5.5` with high reasoning if you want the strongest release-gate style review for the completed Spec-18 slice package.

## Final Audit 18 Override
Timestamp: `2026-06-15 23:21 local time`

Current goal override: close the bounded delegated write-apply candidate rollout with a formal final audit, archive the finished Spec-18 package, and hand off only the documentation closeout.

Active phase override: `janus-final-audit`, canonical state `PASS`. Spec 18 passed final audit and has been moved to `documentation/SPEC/Spec Done/`.

What changed:
- Created `documentation/tasks/TASK-SPEC18_AUDIT_PACKAGE.md` as the compact bounded audit package for the completed three-slice rollout.
- Created `documentation/tasks/TASK-SPEC18_final_audit.md` and validated it with the Janus final-audit validator.
- Appended Spec implementation metadata to Spec 18 and moved it to:
  - `documentation/SPEC/Spec Done/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md`
- Kept the audit decision bounded to:
  - exact allowlist and touched-file-cap entry gating
  - mandatory diff and changed-files evidence
  - mandatory validation-summary evidence plus explicit Codex-owned accept-or-reject wording

Changed files:
- documentation/tasks/TASK-SPEC18_AUDIT_PACKAGE.md
- documentation/tasks/TASK-SPEC18_final_audit.md
- documentation/SPEC/Spec Done/18_bounded_execution_write_apply_candidate_for_or_sidecar_delegation.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python C:\Users\pruve\.codex\skills\janus-final-audit\scripts\validate_final_audit.py documentation/tasks/TASK-SPEC18_final_audit.md`: PASS
- audit package evidence review across `TASK-SPEC18.1`, `TASK-SPEC18.2`, and `TASK-SPEC18.3`: PASS
- Spec-18 archival move to `documentation/SPEC/Spec Done/`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The repo still contains unrelated dirty and untracked changes outside the sealed Spec-18 path, so any later commit must stay scoped.
- No push has happened, so remotes may not contain the passed Spec-18 audit state or the latest `CURRENT_STATE`.
- Documentation closeout for the passed Spec-18 package still remains as the next Janus skill gate.

Next recommended step for ChatGPT override: start `janus-documentation-update` for the passed Spec-18 package so registry/state artifacts can be synchronized against the new final audit.

Next recommended step for Codex override: run `janus-documentation-update` on `5.4 mini` with low reasoning for the documentation-only closeout block.

## Documentation Update 18 Override
Timestamp: `2026-06-16 00:05 local time`

Current goal override: synchronize the passed Spec-18 package across the central registry, project snapshot, changelog, reusable learning memory, and CURRENT_STATE so the bounded delegated write-candidate rollout is queryable as a sealed documentation state.

Active phase override: `janus-documentation-update`, canonical state `PASS`. The passed Spec-18 package is now documented across the required Janus closeout artifacts.

What changed:
- Added a `TASK-SPEC18` closure entry to `documentation/01_CENTRAL_TASK_REGISTRY.md`.
- Updated `PROJECT_STATE.md` so `TASK-SPEC18` appears in the compact current-session delta and the header timestamp reflects the newest sealed package.
- Added an `Unreleased` changelog bullet for the bounded delegated write-apply candidate hardening package in `CHANGELOG.md`.
- Appended the reusable pattern `#DelegatedWriteCandidateNeedsThreeTrustSeams` to `WHAT_I_LEARNED.md`.

Changed files:
- documentation/01_CENTRAL_TASK_REGISTRY.md
- PROJECT_STATE.md
- CHANGELOG.md
- WHAT_I_LEARNED.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- `python documentation/codex/scripts/search_what_i_learned.py --query "bounded delegated write candidate final audit documentation closeout" --limit 5`: PASS
- `python documentation/codex/scripts/append_learning_pattern.py --id DelegatedWriteCandidateNeedsThreeTrustSeams ...`: PASS
- `python C:\Users\pruve\.codex\skills\janus-documentation-update\scripts\validate_doc_update.py --repo C:\KI\Janus-Projekt --marker TASK-SPEC18 --require documentation/01_CENTRAL_TASK_REGISTRY.md --require PROJECT_STATE.md --require CHANGELOG.md --require WHAT_I_LEARNED.md`: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The sealed `BACKLOG-112` package removes the dry-run-only operator-path blocker, but no new live OR pilot has been executed yet through the newly documented quickchange seam.
- The repo still contains unrelated dirty and untracked changes outside the sealed Spec-18 package, so any later commit must stay intentionally scoped.
- No push has happened, so remotes may not contain the `BACKLOG-112` documentation closeout or this synchronized CURRENT_STATE snapshot.
- The next real decision is whether to checkpoint the sealed `BACKLOG-112` package or move directly into the next bounded OR pilot planning or execution gate.

Next recommended step for ChatGPT override: if you want to preserve the sealed package now, route next to `janus-git-governance`; otherwise resume the bounded OR pilot track from the now-unblocked `janus-quickchange` seam or continue the structured-executor precheck path.

Next recommended step for Codex override: use `janus-git-governance` on `5.4` medium for a scoped checkpoint, or `janus-quickchange` / bounded pilot planning on `5.4` medium now that `BACKLOG-112` is sealed.

## First Real OR Pilot Decision Override
Timestamp: `2026-06-16 00:13 local time`

Current goal override: lock the first real bounded OR pilot class so later live testing starts on the safest write-capable Janus surface instead of broad execution work.

Active phase override: `janus-feature-design`, canonical state `PASS`. The first real bounded OR pilot is now decision-locked as a `janus-quickchange` delegated write candidate, not a broader `janus-executioner` slice.

What changed:
- Created `documentation/codex/model-routing/codex_first_real_or_pilot_decision_summary_2026-06-16.md`.
- Locked the first real OR pilot to:
  - existing `janus-quickchange` surface
  - one tiny prechecked write slice
  - exact allowlist, touched-file-cap, diff, changed-files, and validation evidence
  - explicit Codex-owned final accept-or-reject authority
- Explicitly kept broader `janus-executioner` delegation, test-pipeline write retries, Auto Router, and production routing out of scope for the first live pilot.

Changed files:
- documentation/codex/model-routing/codex_first_real_or_pilot_decision_summary_2026-06-16.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- repo evidence reread for `execution_write_apply_candidate` and delegation-matrix guidance: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The pilot class is now chosen, but there is still no concrete tiny quickchange slice bound for the first live OR run.
- The repo still contains unrelated dirty and untracked changes outside the pilot planning artifact.
- No push has happened, so remotes may not contain the sealed Spec-18 closeout or this pilot decision.

Next recommended step for ChatGPT override: bind one tiny real quickchange candidate and route it through `janus-quickchange` as the first bounded OR pilot.

Next recommended step for Codex override: run `janus-quickchange` on `5.4` medium to select and validate one tiny real quickchange slice for the first live OR test.

## Backlog Intake 112 Override
Timestamp: `2026-06-16 00:24 local time`

Current goal override: capture the newly discovered quickchange live-execute gap as a bindable Janus backlog item before any real OR pilot is attempted through that path.

Active phase override: `janus-backlog-intake`, canonical state `PASS`. The first real OR pilot is temporarily blocked by a documented bounded-runner gap, and that gap is now captured as a ready backlog item.

What changed:
- Added `BACKLOG-112` to `documentation/backlog/BACKLOG.md`.
- Captured that the chosen first real OR pilot class (`janus-quickchange`) still routes new delegated runs through a Dry-Run helper path instead of a real bounded live execute path.
- Locked the next concrete work item to enabling a true bounded live execute attempt under the existing allowlist, file-cap, diff, and validation gates.

Changed files:
- documentation/backlog/BACKLOG.md
- documentation/codex/SKILL_USAGE_LOG.md
- documentation/ai/CURRENT_STATE.md

Checks run:
- bounded quickchange runner-path inspection across dispatcher and sidecar runner: PASS
- `git diff --check`: PASS with CRLF warnings only in unrelated dirty-worktree files
- staged-only git guard via `git diff --cached --name-only`: PASS (nothing staged)

Open risks:
- The first real OR pilot still cannot run through the intended quickchange path until `BACKLOG-112` is implemented.
- The repo still contains unrelated dirty and untracked changes outside this backlog-intake artifact.
- No push has happened, so remotes may not contain the new pilot-decision note or `BACKLOG-112`.

Next recommended step for ChatGPT override: prioritize `BACKLOG-112` and route it toward a bounded implementation handoff so the first real OR quickchange pilot can become executable.

Next recommended step for Codex override: run `janus-backlog-prioritization` on `5.4 mini` low if you want to keep the pipeline formal, or stay on `5.4` medium and prepare the bounded implementation route for `BACKLOG-112`.

## Quickchange Pilot Override
Timestamp: `2026-06-16 01:34 local time`

Current goal override: prove the first real bounded delegated `janus-quickchange` workflow on one tiny live frontend copy change now that `BACKLOG-112` has unblocked the operator-facing live-execute seam.

Active phase override: `janus-quickchange`, canonical state `PASS`. One delegated quickchange run has now completed under the shared bounded dispatcher with exact one-file allowlist control and local Codex acceptance.

What changed:
- Created a bounded sidecar prompt fixture in `documentation/codex/model-routing/sidecar-fixtures/quickchange_cost_deepdive_requests_to_anfragen_2026-06-16.md`.
- Ran `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py` with `--task-class quickchange_patch_review`, `--operator-choice delegated`, `--editable-path frontend/js/cost-visualizer.js`, and `--max-touched-files 1` under workflow `BOUNDED-QUICKCHANGE-DEEPDIVE-REQUESTS-001`.
- Accepted the delegated result locally after artifact review: `frontend/js/cost-visualizer.js` now replaces the remaining user-facing `Requests` labels in the DeepDive cost UI with `Anfragen`.

Changed files:
- `documentation/codex/model-routing/sidecar-fixtures/quickchange_cost_deepdive_requests_to_anfragen_2026-06-16.md`
- `frontend/js/cost-visualizer.js`
- `documentation/codex/SKILL_USAGE_LOG.md`
- `documentation/ai/CURRENT_STATE.md`

Checks run:
- bounded dispatcher delegated quickchange run `BOUNDED-QUICKCHANGE-DEEPDIVE-REQUESTS-001`: PASS
- sidecar summary allowlist/touched-file/delete-rename-move gates: PASS
- `node --check frontend/js/cost-visualizer.js`: PASS
- `rg -n "Requests|Anfragen" frontend/js/cost-visualizer.js`: PASS
- diff review of `documentation/codex/model-routing/sidecar-runs/BOUNDED-QUICKCHANGE-DEEPDIVE-REQUESTS-001/git_diff.patch`: PASS

Open risks:
- This is one accepted bounded quickchange live run, not broad delegated write approval for other Janus skills or larger quickchange scopes.
- The worktree still contains many unrelated local changes outside this quickchange slice.
- No new commit or push has happened after this quickchange, so a remote such as GitHub or `backup` does not yet contain this latest `CURRENT_STATE`.

Next recommended step for ChatGPT override: if this pilot should be preserved immediately, route next to `janus-git-governance`; otherwise bind one second tiny delegated quickchange in a similarly narrow frontend copy surface to extend evidence.

Next recommended step for Codex override: use `janus-git-governance` on `5.4` medium for a scoped checkpoint, or stay on `janus-quickchange` with `5.4` medium for one more tiny delegated write candidate in a clean one-file UI copy surface.

## Quickchange Pilot Extension Override
Timestamp: `2026-06-16 01:47 local time`

Current goal override: extend bounded delegated quickchange evidence with a second accepted one-file live run on a different frontend surface so the operator-facing path is no longer proven by only one copy-only example.

Active phase override: `janus-quickchange`, canonical state `PASS`. A second delegated quickchange run has now completed under the shared bounded dispatcher on a separate clean file with the same one-file allowlist and acceptance discipline.

What changed:
- Created a second bounded sidecar prompt fixture in `documentation/codex/model-routing/sidecar-fixtures/quickchange_mail_ai_summary_labels_to_german_2026-06-16.md`.
- Ran `documentation/codex/model-routing/scripts/codex_bounded_delegation_dispatcher.py` with `--task-class quickchange_patch_review`, `--operator-choice delegated`, `--editable-path frontend/js/mail-modal.js`, and `--max-touched-files 1` under workflow `BOUNDED-QUICKCHANGE-MAIL-AI-LABELS-001`.
- Accepted the delegated result locally after artifact review: `frontend/js/mail-modal.js` now uses `Zusammenfassung:` and `Antwort:` for the visible mail AI summary labels while keeping `Prio:` unchanged.

Changed files:
- `documentation/codex/model-routing/sidecar-fixtures/quickchange_mail_ai_summary_labels_to_german_2026-06-16.md`
- `frontend/js/mail-modal.js`
- `documentation/codex/SKILL_USAGE_LOG.md`
- `documentation/ai/CURRENT_STATE.md`

Checks run:
- bounded dispatcher delegated quickchange run `BOUNDED-QUICKCHANGE-MAIL-AI-LABELS-001`: PASS
- sidecar summary allowlist/touched-file/delete-rename-move gates: PASS
- `node --check frontend/js/mail-modal.js`: PASS
- `rg -n "Summary:|Reply:|Prio:|Zusammenfassung:|Antwort:" frontend/js/mail-modal.js`: PASS
- diff review of `frontend/js/mail-modal.js`: PASS

Open risks:
- Two accepted bounded quickchange live runs now exist, but this still does not authorize broad delegated write use for larger Janus skills or multi-file changes.
- The repo still contains many unrelated local changes outside this quickchange slice.
- No new commit or push has happened after this second quickchange, so a remote such as GitHub or `backup` does not yet contain this latest `CURRENT_STATE`.

Next recommended step for ChatGPT override: checkpoint both accepted quickchange pilots with `janus-git-governance`, then decide whether to bind the first bounded delegated non-quickchange workflow or add one more narrow pilot in another safe class.

Next recommended step for Codex override: use `janus-git-governance` on `5.4` medium for a scoped checkpoint commit, or stay on `5.4 mini` low only if you want one more purely mechanical documentation sync before any new live delegated class is attempted.
