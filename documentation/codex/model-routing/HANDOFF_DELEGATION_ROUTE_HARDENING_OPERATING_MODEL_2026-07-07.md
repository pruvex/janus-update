# Codex Handoff: Delegation Route Hardening — Operating Model

**Date:** 2026-07-07  
**Status:** BINDING OPERATOR + CODEX POSTURE  
**Scope:** Codex development-environment delegation only. No Janus product routing. No production Auto Router.  
**Companion docs:**
- `HANDOFF_COST_AWARE_4CHOICE_GATE_2026-07-07.md` (gate implementation — DONE)
- `CURSOR_API_POOL_OPERATOR_PLAYBOOK_2026-07-07.md` (pool + cache conventions)

---

## 0. Executive summary

The 4-choice gate is **live and good enough for productive work**. Route hardening is now a **background discipline**, not a blocker for roadmap execution.

**Core rule:**

```text
Produktive Arbeit zuerst.
Delegation nur wenn Fit klar ist.
Misserfolg = Evidence, kein Stopp.
Härtung in kleinen, seltenen Slices — nie als Dauer-Marathon.
```

---

## 1. Two-track operating model

| Track | Purpose | Priority | When |
| --- | --- | --- | --- |
| **A — Product** | Roadmap slices (M0, M1, …), echte Backlog-Arbeit | **Always first** | Default |
| **B — Hardening** | Runner, Prompt, Timeout, semantic PASS, lane fit | **Background** | Max 1 small slice / week or after explicit failure pattern |

**Never:** Block Track A waiting for Track B completion.  
**Never:** Run A/B backend comparisons on every task.  
**Always:** Preserve failed live runs as evidence; do not delete run dirs.

---

## 2. Operator gate truth (unchanged)

```text
1 = Codex
2 = OpenRouter
3 = Cursor Composer   (Auto+Composer pool)
4 = Cursor API        (API $ pool, per-lane model)
```

- Codex = final reviewer and acceptance owner
- Option 3 and 4 = same Cursor backend / same runner
- `TASK-EX-002` / `execution_write_apply_candidate` = **Deterministic Apply** on choice `2`, not Cursor/OR
- No production routing automatism

---

## 3. Default routing — productive work (2026-07-07 evidence)

Use this table **before** offering or accepting delegation.

### 3.1 By task shape

| Task shape | Default | Try delegation? | Notes |
| --- | --- | --- | --- |
| Roadmap / M1 backend slice (3+ new files, domain logic) | **1 = Codex** | **No** first | M1.1 proof: Composer timeout, API no-op |
| Small bounded patch (1–2 allowlisted files) | **3 = Composer** | **Yes** | Proven: EX-001 shadows, SKILL livedev |
| Debug + shell + repro | **3 = Composer** | **Yes** if DBG-002 package exists | No OR |
| Assist / review / doc draft | **4 = API** (Mini / GLM) | **Yes** | API pool target use case |
| Mechanical apply after accepted source | **EX-002 deterministic** | **Never LLM** | |
| OR only when Cursor model unavailable or deliberate compare | **2 = OR** | Rare | Fallback, not default |

### 3.2 By lane

| Lane | Product default | Option 4 API | Option 2 OR |
| --- | --- | --- | --- |
| `execution_patch_candidate` | **3** if ≤2 files & package exists | Compare only, not default | Fallback |
| `debug_repro_investigation` | **3** | Usually off | Off |
| `test_fixture_worker` | **3** | Optional experiment | Fallback |
| `documentation_draft_review` | **4** Mini | **Yes** | Fallback |
| `backlog_handoff_review` | **4** GLM | **Yes** | Fallback |
| `quickchange_patch_review` | **4** Mini | **Yes** | Fallback |
| `execution_write_apply_candidate` | Deterministic apply | Off | Off |

### 3.3 Slice fitness gate (try Cursor only if ALL true)

```text
□ Allowlist ≤ 3 files (≤ 2 preferred for first live try)
□ Worker package + input package exist and validate
□ Precheck PASS for the target task
□ ROI positive in janus_delegate dry gate
□ Not a greenfield multi-module backend slice (→ Codex)
□ Operator explicit OK for live Cursor (--execute-live-cursor)
```

If any box fails → **Codex local**, no delegation experiment on the critical path.

---

## 4. Transport vs semantic success (binding)

A live Cursor run has **two layers**. Do not conflate them.

| Layer | Meaning | PASS signal |
| --- | --- | --- |
| **Transport** | CLI ran, session may exist, no runner crash | `agent -p` returned, `session_id` maybe set |
| **Semantic** | Task understood, files changed or valid no-op artifact | `changed_files_count > 0` OR explicit `RESULT.json` / reviewable patch |

### 4.1 Outcome taxonomy (use in logs and CURRENT_STATE)

| Code | Meaning | Productive? |
| --- | --- | --- |
| `TRANSPORT_PASS_SEMANTIC_PASS` | Full success | **Yes** |
| `TRANSPORT_PASS_SEMANTIC_FAIL` | Agent ran, no useful edit (e.g. M1.1 API Kimi) | **No** — implement in Codex |
| `TRANSPORT_FAIL_TIMEOUT` | Composer 180s (e.g. M1.1) | **No** — Codex or smaller slice |
| `TRANSPORT_FAIL_BLOCKED` | Contract/allowlist gate | Fix package, retry once |
| `DRY_RUN_READY` | Planned only | Not live |

**Current runner gap (hardening backlog):** `validation_result: PASS` with `changed_files_count: 0` is **transport-only**. Codex must treat as `TRANSPORT_PASS_SEMANTIC_FAIL` until runner is hardened.

### 4.2 Known evidence (do not re-prove on every slice)

| Workflow | Backend | Outcome | Lesson |
| --- | --- | --- | --- |
| `WF-CURSOR-COMPOSER-LIVEDEV-EXECUTIONER-002` | Composer | Semantic PASS | 1-file SKILL slice works |
| `WF-CURSOR-API-LIVEDEV-EXECUTIONER-001` | API Kimi | Transport only | API not for this execution shape |
| `WF-INTENT-M1.1-CURSOR-LIVE-2026-07-07-001` | Composer | Timeout 180s | 5-file backend slice too heavy |
| `WF-INTENT-M1.1-CURSOR-API-LIVE-2026-07-07-001` | API Kimi | Transport only, “prompt missing” | API not for multi-file execution |
| `WF-CURSOR-API-SMOKE-KIMI-002` | API Kimi | Semantic PASS on shadow | Shadow ≠ real repo livedev |

---

## 5. What to do when delegation fails on the critical path

```text
1. Stop retrying backends on the same package (max 1 Composer + 1 API compare per task, ever)
2. Log evidence path in CURRENT_STATE + SKILL_USAGE_LOG
3. Implement task in Codex (5.4 medium, same chat)
4. Park failure in Hardening Backlog (§7) — do not fix runner mid-roadmap slice
5. Continue roadmap
```

**Exception:** If the **same failure pattern** hits 3× in one week → schedule one Hardening slice (§6).

---

## 6. Hardening cadence (Track B)

### 6.1 When to schedule hardening

| Trigger | Action |
| --- | --- |
| Routine productive week | **No** hardening slice |
| Same `TRANSPORT_PASS_SEMANTIC_FAIL` on same lane 3× | One focused hardening slice |
| Operator requests compare | One bounded same-package A/B, document only |
| After M1 major exit | Optional half-day runner review |

### 6.2 Hardening slice rules

- Max **4 hours** Codex time
- One hypothesis per slice (e.g. “semantic PASS gate” OR “timeout tier” OR “top-level task_prompt for API”)
- Must include pytest for runner/delegate changes
- Live smoke only with operator `OK`
- Does **not** delay current roadmap task

### 6.3 Prioritized hardening backlog

| ID | Item | Priority | Effort |
| --- | --- | --- | --- |
| **H-001** | Runner: `SEMANTIC_FAIL` when `changed_files_count==0` on execution lanes (unless explicit no-op) | High | ~2h |
| **H-002** | Dispatcher: distinguish `TRANSPORT_PASS` vs `SEMANTIC_PASS` in `dispatcher_result.json` | High | ~2h |
| **H-003** | Timeout tiers: `JANUS_CURSOR_LIVE_TIMEOUT_SECONDS` by lane or file-count (e.g. 180 default, 300 for 3+ files) | Medium | ~2h |
| **H-004** | Input package: optional top-level `task_prompt` mirror for API models | Medium | ~1h |
| **H-005** | Lane manifest: mark `execution_patch_candidate` API pool `recommended: false` after M1.1 evidence | Low | ~30m |
| **H-006** | Skills: harmonize remaining tri-modal `2=Cursor/3=OR` wording to 4-choice | Low | ~0.5–1d |
| **H-007** | Usage snapshots (`cursor_usage_snapshots.jsonl`) | Deferred | — |

Pick **one** item per hardening week. Default next: **H-001 + H-002** together.

---

## 7. Comparison tests (A/B) — when and how

**Purpose:** Learn backend fit, not block delivery.

### Run A/B only when:

- New lane first live proof
- Operator explicitly asks
- After runner hardening (verify fix)
- **Not** on every execution task

### Protocol (same as M1.1 — gold standard):

```text
1. One bounded input package, frozen
2. Run 3 = Composer live (operator OK)
3. Run 4 = API live (same package, operator OK)
4. Record: session_id, duration_ms, changed_files, dispatcher_result, cursor_response
5. Classify transport vs semantic (§4)
6. Pick winner for future defaults OR document “neither — Codex only”
7. Do not retry again on this task — Codex implements
```

---

## 8. Cache and cost optimization (ongoing, low friction)

### Cursor (Options 3 & 4)

- Keep `Stable prefix` / `Variable suffix` in all worker packages
- Use `session_id` resume on retries, not full repost
- Compact packages; `.cursorignore` for run artifact dirs
- API Mini/GLM for assist; Composer for tools

### Codex (Option 1)

- Same chat through a roadmap milestone when possible
- `5.4 medium` default; `high` only for blockers
- Stay on warm `5.4` vs switching to mini mid-workflow (`janus-skill-router`)
- Short artifact-bound handoffs, not essay reposts

### Cost hints in gate

- Static estimates from manifest pricing are enough for v1
- Dashboard snapshot weekly (manual) — optional, not blocking

---

## 9. Integration with product roadmap

```text
ROADMAP (M0, M1, …)     = Track A, always wins
Delegation experiments  = Track B, never on critical-path blockers
M1.1 lesson             = multi-file intent backend → Codex local
Small patch / fixture   = Cursor Composer candidate
```

When `janus-executioner` runs on a roadmap task:

1. Check §3.3 slice fitness
2. If not fit → **Codex only** (no live Cursor attempt)
3. If fit and operator OK → Choice 3 first
4. On fail → Codex implements, log evidence, move on

---

## 10. Documentation duties (minimal)

| Event | Update |
| --- | --- |
| Any live Cursor run | `cursor_delegation_log.jsonl` (automatic) |
| Productive or blocked delegation attempt | `SKILL_USAGE_LOG.md` one row |
| Material routing lesson | `CURRENT_STATE.md` short entry |
| Hardening slice done | This file §6.3 mark item done + test evidence |

Do **not** write new handoff docs per failed run.

---

## 11. Acceptance — operating model is “active” when

- [x] 4-choice gate live
- [x] M1.1 A/B comparison documented
- [x] Default routing table agreed (this doc §3)
- [ ] H-001/H-002 semantic PASS distinction (next hardening slice, non-blocking)
- [ ] Operator uses §3 defaults for one week without ad-hoc re-debate

---

## 12. Codex copy-paste — daily posture

```text
Delegation operating model (binding):
  documentation/codex/model-routing/HANDOFF_DELEGATION_ROUTE_HARDENING_OPERATING_MODEL_2026-07-07.md

Before live Cursor:
  - Check slice fitness §3.3
  - Multi-file backend / roadmap slices → Codex only (M1.1 evidence)
  - ≤2 allowlisted files → Composer (3) candidate

On delegation fail:
  - Max one Composer + one API compare per task
  - Classify transport vs semantic §4
  - Implement in Codex; log evidence; do not block roadmap

Hardening:
  - Track B only; max 1 item/week from §6.3 backlog
  - Never mid-roadmap runner marathons

Current product work takes precedence over route optimization.
```

---

## 13. Decision log

| Date | Decision |
| --- | --- |
| 2026-07-07 | 4-choice gate EXIT PASS; productive defaults: Composer for small tool slices, API for assist |
| 2026-07-07 | M1.1: neither Composer nor API productive for 5-file intent slice → Codex local rule |
| 2026-07-07 | Hardening decoupled from product track; comparison tests rare and bounded |
| 2026-07-07 | `validation_result PASS` with zero edits = semantic fail until H-001 |

---

**END OF HANDOFF**
