SKILL 5 DEBUG ADDENDUM: CONTACT APPLY NORMALIZATION

Canonical State: NEEDS RETEST
Failure Code: `CONTACT_FACT_STATEMENT_CONTACT_APPLY_NORMALIZATION_GAP`

Summary:
- A new live run showed that the earlier routing/pronoun fixes improved behavior: `Oliver Schwab wohnt in Koeln-Stammheim` no longer fell back to the old unverifiable-knowledge answer, and `und er hat einen Hund` was acknowledged instead of being blocked as ambiguous.
- The remaining defect was not top-level routing. The dog fact did not land cleanly in the address book, and the saved address became malformed because the evidence text for the dog fact still contained the earlier residence sentence as quoted context.

Root Cause:
- `backend/services/contact_manager.py` still allowed a generic address parser to react to embedded `wohnt in ...` text inside evidence-context strings.
- The pet-detail path could therefore confirm the fact while accidentally backfilling residence text into the contact address field.
- `Haustier-Details` also needed an explicit structured mapping into contact `personal_details`.

Fix Summary:
- `backend/services/contact_manager.py` now limits generic address parsing to explicit `adresse` / `anschrift` phrasing.
- `backend/services/contact_manager.py` now uses a dedicated direct residence pattern for genuine `wohnt in ...` facts.
- `backend/services/contact_manager.py` now sanitizes trailing quote/parenthesis artifacts and maps pet facts such as `hat einen Hund` into structured contact `personal_details`.
- `backend/data/crud.py` now applies the same address sanitizer during contact normalization so malformed stored address suffixes are cleaned and persisted on read.

Validation:
- `python -m py_compile backend/services/contact_manager.py backend/data/crud.py backend/tests/test_contact_manager.py backend/tests/test_contact_card_normalization.py`: PASS
- `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS
- `python -m pytest backend/tests/test_contact_manager.py -q`: PASS
- Direct local DB verification after repair: PASS
  - `Oliver Schwab` address normalized
  - `hat einen Hund` present in `personal_details`

Follow-up Verb Coverage:
- A later live retest showed that `und er besitzt einen Hund` still bypassed the older `hat einen Hund` heuristics and fell back to the unverifiable-facts response.
- The local fix now extends fact-telling recognition, contact-extraction candidate selection, and pet-detail normalization to the verb form `besitzt`.
- Additional checks:
  - `python -m py_compile backend/services/orchestrator/intent_engine.py backend/services/chat/tool_selector.py backend/services/contact_manager.py backend/tests/test_calendar_routing_fix.py backend/tests/test_tool_selector_contact_routing.py backend/tests/test_contact_manager.py`: PASS
  - `python -m pytest backend/tests/test_calendar_routing_fix.py::TestContactKnowledgeRecallIntent::test_pronoun_contact_fact_followup_with_besitzt_bypasses_ambiguity_clarification backend/tests/test_tool_selector_contact_routing.py::test_retrieve_candidates_adds_contact_extraction_for_pet_follow_up_with_besitzt backend/tests/test_contact_manager.py::test_pet_detail_memory_with_besitzt_updates_existing_contact_personal_details -q`: PASS
  - `python -m pytest backend/tests/test_contact_manager.py -q -k "pet_detail"`: PASS

Pet-Name Sync Follow-up:
- A later live run showed a narrower persistence gap: the dog name was stored in memory (`Olis hund heißt tasso` / `Tasso ist der hund von oli`), but it did not automatically appear in the address-book contact.
- Root cause: extractor-created pet-detail memories can carry a valid contact alias in `subject_name` while still missing `subject_role=contact`. Those rows were saved, but the extractor only triggered contact sync when `subject_role` was already `contact`.
- Local fix:
  - `backend/services/memory_extractor.py` now attempts contact sync for contact-like memory categories when a usable subject name exists, even if `subject_role` is missing.
  - guarded exclusions remain for `user`, `unbekannt`, and explicit `pet:*` subjects.
- Additional checks:
  - `python -m py_compile backend/services/memory_extractor.py backend/tests/test_contact_manager.py`: PASS
  - `python -m pytest backend/tests/test_contact_manager.py::test_fact_extractor_syncs_pet_name_detail_even_when_subject_role_is_missing backend/tests/test_contact_manager.py::test_pet_detail_memory_updates_existing_contact_personal_details backend/tests/test_contact_manager.py::test_pet_detail_memory_with_besitzt_updates_existing_contact_personal_details backend/tests/test_contact_manager.py::test_pet_detail_evidence_text_does_not_backfill_residence_address -q`: PASS
- Local DB repair verification:
  - memory row `Olis hund heißt tasso` now applies cleanly to `Oliver Schwab`
  - contact details now include `Olis hund heißt tasso`

Pet-Detail Formatting Follow-up:
- A later live user run showed that persistence was functionally improved, but final address-book wording was still fragmented across multiple lines such as `hat einen Hund`, `Olis hund heißt tasso`, `Oli hat auch eine katze`, and `hat eine Katze`.
- Local fix:
  - `backend/data/crud.py` now normalizes named pet details into one sentence, e.g. `Olis hund heißt tasso` -> `hat einen Hund namens tasso`.
  - owner-prefixed generic variants such as `Oli hat auch eine katze` now normalize down to `hat eine Katze`.
  - generic duplicates are dropped when a stronger named variant for the same pet already exists.
- Additional checks:
  - `python -m py_compile backend/data/crud.py backend/tests/test_contact_card_normalization.py`: PASS
  - `python -m pytest backend/tests/test_contact_card_normalization.py -q`: PASS, 5 passed
- Expected final contact-card wording for the current Oliver/Oli case:
  - `hat einen Hund namens tasso`
  - `hat eine Katze`

Retest Gate:
- Restart Janus/backend and retry:
  - `Oliver Schwab wohnt in Koeln-Stammheim`
  - `und er besitzt einen Hund`
  - `Oliver Schwab wohnt in Koeln-Stammheim`
  - `und er hat einen Hund`
- Optional formatting retest:
  - `oli hat auch eine katze`
- Optional focused pet-name retest:
  - `Olis hund heißt tasso`
- Expected result:
  - no `keine verifizierten Fakten`
  - no pronoun clarification
  - address-book persistence contains both residence and compact pet-detail wording
  - no malformed address suffix
