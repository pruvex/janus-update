BACKLOG-115
- Backlog Item: `BACKLOG-115`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-30

## Task

### BACKLOG-115 Sichtbare Oliver-Dubletten und Haustierdetail-Rauschen auf der Kontaktkarte bereinigen
- Ziel:
  - Stelle sicher, dass die relevante Kontaktansicht fuer `Oliver Schwab` keine leeren historischen Dubletten mehr als normale Oliver-Kontakte zeigt und dass Tasso/Garfield-Details nur noch einmal in sauber normalisierter Form erscheinen.
- Scope:
  - Touch only the existing contact-selection, contact-normalization, and address-book presentation paths needed to suppress empty duplicate Oliver rows and dedupe or normalize noisy pet details on the visible contact card.
  - Include a bounded cleanup or read-normalization path for already affected live contacts when strictly needed.
  - Do not redesign the broader contact model, memory architecture, or unrelated recall/response behavior.
- Files:
  - `backend/services/contact_manager.py`
  - `backend/data/crud.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_contact_card_normalization.py`
  - existing address-book UI file(s) only if a small visibility fix is strictly needed after backend cleanup
- Steps:
  1. Trace why multiple `Oliver Schwab` contacts can still surface in the visible address-book view even though earlier slices already preferred the richest contact for pet-detail updates.
  2. Ensure the relevant visible contact path suppresses or cleanly ignores empty historical Oliver duplicates instead of presenting them as normal contacts.
  3. Tighten pet-detail normalization so near-duplicate variants like `gern` versus `gerne` and tautological Garfield lines do not survive beside the cleaner owner- or pet-specific detail.
  4. Add focused regression coverage for visible contact selection and normalized pet-detail output on the Oliver/Tasso/Garfield card.
- Acceptance Criteria:
  - The relevant address-book view exposes only one valid `Oliver Schwab` contact or otherwise suppresses empty historical duplicates from normal user-visible contact selection.
  - Tasso and Garfield details do not appear multiple times in near-identical wording variants such as `gern` versus `gerne`.
  - Tautological details such as `Katze Garfield ist eine katze` do not remain when a better owner- or pet-specific sentence already exists.
  - Existing correct owner-facing details and recall behavior are not regressed by the cleanup.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q`
  - `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`
- Model: 5.4
- Reason:
  - Small, visible address-book cleanup follow-up on an already known Oliver/Tasso/Garfield seam with clear acceptance criteria and bounded risk.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-115
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-115_oliver_kontaktkarte_zeigt_duplikate_und_unsaubere_haustierdetails.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/backlog/BACKLOG.md
  - documentation/ai/CURRENT_STATE.md
  - documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
  - documentation/tasks/backlog_BACKLOG-110_kontakt_wohnort_landet_als_besonderheit_statt_im_adressblock.md
  - documentation/tasks/backlog_BACKLOG-111_kontaktfakt_feedback_und_bereits_bekannt_rueckmeldung.md
- Dropped Context:
  - unrelated READY backlog items
  - broad OR rollout context
  - older DONE history outside the Oliver/Tasso/Garfield contact-card seam
