---
description: Phase 4.0 pre-implementation verification - read task file and validate Impact-Analyse before any code changes
---

## Steps

1. Ask the user which task to verify (task number or filename from `documentation/tasks/`).

2. Read the task file from `documentation/tasks/task_<input>.md`.

3. Validate Section 2 (Impact-Analyse):
   - **Basiert auf:** Must not be empty or "[welche...]"
   - **Beeinflusst:** Must not be empty or "[welche...]"
   - **Risiko-Einschätzung:** Must be LOW, MEDIUM, or HIGH

4. If any field is incomplete:
   - Report: `PRE-CHECK FAILED: Section 2 incomplete`
   - List which fields need filling
   - Do NOT proceed with implementation

5. If all fields are valid:
   - Report: `PRE-CHECK PASSED`
   - Summarize: Ziel, betroffene Dateien, Risiko
   - State: "Implementation may proceed."

6. Read referenced "Basiert auf" tasks and verify they are marked as completed in their Section 6.
