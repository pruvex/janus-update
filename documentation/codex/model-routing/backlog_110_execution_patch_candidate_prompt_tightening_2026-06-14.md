# BACKLOG-110 execution_patch_candidate prompt tightening - 2026-06-14

Status: PASS

## Reason

The first real live delegated `execution_patch_candidate` attempt for `BACKLOG-110` timed out before returning any unified diff.

The saved stderr trace showed a broad exploration pattern:

- task artifact read
- allowed backend files read
- installed executioner skill read
- additional unrelated repository file reads
- no final patch emitted before timeout

## Tightening Applied

The runner prompt was tightened in `documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py`.

Changes:

- reduced the copied task excerpt to a compact task brief instead of a long artifact dump
- removed unnecessary `Spec Path` and handoff-heavy context from the live prompt body
- added an explicit one-pass instruction
- added an explicit "inspect only these files if needed, then immediately output the patch" instruction
- strengthened the diff-only rule
- added a backend-first and no-scope-widening reminder

## Expected Effect

The next live proposal attempt should spend less time re-reading workflow context and more time producing a bounded patch or an immediate `BLOCKED:` line.

## Validation

- `python -m py_compile documentation/codex/model-routing/scripts/codex_execution_patch_candidate_runner.py`: PASS
- regenerated `BACKLOG-110` dry-run prompt after tightening: PASS

## Non-Goal

This note does not count as accepted live execution proposal evidence.

It only documents the prompt hardening step that should happen before any second live delegated attempt.
