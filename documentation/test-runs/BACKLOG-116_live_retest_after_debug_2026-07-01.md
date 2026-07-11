# BACKLOG-116 Live Retest After Debug

Mode: `janus-test-pipeline / LIVE_TEST_EXECUTION`

Canonical State: `PASS`

## Bound Artifacts

- Backlog item: `documentation/backlog/BACKLOG.md` (`BACKLOG-116`)
- Prior failing live retest: `documentation/test-runs/BACKLOG-116_live_retest_preflight_2026-07-01.md`
- Debug handoff: `documentation/test-runs/BACKLOG-116_debug_live_pet_detail_recovery_2026-07-01.md`
- Live evidence JSON: `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_evidence.json`
- Live evidence summary: `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_summary.md`

## Decision

The bounded live Janus API retest is now green after the debug recovery fix. The exact prompt that previously failed now returns Garfield's tuna dislike as a Garfield fact, without turning it into Oli's own generic preference.

## Evidence

- User approval received: `OK START LIVE TEST`
- `GET http://localhost:8001/api/health`: PASS
- `POST /api/chats` with internal local dev header: PASS, created chat `4158`
- `POST /api/chat` with prompt `was weisst du alles ueber olis haustiere?`: PASS
- Assertions:
  - Tasso appears: PASS
  - Garfield appears: PASS
  - Garfield's tuna dislike appears with Garfield: PASS
  - No Oli tuna-dislike misattribution in answer text: PASS

Observed live answer:

```text
Hallo Rolf Adam - zu Olis Haustieren weiss ich Folgendes:

- Hund Tasso: ein Podenco und frisst gerne Thunfisch.
- Katze Garfield: mag Thunfisch ueberhaupt nicht.
```

## Next Skill

`janus-final-audit`

## Model Recommendation

- Model: `5.5`
- Intelligence: `high`

## Keep Context

- `documentation/test-runs/BACKLOG-116_live_retest_preflight_2026-07-01.md`
- `documentation/test-runs/BACKLOG-116_debug_live_pet_detail_recovery_2026-07-01.md`
- `documentation/test-runs/BACKLOG-116_live_retest_after_debug_2026-07-01.md`
- `documentation/test-results/BACKLOG-116-live-retest-after-debug-2026-07-01/BACKLOG-116_live_retest_after_debug_api_evidence.json`

## Drop Context

- unrelated older pet-memory/debug runs outside `BACKLOG-116`
