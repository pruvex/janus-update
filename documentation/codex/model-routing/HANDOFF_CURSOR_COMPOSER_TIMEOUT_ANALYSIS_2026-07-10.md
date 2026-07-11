# Codex Handoff: Cursor Composer Timeout Analysis & Operating Rules

**Date:** 2026-07-10  
**Status:** BINDING OPERATOR + CODEX POSTURE  
**Scope:** Codex development-environment delegation only  
**Companion docs:**
- `HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md`
- `CURSOR_API_POOL_OPERATOR_PLAYBOOK_2026-07-07.md`

---

## 0. Executive summary

Operators report **frequent Composer timeouts** when delegating bounded work via `3 = Cursor Composer`. Investigation shows this is **not a broken integration**. The dominant causes are:

1. **Wall-clock timeout too low** (especially `120s`; default `180s` is also tight for tool-heavy runs)
2. **Composer runs full tool loops** (`--force --trust --approve-mcps`, shell, MCP) and often needs **90–220+ seconds**
3. **`--output-format json`** returns only at end → **no visible output while running** is normal
4. **Task variance** — same package can PASS once and TIMEOUT on retry

**Product rule unchanged:** Timeout = evidence, not a blocker. Implement in Codex locally after one failed Composer attempt on the critical path.

---

## 1. How the timeout works (runner truth)

**File:** `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`

| Setting | Value |
|---------|-------|
| Env var | `JANUS_CURSOR_LIVE_TIMEOUT_SECONDS` |
| Default | **180** seconds |
| On expiry | `invoke_agent_command` → `subprocess.TimeoutExpired` → Windows `taskkill /T /F` |
| Outcome | `final_outcome: CURSOR_AGENT_TIMEOUT` |
| Typical artifacts | partial `stdout.log`, `cursor_response.json: {timeout: true}`, **no session_id**, **0 changed files** |

The runner **intentionally** caps live Cursor runs. This is bounded-live safety, not a Cursor CLI bug.

---

## 2. Evidence from `cursor_delegation_log.jsonl`

### 2.1 Successful Composer runs (duration_ms)

| Workflow | Duration | Notes |
|----------|----------|-------|
| `WF-CURSOR-COMPOSER-LIVEDEV-EXECUTIONER-002` | **124s** | 1 file, PASS |
| `WF-BACKLOG-124-START-GATE-001` | 84s / **138s** | 1 file; second run 0 edits |
| `WF-CURSOR-M3.3-DBG-001` | 98s | PASS |
| `WF-CURSOR-M3.3-OFFER-CONTENT` | **215s** | 3 files — **would fail at 180s** |
| `WF-CURSOR-M3.4-SEMANTIC-ROUTINE-REUSE` | **194s** | 5 files — ran with **timeout=300** |
| `WF-SPEC29.2-DATE-GUARD` | 135s | PASS |
| `WF-SPEC29.2-PASSIVE-LEARN-CAPREG` | 118s | PASS (after 3 timeouts on same WF) |

**Conclusion:** Many **successful** Composer runs exceed **120s**; several exceed **180s**. A **120s cap guarantees frequent false timeouts**.

### 2.2 Documented timeout failures

| Workflow | Timeout setting | Result |
|----------|-----------------|--------|
| `WF-INTENT-M1.1-CURSOR-LIVE` | 180s | TIMEOUT, 5-file backend slice |
| `WF-CURSOR-M3.3-OFFER-LIVE-SHAPE` | 180s | TIMEOUT |
| `WF-SPEC31.1-EXEC-PATCH` | default | TIMEOUT |
| `WF-SPEC31.2-EXEC-PATCH` | default | TIMEOUT |
| `WF-SPEC29.2-PASSIVE-LEARN-CAPREG` | default | 3× TIMEOUT, then PASS at 118s |

### 2.3 API contrast (why API is not a substitute for Composer tool work)

| Backend | Typical duration | Tool work |
|---------|------------------|-----------|
| API Kimi | 9–47s | Usually no real edits on livedev slices |
| Composer | 84–215s | Real tool/shell/write loops |

---

## 3. Why Composer is slow (lane config)

For `execution_patch_candidate` and `debug_repro_investigation`, manifest enables:

```json
"mode": "proposal_first",
"allow_shell": true,
"allow_write": true,
"cli_flags": ["--force", "--trust", "--approve-mcps", "--output-format", "json"]
```

Composer is **supposed** to explore, run checks, and edit. That takes wall-clock time. API models answer faster but often **do not complete** bounded tool tasks.

---

## 4. “No output while running” is normal

- Runner uses `agent -p --output-format json`
- JSON is emitted **when the agent finishes** (or when killed)
- **Silence during the run ≠ hung** in most cases
- Operator/Codex must wait for timeout or completion, then read `cursor-worker-runs/<workflow-id>/`

**Never accept local file changes before reviewing runner artifacts.**

---

## 5. Binding operating rules (effective immediately)

### 5.1 Timeout tiers (until H-003 is implemented in runner)

Set before live Composer runs:

```powershell
# 1 allowlisted file, mechanical edit
$env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "240"

# 2 allowlisted files or debug with shell
$env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "300"

# 3+ files (discouraged — prefer Codex local)
$env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "300"
# or do not delegate
```

**Do not use 120s** for Composer tool lanes unless explicitly experimenting. Evidence shows systematic false timeouts.

### 5.2 Slice fitness (unchanged from Operating Model)

Delegate Composer only if **all** true:

- Allowlist **≤2 files** (≤1 preferred)
- Not multi-file backend / roadmap slice
- Precheck PASS
- Positive ROI in dry gate
- Operator explicit OK for `--execute-live-cursor`

Otherwise: **Codex local**, no live attempt.

### 5.3 Failure protocol (critical path)

```text
1. One Composer live attempt per task (max one API compare if explicitly comparing)
2. On CURSOR_AGENT_TIMEOUT → log evidence, implement in Codex
3. Do not retry Composer 3× on same package with same timeout
4. Optional: one retry with session resume + higher timeout ONLY if operator explicitly requests
```

### 5.4 Outcome taxonomy

| Outcome | Action |
|---------|--------|
| `CURSOR_AGENT_TIMEOUT` | Codex implements; classify `TRANSPORT_FAIL_TIMEOUT` |
| PASS + 0 changed files | `TRANSPORT_PASS_SEMANTIC_FAIL` — do not accept |
| PASS + allowlisted edits | Codex review + validation |

---

## 6. Hardening backlog (Track B — do not block product work)

| ID | Item | Priority |
|----|------|----------|
| **H-003** | Timeout tiers in runner by lane / allowlist count | High |
| **H-001** | `SEMANTIC_FAIL` when `changed_files_count==0` on execution lanes | High |
| **H-002** | `TRANSPORT_PASS` vs `SEMANTIC_PASS` in `dispatcher_result.json` | High |

Schedule **one** hardening slice per week max. Product roadmap (Track A) always wins.

---

## 7. What Codex must NOT do

- Do not treat timeouts as “Cursor integration broken”
- Do not lower timeout below 180s for Composer tool lanes
- Do not retry the same bounded package repeatedly on the critical path
- Do not accept worker output without artifact review
- Do not block roadmap work for runner hardening mid-slice
- Do not use API/Kimi as default replacement for Composer tool lanes

---

## 8. Recommended immediate action (example: BACKLOG-124 start-gate)

Current slice: 1 allowlisted `SKILL.md` file — **good Composer candidate**.

```text
1. Set JANUS_CURSOR_LIVE_TIMEOUT_SECONDS=240 (or 300 if prior run timed out at 240)
2. Run Composer once via janus_delegate choice 3
3. If TIMEOUT → implement the two-copy edit in Codex locally (5.6 Terra low)
4. Log outcome in SKILL_USAGE_LOG + CURRENT_STATE
5. Do not loop Composer on the same task
```

Prior evidence for similar 1-file slice: 84s PASS, 138s PASS with 0 edits (semantic fail), timeouts possible at low caps.

---

## 9. Copy-paste prompt for Codex

```text
Binding context: Cursor Composer timeout analysis
Read: documentation/codex/model-routing/HANDOFF_CURSOR_COMPOSER_TIMEOUT_ANALYSIS_2026-07-10.md
Also: HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md

Key facts:
- Composer timeouts are usually our wall-clock cap, not broken routing
- Default 180s; 120s causes systematic false timeouts
- Successful Composer runs often need 90-220+ seconds
- No output during run is normal (--output-format json)
- On CURSOR_AGENT_TIMEOUT: log evidence, implement in Codex, do not retry 3x

Before live Composer:
  $env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "240"   # 1 file
  $env:JANUS_CURSOR_LIVE_TIMEOUT_SECONDS = "300"   # 2 files or debug+shell

Slice rules:
  - ≤2 allowlisted files only
  - One Composer attempt per task on critical path
  - Never accept changes without reviewing cursor-worker-runs artifacts

If implementing H-003 hardening (only when scheduled):
  - Add lane/file-count timeout tiers to janus_cursor_worker_runner.py
  - Keep default 180 for assist-only; 240/300 for tool lanes
  - pytest test_janus_cursor_worker_runner.py must pass
  - Do not block active product slice for this

Current product work continues regardless of timeout evidence.
```

---

## 10. Decision log

| Date | Decision |
|------|----------|
| 2026-07-10 | Composer timeouts traced to wall-clock cap + tool-loop duration, not integration failure |
| 2026-07-10 | **120s timeout rejected** for Composer tool lanes based on log evidence |
| 2026-07-10 | Recommended live caps: 240s (1 file), 300s (2 files / debug) until H-003 |
| 2026-07-10 | Timeout on critical path → Codex implements, one attempt only |

---

**END OF HANDOFF**
