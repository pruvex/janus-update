# Cursor Handoff: Intent M1 Status after TASK-INTENT-M1.3

**Date:** 2026-07-08  
**Source Branch:** `develop`  
**Latest sealed checkpoint:** `e580ec1941f4034f51579a92957ad99174fbddf7`  
**Backed up to:** `backup/develop`  
**Prepared by:** Codex

## 1. Current Truth

- `TASK-INTENT-M1.1`: EXIT PASS
- `TASK-INTENT-M1.2`: EXIT PASS
- `TASK-INTENT-M1.3`: EXIT PASS WITH CAVEAT
- Parent milestone `M1 I1 Intent Classifier`: still `CAVEAT / FOLLOW-UP`

Why the caveat remains:

- Contact uplift: `+35.0 pp`
- Pet uplift: `+20.0 pp`
- Calendar: unchanged
- Flag-off parity: PASS
- Auxiliary classifier latency: `P95 4.09 ms`
- Recall uplift: `80.0% -> 80.0%` (`+0.0 pp`)

Interpretation:

- The benchmark proof slice is valid and closed.
- The deterministic benchmark seam bug is fixed.
- Unrestricted staged enablement for the full M1 I1 story must still not be claimed as complete, because Recall did not improve.

## 2. Files to Trust

Load only these files first:

- `documentation/ai/CURRENT_STATE.md`
- `documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md`
- `documentation/tasks/TASK-INTENT-M1.3_final_audit.md`
- `documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md`
- `documentation/test-runs/INTENT_BENCHMARK_BASELINE.md`
- `documentation/Cursor specs/ROADMAP_EPIC_ORDER.md`

Optional supporting files:

- `documentation/tasks/TASK-INTENT-M1.3_debug_result.md`
- `documentation/tasks/TASK-INTENT-M1.3_execution_result.md`
- `backend/scripts/run_intent_benchmark.py`
- `backend/tests/test_intent_benchmark.py`

## 3. What Is Already Proven

- The benchmark harness is now truly deterministic on the intended proof path.
- The previous latency blocker came from a config-based reconstruction seam that still hit the real provider path.
- The corrected proof is local, CI-runnable, and validated.
- M1.3 is closed as an evidence slice, not as blanket product readiness.

## 4. What Cursor Must Not Assume

- Do not say that Recall is solved.
- Do not say that M1 I1 is unrestricted staging-ready.
- Do not treat unrelated dirty-tree files as part of this Intent slice.
- Do not start Transport, OAuth, OpenRouter, or delegation hardening from this handoff.
- Do not reinterpret the roadmap to mean that M2 is automatically green.

## 5. Recommended Next Work

Preferred Track A order from this state:

1. Finish `Memory MA/MB`, because the roadmap explicitly allows it in parallel to M1 and it does not depend on pretending the Recall caveat is solved.
2. In parallel or immediately after, prepare one bounded follow-up decision for the Recall gap:
   - either a dedicated Recall hardening/debug slice
   - or an explicit operator decision that M2 may proceed with documented caveat
3. Do not start M2 confidence routing until the team is explicit about how the M1 Recall caveat is being handled.

Operating model note (binding): This state follows `documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md` where Track A (product work, Memory first) always wins over Track B (route hardening).

## 6. Cursor Use Recommendation

Recommended use of Cursor from this exact state:

- `Cursor API`: good for bounded review, summary, or draft handoff work on the sealed M1.3 package
- `Cursor Composer`: only for very small bounded execution patches (≤2 allowlisted files). Not for a new multi-file backend roadmap slice.
- `Codex local`: remains preferred for the next real product implementation slice

For the next roadmap move (`Memory MA/MB`): prefer `Codex local` for implementation. Cursor is allowed only for bounded review/draft of the Memory-slice artifacts (no transport/OAuth/OpenRouter/delegation hardening).

## 7. Compact Prompt For Cursor

```text
You are receiving a status-only Janus handoff.

Current milestone truth:
- TASK-INTENT-M1.1 PASS
- TASK-INTENT-M1.2 PASS
- TASK-INTENT-M1.3 PASS WITH CAVEAT
- M1 I1 parent remains CAVEAT/FOLLOW-UP because Recall stayed 80.0% -> 80.0% (+0.0 pp)

Trust these files first:
- documentation/ai/CURRENT_STATE.md
- documentation/tasks/TASK-INTENT-M1_auxiliary_action_subject_classifier.md
- documentation/tasks/TASK-INTENT-M1.3_final_audit.md
- documentation/test-runs/TASK-INTENT-M1.3_benchmark_uplift_2026-07-08.md
- documentation/test-runs/INTENT_BENCHMARK_BASELINE.md
- documentation/Cursor specs/ROADMAP_EPIC_ORDER.md

Task:
- summarize the safest next bounded roadmap move from this state
- keep Memory MA/MB and Recall-follow-up as the primary options
- do not claim Recall is solved
- do not widen into Transport/OAuth/OpenRouter/delegation hardening
- for Memory MA/MB: recommend Codex for implementation; allow Cursor only for bounded review/draft of Memory-slice artifacts
```
