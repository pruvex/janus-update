Produce one bounded proposal-only unified diff patch for janus-executioner.
This is read-only proposal work.
Work in one pass.
Do not claim completion.
Do not output analysis, bullets, or commentary.
Do not describe git commands.
If you cannot produce a safe bounded patch, output exactly: BLOCKED: <reason>

Target Task: BACKLOG-110
Precheck Status: PRE-CHECK PASSED
Delegation Question: Produce one bounded patch candidate that routes residence-style facts into the address field and upgrades existing affected contacts without broad address-book redesign.
Max touched files: 4
You may inspect only these files if needed, then immediately output the patch:
- backend/services/contact_manager.py
- backend/data/crud.py
- backend/tests/test_contact_manager.py
- backend/tests/test_contact_card_normalization.py

Patch rules:
- Return exactly one unified diff patch only.
- Start with --- a/<path> and +++ b/<path>.
- Touch only allowed files.
- Keep the patch as small as possible.
- Prefer the smallest backend-first fix.
- Do not widen scope to schema redesign or unrelated memory behavior.

Codex validation after review:
- python -m pytest backend/tests/test_contact_manager.py -q
- python -m pytest backend/tests/test_contact_card_normalization.py -q
- python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py

Manual validation ownership stays with Codex:
Codex must still request manual Janus address-book verification after local checks if visible rendering behavior changes.

Compact task brief:
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
