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
