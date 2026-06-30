# Aider/OpenRouter Isolated Worker POC

This is the second bounded worker POC for Janus.

Purpose:
- keep the worker run outside the repository root
- verify that Aider can still complete a tiny docs-only task
- treat any repo-root side effect as a failure signal

Rules:
- run Aider only inside a temporary workspace outside the repo
- allow exactly one target file edit
- no commit
- no push
- no release action
- no repo-root `.aider*` artifacts
- no `.gitignore` mutations

Expected artifacts:
- `worker_task.md`
- `allowed_files.txt`
- `target_doc.md`
- `run_isolated_worker.ps1`
- `worker_report.md`
- `test_output.log`

Success bar:
- Aider edits only `target_doc.md`
- the edited document is clearly improved
- the repo root stays free of new `.aider*` artifacts
- `.gitignore` remains untouched by the run
