# Aider/OpenRouter Real Helper POC

This is the first isolated Aider follow-up that targets a real repo-owned Lean-Dev helper file.

Purpose:
- test the temp-workspace Aider pattern on a real non-product helper
- require one focused red-to-green test
- copy the accepted fix back into the real helper file only after the isolated run passes

Target:
- `development/openrouter-skill-tests/janus-preimplementation-check/lean_precheck_eval.py`

Rules:
- run Aider only inside a temporary workspace outside the repo
- allow edits only to `lean_precheck_eval.py`
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
