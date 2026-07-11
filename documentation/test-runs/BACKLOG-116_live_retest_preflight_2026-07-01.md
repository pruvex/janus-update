# BACKLOG-116 Live Retest Preflight

Mode: `janus-test-pipeline / LIVE_TEST_EXECUTION preflight`

Canonical State: `FAIL`

## Bound Artifacts

- Backlog item: `documentation/backlog/BACKLOG.md` (`BACKLOG-116`)
- Execution result: `documentation/tasks/backlog_BACKLOG-116_execution_result.md`
- Integration regression: `backend/tests/integration/test_pet_recall_chat_path.py`
- Focused contact tests: `backend/tests/test_contact_manager.py`
- Focused contact-card normalization tests: `backend/tests/test_contact_card_normalization.py`

## Decision

Automated local preflight is green. The remaining evidence gap is the live Janus app prompt that originally exposed the bug.

Per `janus-test-pipeline`, live external/provider execution must not start from a vague `ok` or `weiter`. It requires the explicit user approval string:

`OK START LIVE TEST`

## Executed Preflight Checks

- `python -m pytest backend\tests\integration\test_pet_recall_chat_path.py -q`: PASS, 1 passed
- `python -m pytest backend\tests\test_contact_manager.py -q -k "pet_dislike_memory_for_named_pet or pet_preference_memory_for_named_pet"`: PASS, 2 passed, 45 deselected
- `python -m pytest backend\tests\test_contact_card_normalization.py -q -k "pet"`: PASS, 4 passed, 4 deselected

## Live Test Prompt

Ask in the live Janus app:

`was weisst du alles ueber olis haustiere?`

Expected result:

- Tasso appears with known dog details.
- Garfield appears as cat.
- Garfield's dislike fact appears with Garfield: Garfield mag Thunfisch ueberhaupt nicht.
- The Garfield tuna dislike is not presented as Oli's own generic preference/dislike.
- Tasso and Garfield facts are not mixed.

## OR Gate Decision

Strong OR Test Worker was not used for this preflight because no test-authoring or repeated-run worker package was needed. Existing focused tests already covered the local regression surface, and the remaining gap is live app/provider behavior that Codex must own and the user must explicitly approve.

## Live Execution Result

User approval received: `OK START LIVE TEST`

Executed live backend API retest:

- Prompt: `was weißt du alles über olis haustiere?`
- Provider / model: `openai` / `gpt-5.4-nano`
- Chat ID: `4157`
- Evidence JSON: `documentation/test-results/BACKLOG-116-live-retest-2026-07-01/BACKLOG-116_live_retest_api_evidence.json`
- Evidence summary: `documentation/test-results/BACKLOG-116-live-retest-2026-07-01/BACKLOG-116_live_retest_api_summary.md`

Result: `FAIL`

Assertions:

- Tasso appears: PASS
- Garfield appears: PASS
- Garfield's tuna dislike appears with Garfield: FAIL
- Tuna dislike is not presented as Oli's own current answer text: PASS

Observed answer included Tasso as Podenco, Tasso's tuna preference, and Garfield as cat, but omitted Garfield's "mag Thunfisch überhaupt nicht" fact.

Observed contact evidence still places `thunfisch überhaupt nicht` under Oli's generic `preferences` and not under the pet-specific `personal_details` cluster. This keeps the original live failure alive even though the focused local regression tests pass.

## Next Step

Route to `janus-debug` for live-data normalization / migration investigation. The likely remaining gap is not the pet overview fallback alone; it is that the existing live contact card still contains Garfield's tuna dislike as a generic Oli preference instead of a typed Garfield pet detail.
