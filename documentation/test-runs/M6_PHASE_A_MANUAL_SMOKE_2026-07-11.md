# M6 Phase A — Manual Smoke Checklist

**Date:** 2026-07-11  
**Worktree:** `C:\KI\Janus-M6-Transport-Prep` (`codex/m6-transport-prep` @ `2c0b7f30a` or newer)  
**Scope:** Phase A only (`T-A1`–`T-A5`). Default-off sanity + optional flag-on enablement smokes.  
**Not in scope:** Phase B/C, OAuth, OpenRouter, broad regression, production flag flip.

---

## 0. Preflight — run from the correct worktree

Janus must **not** run from `C:\KI\Janus-Projekt` (`develop`) for these smokes. That tree has **no M6 code**.

1. Stop the current Janus dev session (`Ctrl+C` in the terminal running `npm run start-dev`).
2. Open a new terminal:

```powershell
cd C:\KI\Janus-M6-Transport-Prep
npm run start-dev
```

3. Confirm M6 code is loaded (any one):
   - File exists: `backend/llm_providers/shared/tool_loop_runner.py`
   - Backend log on startup does **not** need a special marker; use step A1 below instead.

**Quick wrong-tree detector:** If `backend/llm_providers/shared/tool_loop_runner.py` is missing, you are in the wrong folder.

---

## A. Default-off smokes (recommended, ~5 min)

**Env:** do **not** set `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED` (default = `false`).

| ID | Provider | Prompt | Pass criteria |
|----|----------|--------|---------------|
| A1 | OpenAI | `Suche kurz aktuelle KI-Nachrichten.` | Streaming answer; no error toast; tool runs; final text sensible |
| A2 | Gemini | `Wie ist das Wetter heute in Berlin?` | Weather answer with source/grounding; no provider error |
| A3 | Logs | After A1/A2 | **No** line `STREAM-GATEWAY-HANDOFF` (flag off) |

**Record:**

```text
A1 OpenAI default-off: PASS / FAIL — notes:
A2 Gemini default-off: PASS / FAIL — notes:
A3 No handoff log:     PASS / FAIL
```

---

## B. Flag-on smokes (before Phase B, ~10 min)

**Only after A passes.** These validate the new M6.5 streaming handoff path.

1. Stop Janus (`Ctrl+C`).
2. Start with flag enabled (same worktree):

```powershell
cd C:\KI\Janus-M6-Transport-Prep
$env:TRANSPORT_TOOL_LOOP_RUNNER_ENABLED = "true"
npm run start-dev
```

3. Run smokes:

| ID | Provider | Prompt | Pass criteria |
|----|----------|--------|---------------|
| B1 | OpenAI | Same as A1 (or fresh websearch prompt) | Full answer; no crash; tool + synthesis complete |
| B2 | Gemini | Same as A2 | Full weather answer; grounding/cost behavior normal |
| B3 | Logs | After tool round on B1 or B2 | Log contains `STREAM-GATEWAY-HANDOFF: delegating post-tool round via gateway/runner` |
| B4 | Ollama | Any simple chat (optional) | Still works; **no** gateway handoff expected for Ollama |

**Record:**

```text
B1 OpenAI flag-on:  PASS / FAIL — notes:
B2 Gemini flag-on:  PASS / FAIL — notes:
B3 Handoff log seen: PASS / FAIL — log excerpt:
B4 Ollama sanity:   PASS / FAIL / SKIPPED
```

4. After B, stop Janus and **unset the flag** unless you intentionally continue testing:

```powershell
Remove-Item Env:TRANSPORT_TOOL_LOOP_RUNNER_ENABLED -ErrorAction SilentlyContinue
```

---

## C. Where to look for logs

- Dev backend console (terminal running `npm run start-dev`)
- Optional: `documentation/logs/janus_startup_telemetry.log` in **this** worktree after restart

Search for:

```text
STREAM-GATEWAY-HANDOFF
AUDIT-LOOP-FORCED-START (stream)
```

---

## D. Exit decision

| Outcome | Next step |
|---------|-----------|
| A pass, B pass | Phase A manual evidence complete → `janus-documentation-update` + Phase B planning |
| A pass, B not run yet | OK for commit/doc sync; run B before broad flag enablement or Phase B |
| A fail | Stop — debug in M6 worktree; do not merge to `develop` |
| B fail | Route bounded fix (`janus-debug`); keep flag default-off |

---

## E. Operator sign-off (fill after run)

```text
Operator: local manual smoke operator
Worktree HEAD: `2c0b7f30a` (or newer local review state)
Started from: C:\KI\Janus-M6-Transport-Prep  YES
Default-off (A): PASS
Flag-on (B):     PASS
Overall:         PASS WITH FINDINGS
Notes: A1 OpenAI current-KI-news and A2 Gemini Berlin weather returned normal answers without errors. B1 OpenAI and B2 Gemini repeated successfully with `TRANSPORT_TOOL_LOOP_RUNNER_ENABLED=true`. Backend log recorded `STREAM-GATEWAY-HANDOFF` for OpenAI at 22:09:47 and Gemini at 22:10:04; both streams ended with `status: ok`. B4 Ollama skipped. Non-M6 telemetry warnings reported missing SUPABASE_URL only.
```
