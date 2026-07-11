# Cursor Golden-Path Hardening Smoke — 2026-07-11

**Runner:** hardened `janus_cursor_worker_runner.py` (H-001/H-002/H-003) via `janus_delegate.py` choice `3` + `--execute-live-cursor`  
**Commit:** none (evidence only; Codex owns git)  
**Date:** 2026-07-11

---

## Summary

| Task | Skill | Lane | Result | Transport | Semantic | Duration | Timeout tier |
|------|-------|------|--------|-----------|----------|----------|--------------|
| EX-001 | janus-executioner | `execution_patch_candidate` | **PASS** | TRANSPORT_PASS | SEMANTIC_PASS | ~51s | 300s multi-file |
| DBG-002 | janus-debug | `debug_repro_investigation` | **FAIL (expected)** | TRANSPORT_PASS | SEMANTIC_FAIL | ~61s | 300s multi-file |
| TP-003 | janus-test-pipeline | `test_fixture_worker` | **PASS** | TRANSPORT_PASS | SEMANTIC_PASS | ~53s | 300s multi-file |

**Overall:** 3/3 golden paths PASS with real edits after DBG-002 rerun (see below).

---

## DBG-002 rerun — after shadow re-seed (2026-07-11)

First run returned `SEMANTIC_FAIL` because the shadow fixture was already green. Operator requested full PASS evidence.

**Re-seed:** set `executed_runner_shadow.json` runner_path to `shadow_debug_beta.spec.js` while plan stays on `shadow_debug_alpha.spec.js` (pytest red).

| Field | Value |
|-------|-------|
| Workflow | `WF-GOLDEN-DBG-002-HARDENING-RERUN-2026-07-11` |
| Result | **PASS** |
| Transport / Semantic | TRANSPORT_PASS / SEMANTIC_PASS |
| Duration | ~32s |
| Changed files | `executed_runner_shadow.json` (1 file) |
| Post-run pytest | PASS |
| Session | `000c58f0-2c78-4d4e-b1d2-2402392101d1` |
| Artifacts | `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-DBG-002-HARDENING-RERUN-2026-07-11/` |

**Updated overall:** EX-001 PASS, DBG-002 PASS (rerun), TP-003 PASS — all three skills validated end-to-end.

---

## EX-001 — execution_patch_candidate

- **Workflow:** `WF-GOLDEN-EX-001-HARDENING-2026-07-11`
- **Precondition:** shadow reset via `reset_execution_patch_candidate_shadow_fixture.py` (pytest red before run)
- **Changed files:** `gate_prompt_shadow.py` (1 file)
- **Post-run pytest:** PASS (`test_gate_prompt_shadow.py`)
- **Artifacts:** `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-EX-001-HARDENING-2026-07-11/`
- **Session:** `30b26155-cd88-4837-90e3-82043f2d9440`

---

## DBG-002 — debug_repro_investigation

- **Workflow:** `WF-GOLDEN-DBG-002-HARDENING-2026-07-11`
- **Precondition:** shadow pytest already PASS (fixture previously fixed)
- **Changed files:** none
- **Outcome:** `CURSOR_SEMANTIC_FAIL_NO_CHANGES` — **H-001 working as designed**
- **Artifacts:** `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-DBG-002-HARDENING-2026-07-11/`
- **Session:** `041c1699-f27b-4a3c-9359-0c5fb4bcc6cf`
- **Note:** For a full end-to-end PASS rerun, re-seed the shadow mismatch first; semantic gate prevents accepting a no-op Composer run.

---

## TP-003 — test_fixture_worker

- **Workflow:** `WF-GOLDEN-TP-003-HARDENING-2026-07-11`
- **Changed files:** `contact_memory_fixture.json`, `test_contact_memory_fixture.py`
- **Post-run pytest:** PASS (23 tests)
- **Artifacts:** `documentation/codex/model-routing/cursor-worker-runs/WF-GOLDEN-TP-003-HARDENING-2026-07-11/`
- **Session:** `a02d9d26-eb30-44e3-bb72-075038bba1f9`

---

## Hardening behaviors confirmed

1. **Automatic timeout tier** `300s` / `multi_file_tool_lane` for 2–3 file allowlists (no manual env var)
2. **`transport_result` / `semantic_result`** present in delegate output
3. **Semantic fail** when Composer completes but edits nothing on write-capable lane
4. **Absolute runner path** in `planned_command`
5. **No timeout** on any of the three runs (all finished well under 300s)

---

## Local file impact (uncommitted)

- EX-001 shadow: `gate_prompt_shadow.py` modified
- TP-003 shadow-eval: fixture + test modified
- DBG-002: unchanged
- New run dirs under `cursor-worker-runs/WF-GOLDEN-*`
- Hardening code changes from same session (runner/delegate/tests)

Codex should review diffs before any commit.
