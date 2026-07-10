# TASK-SPEC31.1 Cursor Execution Probe - 2026-07-09

Canonical State: PASS WITH FALLBACK NOTE
Target Task: TASK-SPEC31.1

## Goal

Collect real Cursor-first execution evidence for the bounded `janus-executioner` slice before Codex-owned review/apply and local validation.

## Bound Package

- Input package: `development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/input_package.json`
- Worker package: `development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/worker_package.json`
- Allowlist: `development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/allowlist.txt`

## Execution Evidence

1. Shared prompt gate PASS
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id WF-SPEC31.1-EXEC-PATCH-2026-07-09-001 --operator-choice prompt --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/allowlist.txt --estimated-codex-saved-tokens 18000 --estimated-delegation-overhead-tokens 5000 --minimum-net-codex-saved-tokens 8000`
   - Result:
     - `validation_result = PASS`
     - visible choices: `1 = Codex`, `2 = OpenRouter`, `3 = Cursor Composer`, `4 = Cursor API`
     - ROI: positive (`net_codex_saved_tokens = 13000`)
     - recommendation: `3 = Cursor Composer`

2. Cursor Composer live run BLOCKED
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id WF-SPEC31.1-EXEC-PATCH-2026-07-09-001 --operator-choice 3 --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/allowlist.txt --estimated-codex-saved-tokens 18000 --estimated-delegation-overhead-tokens 5000 --minimum-net-codex-saved-tokens 8000 --execute-live-cursor`
   - Result:
     - `final_outcome = CURSOR_AGENT_TIMEOUT`
     - package validation PASS
     - allowlist validation PASS
     - no changed files

3. Cursor API live wrapper PASS but initial semantic packaging weak
   - Command:
     - `python documentation/codex/model-routing/scripts/janus_delegate.py --lane execution_patch_candidate --task-id TASK-EX-001 --workflow-id WF-SPEC31.1-EXEC-PATCH-2026-07-09-002 --operator-choice 4 --input-package-json development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/input_package.json --allowlist-file development/openrouter-skill-tests/janus-executioner/spec31_1_semantic_routine_reuse_2026-07-09/allowlist.txt --estimated-codex-saved-tokens 18000 --estimated-delegation-overhead-tokens 5000 --minimum-net-codex-saved-tokens 8000 --execute-live-cursor`
   - Result:
     - `final_outcome = CURSOR_WORKER_READY_FOR_CODEX_REVIEW`
     - package validation PASS
     - allowlist validation PASS
     - returned session id: `23ff3aee-3d5b-49d5-8ff6-a2a24c5c1f54`
     - initial worker response asked for the delegated task prompt instead of producing a patch

4. Cursor API resumed follow-up PASS
   - Command:
     - `agent.CMD -p --resume 23ff3aee-3d5b-49d5-8ff6-a2a24c5c1f54 --workspace C:\KI\Janus-Projekt\backend --model kimi-k2.7-code --output-format json --force --trust --approve-mcps "<concise TASK-SPEC31.1 prompt>"`
   - Result:
     - status `PASS`
     - changed files:
       - `backend/services/orchestrator/intent_engine.py`
       - `backend/services/workflow/routine_runner.py`
     - focused checks reported green from Cursor
     - saved response artifact:
       - `documentation/codex/model-routing/cursor-worker-runs/WF-SPEC31.1-EXEC-PATCH-2026-07-09-002/resume_followup_response.json`

## Interpretation

- Cursor was usable and productive for this slice, but not cleanly in one shot through the first wrapper call.
- The first strong evidence point is still valuable:
  - shared gate visibility worked
  - Composer availability and timeout were observed directly
  - API path executed successfully after a bounded follow-up in the same session and produced a concrete patch direction
- This matches the known trust rule from delegated write-candidate work: delegated execution evidence must stay separate from Codex-owned review/apply and local validation.

## Recommended Use

- Keep this probe artifact bound to `TASK-SPEC31.1_execution_result.md`.
- Treat the resumed Cursor API result as advisory implementation evidence, then verify locally before any audit or closeout.
