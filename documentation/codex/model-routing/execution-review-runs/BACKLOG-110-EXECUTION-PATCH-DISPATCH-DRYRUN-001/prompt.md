You are producing a bounded proposal-only execution patch candidate for janus-executioner.
This is read-only proposal work. Do not claim completion. Do not describe git commands. Do not add prose outside the patch.

Target Task: BACKLOG-110
Precheck Status: PRE-CHECK PASSED
Spec Path: documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md
Delegation Question: Produce one bounded patch candidate that routes residence-style facts into the address field and upgrades existing affected contacts without broad address-book redesign.
Max touched files: 4
Allowed files:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/tests/test_contact_manager.py
- backend/tests/test_contact_card_normalization.py

Required validation hints for Codex after review:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py

Manual validation ownership stays with Codex:
Codex must still request manual Janus address-book verification after local checks if visible rendering behavior changes.

Output rule:
- Return exactly one unified diff patch only.
- Start with --- a/<path> and +++ b/<path>.
- Touch only allowed files.
- Keep the patch as small as possible.
- If you cannot produce a safe bounded patch, return exactly one line: BLOCKED: <reason>

Bound task excerpt:
BACKLOG-110
- Backlog Item: `BACKLOG-110`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-09

## Task

### BACKLOG-110 Kontakt-Wohnort aus Besonderheiten in den Adressblock ueberfuehren
- Ziel:
  - Stelle sicher, dass Wohnort-/Adressfakten wie `wohnt in Köln Stammheim` fuer Privatkontakte nicht als `Besonderheit` persistiert oder dargestellt werden, sondern im strukturierten Adressfeld des Kontakts landen.
- Scope:
  - Touch only the existing contact update, normalization, and address-book rendering paths needed to move residence-style facts from `personal_details` into the address/address-like contact field.
  - Include a bounded cleanup or read-normalization path for already affected contacts like `Oliver Schwab`.
  - Do not redesign the broader contact model, proposal architecture, or unrelated memory-recall behavior.
- Files:
  - `backend/services/contact_manager.py`
  - `backend/data/crud.py`
  - `backend/data/contact_schemas.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_contact_card_normalization.py`
  - `frontend/src` or existing address-book UI files only if a small presentation fix is strictly needed after backend normalization
- Steps:
  1. Trace where residence facts like `wohnt in <Ort>` are currently mapped into `personal_details` instead of the structured address/contact field.
  2. Route new residence-style contact facts into the correct address field for private contacts while preserving true personal details such as `vegetarier`.
  3. Add a bounded normalization or cleanup path so existing affected contacts are upgraded from `Besonderheiten` into the address block.
  4. Add focused regression coverage for residence mapping, cleanup, and visible card grouping.
- Acceptance Criteria:
  - Contact facts like `wohnt in <Ort>` are no longer persisted as `personal_details`/`Besonderheiten` when they represent residence/address data.
  - Existing affected contacts are upgraded so the residence appears in the address block instead of under `Besonderheiten`.
  - Genuine details such as `vegetarier` remain in `Besonderheiten`.
  - The contact card shows the residence near the top contact data rather than in the personal details section.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q`
  - `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/data/contact_schemas.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`
- Model: 5.4
- Reason:
  - Small, bounded contact-model and UI-mapping bug with clear acceptance criteria and low risk.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-110
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/backlog/BACKLOG.md
  - documentation/tasks/TASK-SPEC15_semi_automatisches_adressbuch_mit_memory_kopplung.md
  - documentation/tasks/TASK-SPEC16_adressbuch_karten_redesign_und_spitzname_besonderheiten.md
- Dropped Context:
  - unrelated DONE backlog history
  - broader contact-memory recall contamination debugging
  - unrelated address-book redesign work outside residence/address mapping
