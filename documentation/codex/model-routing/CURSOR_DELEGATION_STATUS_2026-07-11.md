# Cursor Delegation Status — 2026-07-11

**Scope:** Dev-environment delegation for `janus-executioner`, `janus-debug`, and `janus-test-pipeline` only.  
**Status:** H-001 / H-002 / H-003 implemented in runner; delegate uses absolute runner path.

---

## What works today (proven lanes)

| Skill | Lane | Cursor backend | Best for |
|-------|------|----------------|----------|
| `janus-executioner` | `execution_patch_candidate` | Composer (`3`) | ≤2 allowlisted files, bounded patch + focused pytest |
| `janus-debug` | `debug_repro_investigation` | Composer (`3`) | Repro, logs, smallest bounded fix |
| `janus-test-pipeline` | `test_fixture_worker` | Composer (`3`) | Fixture/helper authoring + focused pytest |

Golden paths:

- `EXECUTION_PATCH_CANDIDATE_GOLDEN_PATH_2026-07-07.md`
- `DEBUG_REPRO_INVESTIGATION_GOLDEN_PATH_2026-07-07.md`
- `TEST_FIXTURE_WORKER_GOLDEN_PATH_2026-07-06.md`

---

## What stays Codex-owned (by design)

- Precheck, final audit, documentation update, Git/release
- `execution_write_apply_candidate` (deterministic apply)
- Live Playwright / provider execution
- Multi-file roadmap slices (3+ files)
- Final PASS / Backlog routing

---

## Failure taxonomy (operator view)

| Symptom | Meaning | Action |
|---------|---------|--------|
| `CURSOR_AGENT_TIMEOUT` + `TRANSPORT_FAIL` | Wall-clock cap hit | Codex implements locally; do not retry 3× |
| `CURSOR_SEMANTIC_FAIL_NO_CHANGES` + `TRANSPORT_PASS` | Agent ran, changed nothing | Reject; do not accept as success |
| `CURSOR_ALLOWLIST_VIOLATION` | Edited outside allowlist | Reject |
| `CURSOR_WORKER_INPUT_BLOCKED` | Bad package/allowlist before live run | Fix package, one retry |
| Dry-run `BLOCKED` with `duration_ms: null` | No live run attempted | Add `--execute-live-cursor` + operator OK |

---

## Implemented hardening (2026-07-11)

### H-003 — Timeout tiers (automatic)

Unless `JANUS_CURSOR_LIVE_TIMEOUT_SECONDS` is set:

| Lane shape | Default timeout |
|------------|-----------------|
| Assist / review (`allow_write=false`) | 180s |
| Tool lane, 1 allowlisted file | 240s |
| Tool lane, 2+ allowlisted files | 300s |

`dispatcher_result.json` now includes `timeout_tier`.

### H-001 / H-002 — Transport vs semantic truth

Live results now include:

- `transport_result`: `TRANSPORT_PASS` | `TRANSPORT_FAIL`
- `semantic_result`: `SEMANTIC_PASS` | `SEMANTIC_FAIL`
- `validation_result`: overall (`FAIL` when semantic fail on write-capable lanes)

Write-capable lanes (`proposal_first` + `allow_write=true`) fail semantically when **zero allowlisted files changed**, unless the input package sets `explicit_no_op_ok`, `allow_zero_file_pass`, or `cursor_explicit_no_op`.

### Delegate wrapper

- `janus_delegate.py` now invokes the runner via **absolute path**
- `--cursor-pool` is passed only for valid `auto_composer` / `api` values

---

## Everyday operator recipe

```powershell
# Optional override; otherwise runner picks 240/300 automatically for tool lanes
$env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "300"

python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane execution_patch_candidate `
  --workflow-id WF-MY-SLICE-001 `
  --operator-choice 3 `
  --input-package-json <package.json> `
  --allowlist-file <allowlist.txt> `
  --estimated-codex-saved-tokens 12000 `
  --estimated-delegation-overhead-tokens 8000 `
  --execute-live-cursor
```

Rules:

1. One Composer attempt per task on the critical path
2. On timeout → Codex implements locally
3. On `SEMANTIC_FAIL` → reject worker output
4. Review artifacts under `cursor-worker-runs/<workflow-id>/` before accepting any edits

---

## Remaining backlog (not blocking product)

| ID | Item | Priority |
|----|------|----------|
| H-004 | Top-level `task_prompt` mirror for API models | Medium |
| H-005 | Mark execution API pool `recommended: false` in manifest | Low |
| H-006 | Harmonize legacy tri-modal wording in remaining skills | Low |

---

## Next validation step

Run one live golden-path smoke per skill after this hardening:

- `TASK-EX-001` (execution)
- `TASK-DBG-002` (debug)
- `TASK-TP-003` (test fixture)

Expect: fewer false timeouts, explicit semantic failure when Composer returns 0 edits.
