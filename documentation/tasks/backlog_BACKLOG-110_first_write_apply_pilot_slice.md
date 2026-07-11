TASK-BACKLOG-110-W1
- Source: `documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md`
- Backlog Item: `BACKLOG-110`
- Feature: First bounded execution_write_apply_candidate pilot slice for residence-to-address mapping
- Generated At: 2026-06-19

## Generated Tasks

### TASK-BACKLOG-110-W1 Route new explicit residence facts into the structured address path without widening into cleanup or UI follow-up
- Ziel:
  - Prove the first bounded `execution_write_apply_candidate` live pilot on a very small real backend slice by routing newly observed explicit residence facts like `wohnt in <Ort>` into the structured address path instead of `personal_details`.
- Scope:
  - Touch only the smallest backend mapping seam needed for new residence-style facts plus the focused regression coverage that proves the mapping.
  - Keep the first pilot backend-only.
  - Do not include cleanup of already affected contacts, UI/card rendering follow-up, broader address normalization, contact-schema redesign, or unrelated memory/proposal behavior.
- Files:
  - `backend/services/contact_manager.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/data/crud.py` only if strictly required to complete the bounded new-fact mapping seam
  - `backend/tests/test_contact_card_normalization.py` only if strictly required to prove backend-visible normalization without touching UI code
- Steps:
  1. Localize the exact backend branch where explicit residence facts are currently mapped into `personal_details` instead of the structured address path.
  2. Route only new explicit residence facts into the existing address field/path while preserving true personal details such as `vegetarier`.
  3. Add the smallest focused regression coverage that proves residence facts land in the address-oriented path and non-address details stay in `Besonderheiten`.
  4. Keep the pilot inside one backend file cluster and reject any widening into cleanup migration, frontend work, or broader contact-model decisions.
- Acceptance Criteria:
  - New explicit residence facts like `wohnt in <Ort>` no longer land in `personal_details`/`Besonderheiten`.
  - Genuine non-address details such as `vegetarier` remain in `personal_details`/`Besonderheiten`.
  - The bounded pilot can be validated from backend behavior alone without any frontend change.
  - No cleanup/migration of already affected contacts is mixed into this first write-capable pilot slice.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q` only if this file is actually touched for backend-visible normalization proof
  - `python -m py_compile backend/services/contact_manager.py backend/tests/test_contact_manager.py`
  - `python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py` only if those optional files are touched
- Model: 5.4
- Reason:
  - This is the cleanest first live write-capable pilot candidate currently available: a real prechecked Janus backend task with a narrow semantic seam, conservative regression target, and no need to widen into frontend, migration, provider, auth, or release boundaries.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-110
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-110_first_write_apply_pilot_slice.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/tasks/backlog_BACKLOG-110_preimplementation_check.md
  - documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md
  - documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
  - documentation/codex/model-routing/execution_write_apply_candidate_readiness_gate_2026-06-19.md
- Dropped Context:
  - broader `BACKLOG-110` cleanup or existing-contact migration work
  - frontend/address-card presentation follow-up unless a later separate slice proves necessary
  - unrelated contact-memory recall debugging and OR family comparison history
