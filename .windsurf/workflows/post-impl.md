---
description: Post-implementation checklist - fill audit trail, update inventory, backward-reference, update changelog, run tests
---

## Steps

1. Ask the user which task was just implemented (task number or filename from `documentation/tasks/`).

2. Read the task file from `documentation/tasks/`.

3. Fill **Section 6 (Ergebnis & Audit-Trail)** with:
   - Files changed (list with brief description per file)
   - What was done (1-2 sentences)
   - Test result (pass/fail + command used)

4. Fill **Section 7 (Debugging-Log)** with:
   - Any issues encountered during implementation
   - Write "Keine Probleme." if implementation was clean

5. **Backward-Referencing:** Read the "Beeinflusst" list from Section 2. For each referenced task:
   - Open that task file
   - Add a note in its Section 2 under "Beeinflusst": `→ Modified by task_<NR>: <short description>`

6. **Update Inventory:** Read `documentation/04_PROJECT_INVENTORY_AND_STATUS.md` and add/update the entry for this task's component (Skill-ID, Status, Domain, Capabilities).

7. **Update PROJECT_STATE.md:** Add a new row to SECTION 2 (SESSION_LOG) with:
   - Zeitstempel (today)
   - Task-ID
   - Editor (model used)
   - Ergebnis (DONE + summary)
   - Notizen (brief description of what was done)

8. **Update 01_CENTRAL_TASK_REGISTRY.md:** Update the Macro-Dashboard row for this task:
   - Set Status to DONE
   - Fill Ergebnis column
   - If Epic progress changed, update the Epic section

9. **Update CHANGELOG.md:** Add a new entry under [Unreleased] with:
   - Category (Added/Changed/Deprecated/Removed/Fixed/Security)
   - Brief description of the change (1-2 sentences)
   - Reference the task number if applicable

// turbo
10. Run regression tests: `python -m pytest backend/tests -q`

11. Report final status:
    - `POST-IMPL COMPLETE: task_<NR> audit trail filled, inventory updated, PROJECT_STATE synced, backward-refs done, changelog updated, tests <PASS/FAIL>`
