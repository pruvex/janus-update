# BACKLOG-119 Live Retest Preflight

Mode: `janus-test-pipeline / LIVE_TEST_EXECUTION preflight`

Canonical State: `FAIL`

## Bound Artifacts

- Backlog item: `documentation/backlog/BACKLOG.md` (`BACKLOG-119`)
- Execution result: `documentation/tasks/backlog_BACKLOG-119_execution_result.md`
- Debug handoff: `documentation/test-runs/BACKLOG-119_debug_relationship_persistence_2026-07-02.md`
- Focused contact tests: `backend/tests/test_contact_manager.py`
- Focused memory tool tests: `backend/tests/test_memory_tools.py`

## Decision

Automated local preflight was green and the user then approved the bounded live run with the exact phrase `OK START LIVE TEST`.

The live retest still fails overall. The good news is that the contact-card persistence half is now fixed: Nathan's contact card in the live AppData DB contains `Freundin heisst Elena`. The remaining failure is the fresh GPT recall path, which still does not answer from that stored relationship knowledge.

## Executed Preflight Checks

- `GET http://localhost:8001/api/health`: PASS
- `python -m pytest backend\tests\test_contact_manager.py -q -k "relationship_name_fact_updates_existing_contact_by_unique_first_name or relationship_named_owner_fact_updates_existing_contact_by_unique_first_name or skips_contact_recall_turn_to_avoid_self_poisoning or skips_relationship_recall_turn_to_avoid_self_poisoning"`: PASS, 4 passed
- `python -m pytest backend\tests\test_memory_tools.py -q -k "relationship_name_fact_applies_to_existing_contact_card or relationship_named_owner_fact_applies_to_existing_contact_card"`: PASS, 2 passed

## Live Test Prompt Bundle

Run in the live Janus app:

1. In a fresh GPT chat: `mein bester freund, der nathan raimann wohnt in berlin`
2. In another fresh Gemini chat: `nathans freundin heisst elena`
3. In a fresh GPT chat: `wer ist nathans freundin?`
4. Open Nathans contact card in the address book

Expected result:

- Nathan's contact card contains `Freundin heisst Elena`
- The fresh GPT chat can answer that Nathan's Freundin is Elena
- The relationship fact is no longer trapped in same-chat only behavior
- The recall question does not create new junk relationship memories

## OR Gate Decision

The Strong OR Test Worker lane was not used for this preflight. This slice does not need bounded test authoring or repeated worker runs; it needs one Codex-owned live provider/chat verification against the local Janus app boundary.

## Live Execution Result

User approval received: `OK START LIVE TEST`

Executed live backend API retest:

- GPT write prompt: `mein bester freund, der nathan raimann wohnt in berlin`
- Gemini write prompt: `nathans freundin heisst elena`
- Fresh GPT recall prompt: `wer ist nathans freundin?`
- Evidence JSON: `documentation/test-results/BACKLOG-119-live-retest-2026-07-02/BACKLOG-119_live_retest_api_evidence.json`
- Evidence summary: `documentation/test-results/BACKLOG-119-live-retest-2026-07-02/BACKLOG-119_live_retest_api_summary.md`

Result: `FAIL`

Assertions:

- GPT write accepted: PASS
- Gemini write accepted: PASS
- Nathan contact card contains `Freundin heisst Elena`: PASS
- Fresh GPT recall answers Elena: FAIL
- No new recall-turn junk memory created: PASS

Observed failure:

- The live contact card is now correct in `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`.
- The fresh GPT recall still answered that no reliable information exists.
- Backend log evidence shows chat `4166` was classified as ambiguous and forced into `system.wikipedia_summary`, which failed with `No module named 'wikipedia'`, instead of answering from contact/memory knowledge.

## Next Step

Route back to `janus-debug` for one narrower live slice: fix recall routing for relationship questions like `wer ist nathans freundin?` now that contact persistence itself is proven green in product evidence.
