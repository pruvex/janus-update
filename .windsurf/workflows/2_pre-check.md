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

4. If any field is incomplete, first determine whether the issue is purely structural/formal.

   Allowed automatic fixes:
   - If Section 2 exists but is not named `Impact-Analyse`, preserve its content by renaming it to `# 2.1 ...` and insert a new `# 2️⃣ Impact-Analyse` before it.
   - If `Basiert auf` is missing but `source_spec` exists in frontmatter, fill it from `source_spec`.
   - If `Basiert auf` is missing and no dependency/source is inferable, fill `Keine`.
   - If `Beeinflusst` is missing but affected files/modules are listed under Codebase Alignment, Implementation Plan, Existing Modules, Files, or similar sections, extract those file/module paths.
   - If `Risiko-Einschätzung` is missing but a Risk Register exists, map the highest risk to `LOW`, `MEDIUM`, or `HIGH`.
   - If risk is written in German, normalize `NIEDRIG`/`LOW`, `MITTEL`/`MEDIUM`, `HOCH`/`HIGH` to `LOW`, `MEDIUM`, or `HIGH`.

   Auto-fix limits:
   - Do NOT invent missing architecture decisions.
   - Do NOT change acceptance criteria.
   - Do NOT add or remove implementation scope.
   - Do NOT mark dependencies as completed.
   - Do NOT proceed if values cannot be inferred from the task file itself.
   - Do NOT auto-fix contradictions between sections; report them as blockers.

5. After an allowed automatic fix:
   - Write the corrected task file.
   - Report: `PRE-CHECK AUTO-FIX APPLIED`
   - Summarize exactly what was changed.
   - Re-run Section 2 validation from step 3.

6. If any field is still incomplete after allowed auto-fix, or if the issue is not purely formal:
   - Report: `PRE-CHECK FAILED: Section 2 incomplete`
   - List which fields need filling
   - Do NOT proceed with implementation

7. If all fields are valid:
   - Report: `PRE-CHECK PASSED`
   - Summarize: Ziel, betroffene Dateien, Risiko
   - State: "Implementation may proceed."

8. Read referenced "Basiert auf" tasks and verify they are marked as completed in their Section 6.
