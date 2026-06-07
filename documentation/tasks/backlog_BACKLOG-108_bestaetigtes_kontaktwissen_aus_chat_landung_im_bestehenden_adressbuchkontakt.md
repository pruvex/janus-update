BACKLOG-108
- Backlog Item: `BACKLOG-108`
- Source: `documentation/backlog/BACKLOG.md`
- Generated At: 2026-06-07

## Task

### BACKLOG-108 Bestaetigtes Kontaktwissen aus Chat im bestehenden Adressbuchkontakt persistieren
- Ziel:
  - Stelle sicher, dass bestaetigtes Kontaktwissen aus dem Chat bei eindeutig erkanntem bestehendem Kontakt nicht nur im Memory-/Chat-Kontext bleibt, sondern konsistent in den bestehenden Kontaktpersistenzpfad gelangt oder als sauberer Kontakt-Update-Vorschlag behandelt wird.
- Scope:
  - Touch only the existing chat-orchestration, contact-memory coupling, and contact persistence paths needed to close the confirmed-contact-fact gap for existing contacts.
  - Do not redesign the address-book data model, broaden private-contact proposal behavior, or introduce aggressive auto-mutation for ambiguous chat statements.
- Files:
  - `backend/services/chat_orchestrator.py`
  - `backend/services/contact_manager.py`
  - `backend/services/memory_extractor.py`
  - `backend/tools/memory_tools.py`
  - `backend/data/crud.py`
  - `backend/tests/test_contact_manager.py`
  - `backend/tests/test_memory_tools.py`
  - `backend/tests/test_memory_write_update_conflict_handling.py`
- Steps:
  1. Trace the current confirmed-contact-fact flow for an already known contact from chat interpretation through Memory/contact write handling and identify where persistence stops.
  2. Ensure clear confirmed contact facts for an already matched existing contact land in the correct contact update path or explicit reviewable proposal path instead of remaining Memory-only.
  3. Prevent Janus from claiming a contact fact is firmly remembered when it has not reached the intended contact persistence or proposal state.
  4. Add focused regression coverage for the confirmed existing-contact path, including ambiguity-safe behavior and no silent overreach on unclear statements.
- Acceptance Criteria:
  - When an existing contact is clearly matched in chat and the user confirms a direct personal fact such as a preference, dislike, or Besonderheit, the fact reaches the existing address-book contact through the approved persistence or proposal path.
  - Janus no longer states that a contact fact is firmly stored when it only exists in Memory/chat context and has not reached contact persistence.
  - Ambiguous or weak chat statements do not trigger aggressive silent contact mutation.
- Tests:
  - `python -m pytest backend/tests/test_contact_manager.py -q`
  - `python -m pytest backend/tests/test_memory_tools.py -q`
  - `python -m pytest backend/tests/test_memory_write_update_conflict_handling.py -q`
  - `python -m py_compile backend/services/chat_orchestrator.py backend/services/contact_manager.py backend/services/memory_extractor.py backend/tools/memory_tools.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_memory_tools.py backend/tests/test_memory_write_update_conflict_handling.py`
- Model: 5.4
- Reason:
  - Small but persistence-sensitive bugfix on an existing contact/memory path with clear acceptance criteria and bounded backend regression evidence.

HANDOFF_SCOPE:
- Backlog Item: BACKLOG-108
- Entry Point: PRE_IMPLEMENTATION_VERIFICATION
- Required Artifact: documentation/tasks/backlog_BACKLOG-108_bestaetigtes_kontaktwissen_aus_chat_landung_im_bestehenden_adressbuchkontakt.md
- Required Next Skill: janus-preimplementation-check
- Evidence Paths:
  - documentation/backlog/BACKLOG.md
  - documentation/SPEC/Spec Done/15_semi_automatisches_adressbuch_mit_memory_kopplung.md
  - documentation/tasks/TASK-SPEC15.4_preimplementation_check.md
  - documentation/tasks/TASK-SPEC15.4_execution_result.md
- Dropped Context:
  - unrelated DONE backlog history
  - Spec-15 tasks outside the existing-contact memory/contact persistence seam
