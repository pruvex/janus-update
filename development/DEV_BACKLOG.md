# DEV_BACKLOG

This backlog tracks Dev- and OR-infrastructure work only. It is separate from the Janus product backlog.

## Status Rules

- `NEEDS INFO`: required infrastructure context is missing
- `READY`: clear enough for bounded Dev implementation or governance work
- `IN PROGRESS`: explicitly active in the Dev system
- `DONE`: completed with evidence
- `BLOCKED`: cannot proceed without an external decision or dependency

## Scope Rules

- Include only Dev environment, OR infrastructure, runner, wrapper, telemetry, model-routing support, operator-flow support, and related governance work.
- Do not use this backlog for Janus product features, user-facing behavior, release notes, or product bug prioritization.
- If a Janus product item depends on a Dev item here, Janus keeps only the product context and a slim reference.

## IN PROGRESS

## READY

### DEV-001 - Migrate mixed Dev and OR infrastructure topics out of Janus backlog

- **Type:** GOVERNANCE
- **Status:** READY
- **Short Description:** Move existing Dev- and OR-infrastructure topics out of the Janus product backlog into this Dev system without losing product context where a slim Janus reference is still needed.
- **Area:** Backlog governance / migration

### DEV-002 - Harden Janus governance docs to enforce Dev separation

- **Type:** GOVERNANCE
- **Status:** READY
- **Short Description:** Update Janus governance files so future Dev- and OR-infrastructure topics do not drift back into the Janus product system.
- **Area:** Governance hardening

## DONE

### DEV-006 - Add a bounded input-prep helper for MCP recommendation packages

- **Type:** IMPROVEMENT
- **Status:** DONE
- **Created:** 2026-07-04
- **Updated:** 2026-07-04
- **Completed:** 2026-07-04
- **Source:** User Intake
- **Follow-up to:** DEV-005 - Add a lightweight renderer stub for MCP recommendation artifacts
- **Short Description:** Add one small local input-prep helper that assembles the structured recommendation package for the renderer from bounded local evidence fields so Codex does not have to hand-build the JSON payload every time.
- **Expected Behavior:** After reviewing local MCP/live notes and internal evidence, Codex can pass a small bounded evidence bundle into a local input-prep helper and receive one renderer-ready structured package with stable keys and section mapping.
- **Actual Behavior:** CLOSED - `DEV-006.1` adds the bounded local input-prep helper, source bundle, and prepared renderer-ready package while keeping the recommendation-only approval boundary intact.
- **Reproduction / Context:** `DEV-005.1` proved that the renderer path is useful and safe. This follow-up removes repetitive manual JSON assembly while still avoiding live fetches, executor changes, and delegated write authority.
- **Area:** OpenRouter MCP / recommendation package preparation workflow
- **Evidence:** `development/openrouter-skill-tests/openrouter_mcp_recommendation_source_bundle_2026-07-04.json`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_prepared_input_2026-07-04.json`; `development/tasks/DEV-006.1_final_audit.md`
- **Acceptance Criteria:**
  - [x] A bounded Dev helper accepts one small local evidence/input bundle for recommendation preparation.
  - [x] The helper produces one renderer-ready structured package with stable field names and deterministic mapping.
  - [x] The prepared package preserves favorite-first ranking, alternatives, reason, next action, and approval-boundary inputs needed by the renderer.
  - [x] The slice stays local-only and does not add live MCP fetches, executor/runtime changes, production routing, or repo-write delegation.
- **Importance:** HIGH
- **Implementation Risk:** LOW
- **Effort:** S
- **Readiness:** READY
- **Recommendation:** DONE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** This was the next smallest useful follow-up after `DEV-005.1`: a bounded local input-prep helper that reduced repetitive manual package assembly without widening execution or authority boundaries.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-04
- **Handoff:** `development/tasks/DEV-006.1_recommendation_input_prep_helper.md`
- **Recommended next skill:** none
- **Handoff created:** 2026-07-04
- **Completed Task:** `development/tasks/DEV-006.1_recommendation_input_prep_helper.md`
- **Preimplementation Check:** PASS - `development/tasks/DEV-006.1_preimplementation_check.md`
- **Execution Result:** `development/tasks/DEV-006.1_execution_result.md`
- **Audit Package:** `development/tasks/DEV-006.1_AUDIT_PACKAGE.md`
- **Final Audit:** PASS - `development/tasks/DEV-006.1_final_audit.md`
- **Validation Evidence:** `development/tasks/DEV-006.1_execution_result.md`; `development/tasks/DEV-006.1_AUDIT_PACKAGE.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_prepared_input_2026-07-04.json`
- **Missing Information:**
  - None
- **Notes:** This is Dev-/OR-infrastructure only. It does not authorize live-run automation, live MCP fetching, executor/runtime changes, production routing activation, automatic model selection, final validation authority, or repo-write delegation. A future follow-up may add a small comparison-artifact helper for packaging multiple recommendations side by side more conveniently.

### DEV-005 - Add a lightweight renderer stub for MCP recommendation artifacts

- **Type:** IMPROVEMENT
- **Status:** DONE
- **Created:** 2026-07-04
- **Updated:** 2026-07-04
- **Completed:** 2026-07-04
- **Source:** User Intake
- **Follow-up to:** DEV-004 - Add a repeatable recommendation template for MCP pre-run OR selection
- **Short Description:** Add one small local renderer/stub that can fill the locked MCP recommendation template from bounded evidence fields so Codex no longer has to assemble every recommendation artifact manually.
- **Expected Behavior:** After the optional MCP research step and internal evidence review, Codex can pass one small structured input package into a local renderer/stub and receive one stable, archivable markdown recommendation artifact in the locked operator-facing format.
- **Actual Behavior:** CLOSED - `DEV-005.1` adds the bounded local renderer/stub, example input package, and rendered markdown output while keeping the recommendation-only approval boundary intact.
- **Reproduction / Context:** `DEV-004.1` proved the human-readable template shape. This follow-up removes repetitive manual filling while still avoiding executor changes, auto-run behavior, and delegated write authority.
- **Area:** OpenRouter MCP / recommendation render workflow
- **Evidence:** `development/openrouter-skill-tests/openrouter_mcp_pre_run_research_helper_workflow_note_2026-07-03.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_template_2026-07-04.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_rendered_example_2026-07-04.md`; `development/tasks/DEV-005.1_final_audit.md`
- **Acceptance Criteria:**
  - [x] A bounded Dev helper stub accepts one small structured recommendation input package.
  - [x] The helper renders the locked recommendation template into stable markdown with deterministic section order.
  - [x] The rendered output preserves the favorite-first ranking, alternatives, reason, next action, and approval-boundary language.
  - [x] The slice stays local-only and does not add live MCP fetches, executor/runtime changes, production routing, or repo-write delegation.
- **Importance:** HIGH
- **Implementation Risk:** LOW
- **Effort:** S
- **Readiness:** READY
- **Recommendation:** DONE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** This was the smallest useful follow-up after `DEV-004.1`: a bounded local renderer/stub with clear input/output shape that added reuse without opening execution or authority boundaries.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-04
- **Handoff:** `development/tasks/DEV-005.1_recommendation_renderer_stub.md`
- **Recommended next skill:** none
- **Handoff created:** 2026-07-04
- **Completed Task:** `development/tasks/DEV-005.1_recommendation_renderer_stub.md`
- **Preimplementation Check:** PASS - `development/tasks/DEV-005.1_preimplementation_check.md`
- **Execution Result:** `development/tasks/DEV-005.1_execution_result.md`
- **Audit Package:** `development/tasks/DEV-005.1_AUDIT_PACKAGE.md`
- **Final Audit:** PASS - `development/tasks/DEV-005.1_final_audit.md`
- **Validation Evidence:** `development/tasks/DEV-005.1_execution_result.md`; `development/tasks/DEV-005.1_AUDIT_PACKAGE.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_rendered_example_2026-07-04.md`
- **Missing Information:**
  - None
- **Notes:** This is Dev-/OR-infrastructure only. It does not authorize live-run automation, live MCP fetching, executor/runtime changes, production routing activation, automatic model selection, final validation authority, or repo-write delegation. A future follow-up may add a small input-prep helper for assembling the structured package more conveniently.

### DEV-004 - Add a repeatable recommendation template for MCP pre-run OR selection

- **Type:** IMPROVEMENT
- **Status:** DONE
- **Created:** 2026-07-04
- **Updated:** 2026-07-04
- **Completed:** 2026-07-04
- **Source:** User Intake
- **Follow-up to:** DEV-003 - Add optional OpenRouter MCP research helper before live OR candidate tests
- **Short Description:** Define one repeatable, human-readable recommendation template for the completed MCP pre-run helper so Codex can present one clear favorite plus 1 to 2 alternatives before a real OR candidate test.
- **Expected Behavior:** After the optional MCP research step, Codex can present the result in one fixed operator-friendly template with a clear favorite, 1 to 2 alternatives, a short reason, and a concrete recommended next action.
- **Actual Behavior:** CLOSED - `DEV-004.1` defines the repeatable, human-readable MCP recommendation template and keeps the approval boundary intact before any real OR candidate test continues.
- **Reproduction / Context:** The first MCP helper slice is done and audit-clean, and this follow-up locks a consistent recommendation artifact that is easy to read now and suitable for later storage/comparison.
- **Area:** OpenRouter MCP / recommendation output workflow
- **Evidence:** `development/openrouter-skill-tests/openrouter_mcp_pre_run_research_helper_workflow_note_2026-07-03.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_template_2026-07-04.md`; `development/tasks/DEV-004.1_final_audit.md`
- **Acceptance Criteria:**
  - [x] A bounded Dev artifact defines one human-readable recommendation template for the MCP pre-run helper.
  - [x] The template shows one clear favorite first plus 1 to 2 alternatives.
  - [x] The template includes a short reason for the ranking and one concrete recommended next action.
  - [x] The template is intentionally archivable for later comparison and still preserves Codex/operator approval before any live run continues.
- **Importance:** HIGH
- **Implementation Risk:** LOW
- **Effort:** S
- **Readiness:** READY
- **Recommendation:** DONE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** The first bounded slice was a small recommendation-template definition task that produced one Dev artifact without adding helper runtime logic.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-04
- **Handoff:** `development/tasks/DEV-004.1_mcp_recommendation_template.md`
- **Recommended next skill:** none
- **Handoff created:** 2026-07-04
- **Completed Task:** `development/tasks/DEV-004.1_mcp_recommendation_template.md`
- **Preimplementation Check:** PASS - `development/tasks/DEV-004.1_preimplementation_check.md`
- **Execution Result:** `development/tasks/DEV-004.1_execution_result.md`
- **Audit Package:** `development/tasks/DEV-004.1_AUDIT_PACKAGE.md`
- **Final Audit:** PASS - `development/tasks/DEV-004.1_final_audit.md`
- **Validation Evidence:** `development/tasks/DEV-004.1_execution_result.md`; `development/tasks/DEV-004.1_AUDIT_PACKAGE.md`; `development/openrouter-skill-tests/openrouter_mcp_recommendation_template_2026-07-04.md`
- **Missing Information:**
  - None
- **Notes:** This is Dev-/OR-infrastructure only. It does not authorize live-run automation, executor/runtime changes, MCP transport implementation, production routing activation, automatic model selection, final validation authority, or repo-write delegation. A future follow-up may add a lightweight render stub or template-to-artifact helper.

### DEV-003 - Add optional OpenRouter MCP research helper before live OR candidate tests

- **Type:** IMPROVEMENT
- **Status:** DONE
- **Short Description:** Add a bounded optional research step before live OR candidate tests that uses OpenRouter MCP live data plus our own OR evidence to recommend 2 to 3 price-performance candidates and suggested task types.
- **Area:** OpenRouter MCP / model-selection workflow
- **Created:** 2026-07-03
- **Updated:** 2026-07-03
- **Completed:** 2026-07-03
- **Source:** User Intake
- **Expected Behavior:** Before a live OR candidate test, Codex can optionally request a short MCP-backed recommendation that compares 2 to 3 suitable models, highlights the best price-performance option, and suggests fitting task types such as executor, test-run, or debug support.
- **Actual Behavior:** CLOSED - `DEV-003.1` defines the optional pre-run workflow placement, recommendation format, evidence inputs, and approval boundaries.
- **Reproduction / Context:** The user wants a cheaper delegated-fleissarbeit workflow where Codex stays in control, but can offload repetitive work to lower-cost agents more deliberately. The MCP helper must stay informational only, run before real OR tests, remain optional, and never auto-continue into a live run without operator confirmation.
- **Evidence:** `development/openrouter-skill-tests/openrouter_mcp_fit_decision_2026-06-27.md`; `development/openrouter-skill-tests/openrouter_mcp_pre_run_research_helper_workflow_note_2026-07-03.md`; `development/tasks/DEV-003.1_final_audit.md`
- **Acceptance Criteria:**
  - [x] A bounded Dev artifact defines the optional pre-run MCP research step and where it sits in the existing OR workflow.
  - [x] The recommendation format is locked to 2 to 3 candidates with short comparison, price-performance ordering, and suggested task types.
  - [x] The slice records that live MCP data and internal OR/skill evidence may both inform the shortlist.
  - [x] The slice preserves Codex/operator approval before any real OR candidate test continues.
- **Importance:** HIGH
- **Implementation Risk:** LOW
- **Effort:** S
- **Readiness:** READY
- **Recommendation:** DONE
- **Entry Point:** PRE_IMPLEMENTATION_VERIFICATION
- **Routing reason:** The first bounded slice was a small workflow-definition task that produced one Dev artifact without touching executor architecture.
- **Routing confidence:** HIGH
- **Routing decided by:** BACKLOG SKILL 3
- **Routing decided at:** 2026-07-03
- **Handoff:** `development/tasks/DEV-003.1_openrouter_mcp_research_helper_workflow_note.md`
- **Recommended next skill:** none
- **Handoff created:** 2026-07-03
- **Completed Task:** `development/tasks/DEV-003.1_openrouter_mcp_research_helper_workflow_note.md`
- **Execution Result:** `development/tasks/DEV-003.1_execution_result.md`
- **Final Audit:** PASS - `development/tasks/DEV-003.1_final_audit.md`
- **Validation Evidence:** `development/tasks/DEV-003.1_execution_result.md`; `development/tasks/DEV-003.1_AUDIT_PACKAGE.md`
- **Missing Information:**
  - None
- **Notes:** This is Dev-/OR-infrastructure only. It does not authorize executor replacement, direct repo-write delegation, final validation authority, production routing activation, or auto-run without approval. A future follow-up may define a compact recommendation template or lightweight helper stub.
