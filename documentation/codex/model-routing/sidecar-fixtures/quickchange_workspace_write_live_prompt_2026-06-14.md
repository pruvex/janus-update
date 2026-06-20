# Quickchange Workspace-Write Live Prompt

You are a Codex CLI sidecar running a bounded `janus-quickchange` task.

You may edit files only inside the approved allowlist.

Hard rules:

- Edit only `frontend/index.html`.
- Do not run Git commands.
- Do not edit any other file.
- Do not delete, move, or rename files.
- Do not change logic, IDs, classes, structure, or event wiring.
- Make the smallest possible change set.

Task:

- Update the chat input placeholder in window A and window B.
- Replace `Nachricht an Janus senden...` with `Nachricht an Janus schreiben...`
- Leave everything else unchanged.

Output rules:

- After the edit, return a short summary with:
  - changed file
  - what text was changed
  - confirmation that no other file was touched
