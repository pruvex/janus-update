# Aider/OpenRouter Real Helper POC 2

This is the second isolated Aider run against a real repo-owned Lean-Dev helper file.

Purpose:
- test the temp-workspace Aider pattern on another real non-product helper
- require one focused red-to-green test
- patch a brittle validation rule instead of a synthetic toy function

Target:
- `development/openrouter-skill-tests/janus-backlog-prioritization/lean_backlog_prioritization_eval.py`

Rules:
- run Aider only inside a temporary workspace outside the repo
- allow edits only to `lean_backlog_prioritization_eval.py`
- do not modify the test file
- no commit
- no push
- no release action
- no repo-root `.aider*` artifacts
- no real `.gitignore` change

Success bar:
- pretest fails on the current helper copy
- posttest passes after the worker fix
- only the target helper changes
- the accepted helper file is copied back into the real repo path
