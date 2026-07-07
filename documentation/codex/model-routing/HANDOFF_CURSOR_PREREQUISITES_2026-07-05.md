# Codex Handoff: Cursor-Side Prerequisites (Minimal)

**Date:** 2026-07-05  
**Status:** READY FOR IMPLEMENTATION  
**Scope:** Only the required Cursor-side setup for tri-modal delegation (`1=Codex / 2=Cursor / 3=OR`). Assumes manifest, task list, example packages, and `janus_delegate.py` handoffs already exist.

**Goal:** Make `2 = Cursor` reliable, bounded, and cheap enough that Codex can delegate without repeating governance in every prompt.

---

## 1. Deliverables (only these)

| # | Deliverable | Path |
| --- | --- | --- |
| 1 | Cursor worker runner | `documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py` |
| 2 | Delegated-worker rule | `.cursor/rules/janus-delegated-worker.mdc` |
| 3 | Indexing ignore | `.cursorignore` additions for delegation artifact dirs |
| 4 | Delegation log | `documentation/codex/model-routing/cursor_delegation_log.jsonl` (append-only) |
| 5 | Prerequisites doc | `documentation/codex/model-routing/CURSOR_DELEGATION_PREREQUISITES.md` |

Do **not** re-implement manifest, task list, OR runners, or skill rewrites in this task.

---

## 2. `janus_cursor_worker_runner.py`

Thin wrapper around Cursor CLI. No duplicate business logic.

### Required CLI defaults

```bash
agent -p \
  --workspace <REPO_ROOT> \
  --model <from manifest/task list> \
  --output-format json \
  [--force --trust --approve-mcps]   # only when lane allows write/shell
```

### Modes

| Mode | Flags | Lanes |
| --- | --- | --- |
| `assist_only` | no `--force` | debug_hypothesis_review, test_result_triage_review, generator_review |
| `proposal_first` | `--force --trust --approve-mcps` | test_fixture_worker, execution_patch_candidate, debug_repro_investigation |

### Input

- `--lane`
- `--workflow-id`
- `--input-package-json`
- `--allowlist-file` (required when manifest `require_allowlist: true`)
- `--model` (optional override; default from manifest)
- `--resume-session-id` (optional)

### Output run dir

`documentation/codex/model-routing/cursor-worker-runs/<WORKFLOW-ID>/`

Required artifacts:

- `dispatcher_result.json`
- `stdout.log`
- `stderr.log`
- `cursor_response.json`
- `changed_files.txt` (from `git diff --name-only -- <allowlist>`)
- `session_id.txt` (for resume)

Normalized JSON must include: `backend: "cursor"`, `lane_id`, `workflow_id`, `selected_model`, `session_id`, `validation_result`, `codex_review_required: true`.

### Session resume

- Persist `session_id` from Cursor JSON response
- Support `--resume-session-id` for follow-up in same bounded slice
- Do not resume across unrelated lanes/workflows

### Fail-closed

- Missing `CURSOR_API_KEY` → `BLOCKED`, no invoke
- Missing allowlist when required → `BLOCKED`
- Non-zero `agent` exit → `FAIL`, preserve logs
- Any changed file outside allowlist → `FAIL`

### Tests

`documentation/codex/model-routing/tests/test_janus_cursor_worker_runner.py`

- mock `agent` subprocess
- assist vs proposal flag selection
- allowlist violation detection
- missing API key blocked
- session_id persisted

No live Cursor calls in unit tests.

---

## 3. `.cursor/rules/janus-delegated-worker.mdc`

Auto-apply when Cursor runs in this repo via CLI.

```markdown
---
description: Bounded delegated worker contract when invoked by Codex janus_cursor_worker_runner
alwaysApply: false
globs:
  - "**/*"
---

# Janus Delegated Worker (Cursor)

When acting as an external worker invoked by Codex:

- Change only files explicitly listed in the current task allowlist.
- Run only commands explicitly listed in the current task package.
- Do not commit, push, tag, merge, release, or publish.
- Do not declare final audit PASS, release readiness, or Backlog closure.
- Do not output secrets, tokens, cookies, API keys, or auth header values.
- Prefer minimal diffs over broad refactors.
- End with a concise JSON summary: status, changed_files, command_results, summary, blockers.
```

Keep rule short. Detailed lane policy stays in manifest/task list.

---

## 4. `.cursorignore` additions

Append only if not already ignored:

```gitignore
documentation/codex/model-routing/cursor-worker-runs/
documentation/codex/model-routing/bounded-dispatch-runs/
documentation/codex/model-routing/execution-direct-or-runs/
documentation/codex/model-routing/productive-dev-workhorse-runs/
documentation/codex/model-routing/sidecar-runs/
documentation/codex/openrouter-delegation/benchmark_result_*.json
development/openrouter-skill-tests/**/runs/
```

Purpose: faster focused runs, less noise in Cursor context.

---

## 5. `cursor_delegation_log.jsonl`

Append one row per Cursor delegation:

```json
{
  "timestamp": "ISO-8601",
  "workflow_id": "...",
  "lane_id": "...",
  "model": "composer-2.5",
  "session_id": "...",
  "validation_result": "PASS|FAIL|BLOCKED",
  "changed_files_count": 2,
  "resume_used": false
}
```

No prompts, no secrets, no full diffs.

---

## 6. Wire into `janus_delegate.py`

When `--operator-choice 2` or `cursor`:

- resolve model from manifest/task list
- call `janus_cursor_worker_runner.py`
- return normalized result to Codex

Until `janus_delegate.py` exists, document direct fallback:

```powershell
python documentation/codex/model-routing/scripts/janus_cursor_worker_runner.py --lane <lane> --workflow-id <id> --input-package-json <pkg> --allowlist-file <allowlist>
```

---

## 7. Model policy (do not improvise)

| Lane | Cursor model |
| --- | --- |
| assist-only lanes | `auto` |
| test_fixture_worker | `composer-2.5` |
| debug_repro_investigation | `composer-2.5` |
| execution_patch_candidate | `composer-2.5` |
| execution_write_apply_candidate | `composer-2.5` |

Discover account-specific slugs once via `agent models`; do not hardcode unavailable models.

---

## 8. Acceptance criteria

- [ ] `janus_cursor_worker_runner.py` exists with assist/proposal modes
- [ ] allowlist enforcement tested
- [ ] session_id persisted and resumable
- [ ] `.cursor/rules/janus-delegated-worker.mdc` added
- [ ] `.cursorignore` updated for artifact dirs
- [ ] `cursor_delegation_log.jsonl` append on each run
- [ ] no live Cursor calls in tests
- [ ] `janus_delegate.py` routes `2=cursor` to this runner (or documented fallback)

---

## 9. Copy-paste prompt for Codex

```text
Implement only the Cursor-side prerequisites handoff:

documentation/codex/model-routing/HANDOFF_CURSOR_PREREQUISITES_2026-07-05.md

Constraints:
- Do not redo manifest, task list, OR runners, or skill rewrites
- No live Cursor calls without my explicit approval
- No Git commit unless I explicitly ask
- pytest for janus_cursor_worker_runner only (mocked)

Stop after acceptance criteria and report changed files + test output.
```

---

*End of handoff.*
