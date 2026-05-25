# BACKLOG-022 Consolidation Audit - Gemini Performance Investigation

Date: 2026-05-21
Status: PASS - MERGED INTO BACKLOG-007

## Decision

BACKLOG-022 is not closed as a performance fix. It is closed as a duplicate/merged investigation scope because its evidence and acceptance criteria are covered by BACKLOG-007.

## Rationale

Both tasks describe Gemini/GPT latency differences around filesystem-like requests, duplicate tool construction/sanitization and unnecessary tool-call behavior. Keeping both in Active would create duplicate planning and duplicated evidence work.

## Evidence

- BACKLOG-022: Gemini `gemini-3-pro-preview` takes ~20s vs GPT ~1s for a missing-file prompt; duplicate tool sanitization appears 30+ times.
- BACKLOG-007: Gemini takes ~102s vs GPT ~11s for a filesystem move/create task; unnecessary `list_directory` call and model-selection/tool-call efficiency are in scope.
- BACKLOG-007 handoff now explicitly includes the BACKLOG-022 duplicate-tool-sanitization investigation.
- BACKLOG-022 handoff restored at `documentation/tasks/backlog_BACKLOG-022_gemini_performance_investigation.md` and points to BACKLOG-007 as master.

## Verdict

PASS. BACKLOG-022 can be marked DONE/MERGED while BACKLOG-007 remains READY as the single implementation task for the performance block.
