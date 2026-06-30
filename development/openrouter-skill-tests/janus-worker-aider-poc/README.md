# Aider/OpenRouter Worker POC

This sandbox is a single bounded manual worker POC for Janus.

Purpose:
- evaluate whether Aider plus OpenRouter can act as a small delegated worker for Codex
- keep the first signal isolated from the main repo and from Janus product logic
- produce a practical Go/No-Go result instead of a broad infrastructure rollout

Rules:
- only edit files inside this directory
- no commit
- no push
- no release action
- no file creation outside this directory
- no attempts to "improve" unrelated repo files

Expected artifacts:
- `worker_task.md`
- `allowed_files.txt`
- `target_doc.md`
- `worker_report.md`
- `test_output.log`

Success bar:
- the worker changes only the allowlisted target file
- the resulting document is visibly cleaner and more useful
- the run is reviewable via diff plus report/log
