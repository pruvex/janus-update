# Cursor Review Handoff: TASK-MEM-M1.1

**Date:** 2026-07-08  
**Source Branch:** `develop`  
**Current Base Commit:** `e580ec1941f4034f51579a92957ad99174fbddf7`  
**Intent Context:** M1.1, M1.2, M1.3 sealed; M1.3 remains `PASS WITH CAVEAT` because Recall stayed flat  
**Purpose:** bounded review/draft help only, no authoritative implementation

## 1. Why This Handoff Exists

The operator explicitly chose:

- use Cursor as helper on this slice
- keep authoritative product implementation in Codex

This means:

- Cursor may review the slice, identify likely risks, and draft concrete implementation advice
- Cursor must not be treated as the final execution owner for this roadmap step

## 2. Exact Task To Review

- `Target Task:` `TASK-MEM-M1.1`
- `Task File:` `documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md`
- `Precheck:` `documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md`
- `Spec:` `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`

## 3. Scope

Review only this bounded product slice:

- Memory Phase A: Hot-Layer-Caps
- Memory Phase B: On-Demand Memory Injection

Expected code cluster:

- `backend/services/memory/retrieval_service.py`
- `backend/services/memory_budget.py`
- `backend/services/memory_observability.py`
- `backend/services/chat_orchestrator.py`
- `backend/services/orchestrator/intent_engine.py` only if minimal existing signal reuse is needed
- `backend/tests/test_memory_hot_layer_cap.py`
- `backend/tests/test_memory_on_demand_injection.py`
- directly affected existing memory regression tests

## 4. Hard Boundaries

Do not widen into:

- Session-Search / Memory Phase C
- Frozen Core / Memory Phase D
- USER.md export / Memory Phase E
- Intent M2 confidence routing
- Recall-gap implementation for Intent M1
- Transport / OAuth / OpenRouter
- delegation hardening or route experiments
- Git actions or repo-state authority

## 5. Safety Rules That Must Stay True

- Health/Medical protected memory must not be dropped from the protected core path
- Health-injector must not be accidentally gated off by the new on-demand injection logic
- Flag defaults must remain `false`
- Flag-off behavior must remain equivalent to current behavior
- Weather/external-context queries should avoid unnecessary general memory injection
- Personal-scope queries such as recall or location hints must still enable memory when appropriate

## 6. What Cursor Should Produce

Preferred output:

- a short risk review of the planned file cluster
- likely edge cases or regressions to watch
- if useful, a bounded implementation plan or patch suggestion
- focused test emphasis suggestions

Not allowed as final output:

- claims that the slice is implemented
- final repo writes presented as authoritative truth
- any claim that Recall is solved
- any change of roadmap priority

## 7. Files To Trust First

- `documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md`
- `documentation/tasks/TASK-MEM-M1.1_task_breakdown.md`
- `documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md`
- `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`
- `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md`
- `documentation/ai/CURRENT_STATE.md`

## 8. Recommended Cursor Role

- `Cursor API`: preferred for bounded review/draft on this package
- `Cursor Composer`: only if it stays strictly in advisory/draft mode for this slice
- `Codex`: remains final implementation and acceptance owner

## 9. Compact Prompt For Cursor

```text
You are reviewing one bounded Janus roadmap slice.

Review target:
- TASK-MEM-M1.1
- Memory Phase A Hot-Layer-Caps
- Memory Phase B On-Demand Memory Injection

Trust first:
- documentation/tasks/TASK-MEM-M1.1_preimplementation_check.md
- documentation/tasks/TASK-MEM-M1.1_task_breakdown.md
- documentation/tasks/TASK-MEM-M1_memory_phase_ab_hot_layer_caps_and_on_demand_injection.md
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md
- documentation/ai/CURRENT_STATE.md

Task:
- review the bounded file cluster and identify the highest-risk implementation pitfalls
- highlight health/medical safety traps, flag-off parity traps, and weather-vs-personal gating edge cases
- if useful, draft a small implementation plan or patch outline

Hard boundaries:
- no Session-Search, Frozen Core, USER.md export, Intent M2, Recall-gap work, Transport, OAuth, OpenRouter, or delegation hardening
- do not claim implementation is complete
- Codex remains final implementation owner
```
