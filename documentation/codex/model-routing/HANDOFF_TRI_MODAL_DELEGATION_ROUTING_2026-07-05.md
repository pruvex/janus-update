# Codex Handoff: Tri-Modal Delegation (Codex / Cursor / OpenRouter)

**Date:** 2026-07-05  
**Status:** READY FOR IMPLEMENTATION PLANNING  
**Scope:** Codex development-environment orchestration only. No Janus product routing. No production Auto Router. No delegated Git/release/final-audit authority.

**User intent:** Keep maximum flexibility. Every relevant Janus skill should offer:

- `1 = Codex` — local, full governance
- `2 = Cursor` — tool-capable worker (write, run, debug loops)
- `3 = OpenRouter` — cheap bounded assist/proposal workhorse

Before work starts, define a **task routing manifest** that maps each bounded task class to the right backend and model (Cursor: `auto` / `composer-2.5` / specific; OR: lane-specific model). Codex reads the manifest and delegates to the correct worker when the operator chooses `2` or `3`.

---

## 0. Executive Summary

| Layer | Role |
| --- | --- |
| **Codex** | Orchestrator, scope owner, gatekeeper, final reviewer, PASS/BLOCKED |
| **Cursor** | Tool worker: code writes, shell, test execution, debug reproduction |
| **OpenRouter** | Cheap text worker: triage, hypotheses, drafts, proposal-first patches |
| **Routing manifest** | Single source: which task → which backend → which model |

Operator always chooses `1 / 2 / 3`. Codex may **recommend** a default from the manifest when ROI and eligibility pass, but never auto-delegate without visible operator choice.

---

## 1. Design Principles

1. **Three visible choices, one contract** — skills show the same `1=Codex / 2=Cursor / 3=OR` language.
2. **Manifest-driven routing** — no model strings scattered in SKILL.md files.
3. **Backend fits task shape** — not "always cheapest" but "right tool for job".
4. **Codex owns acceptance** — all external workers return normalized artifacts; Codex reviews before bind.
5. **Fail-closed** — if manifest, eligibility, budget, or ROI fails → hide external options, Codex-only.
6. **OR and Cursor coexist** — OR for assist/proposal; Cursor for tool loops.

---

## 2. When To Use Which Backend

| Task shape | Preferred | Why |
| --- | --- | --- |
| Governance, final audit, release | **Codex only** | authority |
| Schema extraction, triage, hypothesis ranking | **OR** | cheap, no tools needed |
| Draft spec/task/doc (proposal-first) | **OR** or **Cursor** | OR cheaper; Cursor if file context heavy |
| Bounded patch proposal | **OR** or **Cursor** | OR proposal-first; Cursor if multi-file + run checks |
| Test fixture write + run + iterate | **Cursor** | needs shell |
| Live Playwright / provider test | **Codex** (+ user `OK START LIVE TEST`) | governance |
| Debug with repro + logs + commands | **Cursor** | needs tools |
| Debug hypothesis ranking only | **OR** | assist-only |
| Tiny obvious change | **Codex** | OR/Cursor overhead > savings |

---

## 3. Routing Manifest (New Canonical File)

**File:** `documentation/codex/model-routing/config/delegation_routing_manifest.json`

```json
{
  "manifest_version": "2026-07-05",
  "status": "OPERATOR_ROUTING_NOT_PRODUCTION_ROUTING",
  "default_operator_gate": "recommend_from_manifest",
  "backends": {
    "codex": {
      "description": "Local Codex execution with full Janus governance"
    },
    "cursor": {
      "description": "Cursor CLI/SDK headless agent with tool and shell access",
      "cli_binary": "agent",
      "auth_env": "CURSOR_API_KEY",
      "discover_models_command": "agent models"
    },
    "openrouter": {
      "description": "Bounded OpenRouter HTTP worker for assist and proposal-first lanes",
      "auth_env": "OPENROUTER_API_KEY"
    }
  },
  "lanes": {
    "debug_hypothesis_review": {
      "skill": "janus-debug",
      "lane_class": "OR_ASSIST_ONLY",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "high" },
      "cursor": {
        "enabled": true,
        "recommended": false,
        "model": "auto",
        "mode": "assist_only",
        "allow_shell": false,
        "allow_write": false
      },
      "openrouter": {
        "enabled": true,
        "recommended": true,
        "model": "qwen/qwen3-coder-30b-a3b-instruct",
        "budget_profile": "debug_hypothesis_review"
      },
      "minimum_net_codex_saved_tokens": 5000
    },
    "test_result_triage_review": {
      "skill": "janus-test-pipeline",
      "lane_class": "OR_ASSIST_ONLY",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "medium" },
      "cursor": { "enabled": true, "recommended": false, "model": "auto", "mode": "assist_only" },
      "openrouter": {
        "enabled": true,
        "recommended": true,
        "model": "qwen/qwen3-coder-30b-a3b-instruct",
        "budget_profile": "test_result_triage_review"
      },
      "minimum_net_codex_saved_tokens": 8000
    },
    "test_fixture_worker": {
      "skill": "janus-test-pipeline",
      "lane_class": "TOOL_WORKER",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "medium" },
      "cursor": {
        "enabled": true,
        "recommended": true,
        "model": "composer-2.5",
        "fallback_model": "auto",
        "mode": "proposal_first",
        "allow_shell": true,
        "allow_write": true,
        "require_allowlist": true
      },
      "openrouter": {
        "enabled": true,
        "recommended": false,
        "model": "moonshotai/kimi-k2.5",
        "worker_profile": "aider-openrouter-kimi",
        "budget_profile": "strong_test_worker",
        "note": "isolated Aider only; no open shell"
      },
      "minimum_net_codex_saved_tokens": 8000
    },
    "execution_patch_candidate": {
      "skill": "janus-executioner",
      "lane_class": "OR_PROPOSAL_FIRST",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "high" },
      "cursor": {
        "enabled": true,
        "recommended": true,
        "model": "composer-2.5",
        "fallback_model": "auto",
        "mode": "proposal_first",
        "allow_shell": true,
        "allow_write": true,
        "require_allowlist": true
      },
      "openrouter": {
        "enabled": true,
        "recommended": false,
        "model": "moonshotai/kimi-k2.5",
        "budget_profile": "execution_patch_candidate"
      },
      "minimum_net_codex_saved_tokens": 10000
    },
    "execution_write_apply_candidate": {
      "skill": "janus-executioner",
      "lane_class": "ACCEPTED_SOURCE_WRITE",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "high" },
      "cursor": {
        "enabled": true,
        "recommended": true,
        "model": "composer-2.5",
        "mode": "accepted_source_apply",
        "requires_accepted_source": true
      },
      "openrouter": {
        "enabled": true,
        "recommended": false,
        "model": "deepseek/deepseek-v4-flash",
        "budget_profile": "execution_write_apply_candidate",
        "requires_accepted_source": true
      },
      "minimum_net_codex_saved_tokens": 12000
    },
    "quickchange_patch_review": {
      "skill": "janus-quickchange",
      "lane_class": "OR_PROPOSAL_FIRST",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "low" },
      "cursor": { "enabled": true, "recommended": true, "model": "auto", "mode": "proposal_first" },
      "openrouter": {
        "enabled": true,
        "recommended": false,
        "model": "deepseek/deepseek-v4-flash",
        "budget_profile": "quickchange_patch_review"
      },
      "minimum_net_codex_saved_tokens": 3000
    },
    "generator_review": {
      "skill": "janus-test-pipeline",
      "lane_class": "STRUCTURED_LOCAL_INTERIM",
      "codex": { "enabled": true, "default_model": "5.4", "default_reasoning": "medium" },
      "cursor": { "enabled": true, "recommended": false, "model": "auto", "mode": "review_only" },
      "openrouter": {
        "enabled": true,
        "recommended": true,
        "model": "openai/gpt-oss-20b",
        "budget_profile": "documentation_draft"
      },
      "minimum_net_codex_saved_tokens": 3000
    }
  }
}
```

**Rule:** Skills, dispatcher, and operator docs read **only** from this manifest. Extend `lanes` as new task classes are validated.

---

## 4. Cursor Model Selection Policy

Within the manifest, Cursor models are chosen per lane:

| Cursor model | Use for |
| --- | --- |
| `auto` | triage, classification, small reviews, quickchange |
| `composer-2.5` | code writes, test authoring, debug loops, execution patches |
| specific (e.g. Kimi/GLM slug from `agent models`) | hard slices only when manifest says so |

**Discovery before live use:**

```bash
agent models
```

Manifest may reference `fallback_model` when primary is unavailable on account.

**CLI invocation pattern:**

```bash
agent -p --model <manifest.cursor.model> \
  --force --trust --approve-mcps \
  --workspace <REPO_ROOT> \
  --output-format json \
  "<bounded task prompt>"
```

Assist-only Cursor lanes: omit `--force`, use read-only prompt contract.

---

## 5. Unified Entry Point (Replaces Single-Backend `janus_or_delegate.py`)

**File:** `documentation/codex/model-routing/scripts/janus_delegate.py`

Single operator entry for all three backends.

### Interface

```powershell
python documentation/codex/model-routing/scripts/janus_delegate.py `
  --lane <lane_id> `
  --workflow-id <WORKFLOW-ID> `
  --operator-choice <prompt|codex|cursor|openrouter|1|2|3> `
  [--input-package-json <path>] `
  [--allowlist-file <path>] `
  [--estimated-cost-usd <n>] `
  [--estimated-codex-saved-tokens <n>] `
  [--estimated-delegation-overhead-tokens <n>] `
  [--dry-run]
```

### Operator choice mapping

| Input | Backend |
| --- | --- |
| `1`, `codex`, `local` | Codex path summary only |
| `2`, `cursor` | Cursor CLI/SDK |
| `3`, `openrouter`, `or`, `opr` | existing OR runners |
| `prompt` | show gate from manifest |

### Gate output (prompt mode)

```text
1 = Codex
2 = Cursor
3 = OpenRouter

Lane: test_fixture_worker
Empfehlung: 2 = Cursor (composer-2.5)
Alternativen: 3 = OR (moonshotai/kimi-k2.5, isolated Aider, kein Shell)
              1 = Codex (5.4 medium)

Geschätzte Einsparung: ~12000 Codex-Tokens (net 4000 nach Overhead)
Cursor-Modell: composer-2.5
OR-Modell: moonshotai/kimi-k2.5
Budget: Session OR $0.02 / $0.36 | Cursor: siehe Usage-Dashboard
```

### Routing logic

1. Load `delegation_routing_manifest.json` → lane config
2. Check eligibility (existing `bounded_or_worker_eligibility.py` + new `cursor_lane_eligibility`)
3. Evaluate ROI (`minimum_net_codex_saved_tokens`)
4. If backend disabled or ROI negative → hide that option
5. Route:
   - `cursor` → `janus_cursor_worker_runner.py` (new)
   - `openrouter` → existing OR runner from lane config
   - `codex` → return local summary, no external call

### Normalized result contract (all backends)

Every delegation returns:

```json
{
  "backend": "cursor|openrouter|codex",
  "lane_id": "...",
  "workflow_id": "...",
  "selected_model": "...",
  "validation_result": "PASS|FAIL|BLOCKED",
  "artifacts": {
    "result_json": "...",
    "diff_patch": "...",
    "stdout_log": "...",
    "cost_json": "..."
  },
  "codex_review_required": true,
  "operator_message": "..."
}
```

---

## 6. New Cursor Worker Runner

**File:** `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py`

Responsibilities:

- Build bounded prompt from input package + allowlist
- Invoke `agent -p` with manifest model
- Capture JSON result, changed files, command output
- Enforce: no git, no release, allowlist-only when `require_allowlist: true`
- Write run dir under `documentation/codex/model-routing/cursor-worker-runs/<WORKFLOW-ID>/`

**Boundaries (same as OR):**

- no commit/push/tag/merge/release
- no final audit PASS
- no secrets in prompts
- Codex reviews all outputs

---

## 7. Skill Gate Standard (All Janus Skills)

Replace per-skill `1=Codex / 2=OR` with:

```text
1 = Codex
2 = Cursor
3 = OpenRouter
```

### Skills to update first (highest value)

| Skill | Lanes |
| --- | --- |
| `janus-executioner` | `execution_patch_candidate`, `execution_write_apply_candidate` |
| `janus-test-pipeline` | `test_fixture_worker`, `test_result_triage_review`, `generator_review` |
| `janus-debug` | `debug_hypothesis_review` |
| `janus-quickchange` | `quickchange_patch_review` |

### Skill snippet template

```markdown
## Delegation Gate

When eligibility passes, show:

- `1 = Codex`
- `2 = Cursor`
- `3 = OpenRouter`

Invoke:

python documentation/codex/model-routing/scripts/janus_delegate.py \
  --lane <lane_id> \
  --workflow-id <WORKFLOW-ID> \
  --operator-choice prompt \
  --input-package-json <bounded-package.json>

Boundaries: Codex remains final reviewer. No delegated Git, release, or audit authority.
```

---

## 8. Task List Workflow (How You Use It Day-to-Day)

### Step 1 — Define routing before the session

Edit or generate manifest slice for today's work:

```text
TASK LIST — 2026-07-05

| Task | Lane | Recommended | Cursor model | OR model |
| --- | --- | --- | --- | --- |
| BACKLOG-142 test fixture | test_fixture_worker | Cursor | composer-2.5 | kimi-k2.5 |
| BACKLOG-142 triage failures | test_result_triage_review | OR | auto | qwen3-coder-30b |
| BACKLOG-138 execution patch | execution_patch_candidate | Cursor | composer-2.5 | kimi-k2.5 |
| BACKLOG-138 debug hypotheses | debug_hypothesis_review | OR | auto | qwen3-coder-30b |
```

Optional helper:

```powershell
python documentation/codex/model-routing/scripts/delegation_task_list.py validate --manifest delegation_routing_manifest.json --tasks tasks-2026-07-05.json
```

### Step 2 — Codex reads task + manifest

When you start a skill, Codex:

1. Identifies `lane_id` from task type
2. Loads manifest recommendation
3. Shows `1/2/3` gate with recommendation
4. You pick (or accept recommendation)
5. `janus_delegate.py` routes to correct backend + model

### Step 3 — Codex reviews artifact

Regardless of backend: diff, logs, cost, validation → Codex accept/reject.

---

## 9. Implementation Phases

| Phase | Deliverable | Stop |
| --- | --- | --- |
| **1** | `delegation_routing_manifest.json` + loader + tests | manifest validates |
| **2** | `janus_delegate.py` tri-modal router (dry-run) | routes all 3 backends in dry-run |
| **3** | `janus_cursor_worker_runner.py` + tests | no-live cursor invoke mocked |
| **4** | Wire OR paths through `janus_delegate.py` (reuse existing runners) | OR lanes unchanged behavior |
| **5** | Update skills to `1/2/3` gate | executioner, test-pipeline, debug |
| **6** | `delegation_task_list.py` validator | task list JSON validates against manifest |
| **7** | One live pilot per backend | cursor + or + codex baseline evidence |

**Do not collapse OR infrastructure** — wrap it behind `janus_delegate.py --operator-choice openrouter`.

---

## 10. Relationship to Existing Handoffs

| Document | Role |
| --- | --- |
| `HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md` | OR lane + registry foundation; OR becomes `3=` path |
| **This handoff** | Tri-modal superset; `janus_or_delegate.py` → `janus_delegate.py` |
| `delegation_routing_manifest.json` | supersedes `or_model_registry.json` as single source |

Migrate `or_model_registry.json` lanes into manifest `openrouter` + `cursor` sections rather than maintaining two files.

---

## 11. Acceptance Criteria

- [ ] All priority skills show `1=Codex / 2=Cursor / 3=OR`
- [ ] Manifest drives model choice for Cursor and OR
- [ ] `janus_delegate.py` is sole operator entry
- [ ] Cursor runner enforces allowlist + no-git
- [ ] OR runners still work unchanged behind `3=`
- [ ] ROI gate hides options when savings negative
- [ ] Task list validator checks lane exists in manifest
- [ ] `CURRENT_OR_STATE.md` renamed/expanded to `CURRENT_DELEGATION_STATE.md`
- [ ] No production routing claim
- [ ] Codex final owner on all paths

---

## 12. Copy-Paste Prompt For Codex

```text
Read and implement:
documentation/codex/model-routing/HANDOFF_TRI_MODAL_DELEGATION_ROUTING_2026-07-05.md

Also read for OR foundation:
documentation/codex/model-routing/HANDOFF_OR_TEST_PIPELINE_AND_UNIFIED_ENTRY_2026-07-05.md

Constraints:
- Keep OpenRouter as option 3; do not remove OR infrastructure
- Add Cursor as option 2
- Codex remains option 1 and final acceptance owner
- No production routing activation
- No Git commit unless I explicitly ask
- No live Cursor or OpenRouter calls without my explicit approval

Execute phases 1-4 only, then stop and report:
- changed files
- pytest results
- sample gate output for test_fixture_worker lane
```

---

## 13. Open Questions

1. Gate numbering fixed as `1/2/3` or allow `opr`/`cursor` aliases only?
2. When manifest recommends Cursor but user has no `CURSOR_API_KEY`, hide `2=` or show blocked?
3. Task list format: JSON only or also markdown table like section 8?

---

*End of handoff.*
