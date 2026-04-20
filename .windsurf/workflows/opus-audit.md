---
description: Prepare a scoped Opus audit block - gather changed files, build scope, format handover for Claude
---

## Steps

1. Ask the user:
   - Which task or feature is being audited?
   - What is the audit focus? (e.g. "Thread-Safety", "Error Handling", "Type Consistency")

2. Read the task file from `documentation/tasks/` to get the list of betroffene Dateien.

// turbo
3. Run `git diff --name-only HEAD~5` to find recently changed files in `backend/`.

4. Cross-reference: task files + git diff → build the final audit file list.

5. For each file in the audit list, read it and note:
   - Total lines
   - Key functions/classes

6. Generate the **Opus Handover Block** in this exact format:

```
Modell: Opus 4.6 Thinking
Thread: → 🏛️ [Epic-Name] fortsetzen

AUDIT SCOPE:
- Prüf-Dateien: [exact file list with line counts]
- Prüf-Fokus: [user-specified focus]
- Ignorieren: [files NOT in scope, e.g. tests, migrations, config]

AUDIT REGELN (Sektion 9.3):
- NUR Issues (nummeriert, mit Datei:Zeile)
- NUR Fix-Anweisungen (copy-paste-fähig)
- NUR Severity (CRITICAL / MEDIUM / LOW)
- KEIN Lob, KEINE Erklärungen, KEINE Zusammenfassungen

KONTEXT:
[Brief summary of what was changed and why, from task file]
```

7. Output the block so the user can copy-paste it into the Claude thread.
