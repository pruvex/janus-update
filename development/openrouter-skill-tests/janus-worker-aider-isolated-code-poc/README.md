# Aider/OpenRouter Isolated Code Worker POC

This is a slightly more realistic bounded worker POC for Janus.

Purpose:
- verify that the isolated temp-workspace pattern also works for a tiny code/test fix
- keep the task fully outside the real repository root
- require a concrete before/after test signal

Rules:
- run Aider only inside a temporary workspace outside the repo
- allow edits only to `text_utils.py`
- treat any modification to `test_text_utils.py` as scope drift
- no commit
- no push
- no release action
- no repo-root `.aider*` artifacts
- no real `.gitignore` change

Expected artifacts:
- `worker_task.md`
- `allowed_files.txt`
- `text_utils.py`
- `test_text_utils.py`
- `run_isolated_code_worker.ps1`
- `worker_report.md`
- `test_output.log`

Success bar:
- pre-run test fails
- post-run test passes
- only `text_utils.py` changes
- the real repo root stays free of new `.aider*` artifacts
- the real `.gitignore` hash stays unchanged
