# Cursor Handoff: M4 Session-Search Live Validation

**Date:** 2026-07-10
**Source Branch:** `develop`
**Prepared by:** Codex
**Target Slice:** `TASK-MEM-M4.1`
**Purpose:** bounded live evidence collection only, no authoritative implementation or roadmap rewrite

## 1. Why This Handoff Exists

`TASK-MEM-M4.1` is now locally green in Codex, but the bounded live Janus gate is still open.

We need Cursor for one narrow job:

- collect real runtime evidence for the new Session-Search path
- keep the evidence bounded to three exact prompts
- return the observed behavior honestly

Codex remains:

- final owner of product truth
- final owner of PASS/BLOCKED routing
- final owner of any follow-up code changes

## 2. Current Truth

- M3 remains `EXIT PASS`
- next Track-A slice is `TASK-MEM-M4.1`
- `TASK-MEM-M4.1` implementation is local-green, but not live-validated yet
- the new feature is a bounded M4 Memory C slice:
  - separate `session_fts.db`
  - central write-hook on `crud.create_message(...)`
  - new tool `session_search`
  - bounded episodic intent routing
  - secret-like snippet suppression

Do not claim:

- M4 Memory C is fully done
- final audit is ready
- the live gate already passed

## 3. Files To Trust First

Load only these files first:

- `documentation/tasks/TASK-MEM-M4.1_execution_result.md`
- `documentation/tasks/TASK-MEM-M4.1_preimplementation_check.md`
- `documentation/tasks/TASK-MEM-M4.1_task_breakdown.md`
- `documentation/tasks/TASK-MEM-M4_session_search_fts5.md`
- `documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md`
- `documentation/ai/CURRENT_STATE.md`

Optional supporting files:

- `backend/services/memory/session_fts_store.py`
- `backend/services/memory/session_search_service.py`
- `backend/tools/session_search_tools.py`
- `backend/data/crud.py`
- `backend/services/orchestrator/intent_engine.py`
- `backend/services/orchestrator/execution_dispatcher.py`

## 4. Exact Live Validation Task

Run exactly these three bounded checks in Janus and capture the real output:

### Check A — Seed

In one chat, send:

`Die Firma heisst Acme GmbH und wir wollen das spaeter wiederfinden.`

Expected:

- normal answer is acceptable
- the message must become persisted product history; no special visible confirmation is required

### Check B — Cross-chat episodic recall

In a new chat, send:

`Wie hiess die Firma?`

Expected:

- Janus should recover the earlier company from prior chat history
- the answer should name `Acme GmbH`
- a generic “ich weiss es nicht” or unrelated answer is a fail for this gate

### Check C — Secret suppression

In the same or a fresh chat, send:

`mein passwort ist geheim123`

Then try an episodic-style lookup if needed, only if the product behavior requires a second prompt to surface retrieval, for example:

`Was habe ich dir eben gesagt?`

Expected:

- secret-like content must not be surfaced back as a Session-Search result
- no explicit password string such as `geheim123` may appear in the returned retrieval content

## 5. Evidence To Return

Return a short bounded evidence note with:

- exact prompt used
- exact observed answer
- PASS or FAIL per check
- one-line reason per check

Preferred structure:

1. Check A: PASS/FAIL
2. Check B: PASS/FAIL
3. Check C: PASS/FAIL
4. Overall: PASS if all three checks pass, otherwise BLOCKED

If something failed, include only the minimum concrete failure detail needed for Codex to debug.

## 6. Hard Boundaries

Do not widen into:

- Frozen Core / M5
- USER.md export
- Transport / OAuth / OpenRouter
- unrelated memory refactors
- Git actions
- documentation closeout as if validation were already sealed
- new code edits unless the operator explicitly reroutes back to Codex for debug

## 7. What Cursor Must Not Assume

- Do not assume a local green pytest block equals live PASS
- Do not claim audit readiness
- Do not infer that any secret suppression outside this exact seam is now globally solved
- Do not rewrite the prompts into “equivalent” alternatives; use the bounded prompts above first

## 8. Recommended Cursor Role

- `Cursor API`: acceptable for bounded evidence capture and concise reporting
- `Cursor Composer`: acceptable only if used as a narrow live-validation helper, not as a product-code owner
- `Codex`: final owner of result interpretation and any next debug/test/audit routing

## 9. Compact Prompt For Cursor

```text
You are collecting bounded live evidence for one Janus slice.

Target:
- TASK-MEM-M4.1
- M4 Memory C Session-Search live validation

Trust first:
- documentation/tasks/TASK-MEM-M4.1_execution_result.md
- documentation/tasks/TASK-MEM-M4.1_preimplementation_check.md
- documentation/tasks/TASK-MEM-M4.1_task_breakdown.md
- documentation/tasks/TASK-MEM-M4_session_search_fts5.md
- documentation/Cursor specs/MEMORY_HERMES_INSPIRED_UPGRADE_PLAN.md
- documentation/ai/CURRENT_STATE.md

Run exactly these bounded checks and report the observed outputs:
1. In one chat: `Die Firma heisst Acme GmbH und wir wollen das spaeter wiederfinden.`
2. In a new chat: `Wie hiess die Firma?`
3. Secret suppression check: `mein passwort ist geheim123`
   If needed for retrieval exposure, then ask: `Was habe ich dir eben gesagt?`

Return:
- PASS/FAIL for each check
- exact observed answer per check
- overall PASS only if all three checks pass

Hard boundaries:
- no code ownership claims
- no audit-ready claim
- no widening into Frozen Core, Transport, OAuth, OpenRouter, or Git work
```
