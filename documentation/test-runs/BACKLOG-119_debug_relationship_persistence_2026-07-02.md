SKILL 5 DEBUG RESULT: FIXED

Iteration: 1
Progress-Validierung: Failure Code `RELATIONSHIP_CONTACT_APPLY_PENDING_AND_RECALL_SELF_POISON`; Evidence geaendert ggue. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

Root Cause:
- The live Nathan/Elena failure was not a generic memory-loss problem. The productive relationship memory `Nathan hat eine Freundin namens Elena` was being staged as a pending contact proposal instead of updating the `Nathan Raimann` contact card directly.
- `backend/services/contact_manager.py` already normalized the variant `Freundin heisst Elena`, but not the productive live variant `hat eine Freundin namens Elena`, so the contact-backed cross-chat path stayed stale.
- `backend/services/memory_extractor.py` did not recognize relationship recall prompts like `wer ist nathans freundin?` as recall turns, so the assistant answer could be re-extracted into junk memories such as `freundin_von_nathan`.

Fix Summary:
- Extended relationship-detail normalization in `backend/services/contact_manager.py` so owner-style facts like `Nathan hat eine Freundin namens Elena` resolve to the same durable contact detail as `Nathans Freundin heisst Elena`.
- Hardened `backend/services/memory_extractor.py` so relationship recall questions using `wer ist ...` and `wie heisst ...` for family/partner relations are skipped as contact recall turns instead of becoming new memories.
- Added focused regressions for the direct contact-manager path, the `memory.write` tool path, and the relationship-recall self-poison guard.

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m py_compile backend/services/contact_manager.py backend/services/memory_extractor.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py`: PASS
  - `python -m pytest backend/tests/test_contact_manager.py -q -k "relationship_name_fact_updates_existing_contact_by_unique_first_name or relationship_named_owner_fact_updates_existing_contact_by_unique_first_name or skips_contact_recall_turn_to_avoid_self_poisoning or skips_relationship_recall_turn_to_avoid_self_poisoning"`: PASS (`4 passed, 46 deselected`)
  - `python -m pytest backend/tests/test_memory_tools.py -q -k "relationship_name_fact_applies_to_existing_contact_card or relationship_named_owner_fact_applies_to_existing_contact_card"`: PASS (`2 passed, 28 deselected`)
  - direct live evidence inspection before fix authoring: `documentation/logs/janus_frontend.log`, `documentation/logs/janus_backend.log`, and `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db` confirmed that `Nathan hat eine Freundin namens Elena` created a pending proposal while `wer ist nathans freundin?` produced a self-poisoned recall-turn memory

Artifact Identity Check: PASS
Final Feature Suite: PASS
Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-119_debug_relationship_persistence_2026-07-02.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/backlog_BACKLOG-119_execution_result.md`
- `documentation/test-runs/BACKLOG-119_debug_relationship_persistence_2026-07-02.md`
- `documentation/logs/janus_frontend.log`
- `documentation/logs/janus_backend.log`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Evidence Paths:
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
- `documentation/logs/janus_frontend.log`
- `documentation/logs/janus_backend.log`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
Failure Code:
- `RELATIONSHIP_CONTACT_APPLY_PENDING_AND_RECALL_SELF_POISON`
Changed Files:
- `backend/services/contact_manager.py`
- `backend/services/memory_extractor.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_memory_tools.py`
- `documentation/test-runs/BACKLOG-119_debug_relationship_persistence_2026-07-02.md`
Decision:
- rerun the bounded BACKLOG-119 validation in `janus-test-pipeline`; do not move to `janus-final-audit` until a fresh live Janus retest shows that Gemini stores Elena under Nathan's contact and GPT can answer the relationship in a new chat
Reason:
- the local root causes are fixed and regression-covered, but the original failure was observed in live provider/chat behavior and still needs a fresh cross-chat product retest
Recommended Model:
- `5.4`
Recommended Intelligence:
- `high`
Next User Action:
- Run one fresh Janus live retest that writes Nathan/Elena through Gemini and verifies retrieval from a new GPT chat plus contact-card persistence in the address book before any final audit claim.
