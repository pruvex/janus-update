# BACKLOG-108 Execution Validation

- **Target Task:** BACKLOG-108
- **Date:** 2026-06-07
- **Scope:** Bounded backend fix for confirmed existing-contact knowledge from chat so safe exact-match facts reach the existing address-book contact instead of remaining memory-only.

## Checks

- `python -m pytest backend/tests/test_contact_manager.py -q` - PASS
- `python -m pytest backend/tests/test_memory_tools.py -q` - PASS
- `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q` - PASS
- `python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py backend/services/memory_extractor.py backend/tools/memory_tools.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py` - PASS
- `python -m pytest backend/tests/test_contact_manager.py -q -k "confirmed_chat_fact_for_exact_existing_contact_updates_contact_without_pending_proposal"` - PASS
- `python -m pytest backend/tests/test_memory_tools.py -q -k "confirmed_memory_write_can_stage_contact_update_suggestion"` - PASS

## Bounded End-to-End Evidence

- Exact existing-contact chat-fact seam is covered by `test_confirmed_chat_fact_for_exact_existing_contact_updates_contact_without_pending_proposal`:
  - stores the extracted chat fact `Christoph Gier liebt Star Wars` with `source_type="text"`
  - runs `contact_manager.stage_contact_update_from_memory(...)`
  - verifies the existing contact is updated immediately
  - verifies no pending contact proposal remains
  - verifies the contact outcome is `proposal_source_context == "direct_context"` and `proposal_last_outcome == "applied_from_confirmed_chat_fact"`
- Guardrail counter-proof is covered by `test_confirmed_memory_write_can_stage_contact_update_suggestion`:
  - Memory-tool writes still create a pending contact proposal instead of silently mutating the contact
  - this preserves the reviewed distinction between confirmed chat extraction and later memory-originated suggestions

## Manual Janus Evidence

N/A WITH REASON - The fix changes no UI, frontend, provider routing, or visible settings rendering. The user-visible regression is a backend chat-to-contact persistence seam, and the bounded reproducible evidence above directly exercises that seam with deterministic fixtures.

## Notes

- The direct-apply path is intentionally limited to `source_type="text"`, exact existing-contact matches, non-sensitive facts, and `preferences`/`dislikes` only.
- Sensitive facts, near matches, ambiguous matches, and Memory-tool writes remain on the existing review/proposal path.
