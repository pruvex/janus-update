# Codex Handoff: Cost-Aware 4-Choice Delegation Gate + Cursor API Pool

**Date:** 2026-07-07  
**Status:** READY FOR IMPLEMENTATION  
**Branch baseline:** `develop` (tri-modal core committed; local commits may need push before start)  
**Owner:** Codex (implementation) · Operator (choice + live approvals)  
**Estimated effort:** 2 implementation days + 0.5 day real bounded slice validation

---

## 0. Executive summary

Upgrade the existing tri-modal delegation gate from `1/2/3 = Codex/Cursor/OR` to a **cost-aware 4-choice operator surface**:

```text
1 = Codex
2 = OpenRouter
3 = Cursor Auto+Composer pool (composer-2.5 / auto)
4 = Cursor API pool ($20 included credit; explicit model per lane)
```

**Critical constraint:** Option 3 and Option 4 both use the **same** backend (`cursor`) and the **same** runner (`janus_cursor_worker_runner.py` → `agent -p`). Do **not** build a fourth backend, second runner, or parallel harness.

After implementation + one real bounded slice, **stop meta work**. No usage-% prediction, no OR removal, no full model catalog.

---

## 1. Why now

| Reason | Detail |
| --- | --- |
| Infrastructure exists | `janus_delegate.py`, cursor runner, live proofs for EX-001 / TP-003 / DBG-002 |
| Manifest IDs wrong | `z-ai/glm-5.2` / `moonshotai/kimi-k2.5` must become real CLI IDs |
| API credit unused | Operator dashboard shows API pool at 0%; OR charges extra for overlapping assist work |
| Operator goal | Codex should show estimated cost **before** delegation |
| Finish line | 2 days gate + half-day real task = delegation stack "under one roof" |

---

## 2. Operator model (target)

### 2.1 Visible choices (lane-dependent)

Not every lane shows all four. Example for `execution_patch_candidate` (TASK-EX-001):

```text
Wie soll ich delegieren?

1. Codex 5.4 — volle Governance (Codex-Tokens)
2. OpenRouter — qwen/… — voraussichtlich ~$0.0005 (Fallback)
3. Cursor Composer 2.5 — Auto+Composer-Pool — voraussichtlich ~0,3–0,6 % Monatskontingent  ← Empfehlung
4. Cursor API — kimi-k2.7-code — voraussichtlich ~$0,02 vom $20-Pool

Empfehlung: 3
```

Example for `documentation_draft_review`:

```text
1. Codex 5.4
2. OpenRouter — … — ~$0.0005
4. Cursor API — gpt-5.4-mini-medium — ~$0,016 vom $20-Pool  ← Empfehlung

(Option 3 Composer nicht angeboten — kein Tool-Bedarf)
```

### 2.2 Lane-specific visibility rules

| Lane | 1 Codex | 2 OR | 3 Composer-% | 4 Cursor API $ | Notes |
| --- | --- | --- | --- | --- | --- |
| `execution_patch_candidate` | yes | yes | yes (`composer-2.5`) | yes (`kimi-k2.7-code`) | Tool proposal |
| `debug_repro_investigation` | yes | **no** | yes (`composer-2.5`) | optional off by default | Shell/tools required |
| `test_fixture_worker` | yes | yes | yes (`composer-2.5`) | yes (`kimi-k2.7-code`) | |
| `execution_write_apply_candidate` | yes | **no** | **no** | **no** | Option 2 = **Deterministic Apply** (special) |
| `documentation_draft_review` | yes | yes | no | yes (`gpt-5.4-mini-medium`) | |
| `quickchange_patch_review` | yes | yes | no | yes (`gpt-5.4-mini-medium`) | |
| `backlog_handoff_review` | yes | yes | no | yes (`glm-5.2-high`) | short prompts only |

**EX-002 exception (unchanged):** visible operator surface remains `1=Codex / 2=Deterministic Apply`. Do not expose Cursor API or Composer here.

### 2.3 Backend mapping (under the hood)

| Operator choice | `backend` | Runner | `--model` | Billing pool |
| --- | --- | --- | --- | --- |
| `1` | `codex` | none | — | Codex |
| `2` | `openrouter` | existing OR runners | per manifest | OR account |
| `3` | `cursor` | `janus_cursor_worker_runner.py` | `composer-2.5` (or `auto` if lane says so) | Auto+Composer % |
| `4` | `cursor` | **same runner** | per-lane `cursor_api_model` | API $ pool |
| EX-002 `2` | `deterministic_apply` | `codex_execution_write_apply_candidate_runner.py` | — | none |

---

## 3. Approved model shortlist (CLI IDs from `agent models`)

Replace obsolete manifest IDs. Use **exact** strings below.

### 3.1 Option 3 — Auto+Composer pool

| CLI ID | Role |
| --- | --- |
| `composer-2.5` | Default for all tool lanes (EX-001, DBG-002, TP-003) |
| `auto` | Only when lane explicitly sets `cursor.model: auto` |

### 3.2 Option 4 — API pool ($20)

| CLI ID | Lane role | Priority |
| --- | --- | --- |
| `gpt-5.4-mini-medium` | Doc draft, read-only review | **#1 assist** |
| `kimi-k2.7-code` | Code proposals, fixtures | **#1 code API** |
| `glm-5.2-high` | Backlog triage, short review | use only for short prompts |
| `gpt-5.3-codex-low` | Escalation only | **reserve**, never default |

**Do not** add Opus/GPT-5.5 high/xhigh/Codex-max variants to the shortlist.

### 3.3 Operator-confirmed pricing (per 1M tokens)

Use for **static** v1 cost hints in the gate (no dashboard polling).

| Model | Input $/M | Output $/M | 4th column (informational) |
| --- | ---: | ---: | ---: |
| `composer-2.5` | 0.50 | 0.20 | 2.5 |
| `kimi-k2.7-code` | 0.95 | 0.19 | 4.0 |
| `gpt-5.4-mini-medium` | 0.75 | 0.075 | 4.5 |
| `glm-5.2-high` | 1.40 | 0.26 | 4.4 |
| `gpt-5.3-codex-low` | 1.75 | 0.175 | 14 |

### 3.4 Static per-run estimate formula (v1)

Assume bounded Janus default package unless lane overrides:

- `default_input_tokens = 20000`
- `default_output_tokens = 2000`

```text
estimated_usd = (input/1e6 * input_rate) + (output/1e6 * output_rate)
```

Display as a range: `±30%` in operator text.

**Composer % hint (v1):** use heuristic only, e.g. `0.2–0.8 % Monatskontingent` for a typical bounded tool run; do **not** block on dashboard API.

**OR hint:** use existing `prompt_estimated_or_cost` from manifest when present.

---

## 4. Manifest changes

**File:** `documentation/codex/model-routing/config/delegation_routing_manifest.json`

### 4.1 Replace `cursor_model_policy`

```json
"cursor_model_policy": {
  "composer_pool": {
    "default_model": "composer-2.5",
    "alternate_model": "auto",
    "pool": "auto_composer",
    "pool_note": "Bills to Auto+Composer monthly pool (percent on dashboard)"
  },
  "api_pool": {
    "pool": "api",
    "pool_note": "Bills to included API dollar credit",
    "models": {
      "assist_default": "gpt-5.4-mini-medium",
      "code_proposal": "kimi-k2.7-code",
      "triage_short": "glm-5.2-high",
      "codex_escalation": "gpt-5.3-codex-low"
    }
  },
  "pricing_per_million_tokens": {
    "composer-2.5": {"input_usd": 0.5, "output_usd": 0.2},
    "kimi-k2.7-code": {"input_usd": 0.95, "output_usd": 0.19},
    "gpt-5.4-mini-medium": {"input_usd": 0.75, "output_usd": 0.075},
    "glm-5.2-high": {"input_usd": 1.4, "output_usd": 0.26},
    "gpt-5.3-codex-low": {"input_usd": 1.75, "output_usd": 0.175}
  },
  "default_token_assumptions": {
    "input_tokens": 20000,
    "output_tokens": 2000
  }
}
```

Remove obsolete `discover_before_use` entries (`z-ai/glm-5.2`, `moonshotai/kimi-k2.5`).

### 4.2 Per-lane fields

For each eligible lane add:

```json
"cursor": {
  "enabled": true,
  "composer_pool": {
    "enabled": true,
    "recommended": true,
    "model": "composer-2.5"
  },
  "api_pool": {
    "enabled": true,
    "recommended": false,
    "model": "kimi-k2.7-code"
  }
}
```

Assist lanes: `composer_pool.enabled: false`, `api_pool.model: gpt-5.4-mini-medium`.

### 4.3 Operator gate numbering

Add top-level manifest block:

```json
"operator_gate": {
  "version": "4choice_cost_aware_2026-07-07",
  "choices": {
    "1": {"backend": "codex", "label": "Codex"},
    "2": {"backend": "openrouter", "label": "OpenRouter"},
    "3": {"backend": "cursor", "pool": "auto_composer", "label": "Cursor Composer"},
    "4": {"backend": "cursor", "pool": "api", "label": "Cursor API"}
  }
}
```

---

## 5. Code changes

### 5.1 `delegation_routing.py`

- Extend `normalize_operator_choice()` to accept `4`, `cursor-api`, `cursor_api`.
- Map `3` → cursor + `pool=auto_composer`; `4` → cursor + `pool=api`.
- Keep backward aliases during transition:
  - legacy `2=cursor` → treat as `3` (composer pool) **or** emit deprecation warning in gate JSON.
  - legacy `3=openrouter` → treat as `2`.
- Add `visible_operator_choices(lane, task, roi) -> list[dict]` returning choice id, label, model, pool, cost_hint, recommended.
- Add `estimate_run_cost_usd(model, manifest) -> float`.
- Add `lane_cursor_model(lane, pool) -> str`.

### 5.2 `janus_delegate.py`

- `--operator-choice prompt` prints **4-choice** human text + JSON `visible_choices[]`.
- Route `3` and `4` through same cursor plan builder; pass `--model` and log `cursor_pool`.
- Include `cost_estimate` in plan JSON.
- EX-002 unchanged: choice `2` = deterministic apply, not OR/Cursor.

### 5.3 `janus_cursor_worker_runner.py`

- Accept `--cursor-pool auto_composer|api` (optional; infer from model if omitted).
- Log fields: `cursor_pool`, `estimated_cost_usd_static`, `duration_ms` (from CLI JSON when present).
- Append to `cursor_delegation_log.jsonl`.

### 5.4 Cache optimization conventions (implement in templates, not a new service)

Update worker package / prompt templates for lanes touched:

1. **Stable prefix block** (cache-friendly): lane contract, allowlist rules, output schema, `janus-delegated-worker` rules.
2. **Variable suffix block**: task-specific bug, paths, acceptance, validation command.
3. Prefer `session_id` resume on retries (DBG-002); do not resend full package.
4. Keep packages compact; no handoff essays in worker prompts.

Document in: `CURSOR_API_POOL_OPERATOR_PLAYBOOK_2026-07-07.md` (new, max 1 page).

### 5.5 Task list + skills

- Update `config/delegation_task_list_2026-07-05.md` / `.json` choice wording.
- Update `test_skill_surface_operator_mappings.py` for new `1/2/3/4` truth.
- Fix any stale EX-002 "Cursor" wording in examples/README if encountered (minimal).

---

## 6. Tests (required)

| Test file | Requirement |
| --- | --- |
| `test_delegation_routing.py` or extend existing | `normalize_operator_choice` for 1–4; legacy alias behavior |
| `test_janus_delegate.py` | prompt mode shows 4 choices where enabled; EX-001 shows 3+4; DBG-002 hides OR; EX-002 shows deterministic |
| `test_skill_surface_operator_mappings.py` | updated representative gates PASS |
| `test_janus_cursor_worker_runner.py` | `--cursor-pool api` + model passed to planned command |

Run:

```bash
python -m pytest documentation/codex/model-routing/tests/test_janus_delegate.py -q
python -m pytest documentation/codex/model-routing/tests/test_skill_surface_operator_mappings.py -q
python -m pytest documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py -q
```

---

## 7. Live validation (operator approval required)

One bounded live smoke per API model (dry-run planning PASS is not enough for API pool billing proof):

| Workflow ID | Lane | Choice | Model | Success criterion |
| --- | --- | --- | --- | --- |
| `WF-CURSOR-API-SMOKE-MINI-001` | `documentation_draft_review` or shadow | 4 | `gpt-5.4-mini-medium` | PASS + log row |
| `WF-CURSOR-API-SMOKE-KIMI-001` | `execution_patch_candidate` shadow | 4 | `kimi-k2.7-code` | PASS + proposal artifact |
| `WF-CURSOR-API-SMOKE-GLM-001` | `backlog_handoff_review` shadow | 4 | `glm-5.2-high` | PASS + short output |

After smokes: operator checks dashboard — API pool should move above 0%.

**Do not** run live smokes without explicit operator `OK` for this handoff slice.

---

## 8. Mandatory closing slice (half day)

After gate + smokes, run **one real bounded backlog task** end-to-end using the **new** gate:

```text
janus-preimplementation-check
→ EX-001 choice 3 or 4 (operator picks)
→ Codex review
→ EX-002 choice 2 deterministic apply
→ bounded pytest
→ evidence line in CURRENT_STATE / SKILL_USAGE_LOG
```

No new harness. No additional handoff docs beyond playbook + this file's completion note.

---

## 9. Explicitly out of scope

- Fourth backend `cursor_api` or second runner
- Dashboard / quota API polling or % prediction calibration
- Removing OpenRouter lanes
- Supporting full `agent models` catalog
- Usage snapshot tooling (`cursor_usage_snapshots.jsonl`)
- Production routing activation
- Git push / release (unless operator asks)
- Backend unrelated dirty-tree changes on `develop`

---

## 10. Acceptance criteria (PASS / BLOCKED)

### PASS requires all

1. Operator prompt shows cost-aware choices `1–4` per lane rules above.
2. Choices `3` and `4` route through same cursor runner with correct `--model` and pool metadata.
3. Manifest uses real CLI IDs (`kimi-k2.7-code`, `glm-5.2-high`, etc.).
4. EX-002 still deterministic apply on choice `2`; no Cursor/OR on apply.
5. DBG-002 still hides OR.
6. Tests listed in §6 PASS.
7. At least **two** of three API smokes PASS with operator approval.
8. One real bounded slice completes through new gate.
9. `cursor_delegation_log.jsonl` logs `cursor_pool` + `estimated_cost_usd_static`.

### BLOCKED if

- New parallel backend/runner introduced
- Scope expands into usage telemetry or OR deprecation
- No real bounded slice at end
- Legacy `1/2/3 = codex/cursor/or` left as primary operator truth without migration path

---

## 11. Suggested commit sequence

1. `feat(model-routing): add 4-choice cost-aware operator gate`
2. `feat(model-routing): route cursor api pool via shared runner`
3. `docs(model-routing): cursor api pool playbook and manifest ids`
4. `test(model-routing): harden 4-choice gate and skill surfaces`
5. `docs(governance): evidence for api pool smokes and real slice` (only after live runs)

---

## 12. Copy-paste prompt for Codex session

```text
Implement HANDOFF_COST_AWARE_4CHOICE_GATE_2026-07-07.md exactly.

Scope: 4-choice cost-aware gate (1=Codex, 2=OR, 3=Cursor Composer-%, 4=Cursor API-$).
Same cursor runner for 3 and 4; no fourth backend.
Update manifest CLI model IDs and static pricing table from handoff §3.
Implement cache-friendly prompt prefix/suffix conventions in worker templates.
Run tests in §6.
Live API smokes and real bounded slice only with explicit operator OK.

Do not: usage prediction, OR removal, production routing, unrelated backend edits.
Stop after acceptance criteria §10 PASS or report BLOCKED with evidence.
```

---

## 13. Reference — current baseline evidence

- Tri-modal core commits on `develop`: `591865bcc` … `8fe058898`
- Live cursor proofs: `WF-CURSOR-REAL-RUNNER-001`, `WF-CURSOR-REAL-TP-001`, `WF-CURSOR-REAL-DBG-001`
- Operator API dashboard (2026-07-07): API 0%; Auto+Composer 25.2M tokens / 6.4%
- CLI model list: operator-provided `agent models` output (2026-07-07)
