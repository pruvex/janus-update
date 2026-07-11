# Codex Handoff — Cursor Delegation Hardening + Golden-Path Smokes

**Date:** 2026-07-11  
**From:** Cursor (this session)  
**To:** Codex  
**Branch context:** `develop` @ `666391b44` (mixed worktree — commit **only** the bounded slice below)  
**Commit:** **NOT DONE** — operator explicitly deferred commit to Codex

---

## Executive summary

Cursor implemented Track B hardening for everyday delegation on three skills:

- `janus-executioner` → lane `execution_patch_candidate`
- `janus-debug` → lane `debug_repro_investigation`
- `janus-test-pipeline` → lane `test_fixture_worker`

Then ran live golden-path smokes on the hardened runner. **All three PASS** (DBG-002 needed one shadow re-seed + rerun).

Operator also completed **M6 Phase A manual smokes** separately in worktree `C:\KI\Janus-M6-Transport-Prep` — that is **out of scope** for this handoff unless explicitly merged later.

---

## What changed (implementation)

### H-001 + H-002 — Semantic vs transport truth

**File:** `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`

Live results now include:

- `transport_result`: `TRANSPORT_PASS` | `TRANSPORT_FAIL`
- `semantic_result`: `SEMANTIC_PASS` | `SEMANTIC_FAIL`

Write-capable lanes (`proposal_first` + `allow_write=true`) fail semantically when **zero allowlisted files changed**, unless input package sets one of:

- `explicit_no_op_ok`
- `allow_zero_file_pass`
- `cursor_explicit_no_op`

Overall `validation_result` is `FAIL` with `final_outcome: CURSOR_SEMANTIC_FAIL_NO_CHANGES` on semantic fail.

### H-003 — Automatic timeout tiers

Unless `JANUS_CURSOR_LIVE_TIMEOUT_SECONDS` is set:

| Lane shape | Timeout |
|------------|---------|
| Assist / review | 180s |
| Tool lane, 1 allowlisted file | 240s |
| Tool lane, 2+ allowlisted files | 300s |

`dispatcher_result.json` includes `timeout_tier`.

### Delegate wrapper

**File:** `documentation/codex/model-routing/scripts/janus_delegate.py`

- Invokes runner via **absolute path** to `janus_cursor_worker_runner.py`
- Passes `--cursor-pool` only for valid `auto_composer` / `api`

### Tests

- `documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py` — tier + semantic tests
- `documentation/codex/model-routing/tests/test_janus_delegate.py` — absolute path assertion

**Validation run:** `python -m pytest documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py documentation/codex/model-routing/tests/test_janus_delegate.py -q` → **37 passed**

---

## Live smoke evidence (hardened runner)

**Doc:** `documentation/test-runs/CURSOR_GOLDEN_PATH_HARDENING_SMOKE_2026-07-11.md`  
**Operator doc:** `documentation/codex/model-routing/CURSOR_DELEGATION_STATUS_2026-07-11.md`

| Task | Skill | Workflow ID | Result | Duration | Changed files |
|------|-------|-------------|--------|----------|---------------|
| EX-001 | executioner | `WF-GOLDEN-EX-001-HARDENING-2026-07-11` | PASS | ~51s | 1 (`gate_prompt_shadow.py`) |
| DBG-002 (1st) | debug | `WF-GOLDEN-DBG-002-HARDENING-2026-07-11` | SEMANTIC_FAIL | ~61s | 0 (fixture already green — gate worked) |
| DBG-002 (rerun) | debug | `WF-GOLDEN-DBG-002-HARDENING-RERUN-2026-07-11` | PASS | ~32s | 1 (`executed_runner_shadow.json`) |
| TP-003 | test-pipeline | `WF-GOLDEN-TP-003-HARDENING-2026-07-11` | PASS | ~53s | 2 (fixture + test) |

Run artifacts: `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-*`

Post-smoke pytest:

- EX-001 shadow test PASS
- DBG-002 rerun shadow test PASS
- TP-003 shadow-eval tests PASS (24)

---

## Files to include in a bounded Codex commit

**Code + tests (hardening slice):**

- `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`
- `documentation/codex/model-routing/scripts/janus_delegate.py`
- `documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py`
- `documentation/codex/model-routing/tests/test_janus_delegate.py`

**Documentation / evidence:**

- `documentation/codex/model-routing/CURSOR_DELEGATION_STATUS_2026-07-11.md`
- `documentation/codex/model-routing/HANDOFF_CURSOR_HARDENING_TO_CODEX_2026-07-11.md` (this file)
- `documentation/test-runs/CURSOR_GOLDEN_PATH_HARDENING_SMOKE_2026-07-11.md`
- `documentation/ai/CURRENT_STATE.md` (top snapshots only — do not bulk-merge unrelated history)

**Smoke side effects (review before staging):**

- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/execution_patch_candidate/sandbox/gate_prompt_shadow.py`
- `documentation/codex/model-routing/fixtures/cursor-shadow-catalog/debug_repro_investigation/sandbox/executed_runner_shadow.json`
- `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/fixtures/contact_memory_fixture.json`
- `development/openrouter-skill-tests/janus-worker-gateway-shadow-eval/test_fixture_arbeit/tests/test_contact_memory_fixture.py`

**Run artifacts (optional in commit — operator preference):**

- `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-EX-001-HARDENING-2026-07-11/`
- `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-DBG-002-HARDENING-2026-07-11/`
- `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-DBG-002-HARDENING-RERUN-2026-07-11/`
- `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-TP-003-HARDENING-2026-07-11/`

---

## Do NOT include in this commit

- Unrelated mixed `develop` worktree changes (~1000+ dirty entries)
- M6 Transport Phase A code (lives in worktree `Janus-M6-Transport-Prep`, branch `codex/m6-transport-prep`)
- Blind `git add .`

---

## Recommended next steps for Codex

1. Read `CURRENT_STATE.md` top snapshot + this handoff + smoke doc.
2. `janus-git-governance`: stage **only** the bounded file set above.
3. Re-run: `python -m pytest documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py documentation/codex/model-routing/tests/test_janus_delegate.py -q`
4. Commit with message like: `feat(dev): harden Cursor delegation runner for execution/debug/test lanes`
5. Optional: update `HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md` backlog H-001/H-002/H-003 as DONE.
6. Do **not** merge M6 worktree unless operator explicitly requests.

---

## Everyday operator rule (post-hardening)

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane execution_patch_candidate|debug_repro_investigation|test_fixture_worker `
  --workflow-id <WF-ID> `
  --operator-choice 3 `
  --input-package-json <package.json> `
  --allowlist-file <allowlist.txt> `
  --estimated-codex-saved-tokens <n> `
  --estimated-delegation-overhead-tokens <n> `
  --execute-live-cursor
```

- One Composer attempt per task on critical path
- `SEMANTIC_FAIL` or timeout → Codex implements locally, no retry loop
- Codex remains review/audit/git authority

---

## Copy-paste prompt for Codex

```text
Binding context: Cursor delegation hardening handoff (2026-07-11)

Read first:
- documentation/codex/model-routing/HANDOFF_CURSOR_HARDENING_TO_CODEX_2026-07-11.md
- documentation/test-runs/CURSOR_GOLDEN_PATH_HARDENING_SMOKE_2026-07-11.md
- documentation/codex/model-routing/CURSOR_DELEGATION_STATUS_2026-07-11.md
- documentation/ai/CURRENT_STATE.md (top snapshot only)

Task:
1. Review uncommitted hardening slice (H-001/H-002/H-003 + delegate path fix)
2. janus-git-governance: commit ONLY bounded files listed in handoff — NO git add .
3. Re-run delegation pytest (37 tests)
4. Report canonical state PASS or BLOCKED

Do NOT merge M6 transport worktree or unrelated develop dirty files.
Commit only after explicit operator ok if governance requires it.
```

---

**END OF HANDOFF**
