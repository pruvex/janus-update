SKILL 5 DEBUG RESULT: FIXED

Iteration: 1

Progress-Validierung: Failure Code `TASK_MEM_M4_1_QUERY_ECHO_RELEVANCE_DRIFT`; Evidence geaendert ggü. N-1: JA; Stagnationszaehler: 0; Stopp-Regel ausgeloest: NEIN

## Root Cause

- The direct Janus runtime probe on `http://127.0.0.1:8001` proved that the live episodic-recall route is wired and tries to call `session_search`, but the product-default flag still blocks the feature with `MEMORY_SESSION_SEARCH_ENABLED=false`.
- After switching to direct local evidence collection, two real code defects were reproduced and fixed inside the bounded M4 surface:
  - natural-language queries such as `Wie hiess die Firma?` could break the FTS layer with `sqlite3.OperationalError: fts5: syntax error near "?"`
  - plain password-like rows such as `mein passwort ist geheim123` were not filtered fail-closed by the Session-Search sanitizer
- The remaining live gap after those first fixes was bounded to Session-Search relevance/ranking for natural recall questions in a realistic multi-chat dataset: repeated question rows like `Wie hiess die Firma?` could appear ahead of the earlier fact row containing `Acme GmbH`.

## Fix Summary

- verified the real local Janus auth path using the same internal runtime credential pattern as the Electron-backed app
- reproduced the live product-default flag block on `/api/chat`
- hardened `backend/services/memory/session_fts_store.py` so natural-language queries are normalized into safe FTS candidates instead of crashing on punctuation
- hardened `backend/services/memory/session_search_service.py` so plain password/secret hints are filtered fail-closed for Session-Search output
- expanded Session-Search retrieval to fetch a broader bounded candidate window and skip exact question-echo rows for natural recall queries
- updated the FTS store to collect fallback candidate hits across multiple query candidates instead of stopping after the first echo-only match set
- added focused regressions for both fixes in:
  - `backend/tests/test_session_fts_store.py`
  - `backend/tests/test_session_search_tools.py`
- stopped the temporary local port-`8011` validation processes after the bounded runtime probe

Auto-Verification:
- Status: PASS
- Evidence:
  - `python -m pytest backend/tests/test_session_fts_store.py -q`: PASS (`4 passed`)
  - `python -m pytest backend/tests/test_session_search_tools.py -q`: PASS (`5 passed`)
  - `python -m py_compile backend/services/memory/session_fts_store.py backend/services/memory/session_search_service.py backend/tools/session_search_tools.py`: PASS
  - direct service probe with `MEMORY_SESSION_SEARCH_ENABLED=true` now returns `secret_count 0`
  - direct service probe with `MEMORY_SESSION_SEARCH_ENABLED=true` now returns `acme_row` fact matches headed by `Die Firma heisst Acme GmbH ...` instead of question-echo rows

Artifact Identity Check: PASS

Final Feature Suite: N/A WITH REASON - this debug block fixed the bounded technical blockers, but it did not by itself run a final Janus product chat gate with the feature enabled in the main live runtime.

Changed Files:
- `backend/services/memory/session_fts_store.py`
- `backend/services/memory/session_search_service.py`
- `backend/tests/test_session_fts_store.py`
- `backend/tests/test_session_search_tools.py`
- `documentation/tasks/TASK-MEM-M4.1_debug_result_2026-07-10.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`

NEXT_STEP
Target Skill: janus-test-pipeline
Canonical State: HANDOFF
Required Artifacts:
- `documentation/tasks/TASK-MEM-M4_session_search_fts5.md`
- `documentation/tasks/TASK-MEM-M4.1_execution_result.md`
- `documentation/tasks/TASK-MEM-M4.1_debug_result_2026-07-10.md`
- `documentation/test-results/TASK-MEM-M4.1_cursor_live_validation_2026-07-10.md`
- `documentation/codex/model-routing/test-fixture-review-fixtures/TASK-MEM-M4.1_cursor_live_validation_result_2026-07-10.json`
Evidence Paths:
- `backend/services/memory/session_fts_store.py`
- `backend/services/memory/session_search_service.py`
- `backend/tests/test_session_fts_store.py`
- `backend/tests/test_session_search_tools.py`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\janus.db`
- `C:\Users\pruve\AppData\Roaming\Janus Projekt\session_fts.db`
Failure Code:
- N/A
Changed Files:
- `backend/services/memory/session_fts_store.py`
- `backend/services/memory/session_search_service.py`
- `backend/tests/test_session_fts_store.py`
- `backend/tests/test_session_search_tools.py`
- `documentation/tasks/TASK-MEM-M4.1_debug_result_2026-07-10.md`
- `documentation/ai/CURRENT_STATE.md`
- `documentation/codex/SKILL_USAGE_LOG.md`
Decision:
- The bounded M4 blocker-debug slice is fixed locally. The next clean gate is to rerun the M4 evidence check in a live Janus runtime where Session-Search is enabled, then decide audit readiness from that runtime evidence.
Reason:
- The worker path, local auth path, punctuation handling, secret suppression, and question-echo relevance blocker are now all evidenced and repaired in the bounded M4 slice.
- The remaining uncertainty is no longer debug-class product logic; it is the final live-validation gate with the feature enabled in the actual runtime context.
Recommended Model: 5.6 Terra
Recommended Intelligence: medium
Next User Action:
- Say `ok` to run the next M4 live-validation gate or prepare the matching Janus test-pipeline artifact from this repaired state.
