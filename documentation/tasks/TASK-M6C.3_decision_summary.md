# LATEST DECISION SUMMARY - TASK-M6C.3

Feature Name: M6C.3 Provider-Branch Reachability Inventory

Primary Goal: Establish evidence for which provider-specific branches are genuinely unused before any Phase-C cleanup deletion is proposed.

User Problem: The parent T-C3 wording is too broad to distinguish obsolete branches from active streaming, normalization, fallback, and internal-generation contracts.

User Value: Cleanup can proceed safely in later narrow tasks without silently breaking provider behavior.

Primary Target Surface: Existing internal provider-routing and orchestration seams.

Existing or New Surface: Existing, verified by repository scan.

Existence Confirmation: confirmed by repository review.

User Trigger: Phase-C T-C3 continuation after C1/C2 completion.

Success Behavior: A read-only inventory identifies each candidate branch, its direct call sites or absence thereof, its runtime contract, and whether it is eligible for a separate deletion task. No runtime behavior changes.

Failure Behavior: If dynamic or indirect reachability cannot be disproven, the candidate remains retained and is marked `NEEDS_RUNTIME_EVIDENCE`; no deletion task is released.

User Action Surface: None; internal technical-debt evidence only.

Data / Persistence: No product data or persistence changes. One bounded documentation artifact records the inventory.

Security / Privacy: No new external calls, credential use, logging, or data exposure.

Edge Cases: Streaming branches remain active when called from the tool-loop; helper definitions with no static caller are not automatically deleted because dynamic dispatch or test/runtime evidence may still exist.

Out of Scope: Removing provider branches; changing streaming, history normalization, provider fallback, internal generation, transport enablement, tool execution, persistence, UI, OpenRouter, or T-C4 parity tests.

Routing Decision: FULL FEATURE PIPELINE

Routing Reason: The user selected an evidence-first technical-debt slice that must lock the proof standard and explicit non-goals before it can produce deletion subtasks.

Recommended Next Skill: janus-spec-generator

## Initial Read-Only Evidence

- `_async_iter_llm_stream` is actively called from `execution_engine.py` tool-loop streaming code and directly selects provider-native streaming services; it is retained.
- `simple_llm_generate_content` is actively called by `agent_planner.py`, `finance_tools.py`, and `project_service.py`; it is retained.
- `_reason_and_respond_with_provider_fixes` has no static caller in the repository scan, but it remains `NEEDS_RUNTIME_EVIDENCE` until the inventory Spec defines the proof standard.
