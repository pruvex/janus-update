BACKLOG-110 PRE-CHECK
- Backlog Item: `BACKLOG-110`
- Task Artifact: `documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md`
- Generated At: 2026-06-09

## Decision

PRE-CHECK PASSED

## Bound Scope

- The task is atomic enough for execution.
- The primary defect is already localized in the current backend contact-mapping path:
  - `backend/services/contact_manager.py` currently turns residence facts like `wohnt in <Ort>` into `personal_details` instead of the structured `address` field.
  - `backend/data/crud.py` currently normalizes and dedupes `personal_details`, but does not upgrade residence-style values into the address field.
- Existing UI grouping from the address-book surface should already render `address` near the top, so frontend edits are not required unless a tiny follow-up presentation fix becomes unavoidable after backend normalization.

## Required Files

- `backend/services/contact_manager.py`
- `backend/data/crud.py`
- `backend/tests/test_contact_manager.py`
- `backend/tests/test_contact_card_normalization.py`

## Optional Only If Needed

- `backend/data/contact_schemas.py`
- existing address-book UI files under `frontend/src` only if the backend fix proves insufficient for visible grouping

## Execution Notes

1. Route new residence facts into `address` instead of `personal_details`.
2. Add a bounded cleanup/read-normalization path that upgrades existing `wohnt in <Ort>` details into `address`.
3. Preserve genuine personal details like `vegetarier`.
4. Keep the change off unrelated memory-recall, proposal, and broader address-book redesign logic.

## Acceptance Focus

- `Oliver Schwab`-style residence data appears in the address block, not under `Besonderheiten`.
- `vegetarier` remains a `Besonderheit`.
- Existing affected contacts are upgraded without broad data-model churn.

## Tests

- `python -m pytest backend/tests/test_contact_manager.py -q`
- `python -m pytest backend/tests/test_contact_card_normalization.py -q`
- `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`

## Risks

- Low risk if execution stays backend-scoped.
- Main seam risk is over-migrating free-text detail strings that only look address-like; implementation should stay conservative and target explicit `wohnt in` residence facts.

## Execution Handoff

- Entry Point: `PRE_IMPLEMENTATION_VERIFICATION`
- Required Next Skill: `janus-executioner`
- Target Task: `BACKLOG-110`
- Recommended Model: `5.4`
- Recommended Intelligence: `medium`

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-110
- Precheck Artifact: documentation/tasks/backlog_BACKLOG-110_preimplementation_check.md
- Target Task: BACKLOG-110
- Keep:
  - residence-to-address mapping seam
  - backend-only default plan
  - bounded cleanup for existing contacts
- Drop:
  - unrelated contact-memory recall debugging
  - DB-backup feature work
  - broader address-book redesign history
